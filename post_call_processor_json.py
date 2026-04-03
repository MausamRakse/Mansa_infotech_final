import os
import requests
import json
import re
from datetime import datetime, timedelta, date, time
from dotenv import load_dotenv
from pymongo import MongoClient

# Load environment variables
load_dotenv()
API_KEY = os.getenv("TABBLY_API_KEY")
ORG_ID = os.getenv("TABBLY_ORG_ID")
AGENT_ID = os.getenv("TABBLY_AGENT_ID")
CAL_API_KEY = os.getenv("CAL_API_KEY")
CAL_EVENT_TYPE_ID = os.getenv("CAL_EVENT_TYPE_ID", "1599599")
MONGODB_URI = os.getenv("MONGODB_URI")

TABBLY_CALL_LOGS_URL = "https://www.tabbly.io/dashboard/agents/endpoints/call-logs-v2"
CAL_BOOKING_URL = "https://api.cal.com/v2/bookings"

def fetch_latest_call_json(target_phone_number):
    """
    Fetches the latest call logs from Tabbly and extracts the JSON output
    for the given phone number.
    """
    params = {
        "api_key": API_KEY,
        "organization_id": ORG_ID,
        "use_agent_id": AGENT_ID,
        "limit": 10
    }
    
    print("Fetching recent call logs from Tabbly...")
    try:
        response = requests.get(TABBLY_CALL_LOGS_URL, params=params)
        if response.status_code == 200:
            call_logs = response.json().get("data", [])
            
            # Find the most recent call to the target number
            for log in call_logs:
                called_to = log.get("called_to", "").replace("+", "")
                if target_phone_number.replace("+", "") in called_to:
                    json_output_str = log.get("call_json_output")
                    if json_output_str and json_output_str.strip():
                        return log.get("participant_identity"), json_output_str
                    else:
                        print(f"Found a recent call for {target_phone_number}, but the JSON output is not ready yet.")
                        return None, None
            print(f"No fully processed call found for {target_phone_number}.")
            return None, None
        else:
            print(f"Failed to fetch logs: {response.status_code} - {response.text}")
            return None, None
    except Exception as e:
        print(f"Error fetching logs: {e}")
        return None, None

def parse_date_robust(date_str):
    if not date_str: return None
    date_str = str(date_str).strip()
    
    # Try YYYY-MM-DD, DD-MM-YYYY, DD/MM/YYYY
    for fmt in ["%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y"]:
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue
    
    # Try natural language, e.g. "March 2nd", "Feb 28"
    now = datetime.utcnow()
    clean_date = re.sub(r'(\d+)(st|nd|rd|th)', r'\1', date_str).strip()
    
    for fmt in ["%B %d", "%b %d", "%B %d %Y", "%b %d %Y"]:
        try:
            parsed = datetime.strptime(clean_date, fmt)
            if "%Y" not in fmt:
                parsed = parsed.replace(year=now.year)
                # If parsed date is somehow in the past relative to now, adjust to next year
                if parsed.date() < now.date() - timedelta(days=60):
                    parsed = parsed.replace(year=now.year + 1)
            return parsed.date()
        except ValueError:
            pass
            
    return None

def parse_time_robust(time_str):
    if not time_str: return None
    time_str = str(time_str).strip()
    
    # Extract first part if it's a range like "1:00 PM - 1:15 PM"
    if "-" in time_str:
        time_str = time_str.split("-")[0].strip()
    elif " to " in time_str.lower():
        time_str = re.split("(?i) to ", time_str)[0].strip()
        
    # Standardize am/pm spacing (e.g. 9AM -> 9 AM)
    time_str = re.sub(r'(?i)(\d)(am|pm)', r'\1 \2', time_str)
    
    # Add :00 if missing minutes (e.g. "9 AM" -> "9:00 AM")
    time_str = re.sub(r'(?i)^(\d{1,2})\s+(AM|PM)$', r'\1:00 \2', time_str)
    
    for fmt in ["%I:%M %p", "%H:%M:%S", "%H:%M", "%I %p"]:
        try:
            return datetime.strptime(time_str, fmt).time()
        except ValueError:
            pass
    return None

def extract_date_from_summary(text):
    if not text: return None
    matches = re.findall(r'(January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2})(st|nd|rd|th)?', text, re.IGNORECASE)
    if matches:
        month, day, _ = matches[0]
        return parse_date_robust(f"{month} {day}")
    return None

