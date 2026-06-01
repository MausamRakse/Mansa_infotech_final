import os, requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
load_dotenv(dotenv_path=env_path, override=True)

# Global configurations removed to ensure strict database-driven credentials


def get_valid_cal_token_for_user(user_id: str) -> str:
    """
    Checks if the user has a Cal.com OAuth token in Supabase (profiles table).
    If so, verifies if it is expired. If expired, refreshes it using the refresh token,
    saves the new tokens to the database, and returns the valid access token.
    Otherwise, returns None (so we fallback to CAL_API_KEY).
    """
    try:
        from middleware.auth import supabase
        resp = supabase.table("profiles").select("*").eq("id", user_id).execute()
        if not resp.data:
            return None
            
        profile = resp.data[0]
        access_token = profile.get("cal_access_token")
        refresh_token = profile.get("cal_refresh_token")
        expiry_str = profile.get("cal_token_expiry")
        
        if not access_token:
            return None
            
        # Check if expired
        is_expired = False
        if expiry_str:
            try:
                clean_expiry = expiry_str.split("+")[0].split(".")[0].replace("Z", "")
                expiry_dt = datetime.strptime(clean_expiry, "%Y-%m-%dT%H:%M:%S")
                if datetime.utcnow() >= expiry_dt - timedelta(minutes=5):
                    is_expired = True
            except Exception as e:
                print(f"[CAL_AUTH] Error parsing token expiry: {e}")
                is_expired = True
        else:
            is_expired = True
            
        if is_expired and refresh_token:
            print(f"[CAL_AUTH] 🔄 Access token expired. Refreshing token for user {user_id}...")
            CAL_CLIENT_ID = os.getenv("CAL_CLIENT_ID")
            CAL_CLIENT_SECRET = os.getenv("CAL_CLIENT_SECRET")
            
            if not CAL_CLIENT_ID or not CAL_CLIENT_SECRET:
                print("[CAL_AUTH] ⚠️ Missing client ID/secret, cannot refresh token.")
                return access_token
                
            payload = {
                "client_id": CAL_CLIENT_ID,
                "client_secret": CAL_CLIENT_SECRET,
                "refresh_token": refresh_token,
                "grant_type": "refresh_token"
            }
            
            r = requests.post("https://api.cal.com/v2/auth/oauth2/token", json=payload, headers={"Content-Type": "application/json"})
            if r.status_code == 200:
                data = r.json()
                new_access = data.get("access_token")
                new_refresh = data.get("refresh_token") or refresh_token
                expires_in = data.get("expires_in", 3600)
                new_expiry = datetime.utcnow() + timedelta(seconds=expires_in)
                
                supabase.table("profiles").update({
                    "cal_access_token": new_access,
                    "cal_refresh_token": new_refresh,
                    "cal_token_expiry": new_expiry.isoformat()
                }).eq("id", user_id).execute()
                
                print(f"[CAL_AUTH] ✅ Token refreshed successfully!")
                return new_access
            else:
                print(f"[CAL_AUTH] ❌ Token refresh failed: {r.text}")
                
        return access_token
    except Exception as e:
        print(f"[CAL_AUTH] Error checking/refreshing Cal.com token: {e}")
        return None


def get_valid_cal_token_for_agent(agent_id: str) -> str:
    """
    Checks if a specific agent has its own Cal.com OAuth token in agent_mappings.
    If expired, refreshes and saves the new tokens back to agent_mappings.
    Returns the valid access_token string, or None if no agent-specific token exists.
    This is the PREFERRED method — it enforces per-agent calendar isolation.
    """
    try:
        from middleware.auth import supabase
        resp = supabase.table("agent_mappings").select("*").eq("agent_id", str(agent_id)).execute()
        if not resp.data:
            return None

        mapping = resp.data[0]
        access_token = mapping.get("cal_access_token")
        refresh_token = mapping.get("cal_refresh_token")
        expiry_str = mapping.get("cal_token_expiry")

        if not access_token:
            return None

        # Check if expired
        is_expired = False
        if expiry_str:
            try:
                clean_expiry = expiry_str.split("+")[0].split(".")[0].replace("Z", "")
                expiry_dt = datetime.strptime(clean_expiry, "%Y-%m-%dT%H:%M:%S")
                if datetime.utcnow() >= expiry_dt - timedelta(minutes=5):
                    is_expired = True
            except Exception as e:
                print(f"[CAL_AUTH_AGENT] Error parsing token expiry: {e}")
                is_expired = True
        else:
            is_expired = True

        if is_expired and refresh_token:
            print(f"[CAL_AUTH_AGENT] 🔄 Access token expired. Refreshing for agent {agent_id}...")
            CAL_CLIENT_ID = os.getenv("CAL_CLIENT_ID")
            CAL_CLIENT_SECRET = os.getenv("CAL_CLIENT_SECRET")

            if not CAL_CLIENT_ID or not CAL_CLIENT_SECRET:
                print("[CAL_AUTH_AGENT] ⚠️ Missing client credentials, cannot refresh.")
                return access_token

            payload = {
                "client_id": CAL_CLIENT_ID,
                "client_secret": CAL_CLIENT_SECRET,
                "refresh_token": refresh_token,
                "grant_type": "refresh_token"
            }
            r = requests.post("https://api.cal.com/v2/auth/oauth2/token", json=payload, headers={"Content-Type": "application/json"})
            if r.status_code == 200:
                data = r.json()
                new_access = data.get("access_token")
                new_refresh = data.get("refresh_token") or refresh_token
                expires_in = data.get("expires_in", 3600)
                new_expiry = datetime.utcnow() + timedelta(seconds=expires_in)

                supabase.table("agent_mappings").update({
                    "cal_access_token": new_access,
                    "cal_refresh_token": new_refresh,
                    "cal_token_expiry": new_expiry.isoformat()
                }).eq("agent_id", str(agent_id)).execute()

                print(f"[CAL_AUTH_AGENT] ✅ Token refreshed for agent {agent_id}!")
                return new_access
            else:
                print(f"[CAL_AUTH_AGENT] ❌ Token refresh failed: {r.text}")

        return access_token
    except Exception as e:
        print(f"[CAL_AUTH_AGENT] Error checking/refreshing agent Cal.com token: {e}")
        return None


