import os
import requests
import json
import re
from datetime import datetime, timedelta
import logging
from services import tabbly, cal, supabase_service
# Note: Since the existing project uses Supabase, we can use Supabase or MongoDB. 
# I'll stick to the logic you provided but adapt it for the service layer.

logger = logging.getLogger(__name__)

CAL_API_KEY = os.getenv("CAL_API_KEY")
CAL_EVENT_TYPE_ID = os.getenv("CAL_EVENT_TYPE_ID", "1599599")
CAL_BOOKING_URL = "https://api.cal.com/v2/bookings"

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

def process_call_results(call_id: str, retries: int = 8, delay: int = 30):
    """
    Called after a call ends. Fetches results from Tabbly, 
    parses them, and books on Cal.com if interested.
    Includes retries as Tabbly takes time to generate JSON output.
    """
    print(f"\n[POST_CALL] 🚀 Proactive processing scheduled for Call ID: {call_id}")
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
        
        # --- NEW CHECK: Respect the Meeting Booking Button ---
        # Get raw identifiers and ensure it's a string to avoid crashes
        raw_identifiers = log.get("custom_identifiers")
        identifiers = str(raw_identifiers or "").lower()
        
        print(f"[POST_CALL] 🏷️ Call Tags: '{identifiers}'")
        
        if "booking:disabled" in identifiers:
            print(f"[POST_CALL] ⏹️ Booking is DISABLED for this call. Ending process.")
            return
        elif "booking:enabled" in identifiers:
            print(f"[POST_CALL] 🏷️ Booking is ENABLED for this call. Proceeding...")
        else:
            print(f"[POST_CALL] ℹ️ No specific booking identifier found. Proceeding as safety fallback.")

        json_output_str = log.get("call_json_output")
        
        if not json_output_str:
            print(f"[POST_CALL] ⏳ Call summary/JSON is NOT ready yet for {call_id}. Retrying in {delay}s...")
            time.sleep(delay)
            continue

        print(f"[POST_CALL] ✅ JSON data located for {call_id}!")
        
        # 2. Extract Details
        try:
            # Handle potential markdown wrappers in JSON
            json_output_clean = json_output_str.replace("```json", "").replace("```", "").strip()
            print(f"[POST_CALL] 📦 Raw JSON received: {json_output_clean}")
            data = json.loads(json_output_clean)
            
            # Check for interested status (optional in some schemas)
            interested = data.get("interested", True)
            if str(interested).lower() == "false":
                print(f"[POST_CALL] ⏭️ User marked as NOT interested. Skipping booking.")
                return

            # Robust field extraction (supports various schemas)
            details = data.get("meeting_details") or {}
            
            # Default fallbacks if AI extraction fails
            name = details.get("full_name") or data.get("user_name") or data.get("name") or "Mousam Rakse"
            email_raw = details.get("email") or data.get("user_email") or data.get("email_id") or "mousamrakse@gmail.com"
            date_raw = details.get("scheduled_date") or data.get("meeting_date")
            time_raw = details.get("scheduled_time") or data.get("meeting_time")
            
            print(f"[POST_CALL] 🔍 Parsed Data: Name='{name}', Email='{email_raw}', Date='{date_raw}', Time='{time_raw}'")

            if not email_raw or email_raw.lower() == "unknown@example.com":
                email_raw = "mousamrakse@gmail.com"
                print(f"[POST_CALL] ℹ️ Using default email: {email_raw}")

            email_clean = email_raw.replace("-", "").replace(" ", "").lower()
            parsed_date = parse_date_robust(date_raw)
            parsed_time = parse_time_robust(time_raw)

            if not parsed_date or not parsed_time:
                print(f"[POST_CALL] ❌ Failed to parse Date ({date_raw}) or Time ({time_raw}).")
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
                "Authorization": f"Bearer {CAL_API_KEY}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "start": start_time_iso,
                "eventTypeId": int(CAL_EVENT_TYPE_ID),
                "attendee": {
                    "name": name,
                    "email": email_clean,
                    "timeZone": "Asia/Kolkata",
                    "language": "en"
                }
            }
            
            resp = requests.post(CAL_BOOKING_URL, headers=headers, json=payload)
            if resp.status_code in [200, 201]:
                print(f"[POST_CALL] ✅ SUCCESS! Booking confirmed for {email_clean}. Meeting URL: {resp.json().get('data', {}).get('meetingUrl')}")
                return
            else:
                print(f"[POST_CALL] ❌ Cal.com API Error ({resp.status_code}): {resp.text}")
                return

        except Exception as e:
            print(f"[POST_CALL] 💥 Critical error during parsing: {e}")
            return
            
    print(f"[POST_CALL] 🛑 Max retries reached for {call_id}. Tabbly did not provide JSON data in time.")