def extract_booking_details(json_output_str):
    """
    Extracts booking details directly from Tabbly's JSON output.
    Uses the schema: {name, email_id, meeting_date, meeting_time, meeting_topic, summary, interested}
    """
    print("\n--- Analysing JSON Output ---")
    print(json_output_str)
    print("--------------------------\n")
    
    try:
        # Clean up formatting if necessary (remove markdown blocks if present)
        json_output_clean = json_output_str.replace("```json", "").replace("```", "").strip()
        data = json.loads(json_output_clean)
        
        # 1. Handle "Interested" status (if false, we skip booking)
        interested = data.get("interested", True)
        if interested is False or interested == "false":
            print("User is marked as NOT interested. Skipping booking.")
            return None

        # 2. Extract specific fields from the user's JSON schema
        name_str = data.get("name") or "Unknown"
        email_raw = data.get("email_id") or "unknown@example.com"
        
        # Clean email: Remove hyphens, spaces, and ensure lowercase
        # (Handling cases like 'M-O-U-S-E@gmail.com')
        email_clean = email_raw.replace("-", "").replace(" ", "").lower()
        
        date_str = data.get("meeting_date")
        time_str = data.get("meeting_time")
        topic_str = data.get("meeting_topic") or "Consultation Meeting"
        summary_text = data.get("summary", "")
        
        # 3. Parse date and time
        parsed_date = parse_date_robust(date_str)
        parsed_time = parse_time_robust(time_str)

        if not parsed_date or not parsed_time:
            print(f"❌ Missing or unparseable date ({date_str}) or time ({time_str}).")
            return None
            
        # 4. Convert to ISO 8601 UTC for Cal.com
        dt_ist = datetime.combine(parsed_date, parsed_time)
        # dt_ist represents local IST (UTC+5:30)
        dt_utc = dt_ist - timedelta(hours=5, minutes=30)
        start_time_iso = dt_utc.strftime("%Y-%m-%dT%H:%M:%S.000Z")
        
        details = {
            "name": name_str,
            "email": email_clean,
            "notes": f"{topic_str}\n\nSummary: {summary_text}",
            "start_time_iso": start_time_iso
        }
        
        print("\n✅ Successfully extracted details from JSON output:")
        print(json.dumps(details, indent=2))
        return details
        
    except json.JSONDecodeError as e:
        print(f"Failed to parse JSON output: {e}")
        return None
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Error processing JSON details: {e}")
        return None

def save_to_mongodb(participant_identity, json_output_str, details=None, transcript=None):
    """
    Saves the call record and details to MongoDB.
    """
    if not MONGODB_URI:
        print("⚠️ MONGODB_URI not found in .env. Skipping database save.")
        return

    try:
        # Create client and access database
        client = MongoClient(MONGODB_URI)
        db = client.get_database("calling_agent_db") # Name of your database
        calls_collection = db.get_collection("call_logs") # Name of your collection

        # Prepare the record
        record = {
            "participant_identity": participant_identity,
            "created_at": datetime.utcnow(),
            "raw_json_output": json_output_str,
            "transcript": transcript,
            "call_date": datetime.utcnow().strftime("%Y-%m-%d"),
            "call_time": datetime.utcnow().strftime("%H:%M:%S")
        }

        # If we successfully parsed details, flatten them into the record
        if details:
            record.update({
                "user_name": details.get("name"),
                "user_email": details.get("email"),
                "meeting_start_time": details.get("start_time_iso"),
                "meeting_notes": details.get("notes"),
                "interested": True
            })
            
            # Since we have the raw json, let's also pull the original phone if possible
            try:
                data = json.loads(json_output_str.replace("```json", "").replace("```", "").strip())
                record["phone_number"] = data.get("phone_number")
                record["meeting_topic"] = data.get("meeting_topic")
                # Ensure we capture exact 'interested' boolean from source
                record["interested"] = data.get("interested", True)
            except:
                pass
        else:
            # If details weren't parsed, we still try to get the 'interested' status from raw JSON
            try:
                data = json.loads(json_output_str.replace("```json", "").replace("```", "").strip())
                record["interested"] = data.get("interested", False)
                record["user_name"] = data.get("name", "Unknown")
                record["phone_number"] = data.get("phone_number")
            except:
                record["interested"] = False

        # Insert into database
        result = calls_collection.insert_one(record)
        print(f"✅ Successfully saved call record to MongoDB. ID: {result.inserted_id}")
        
    except Exception as e:
        print(f"❌ Error saving to MongoDB: {e}")
    finally:
        if 'client' in locals():
            client.close()

def book_via_cal_com(details):
    headers = {
        "cal-api-version": "2024-08-13",
        "Authorization": f"Bearer {CAL_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "start": details["start_time_iso"],
        "eventTypeId": int(CAL_EVENT_TYPE_ID),
        "attendee": {
            "name": details["name"],
            "email": details["email"],
            "timeZone": "Asia/Kolkata",
            "language": "en"
        }
    }
    
    print("Sending Booking Request to Cal.com...")
    
    try:
        response = requests.post(CAL_BOOKING_URL, headers=headers, json=payload)
        if response.status_code in [200, 201]:
            print(f"✅ Booking Successful! Cal.com Response Code: {response.status_code}")
            return True
        else:
            print(f"❌ Booking Failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"Error during Cal.com API call: {e}")
        return False

def main():
    target_number = os.getenv("TABBLY_PHONE_NUMBER")
    print(f"Starting JSON-based post-call processing for recent calls to {target_number}...")
    
    call_id, json_output_str = fetch_latest_call_json(target_number)
    
    if not json_output_str:
        return
        
    print(f"Processsing Call ID: {call_id}...")
    
    details = extract_booking_details(json_output_str)
    
    # NEW: Save to MongoDB regardless of booking success
    save_to_mongodb(call_id, json_output_str, details)
    
    if details:
        success = book_via_cal_com(details)
        if success:
            print("Post-call workflow completed successfully! The Cal.com system will email the user directly. 🎉")
    else:
        print("Could not extract booking details from JSON output.")

if __name__ == "__main__":
    main()
