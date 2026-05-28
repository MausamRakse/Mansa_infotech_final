import requests
import json
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta

# Load environment variables
env_path = os.path.join(os.path.dirname(__file__), 'backend', '.env')
if os.path.exists(env_path):
    load_dotenv(dotenv_path=env_path)
else:
    load_dotenv()

# Configuration
API_KEY = os.getenv("TABBLY_API_KEY")
ORG_ID = os.getenv("TABBLY_ORG_ID")
AGENT_ID = os.getenv("TABBLY_AGENT_ID")
CALL_FROM = os.getenv("TABBLY_CALL_FROM_NUMBER")
CALLED_TO = os.getenv("TABBLY_PHONE_NUMBER")
# Global configurations removed to ensure strict database-driven credentials

CUSTOM_FIRST_LINE = "Hello! I am the automated assistant from Mansa Infotech. I am calling to discuss our IT services."


def utc_to_ist_with_hour(utc_str):
    """Convert a UTC time string to IST display string and return the 24h IST hour."""
    hour = int(utc_str[11:13])
    minute = int(utc_str[14:16])
    minute += 30
    if minute >= 60:
        minute -= 60
        hour += 1
    hour += 5
    if hour >= 24:
        hour -= 24
        
    ist_hour = hour
    ampm = "AM"
    display_hour = hour
    if display_hour >= 12:
        ampm = "PM"
        if display_hour > 12:
            display_hour -= 12
    elif display_hour == 0:
        display_hour = 12
        
    return f"{display_hour}:{minute:02d} {ampm}", ist_hour

def get_window_name(hour):
    if 9 <= hour < 11: return "9 AM to 11 AM"
    elif 11 <= hour < 13: return "11 AM to 1 PM"
    elif 13 <= hour < 15: return "1 PM to 3 PM"
    elif 15 <= hour < 17: return "3 PM to 5 PM"
    elif 17 <= hour < 19: return "5 PM to 7 PM"
    return "Other Times"

def fetch_cal_availability(api_key, event_type_id, user_id=None):
    """Pre-fetch available slots from Cal.com for the next 5 days, 9 AM - 6 PM IST, grouped by 2-hour windows."""
    # Pre-flight validations before Cal.com slots API request
    resolved_oauth_token = api_key if (api_key and not str(api_key).startswith("cal_live_")) else None
    resolved_api_key = api_key if (api_key and str(api_key).startswith("cal_live_")) else None
    
    if not event_type_id:
        raise Exception("Missing Cal.com event type ID")
        
    if not resolved_api_key and not resolved_oauth_token:
        raise Exception("Missing Cal.com credentials")
        
    # Detailed debug logging
    print(f"Resolved agent_id: {AGENT_ID}")
    print(f"Resolved user_id: {user_id}")
    print(f"Resolved event_type_id: {event_type_id}")
    print("OAuth/API credentials loaded successfully")

    results = {}  # { "2026-02-27": { "9 AM to 11 AM": ["9:00 AM", ...], ... }, ... }
    
    for day_offset in range(0, 6):  # Today + Next 5 days
        day = (datetime.utcnow() + timedelta(days=day_offset)).strftime("%Y-%m-%d")
        
        # We fetch the full day: 9 AM - 6 PM IST = 03:30 - 12:30 UTC
        # Cal.com API will automatically exclude slots that have already passed today.
        start = f"{day}T03:30:00.000Z"
        end = f"{day}T12:30:00.000Z"
        
        url = "https://api.cal.com/v1/slots"
        params = {
            "eventTypeId": event_type_id,
            "apiKey": api_key,
            "startTime": start,
            "endTime": end,
        }
        try:
            r = requests.get(url, params=params, timeout=10)
            data = r.json()
            daily_windows = {}
            for date_key, slots in data.get("slots", {}).items():
                for slot in slots:
                    utc_str = slot.get("time", "")
                    if utc_str:
                        display_str, hour = utc_to_ist_with_hour(utc_str)
                        window = get_window_name(hour)
                        if window not in daily_windows:
                            daily_windows[window] = []
                        daily_windows[window].append(display_str)
            if daily_windows:
                results[day] = daily_windows
                print(f"  {day}: slots found across {len(daily_windows)} windows")
        except Exception as e:
            print(f"  Warning: Could not fetch {day}: {e}")
    
    return results

