import os
import requests
import json
import re
from datetime import datetime, timedelta
import logging
from services import tabbly, cal, supabase_service
import google.generativeai as genai

logger = logging.getLogger(__name__)

CAL_API_KEY = os.getenv("CAL_API_KEY")
CAL_EVENT_TYPE_ID = os.getenv("CAL_EVENT_TYPE_ID", "1599599")
CAL_BOOKING_URL = "https://api.cal.com/v2/bookings"

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

def extract_details_from_transcript(transcript):
    """
    Uses Gemini to extract meeting details from the raw transcript.
    Returns: dict with name, email, date, time
    """
    if not GEMINI_API_KEY:
        print("[GEMINI] ⚠️ No GEMINI_API_KEY found. Skipping AI extraction.")
        return {}

    print(f"[GEMINI] 🤖 Analyzing transcript (Length: {len(transcript)} chars)...")
    
    prompt = f"""
    Read the following call transcript and extract meeting booking details.
    
    INSTRUCTIONS:
    1. Use the year 2026 for any dates mentioned without a year.
    2. Extract the email address using ONLY standard English (ASCII) characters. (Example: convert 'साहिल' to 'sahil').
    3. Fix obvious typos (e.g., 'gmal.com' to 'gmail.com').
    4. If the user spelled out the email, join the characters correctly.
    
    Transcript:
    {transcript}
    
    Return ONLY a JSON object with these exact keys:
    {{
        "full_name": "...",
        "email": "...",
        "scheduled_date": "YYYY-MM-DD",
        "scheduled_time": "HH:MM AM/PM",
        "meeting_topic": "...",
        "interested": true/false
    }}
    If any field is missing, use null.
    """
    
    try:
        model = genai.GenerativeModel('gemini-flash-latest')
        response = model.generate_content(prompt)
        # Clean up the response to extract JSON
        text = response.text.replace("```json", "").replace("```", "").strip()
        print(f"[GEMINI] 📦 AI Result: {text}")
        return json.loads(text)
    except Exception as e:
        print(f"[GEMINI] ❌ AI extraction failed: {e}")
        return {}

def parse_date_robust(date_str):
    if not date_str: return None
    date_str = str(date_str).strip()
    for fmt in ["%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y"]:
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue
    
    now = datetime.utcnow()
    clean_date = re.sub(r'(\d+)(st|nd|rd|th)', r'\1', date_str).strip()
    for fmt in ["%B %d", "%b %d", "%B %d %Y", "%b %d %Y"]:
        try:
            parsed = datetime.strptime(clean_date, fmt)
            if "%Y" not in fmt:
                parsed = parsed.replace(year=now.year)
                if parsed.date() < now.date() - timedelta(days=60):
                    parsed = parsed.replace(year=now.year + 1)
            return parsed.date()
        except ValueError:
            pass
    return None

def parse_time_robust(time_str):
    if not time_str: return None
    time_str = str(time_str).strip()
    if "-" in time_str:
        time_str = time_str.split("-")[0].strip()
    elif " to " in time_str.lower():
        time_str = re.split("(?i) to ", time_str)[0].strip()
    time_str = re.sub(r'(?i)(\d)(am|pm)', r'\1 \2', time_str)
    time_str = re.sub(r'(?i)^(\d{1,2})\s+(AM|PM)$', r'\1:00 \2', time_str)
    
    for fmt in ["%I:%M %p", "%H:%M:%S", "%H:%M", "%I %p"]:
        try:
            return datetime.strptime(time_str, fmt).time()
        except ValueError:
            pass
    return None

import time

