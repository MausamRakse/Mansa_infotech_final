import os, requests
from dotenv import load_dotenv
load_dotenv(override=True)

TABBLY_API_KEY   = os.getenv("TABBLY_API_KEY")
TABBLY_ORG_ID    = os.getenv("TABBLY_ORG_ID")

def format_phone_e164(phone: str) -> str:
    if not phone:
        return ""
    cleaned = "".join(c for c in str(phone) if c.isdigit() or c == "+")
    if cleaned and not cleaned.startswith("+"):
        cleaned = "+" + cleaned
    return cleaned

raw_call_from = os.getenv("TABBLY_CALL_FROM_NUMBER") or "+918035736739"
TABBLY_CALL_FROM = format_phone_e164(raw_call_from)

if not TABBLY_ORG_ID:
    raise ValueError("TABBLY_ORG_ID not set")

BASE = "https://www.tabbly.io"

def get_valid_voice_id(api_key: str, requested_vid: int) -> int:
    # Map frontend options: Voice 1 -> 125 (Ara), Voice 2 -> 93 (Akash), Voice 3 -> 92 (Asha)
    mapping = {
        1: 125,
        2: 93,
        3: 92
    }
    mapped_id = mapping.get(requested_vid, requested_vid)
    
    try:
        r = requests.get('https://www.tabbly.io/api/get-voices', params={'api_key': api_key}, timeout=5)
        if r.status_code == 200:
            voices = r.json().get('voices', [])
            valid_ids = [v.get('id') for v in voices if v.get('id') is not None]
            if mapped_id in valid_ids:
                return mapped_id
            if 125 in valid_ids:
                return 125
            if valid_ids:
                return valid_ids[0]
    except Exception as e:
        print(f"Error fetching voice list: {e}")
        
    return mapped_id

def create_agent(agent_name, custom_first_line, prompt_text,
                 stt_language="en", voice_id=1, enable_calendar_booking="yes"):
    """
    Maps to: POST https://www.tabbly.io/api/create-agent
    Returns: agent_id (string) or raises exception
    """
    booking_val = 1
    if enable_calendar_booking in [False, 0, "0", "no", "disabled"]:
        booking_val = 0

    validated_voice_id = get_valid_voice_id(TABBLY_API_KEY, int(voice_id))

    payload = {
        "api_key": TABBLY_API_KEY,
        "agent_name": agent_name,
        "custom_first_line": custom_first_line,
        "stt_language": stt_language,
        "voice_id": validated_voice_id,
        "phone_number": TABBLY_CALL_FROM,
        "prompt_text": prompt_text,
        "enable_calendar_booking": booking_val,
    }
    r = requests.post(f"{BASE}/api/create-agent",
                      headers={"Content-Type": "application/json",
                               "Accept": "application/json",
                               "X-Requested-With": "XMLHttpRequest"},
                      json=payload)
    r.raise_for_status()
    return r.json().get("data", {}).get("agent_id")


def trigger_call(agent_id, called_to, custom_instruction="", custom_first_line="", custom_identifiers="dashboard_trigger"):
    """
    Maps to: POST https://www.tabbly.io/dashboard/agents/endpoints/trigger-call
    Before calling this, the router should pre-fetch Cal.com slots via cal.py
    and pass them as custom_instruction.
    Returns: full Tabbly response dict
    """
    try:
        parsed_agent_id = int(agent_id)
    except (ValueError, TypeError):
        raise ValueError(f"Invalid agent_id provided: {agent_id}. Agent ID must be a numeric value associated with Tabbly.")

    payload = {
        "organization_id": int(os.getenv("TABBLY_ORG_ID")),
        "use_agent_id": parsed_agent_id,
        "called_to": format_phone_e164(called_to),
        "call_from": TABBLY_CALL_FROM,
        "custom_first_line": custom_first_line or "Hello! How can I assist you today?",
        "custom_instruction": custom_instruction,
        "called_by_account": "API",
        "api_key": TABBLY_API_KEY,
        "custom_identifiers": custom_identifiers,
    }
    r = requests.post(f"{BASE}/dashboard/agents/endpoints/trigger-call",
                      headers={"Content-Type": "application/json"},
                      json=payload)
    r.raise_for_status()
    return r.json()

def get_agents():
    payload = {"api_key": TABBLY_API_KEY}
    r = requests.post(f"{BASE}/api/get-agents", json=payload, headers={"Content-Type": "application/json"})
    r.raise_for_status()
    return r.json().get("data", [])