def get_default_event_type_id(key: str, preferred_eid: any = None) -> int:
    """
    Fetches the first active/public event type ID from Cal.com
    using the provided OAuth access token or legacy API key.
    Refactored strictly for Cal.com v2 Event Type payload.
    Uses version 2024-06-14 to prevent 404 errors and parse flat list.

    If preferred_eid is provided, it validates it against the active list.
    If it is in the list, it returns preferred_eid. Otherwise, it falls back
    to the first active event type.
    """
    if not key:
        return None
        
    try:
        url = "https://api.cal.com/v2/event-types"
        headers = {
            "cal-api-version": "2024-06-14",
            "Content-Type": "application/json"
        }
        params = {}
        
        if str(key).startswith("cal_live_"):
            params["apiKey"] = key
        else:
            headers["Authorization"] = f"Bearer {key}"
            
        print(f"[CAL] 🔄 Querying Cal.com v2: {url}")
        r = requests.get(url, headers=headers, params=params, timeout=10)
        print(f"[CAL] GET /v2/event-types status: {r.status_code}, response: {r.text[:500]}")
        
        if r.status_code == 200:
            data = r.json()
            if data.get("status") == "success":
                event_list = data.get("data", [])
                if isinstance(event_list, list) and len(event_list) > 0:
                    active_ids = []
                    for et in event_list:
                        if et.get("active") is not False:
                            active_ids.append(int(et.get("id")))
                    
                    if not active_ids:
                        active_ids = [int(et.get("id")) for et in event_list]
                        
                    # Validate preferred_eid against the active list
                    if preferred_eid:
                        try:
                            pref_id = int(preferred_eid)
                            if pref_id in active_ids:
                                print(f"[CAL] ✅ Preferred eventTypeId {pref_id} is active and verified.")
                                return pref_id
                            else:
                                print(f"[CAL] ⚠️ Preferred eventTypeId {pref_id} is not in the active event types list: {active_ids}. Falling back.")
                        except ValueError:
                            print(f"[CAL] ⚠️ Preferred eventTypeId {preferred_eid} is not a valid integer. Falling back.")
                    
                    if active_ids:
                        resolved_id = active_ids[0]
                        print(f"[CAL] ⚡ Dynamically resolved active eventTypeId {resolved_id} from Cal.com v2 API")
                        return resolved_id
            print("[CAL] ⚠️ Warning: No event types found in data list.")
        else:
            print(f"[CAL] ⚠️ Error: Cal.com API returned non-200 status {r.status_code}.")
            
    except Exception as e:
        print(f"[CAL] ⚠️ Warning: Failed to dynamically retrieve Cal.com eventTypeId: {e}")
        
    if preferred_eid:
        try:
            return int(preferred_eid)
        except ValueError:
            return None
    return None

def utc_to_ist(utc_str):
    h, m = int(utc_str[11:13]), int(utc_str[14:16])
    m += 30
    if m >= 60: m -= 60; h += 1
    h += 5
    if h >= 24: h -= 24
    ampm = "AM" if h < 12 else "PM"
    dh = h % 12 or 12
    return f"{dh}:{m:02d} {ampm}", h

def get_window(hour):
    for start, end, label in [(9,11,"9 AM to 11 AM"),(11,13,"11 AM to 1 PM"),
                               (13,15,"1 PM to 3 PM"),(15,17,"3 PM to 5 PM"),
                               (17,19,"5 PM to 7 PM")]:
        if start <= hour < end:
            return label
    return "Other"

