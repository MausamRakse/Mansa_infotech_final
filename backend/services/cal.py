import os, requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
load_dotenv(dotenv_path=env_path, override=True)

CAL_API_KEY       = os.getenv("CAL_API_KEY")
CAL_EVENT_TYPE_ID = os.getenv("CAL_EVENT_TYPE_ID", "1599599")

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

def build_availability_instruction(api_key=None, event_type_id=None):
    """
    Fetches next 5 days of Cal.com availability (9AM-6PM IST).
    Returns a formatted string to inject into the agent's custom_instruction.
    """
    key = api_key or CAL_API_KEY
    eid = event_type_id or CAL_EVENT_TYPE_ID

    results = {}
    for offset in range(6):
        day = (datetime.utcnow() + timedelta(days=offset)).strftime("%Y-%m-%d")
        start = f"{day}T03:30:00.000Z"
        end   = f"{day}T12:30:00.000Z"
        try:
            r = requests.get("https://api.cal.com/v2/slots/available",
                             params={"eventTypeId": eid,
                                     "apiKey": key,
                                     "startTime": start, "endTime": end},
                             timeout=10)
            windows = {}
            data = r.json().get("data", {})
            slots_by_date = data.get("slots", {}) if isinstance(data, dict) else {}
            for _, slots in slots_by_date.items():
                for s in slots:
                    disp, hour = utc_to_ist(s.get("time",""))
                    w = get_window(hour)
                    windows.setdefault(w, []).append(disp)
            if windows:
                results[day] = windows
        except Exception as e:
            print("Error fetching slots for", day, ":", e)

    if not results:
        return "No slots available for the next 5 days. Apologize and inform the user."

    lines = ["AVAILABLE CONSULTATION SLOTS (IST, grouped by 2-hour windows):"]
    for day, windows in results.items():
        lines.append(f"\nDate: {day}")
        for w, slots in windows.items():
            lines.append(f"  - Window [{w}]: {', '.join(slots)}")
    lines.append("\nOffer windows one at a time. Only reveal specific slots after user agrees to a window.")
    return "\n".join(lines)
