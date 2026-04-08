import os, requests
from dotenv import load_dotenv
load_dotenv(override=True)

TABBLY_API_KEY  = os.getenv("TABBLY_API_KEY")
TABBLY_ORG_ID   = os.getenv("TABBLY_ORG_ID")
TABBLY_CALL_FROM = os.getenv("TABBLY_CALL_FROM_NUMBER")

BASE = "https://www.tabbly.io"

def create_agent(agent_name, custom_first_line, prompt_text,
                 stt_language="en", voice_id=1, enable_calendar_booking="yes"):
    """
    Maps to: POST https://www.tabbly.io/api/create-agent
    Returns: agent_id (string) or raises exception
    """
    payload = {
        "api_key": TABBLY_API_KEY,
        "agent_name": agent_name,
        "custom_first_line": custom_first_line,
        "stt_language": stt_language,
        "voice_id": int(voice_id),
        "phone_number": TABBLY_CALL_FROM,
        "prompt_text": prompt_text,
        "enable_calendar_booking": enable_calendar_booking,
    }
    r = requests.post(f"{BASE}/api/create-agent",
                      headers={"Content-Type": "application/json",
                               "Accept": "application/json",
                               "X-Requested-With": "XMLHttpRequest"},
                      json=payload)
    r.raise_for_status()
    return r.json().get("data", {}).get("agent_id")


def trigger_call(agent_id, called_to, custom_instruction="", custom_first_line=""):
    """
    Maps to: POST https://www.tabbly.io/dashboard/agents/endpoints/trigger-call
    Before calling this, the router should pre-fetch Cal.com slots via cal.py
    and pass them as custom_instruction.
    Returns: full Tabbly response dict
    """
    if str(agent_id).startswith("default-"):
        parsed_agent_id = int(os.getenv("TABBLY_AGENT_ID", 1))
    else:
        try:
            parsed_agent_id = int(agent_id)
        except (ValueError, TypeError):
            raise ValueError(f"Invalid agent_id provided: {agent_id}. Agent ID must be a numeric value associated with Tabbly.")

    payload = {
        "organization_id": int(os.getenv("TABBLY_ORG_ID")),
        "use_agent_id": parsed_agent_id,
        "called_to": called_to,
        "call_from": TABBLY_CALL_FROM,
        "custom_first_line": custom_first_line or "Hello! How can I assist you today?",
        "custom_instruction": custom_instruction,
        "called_by_account": "API",
        "api_key": TABBLY_API_KEY,
        "custom_identifiers": "dashboard_trigger",
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

def update_agent(agent_id, agent_name, prompt_text, voice_id=1, status="active"):
    payload = {
        "api_key": TABBLY_API_KEY,
        "agent_id": int(agent_id),
        "agent_name": agent_name,
        "prompt_text": prompt_text,
        "voice_id": int(voice_id),
        "status": status
    }
    r = requests.post(f"{BASE}/api/update-agent", json=payload, headers={"Content-Type": "application/json"})
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


def create_campaign(campaign_name, agent_id, start_time, end_time, time_zone, custom_first_line, retries="0"):
    """
    Maps to: POST https://www.tabbly.io/dashboard/agents/endpoints/create-campaign
    """
    payload = {
        "api_key": TABBLY_API_KEY,
        "organization_id": int(os.getenv("TABBLY_ORG_ID")),
        "created_by": int(os.getenv("TABBLY_ORG_ID")), # Bypasses the 'API' string error
        "campaign_name": campaign_name,
        "agent_id": int(agent_id),
        "start_time": start_time,
        "end_time": end_time,
        "time_zone": time_zone,
        "custom_first_line": custom_first_line,
        "retries": int(retries)
    }
    print(f"DEBUG: Tabbly Campaign Payload (JSON): {payload}")
    r = requests.post(f"{BASE}/dashboard/agents/endpoints/create-campaign",
                      headers={"Content-Type": "application/json"},
                      json=payload)
    if r.status_code != 200:
        print(f"DEBUG: Tabbly Error Response: {r.text}")
    r.raise_for_status()
    return r.json()
