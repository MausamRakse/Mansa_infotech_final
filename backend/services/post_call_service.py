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

def process_call_results(call_id: str, retries: int = 5, delay: int = 30):
    """
    Called after a call ends. Fetches results from Tabbly, 
    parses them, and books on Cal.com if interested.
    Includes retries as Tabbly takes time to generate JSON output.
    """
    logger.info(f"Processing post-call results for Call ID: {call_id}")
    
    for attempt in range(retries):
        logger.info(f"Attempt {attempt + 1}/{retries} for call {call_id}...")
        
        # 1. Fetch the call details from Tabbly
        call_logs = tabbly.fetch_call_logs_by_id(call_id)
        if not call_logs:
            logger.warning(f"No logs found yet for call_id: {call_id}. Waiting {delay}s...")
            time.sleep(delay)
            continue

        log = call_logs[0]
        json_output_str = log.get("call_json_output")
        if not json_output_str:
            logger.warning(f"No JSON output ready yet for call_id: {call_id}. Waiting {delay}s...")
            time.sleep(delay)
            continue

        # 2. Extract Details
        try:
            json_output_clean = json_output_str.replace("```json", "").replace("```", "").strip()
            data = json.loads(json_output_clean)
            
            interested = data.get("interested", True)
            if interested is False or interested == "false":
                logger.info(f"User {call_id} not interested. Status: {data.get('interested')}")
                return

            name = data.get("name") or "Unknown"
            email_raw = data.get("email_id") or ""
            email_clean = email_raw.replace("-", "").replace(" ", "").lower()
            
            parsed_date = parse_date_robust(data.get("meeting_date"))
            parsed_time = parse_time_robust(data.get("meeting_time"))

            if not parsed_date or not parsed_time:
                logger.error(f"Failed to parse date ({data.get('meeting_date')}) or time ({data.get('meeting_time')}) for call {call_id}")
                return

            # Convert IST to UTC
            dt_ist = datetime.combine(parsed_date, parsed_time)
            dt_utc = dt_ist - timedelta(hours=5, minutes=30)
            start_time_iso = dt_utc.strftime("%Y-%m-%dT%H:%M:%S.000Z")

            # 3. Book via Cal.com
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
                logger.info(f"✅ Booking successful for {email_clean}")
                return # Done
            else:
                logger.error(f"❌ Booking failed for {email_clean}: {resp.text}")
                return

        except Exception as e:
            logger.error(f"Error in parsing/booking logic: {e}")
            return
            
    logger.error(f"Max retries reached for call {call_id} without finding JSON results.")