def update_agent(agent_id, agent_name, prompt_text, voice_id=1, custom_first_line="Hello!", stt_language="en", enable_calendar_booking="yes"):
    booking_val = 1
    if enable_calendar_booking in [False, 0, "0", "no", "disabled"]:
        booking_val = 0

    validated_voice_id = get_valid_voice_id(TABBLY_API_KEY, int(voice_id))

    payload = {
        "api_key": TABBLY_API_KEY,
        "agent_id": int(agent_id),
        "agent_name": agent_name,
        "custom_first_line": custom_first_line,
        "stt_language": stt_language,
        "voice_id": validated_voice_id,
        "phone_number": TABBLY_CALL_FROM,
        "prompt_text": prompt_text,
        "enable_calendar_booking": booking_val,
    }
    r = requests.post(f"{BASE}/api/create-agent",
                      headers={"Content-Type": "application/json",
                               "Accept": "application/json",
                               "X-Requested-With": "XMLHttpRequest"},
                      json=payload)
    r.raise_for_status()
    return r.json()

def delete_agent(agent_id):
    payload = {
        "api_key": TABBLY_API_KEY,
        "agent_id": int(agent_id)
    }
    r = requests.post(f"{BASE}/api/delete-agent", json=payload, headers={"Content-Type": "application/json"})
    r.raise_for_status()
    return r.json()


def fetch_call_logs(agent_id, limit=50):
    """
    Maps to: GET https://www.tabbly.io/dashboard/agents/endpoints/call-logs-v2
    Returns: list of call log dicts with:
      - participant_identity, called_to, called_time,
        call_transcript, call_recording_url, call_json_output
    """
    params = {
        "api_key": TABBLY_API_KEY,
        "organization_id": os.getenv("TABBLY_ORG_ID"),
        "use_agent_id": agent_id,
        "limit": limit,
    }
    r = requests.get(f"{BASE}/dashboard/agents/endpoints/call-logs-v2", params=params)
    r.raise_for_status()
    return r.json().get("data", [])


def create_campaign(campaign_name, agent_id, start_time, end_time, time_zone, custom_first_line):
    """
    Maps to: POST https://www.tabbly.io/dashboard/agents/endpoints/create-campaign
    Includes enhanced headers and explicit ID mapping to resolve the 'created_by' SQL error.
    """
    payload = {
        "campaign_name": campaign_name,
        "agent_id": int(agent_id),
        "start_time": f"{start_time}",
        "end_time": f"{end_time}",
        "time_zone": f"{time_zone}",
        "custom_first_line": custom_first_line,
        "api_key": TABBLY_API_KEY,
        "created_by": int(TABBLY_ORG_ID)
    }

    print("FINAL PAYLOAD:", payload)
    r = requests.post(
        f"{BASE}/dashboard/agents/endpoints/create-campaign",
        headers={
            "Content-Type": "application/json"
        },
        json=payload
    )

    print("STATUS:", r.status_code)
    print("RAW RESPONSE:", r.text)

    try:
        response = r.json()
    except Exception:
        raise Exception(f"Non-JSON response from Tabbly: {r.text}")

    if r.status_code != 200:
        raise Exception(response.get("message", r.text) if isinstance(response, dict) else r.text)

    return response
def fetch_call_logs_by_id(call_id: str):
    """
    Fetches call logs from Tabbly and filters for a specific call_id (participant_identity).
    """
    params = {
        "api_key": TABBLY_API_KEY,
        "organization_id": TABBLY_ORG_ID,
        "limit": 100,
    }
    r = requests.get(f"{BASE}/dashboard/agents/endpoints/call-logs-v2", params=params)
    r.raise_for_status()
    logs = r.json().get("data", [])
    # Filter for the specific call_id
    return [log for log in logs if log.get("participant_identity") == call_id]

def update_campaign(campaign_id, current_status=None, start_time=None, end_time=None):
    """
    Maps to: POST https://www.tabbly.io/dashboard/agents/endpoints/update-campaign
    """
    payload = {
        "api_key": TABBLY_API_KEY,
        "organization_id": int(TABBLY_ORG_ID),
        "id": int(campaign_id)
    }
    if current_status: payload["current_status"] = current_status
    if start_time: payload["start_time"] = start_time
    if end_time: payload["end_time"] = end_time

    r = requests.post(
        f"{BASE}/dashboard/agents/endpoints/update-campaign",
        headers={"Content-Type": "application/json"},
        json=payload
    )
    r.raise_for_status()
    return r.json()
