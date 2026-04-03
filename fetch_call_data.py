import requests
import os
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
API_KEY = os.getenv("TABBLY_API_KEY")
ORG_ID = os.getenv("TABBLY_ORG_ID")
AGENT_ID = os.getenv("TABBLY_AGENT_ID")

# Directories for saving data
RECORDINGS_DIR = "recordings"
TRANSCRIPTS_DIR = "transcripts"

# Create directories if they don't exist
os.makedirs(RECORDINGS_DIR, exist_ok=True)
os.makedirs(TRANSCRIPTS_DIR, exist_ok=True)

def fetch_and_save_call_data():
    url = "https://www.tabbly.io/dashboard/agents/endpoints/call-logs-v2"
    
    params = {
        "api_key": API_KEY,
        "organization_id": ORG_ID,
        "use_agent_id": AGENT_ID,
        "limit": 100
    }
    
    print(f"Fetching call logs for Org: {ORG_ID}, Agent: {AGENT_ID}...")
    
    try:
        response = requests.get(url, params=params)
        
        if response.status_code == 200:
            result = response.json()
            
            call_logs = result.get("data", [])
            print(f"Found {len(call_logs)} call records.")
            
            for log in call_logs:
                # Debug: Print the full log for the first call to see hidden fields
                if log == call_logs[0]:
                    print("Debug - Full log structure:")
                    print(json.dumps(log, indent=2))
                
                # Correct field names based on API response
                call_id = log.get("participant_identity", "unknown")
                called_to = log.get("called_to", "unknown").replace("+", "")
                recording_url = log.get("call_recording_url")
                transcript = log.get("call_transcript")
                created_at = log.get("called_time", "unknown").replace(" ", "_").replace(":", "-")
                
                # Base filename
                base_name = f"call_{call_id}_{called_to}_{created_at}"
                
                # 1. Save Transcript
                if transcript:
                    transcript_path = os.path.join(TRANSCRIPTS_DIR, f"{base_name}.txt")
                    with open(transcript_path, "w", encoding="utf-8") as f:
                        f.write(transcript)
                    print(f"  [✓] Saved transcript: {transcript_path}")
                else:
                    print(f"  [ ] No transcript for call {call_id}")
                
                # 2. Download and Save Recording
                if recording_url and recording_url != "N/A":
                    recording_path = os.path.join(RECORDINGS_DIR, f"{base_name}.mp3")
                    try:
                        print(f"  [→] Downloading recording: {recording_url}")
                        rec_res = requests.get(recording_url)
                        if rec_res.status_code == 200:
                            with open(recording_path, "wb") as f:
                                f.write(rec_res.content)
                            print(f"  [✓] Saved recording: {recording_path}")
                        else:
                            print(f"  [✗] Failed to download recording {call_id}: HTTP {rec_res.status_code}")
                    except Exception as e:
                        print(f"  [✗] Error downloading recording {call_id}: {e}")
                else:
                    print(f"  [ ] No recording available for call {call_id}")
                    
            print("\nSync completed successfully.")
            return True
        else:
            print(f"Failed to fetch call logs. Status Code: {response.status_code}")
            print(response.text)
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return False

if __name__ == "__main__":
    if not API_KEY or not ORG_ID or not AGENT_ID:
        print("Missing configuration. Please ensure TABBLY_API_KEY, TABBLY_ORG_ID, and TABBLY_AGENT_ID are set in your .env file.")
    else:
        fetch_and_save_call_data()
