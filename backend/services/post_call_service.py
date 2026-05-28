import os
import requests
import json
import re
from datetime import datetime, timedelta
import logging
from services import tabbly, cal, supabase_service
import google.generativeai as genai

logger = logging.getLogger(__name__)

# Global configurations removed to ensure strict database-driven credentials
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
    
    now_ist = datetime.utcnow() + timedelta(hours=5, minutes=30)
    current_date_str = now_ist.strftime("%Y-%m-%d")
    current_time_str = now_ist.strftime("%I:%M %p")

    prompt = f"""
You are an expert AI system for extracting and CORRECTING meeting details from noisy, multi-language call transcripts.

IMPORTANT CONTEXT:
- TODAY'S DATE: {current_date_str}
- CURRENT TIME: {current_time_str}

The transcript may include:
- Speech recognition errors
- Hindi + English mixing
- Multiple corrections by the user
- Spelled-out email characters
- Repeated wrong attempts

------------------------
CRITICAL RULES:
------------------------

1. EMAIL RECONSTRUCTION (VERY IMPORTANT):
- The user may provide the email multiple times with mistakes.
- DO NOT rely only on the last attempt.
- Collect ALL email attempts from the transcript.
- Combine and analyze all attempts to reconstruct the MOST LIKELY correct email.

Use:
- Frequency (what appears most)
- Similarity (closest matching words)
- Context (common names/domains)

Example:
"bimel", "vimel", "vimal" → "vimal"  
"manhinfteeh", "manta infotech", "mansainfotech" → "mansainfotech"

FINAL EMAIL = best username + best domain

------------------------

2. EMAIL NORMALIZATION:
Convert:
- "at", "at the rate" → "@"
- "dot" → "."
- "underscore" → "_"
- "dash" → "-"
- remove spaces

------------------------

3. SPELLING HANDLING:
Join sequences like:
"v i m a l" → "vimal"

------------------------

4. LANGUAGE NORMALIZATION:
Convert Hindi words to English phonetics:
- "विमल" → "vimal"
- "मंसा infotech" → "mansainfotech"

------------------------

5. ERROR CORRECTION:
Fix ASR mistakes intelligently using ALL attempts:
- manhinfteeh → mansainfotech
- manta infotech → mansainfotech

------------------------

6. VALIDATION:
Final email MUST:
- follow format: name@domain.com
- contain no spaces
- be logically consistent

If multiple possibilities exist, choose the MOST PROBABLE one.

If still ambiguous, return null.

------------------------

7. DATE & TIME:
- Resolve relative dates ("tomorrow", "today", "next monday") relative to TODAY ({current_date_str}).
- The date MUST be in the future (on or after {current_date_str}).
- Convert time to: HH:MM AM/PM

------------------------

TRANSCRIPT:
{transcript}

------------------------

OUTPUT (STRICT JSON):
{{
    "full_name": "...",
    "email": "...",
    "scheduled_date": "YYYY-MM-DD",
    "scheduled_time": "HH:MM AM/PM",
    "meeting_topic": "...",
    "interested": true/false
}}
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

def process_call_results(call_id, retries=15, delay=30, agent_id=None, user_id=None, skip_sleep=False):
    """
    Called after a call ends. Fetches results from Tabbly, 
    parses them, and books on Cal.com if interested.
    Includes retries as Tabbly takes time to generate JSON output.
    """
    print(f"\n[POST_CALL] 🚀 Proactive processing scheduled for Call ID: {call_id} (Agent: {agent_id})")
    if not skip_sleep:
        print(f"[POST_CALL] ⏳ Waiting 120s (2 mins) for the conversation to finish before checking results...")
        time.sleep(120) 
    
    logger.info(f"Processing post-call results for Call ID: {call_id}")
    
    for attempt in range(retries):
        print(f"[POST_CALL] ⏳ Attempt {attempt + 1}/{retries} - Checking Tabbly for updates...")
        
        # 1. Fetch the call details from Tabbly
        call_logs = tabbly.fetch_call_logs_by_id(call_id)
        if not call_logs:
            print(f"[POST_CALL] ⚠️ No logs found yet for {call_id}. Waiting {delay}s...")
            time.sleep(delay)
            continue

        log = call_logs[0]

        # Resolve agent_id and user_id dynamically from log and database mappings if not provided
        current_agent_id = agent_id or log.get("use_agent_id") or log.get("agent_id")
        current_user_id = user_id

        if current_agent_id and not current_user_id:
            try:
                from middleware.auth import supabase
                resp = supabase.table('agent_mappings').select('user_id').eq('agent_id', str(current_agent_id)).execute()
                if resp.data:
                    current_user_id = resp.data[0]['user_id']
                    print(f"[POST_CALL] 🔍 Dynamically resolved user_id {current_user_id} for agent {current_agent_id}")
            except Exception as e:
                print(f"[POST_CALL] ⚠️ Error dynamically resolving user_id: {e}")

        # Resolve Cal.com credentials strictly (NO fallback to global environment keys)
        custom_key = None
        custom_eid = None

        if current_user_id:
            try:
                from services.cal import get_valid_cal_token_for_user
                oauth_token = get_valid_cal_token_for_user(current_user_id)
                if oauth_token:
                    custom_key = oauth_token
                    print(f"[POST_CALL] 🔑 Using Cal.com OAuth token for user {current_user_id}")
            except Exception as e:
                print(f"[POST_CALL] ⚠️ Error loading OAuth credentials: {e}")

        if current_agent_id:
            try:
                from middleware.auth import supabase
                resp = supabase.table('agent_mappings').select('*').eq('agent_id', str(current_agent_id)).execute()
                if resp.data:
                    mapping = resp.data[0]
                    if not custom_key and mapping.get('cal_api_key'):
                        custom_key = mapping['cal_api_key']
                    if mapping.get('cal_event_type_id'):
                        custom_eid = mapping['cal_event_type_id']
                    print(f"[POST_CALL] 🔑 Loaded agent-specific Cal.com credentials for agent {current_agent_id}")
            except Exception as e:
                print(f"[POST_CALL] ⚠️ Error fetching agent-specific credentials: {e}")

        if current_user_id and (not custom_key or not custom_eid):
            try:
                profile = supabase_service.get_user_profile(current_user_id)
                if profile:
                    if not custom_key and profile.get('cal_api_key'):
                        custom_key = profile['cal_api_key']
                    if not custom_eid and profile.get('cal_event_type_id'):
                        custom_eid = profile['cal_event_type_id']
                    print(f"[POST_CALL] 🔑 Loaded custom Cal.com credentials from profile for user {current_user_id}")
            except Exception as e:
                print(f"[POST_CALL] ⚠️ Error loading profile credentials: {e}")

        if custom_key and not custom_eid:
            try:
                from services.cal import get_default_event_type_id
                resolved_eid = get_default_event_type_id(custom_key)
                if resolved_eid:
                    custom_eid = resolved_eid
                    print(f"[POST_CALL] 🔑 Dynamically resolved default eventTypeId {custom_eid} for booking")
            except Exception as e:
                print(f"[POST_CALL] ⚠️ Error dynamically resolving eventTypeId: {e}")

        # Validate that we have connected credentials
        if not custom_key or not custom_eid:
            print("[POST_CALL] ❌ Skip: Cal.com calendar is not integrated for this agent/user. Cannot book.")
            if current_user_id:
                supabase_service.log_meeting(
                    current_user_id, 
                    current_agent_id, 
                    call_id, 
                    status="failed", 
                    error_reason="Cal.com calendar not connected or configured"
                )
            return
        
        # --- NEW CHECK: Respect the Meeting Booking Button ---
        raw_identifiers = log.get("custom_identifiers")
        identifiers = str(raw_identifiers or "").lower()
        
        print(f"[POST_CALL] 🏷️ Call Tags: '{identifiers}'")
        
        if "booking:disabled" in identifiers:
            print(f"[POST_CALL] ⏹️ Booking is DISABLED for this call. Ending process.")
            if current_user_id:
                supabase_service.log_meeting(current_user_id, current_agent_id, call_id, status="skipped", error_reason="Booking disabled for this agent")
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
                if current_user_id:
                    supabase_service.log_meeting(current_user_id, current_agent_id, call_id, status="failed", error_reason="AI could not extract an email address", meeting_topic=topic, is_interested=ai_data.get("interested", False))
                return

            email_clean = email_raw.replace("-", "").replace(" ", "").lower()
            parsed_date = parse_date_robust(date_raw)
            parsed_time = parse_time_robust(time_raw)

            # NO FALLBACKS: If date or time is missing, we stop.
            if not parsed_date or not parsed_time:
                print(f"[POST_CALL] ❌ Skip: Missing or invalid Date ({date_raw}) or Time ({time_raw}).")
                if current_user_id:
                    supabase_service.log_meeting(current_user_id, current_agent_id, call_id, status="failed", error_reason=f"Missing Date or Time (Date: {date_raw}, Time: {time_raw})", extracted_email=email_raw, meeting_topic=topic, is_interested=ai_data.get("interested", False))
                return

            # Convert IST to UTC
            dt_ist = datetime.combine(parsed_date, parsed_time)
            dt_utc = dt_ist - timedelta(hours=5, minutes=30)
            start_time_iso = dt_utc.strftime("%Y-%m-%dT%H:%M:%S.000Z")
            print(f"[POST_CALL] ⏰ Scheduled for: {dt_ist} IST ({start_time_iso} UTC)")

            # Pre-flight validations before Cal.com booking API request
            resolved_oauth_token = custom_key if (custom_key and not str(custom_key).startswith("cal_live_")) else None
            resolved_api_key = custom_key if (custom_key and str(custom_key).startswith("cal_live_")) else None
            
            if not custom_eid:
                raise Exception("Missing Cal.com event type ID")
                
            if not resolved_api_key and not resolved_oauth_token:
                raise Exception("Missing Cal.com credentials")
                
            # Detailed debug logging
            logger.info(f"Resolved agent_id: {current_agent_id}")
            logger.info(f"Resolved user_id: {current_user_id}")
            logger.info(f"Resolved event_type_id: {custom_eid}")
            logger.info("OAuth/API credentials loaded successfully")

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
                if current_user_id:
                    supabase_service.log_meeting(current_user_id, current_agent_id, call_id, status="booked", extracted_email=email_clean, meeting_topic=topic, is_interested=ai_data.get("interested", False))
                return
            else:
                error_msg = resp.text
                try:
                    js = resp.json()
                    error_msg = js.get("message") or js.get("error", {}).get("message") or resp.text
                except: pass
                print(f"[POST_CALL] ❌ Cal.com API Error ({resp.status_code}): {error_msg}")
                if current_user_id:
                    supabase_service.log_meeting(current_user_id, current_agent_id, call_id, status="failed", error_reason=f"Cal.com API Error: {error_msg}", extracted_email=email_clean, meeting_topic=topic, is_interested=ai_data.get("interested", False))
                return

        except Exception as e:
            print(f"[POST_CALL] 💥 Critical error during processing: {e}")
            if current_user_id:
                supabase_service.log_meeting(current_user_id, current_agent_id, call_id, status="failed", error_reason=f"Internal Server Error: {str(e)}")
            return
            
    print(f"[POST_CALL] 🛑 Max retries reached for {call_id}. Tabbly did not provide JSON data in time.")