def build_availability_instruction(api_key=None, event_type_id=None, user_id=None, agent_id=None):
    """
    Fetches next 5 days of Cal.com availability (9AM-6PM IST).
    Filters out slots that have already passed for today.
    Supports OAuth access tokens or legacy API Keys.
    Returns a formatted string to inject into the agent's custom_instruction.

    TOKEN RESOLUTION ORDER (strict isolation):
    1. Agent-specific OAuth token from agent_mappings (preferred — per-agent isolation)
    2. Agent-specific API key from agent_mappings
    3. Global user profile OAuth token (fallback only if agent has no own tokens)
    4. Provided api_key argument
    """
    oauth_token = None

    # 1. Check agent-specific OAuth token first (strict isolation)
    if agent_id:
        oauth_token = get_valid_cal_token_for_agent(agent_id)
        if oauth_token:
            print(f"[CAL] 🔐 Using AGENT-SPECIFIC OAuth token for agent {agent_id}")

    # 2. Fallback to global user profile token only if no agent-specific token
    if not oauth_token and user_id:
        oauth_token = get_valid_cal_token_for_user(user_id)
        if oauth_token:
            print(f"[CAL] ⚠️ Falling back to USER-LEVEL OAuth token for user {user_id}")

    key = oauth_token or api_key
    if not key:
        print("[CAL] ⚠️ No connected Cal.com calendar credentials (OAuth/Agent key) found. Disabling slot retrieval.")
        return "STRICT INSTRUCTION: Meeting booking is currently disabled. Do NOT suggest any dates or times to the user. Inform them that booking is unavailable if they ask."

    # Always validate/resolve the event_type_id to make sure it exists/is active
    eid = get_default_event_type_id(key, preferred_eid=event_type_id)

    if not eid:
        print("[CAL] ⚠️ No active Cal.com eventTypeId found. Disabling slot retrieval.")
        return "STRICT INSTRUCTION: Meeting booking is currently disabled. Do NOT suggest any dates or times to the user. Inform them that booking is unavailable if they ask."

    # Pre-flight validations
    resolved_oauth_token = key if (key and not str(key).startswith("cal_live_")) else None
    resolved_api_key = key if (key and str(key).startswith("cal_live_")) else None
    
    if not eid:
        raise Exception("Missing Cal.com event type ID")
        
    if not resolved_api_key and not resolved_oauth_token:
        raise Exception("Missing Cal.com credentials")
        
    # Detailed debug logging
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"Resolved agent_id: {agent_id}")
    logger.info(f"Resolved user_id: {user_id}")
    logger.info(f"Resolved event_type_id: {eid}")
    logger.info("OAuth/API credentials loaded successfully")

    now_utc = datetime.utcnow()
    # Approximate IST from UTC for filtering
    now_ist_hour = (now_utc.hour + 5) + (1 if now_utc.minute + 30 >= 60 else 0)
    if now_ist_hour >= 24: now_ist_hour -= 24
    now_ist_minute = (now_utc.minute + 30) % 60

    results = {}
    for offset in range(6):
        date_obj = (now_utc + timedelta(days=offset))
        day = date_obj.strftime("%Y-%m-%d")
        
        # 9 AM to 6 PM IST is approx 03:30 to 12:30 UTC
        start_ts = f"{day}T03:30:00.000Z"
        end_ts   = f"{day}T12:30:00.000Z"
        
        try:
            headers = {}
            params = {
                "eventTypeId": eid,
                "startTime": start_ts,
                "endTime": end_ts
            }
            
            # If using OAuth token (no "cal_live_" prefix), authorize with Bearer header
            if key and not str(key).startswith("cal_live_"):
                headers["Authorization"] = f"Bearer {key}"
            else:
                params["apiKey"] = key
                
            r = requests.get("https://api.cal.com/v2/slots/available",
                             params=params,
                             headers=headers,
                             timeout=10)
            windows = {}
            data = r.json().get("data", {})
            slots_by_date = data.get("slots", {}) if isinstance(data, dict) else {}
            
            for _, slots in slots_by_date.items():
                for s in slots:
                    time_str = s.get("time", "") # format: 2026-04-21T04:00:00Z
                    disp, hour = utc_to_ist(time_str)
                    
                    # EXTRACT MINUTE FOR FILTERING
                    slot_minute = int(time_str[14:16])
                    
                    # FILTER OUT PAST SLOTS FOR TODAY
                    if offset == 0:
                        if hour < now_ist_hour or (hour == now_ist_hour and slot_minute <= now_ist_minute):
                            continue
                    
                    w = get_window(hour)
                    windows.setdefault(w, []).append(disp)
            
            if windows:
                results[day] = windows
        except Exception as e:
            print("Error fetching slots for", day, ":", e)

    if not results:
        return "CRITICAL: No slots available for the next 5 days. Inform the user that the calendar is fully booked and suggest calling back later."

    lines = [
        "STRICT INSTRUCTION: Suggest ONLY the following available slots.",
        "DO NOT suggest any time that is not explicitly mentioned below.",
        "The following slots are GUARANTEED to be free right now.",
        "\nAVAILABLE CONSULTATION SLOTS (IST, grouped by 2-hour windows):"
    ]
    for day, windows in results.items():
        lines.append(f"\nDate: {day}")
        for w, slots in windows.items():
            lines.append(f"  - Window [{w}]: {', '.join(slots)}")
            
    lines.append("\nOffer windows one at a time. Do NOT suggest already passed or booked times.")
    return "\n".join(lines)
