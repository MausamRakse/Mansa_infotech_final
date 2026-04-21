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
    Filters out slots that have already passed for today.
    Returns a formatted string to inject into the agent's custom_instruction.
    """
    key = api_key or CAL_API_KEY
    eid = event_type_id or CAL_EVENT_TYPE_ID

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
            r = requests.get("https://api.cal.com/v2/slots/available",
                             params={"eventTypeId": eid,
                                     "apiKey": key,
                                     "startTime": start_ts, "endTime": end_ts},
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