def trigger_outbound_call():
    """Fetch availability dynamically from database, inject into custom_instruction, trigger call."""
    
    # Step 1: Resolve agent credentials dynamically from Supabase database
    print("Step 1: Resolving agent credentials dynamically from database...")
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))
    from middleware.auth import supabase
    from services import cal, supabase_service
    
    custom_key = None
    custom_eid = None
    user_id = None
    
    try:
        resp = supabase.table('agent_mappings').select('*').eq('agent_id', str(AGENT_ID)).execute()
        if resp.data:
            mapping = resp.data[0]
            user_id = mapping.get('user_id')
            if mapping.get('cal_api_key'):
                custom_key = mapping['cal_api_key']
            if mapping.get('cal_event_type_id'):
                custom_eid = mapping['cal_event_type_id']
            print(f"  Loaded agent-specific Cal.com credentials for agent {AGENT_ID}")
    except Exception as e:
        print(f"  Warning loading credentials from database: {e}")
        
    if user_id:
        try:
            oauth_token = cal.get_valid_cal_token_for_user(user_id)
            if oauth_token:
                custom_key = oauth_token
                print(f"  Using Cal.com OAuth token for user {user_id}")
        except Exception as e:
            print(f"  Warning checking OAuth credentials: {e}")
            
    if user_id and (not custom_key or not custom_eid):
        try:
            profile = supabase_service.get_user_profile(user_id)
            if profile:
                if not custom_key and profile.get('cal_api_key'):
                    custom_key = profile['cal_api_key']
                if not custom_eid and profile.get('cal_event_type_id'):
                    custom_eid = profile['cal_event_type_id']
                print(f"  Loaded custom credentials from profile for user {user_id}")
        except Exception as e:
            print(f"  Warning loading profile credentials: {e}")
            
    if custom_key and not custom_eid:
        try:
            resolved = cal.get_default_event_type_id(custom_key)
            if resolved:
                custom_eid = resolved
                print(f"  Dynamically resolved default eventTypeId {custom_eid} from Cal.com")
        except Exception as e:
            print(f"  Warning dynamically resolving eventTypeId: {e}")
            
    # Validate that we have connected credentials
    if not custom_key or not custom_eid:
        print("❌ Error: Cal.com calendar is not integrated for this agent. Booking is disabled.")
        custom_instruction = "IMPORTANT: Meeting booking is currently disabled. Do NOT suggest any dates or times to the user. Inform them that booking is unavailable if they ask."
    else:
        print(f"  Using dynamic Event Type ID: {custom_eid}")
        print("  Fetching Cal.com availability (next 5 days, 9 AM - 6 PM IST)...")
        availability = fetch_cal_availability(custom_key, custom_eid, user_id=user_id)
        
        if availability:
            lines = ["AVAILABLE CONSULTATION SLOTS (grouped by 2-hour windows, all times in IST):"]
            total_slots = 0
            for day, windows in availability.items():
                lines.append(f"\nDate: {day}")
                for window, slots in windows.items():
                    slot_text = ", ".join(slots)
                    lines.append(f"  - Window [{window}]: {slot_text}")
                    total_slots += len(slots)
            lines.append("\nWhen the user asks about availability, sequentially offer these 2-hour windows.")
            lines.append("If they reject a window, offer the next one. Only read the specific slots if they agree to the window.")
            custom_instruction = "\n".join(lines)
            print(f"  Loaded {total_slots} total slots across {len(availability)} days")
        else:
            custom_instruction = "No slots are available for the next 5 days. Inform the user and apologize."
            print("  No slots found.")
    
    # Step 2: Trigger the call with pre-loaded availability
    print(f"\nStep 2: Triggering call to {CALLED_TO}...")
    url = "https://www.tabbly.io/dashboard/agents/endpoints/trigger-call"
    
    payload = {
        "organization_id": int(ORG_ID),
        "use_agent_id": int(AGENT_ID),
        "called_to": CALLED_TO,
        "call_from": CALL_FROM,
        "custom_first_line": CUSTOM_FIRST_LINE,
        "custom_instruction": custom_instruction,
        "called_by_account": "API",
        "api_key": API_KEY,
        "custom_identifiers": "script_test_001"
    }
    
    headers = {'Content-Type': 'application/json'}
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        response_data = response.json()
        
        print(f"Response Status Code: {response.status_code}")
        print("\n" + "="*50)
        print("CALL TRIGGERED! 📞")
        print("1. Answer the call and negotiate a booking time.")
        print("2. Spell your email character-by-character when asked.")
        print("="*50 + "\n")
        
        if response.status_code == 200 and response_data.get("success"):
            call_id = response_data.get("participant_identity")
            print(f"Tracking Call ID: {call_id}")
            print("Listening for call completion... (this may take a few minutes)")
            
            # Start polling for the call log
            import time
            import subprocess
            
            logs_url = "https://www.tabbly.io/dashboard/agents/endpoints/call-logs-v2"
            logs_params = {
                "api_key": API_KEY,
                "organization_id": ORG_ID,
                "use_agent_id": AGENT_ID,
                "limit": 5
            }
            
            max_attempts = 40 # Up to 10 minutes total waiting
            for attempt in range(max_attempts):
                time.sleep(15) # Check every 15 seconds
                try:
                    logs_response = requests.get(logs_url, params=logs_params)
                    if logs_response.status_code == 200:
                        call_logs = logs_response.json().get("data", [])
                        found_call = next((log for log in call_logs if log.get("participant_identity") == call_id), None)
                        
                        if found_call:
                            print(f"\n✅ Call {call_id} has ended!")
                            transcript = found_call.get("call_transcript")
                            if transcript and transcript.strip():
                                print("Call JSON output is ready. Executing Post-Call Processor (JSON Method)...\n")
                                subprocess.run(["python3", "post_call_processor_json.py"], check=True)
                                return response_data
                            else:
                                print(f"Call {call_id} ended, but Tabbly is still generating the transcript... waiting.")
                except Exception as e:
                    print(f"Error checking logs: {e}")
            
            print("Timeout waiting for call to end or transcript to generate. Please run post_call_processor.py manually later.")
            return response_data
        
        return response_data
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return None


if __name__ == "__main__":
    missing_vars = []
    if not API_KEY: missing_vars.append("TABBLY_API_KEY")
    if not ORG_ID: missing_vars.append("TABBLY_ORG_ID")
    if not AGENT_ID: missing_vars.append("TABBLY_AGENT_ID")
    if not CALL_FROM: missing_vars.append("TABBLY_CALL_FROM_NUMBER")
    if not CALLED_TO: missing_vars.append("TABBLY_PHONE_NUMBER")

    if missing_vars:
        print("Missing configuration. Please update .env with:")
        for var in missing_vars:
            print(f"- {var}")
    else:
        trigger_outbound_call()
