import os
import requests
import json
import re
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("TABBLY_API_KEY")
ORG_ID = os.getenv("TABBLY_ORG_ID")
AGENT_ID = os.getenv("TABBLY_AGENT_ID")
CAL_API_KEY = os.getenv("CAL_API_KEY")
CAL_EVENT_TYPE_ID = os.getenv("CAL_EVENT_TYPE_ID", "1599599")

TABBLY_CALL_LOGS_URL = "https://www.tabbly.io/dashboard/agents/endpoints/call-logs-v2"
CAL_BOOKING_URL = "https://api.cal.com/v2/bookings"

def fetch_latest_transcript(target_phone_number):
    """
    Fetches the latest call logs from Tabbly and finds the most recent transcript
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
                    transcript = log.get("call_transcript")
                    if transcript and transcript.strip():
                        return log.get("participant_identity"), transcript
                    else:
                        print(f"Found a recent call for {target_phone_number}, but the transcript is still processing in Tabbly.")
                        print("Tabbly usually takes 1-2 minutes to generate transcripts after you hang up. Please wait a moment and try again.")
                        return None, None
            print(f"No completed transcript found for {target_phone_number}.")
            return None, None
        else:
            print(f"Failed to fetch logs: {response.status_code} - {response.text}")
            return None, None
    except Exception as e:
        print(f"Error fetching logs: {e}")
        return None, None

# import google.generativeai as genai
# 
# # Try to get Gemini API key
# GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
# if GEMINI_API_KEY:
#     genai.configure(api_key=GEMINI_API_KEY)

# def extract_booking_details(transcript):
#     """
#     [DISABLED] This function used Gemini to extract details. 
#     It is now disabled in favor of post_call_processor_json.py.
#     """
#     print("Gemini transcript extraction is currently disabled (Old Method).")
#     return None

# def extract_booking_details_old(transcript):
#     """
#     Extracts spelling of email, name, and topic from the transcript using Gemini.
#     """
#     print("\n--- Analysing Transcript ---")
#     print(transcript[:500] + "...\n" if len(transcript) > 500 else transcript)
#     print("--------------------------\n")
#     
#     if not GEMINI_API_KEY:
#         print("⚠️ No GEMINI_API_KEY found in .env! Falling back to mock data.")
#         return None
# 
#     prompt = f"""
# You are a booking assistant data extractor. Read the following call transcript and extract the finalized booking details.
# ...
# """

def book_via_cal_com(details):
    """
    Uses the extracted details to actually hit the Cal.com API and create the booking.
    """
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
    # print(json.dumps(payload, indent=2))
    
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
    print(f"Starting post-call processing for recent calls to {target_number}...")
    
    call_id, transcript = fetch_latest_transcript(target_number)
    
    if not transcript:
        return
        
    print(f"Processsing Call ID: {call_id}...")
    
    # details = extract_booking_details(transcript)
    details = None # Gemini extraction disabled
    
    if details:
        success = book_via_cal_com(details)
        if success:
            print("Post-call workflow completed successfully! The Cal.com system will email the user directly. 🎉")
    else:
        print("Could not extract booking details from transcript.")

if __name__ == "__main__":
    main()