def process_call_results(call_id, retries=8, delay=30, agent_id=None, user_id=None):
    """
    Called after a call ends. Fetches results from Tabbly, 
    parses them, and books on Cal.com if interested.
    Includes retries as Tabbly takes time to generate JSON output.
    """
    print(f"\n[POST_CALL] 🚀 Proactive processing scheduled for Call ID: {call_id} (Agent: {agent_id})")
    print(f"[POST_CALL] ⏳ Waiting 120s (2 mins) for the conversation to finish before checking results...")
    time.sleep(120) 
    
    logger.info(f"Processing post-call results for Call ID: {call_id}")
    
    # Pre-fetch agent specific credentials if possible
    custom_key = CAL_API_KEY
    custom_eid = CAL_EVENT_TYPE_ID
    
    if agent_id:
        try:
            from middleware.auth import supabase
            resp = supabase.table('agent_mappings').select('*').eq('agent_id', str(agent_id)).execute()
            if resp.data:
                mapping = resp.data[0]
                if mapping.get('cal_api_key'): custom_key = mapping['cal_api_key']
                if mapping.get('cal_event_type_id'): custom_eid = mapping['cal_event_type_id']
                print(f"[POST_CALL] 🔑 Using personalized Cal.com credentials for agent {agent_id}")
        except Exception as e:
            print(f"[POST_CALL] ⚠️ Error fetching special credentials: {e}. Using defaults.")
    
    for attempt in range(retries):
        print(f"[POST_CALL] ⏳ Attempt {attempt + 1}/{retries} - Checking Tabbly for updates...")
        
        # 1. Fetch the call details from Tabbly
        call_logs = tabbly.fetch_call_logs_by_id(call_id)
        if not call_logs:
            print(f"[POST_CALL] ⚠️ No logs found yet for {call_id}. Waiting {delay}s...")
            time.sleep(delay)
            continue

        log = call_logs[0]
        
        # --- NEW CHECK: Respect the Meeting Booking Button ---
        raw_identifiers = log.get("custom_identifiers")
        identifiers = str(raw_identifiers or "").lower()
        
        print(f"[POST_CALL] 🏷️ Call Tags: '{identifiers}'")
        
        if "booking:disabled" in identifiers:
            print(f"[POST_CALL] ⏹️ Booking is DISABLED for this call. Ending process.")
            if user_id:
                supabase_service.log_meeting(user_id, agent_id, call_id, status="skipped", error_reason="Booking disabled for this agent")
            return
        elif "booking:enabled" in identifiers:
            print(f"[POST_CALL] 🏷️ Booking is ENABLED for this call. Proceeding...")
        else:
            print(f"[POST_CALL] ℹ️ No specific booking identifier found. Proceeding as safety fallback.")

        # --- TRANSCRIPT & AI EXTRACTION ---
        transcript = log.get("call_transcript")
        # Proceed only if transcript exists or it's the last attempt
        if not transcript and attempt < retries - 1:
            print(f"[POST_CALL] ⏳ Transcript not yet available for {call_id}. Retrying...")
            time.sleep(delay)
            continue

        print(f"[POST_CALL] ✅ Data located for {call_id}!")
        
        try:
            # Extract Details (STRICTLY using AI from Transcript)
            ai_data = extract_details_from_transcript(transcript) if transcript else {}
            
            name = ai_data.get("full_name") or "Unknown"
            email_raw = ai_data.get("email")
            date_raw = ai_data.get("scheduled_date")
            time_raw = ai_data.get("scheduled_time")
            topic = ai_data.get("meeting_topic") or "General Consultation"
            
            print(f"[POST_CALL] 🔍 MERGED DATA: Name='{name}', Email='{email_raw}', Date='{date_raw}', Time='{time_raw}', Topic='{topic}'")

            if not email_raw:
                print(f"[POST_CALL] ❌ Skip: No email found in transcript. Cannot book.")
                if user_id:
                    supabase_service.log_meeting(user_id, agent_id, call_id, status="failed", error_reason="AI could not extract an email address", meeting_topic=topic, is_interested=ai_data.get("interested", False))
                return

            email_clean = email_raw.replace("-", "").replace(" ", "").lower()
            parsed_date = parse_date_robust(date_raw)
            parsed_time = parse_time_robust(time_raw)

            # NO FALLBACKS: If date or time is missing, we stop.
            if not parsed_date or not parsed_time:
                print(f"[POST_CALL] ❌ Skip: Missing or invalid Date ({date_raw}) or Time ({time_raw}).")
                if user_id:
                    supabase_service.log_meeting(user_id, agent_id, call_id, status="failed", error_reason=f"Missing Date or Time (Date: {date_raw}, Time: {time_raw})", extracted_email=email_raw, meeting_topic=topic, is_interested=ai_data.get("interested", False))
                return

            # Convert IST to UTC
            dt_ist = datetime.combine(parsed_date, parsed_time)
            dt_utc = dt_ist - timedelta(hours=5, minutes=30)
            start_time_iso = dt_utc.strftime("%Y-%m-%dT%H:%M:%S.000Z")
            print(f"[POST_CALL] ⏰ Scheduled for: {dt_ist} IST ({start_time_iso} UTC)")

            # 3. Book via Cal.com
            print(f"[POST_CALL] 📅 Sending booking request to Cal.com for {email_clean}...")
            headers = {
                "cal-api-version": "2024-08-13",
                "Authorization": f"Bearer {custom_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "start": start_time_iso,
                "eventTypeId": int(custom_eid),
                "attendee": {
                    "name": name,
                    "email": email_clean,
                    "timeZone": "Asia/Kolkata",
                    "language": "en"
                },
                "metadata": {
                    "topic": topic
                }
            }
            
            resp = requests.post(CAL_BOOKING_URL, headers=headers, json=payload)
            if resp.status_code in [200, 201]:
                print(f"[POST_CALL] ✅ SUCCESS! Booking confirmed for {email_clean}. Meeting URL: {resp.json().get('data', {}).get('meetingUrl')}")
                if user_id:
                    supabase_service.log_meeting(user_id, agent_id, call_id, status="booked", extracted_email=email_clean, meeting_topic=topic, is_interested=ai_data.get("interested", False))
                return
            else:
                error_msg = resp.text
                try:
                    js = resp.json()
                    error_msg = js.get("message") or js.get("error", {}).get("message") or resp.text
                except: pass
                print(f"[POST_CALL] ❌ Cal.com API Error ({resp.status_code}): {error_msg}")
                if user_id:
                    supabase_service.log_meeting(user_id, agent_id, call_id, status="failed", error_reason=f"Cal.com API Error: {error_msg}", extracted_email=email_clean, meeting_topic=topic, is_interested=ai_data.get("interested", False))
                return

        except Exception as e:
            print(f"[POST_CALL] 💥 Critical error during processing: {e}")
            if user_id:
                supabase_service.log_meeting(user_id, agent_id, call_id, status="failed", error_reason=f"Internal Server Error: {str(e)}")
            return
            
    print(f"[POST_CALL] 🛑 Max retries reached for {call_id}. Tabbly did not provide JSON data in time.")
