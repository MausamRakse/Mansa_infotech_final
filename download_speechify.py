import requests
import base64
import os

# ── config ────────────────────────────────────────────────────────────────────
VOICE_ID    = "95d51f79-c397-46f9-b49a-23763d3eaa2d"
TRANSCRIPT  = "Hey Helloo! Welcome to Convexa AI, this is how i sound"
OUTPUT_FILE = "Riya_Mehta.mp3"

URL = "https://www.tabbly.io/dashboard/agents/get_speechify_audio.php"

HEADERS = {
    "Accept":             "application/json, text/javascript, */*; q=0.01",
    "Accept-Language":    "en-US,en;q=0.9",
    "Connection":         "keep-alive",
    "Content-Type":       "application/json",
    "Origin":             "https://www.tabbly.io",
    "Referer":            "https://www.tabbly.io/dashboard/agents/select_voices",
    "Sec-Fetch-Dest":     "empty",
    "Sec-Fetch-Mode":     "cors",
    "Sec-Fetch-Site":     "same-origin",
    "User-Agent":         "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36",
    "X-Requested-With":   "XMLHttpRequest",
    "sec-ch-ua":          '"Chromium";v="148", "Google Chrome";v="148", "Not/A)Brand";v="99"',
    "sec-ch-ua-mobile":   "?0",
    "sec-ch-ua-platform": '"macOS"',
    "Cookie":             (
        "_ga=GA1.1.1920423279.1771564978; "
        "_fbp=fb.1.1771565108873.169724636732598065; "
        "crisp-client%2Fsession%2Fe2990622-17d4-48b9-a373-c9b9b22988e9=session_4cc5e0cd-b247-4f0c-ae83-0fc639779855; "
        "_ga_VCQP325T6X=GS2.1.s1772005258$o1$g1$t1772005280$j38$l0$h0; "
        "member_id=3373; "
        "PHPSESSID=k4tq5ratjam7848dd2ukafej0o; "
        'g_state={"i_l":0,"i_ll":1780037816391,"i_b":"Y5aWnN7/prcmPRvr/oDdfB2OfTgf2xzeeNJniUsiHFY","i_e":{"enable_itp_optimization":0},"i_et":1776666764999}; '
        "_ga_P2CGRDPBZP=GS2.1.s1780037810$o79$g1$t1780037817$j53$l0$h0; "
        "PHPSESSID=kc5kok42oukkr5kftuolil91oj"
    ),
}

# ── request ───────────────────────────────────────────────────────────────────
response = requests.post(URL, headers=HEADERS, json={"voice_id": VOICE_ID, "transcript": TRANSCRIPT})
response.raise_for_status()

data = response.json()

# ── decode "data:audio/mpeg;base64,<data>" ────────────────────────────────────
audio_url = data["audio_url"]  # e.g. "data:audio/mpeg;base64,SUQz..."

# strip the "data:audio/mpeg;base64," prefix
base64_data = audio_url.split(",", 1)[1]
audio_bytes = base64.b64decode(base64_data)

with open(OUTPUT_FILE, "wb") as f:
    f.write(audio_bytes)

print(f"✅ Saved → {os.path.abspath(OUTPUT_FILE)}")
print(f"   Format : {data.get('audio_format', 'unknown')}")
print(f"   Billed : {data.get('billable_characters_count', '?')} characters")