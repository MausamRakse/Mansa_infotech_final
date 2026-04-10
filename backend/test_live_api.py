import requests
from supabase import create_client, Client
import os

SUPABASE_URL = "https://kkmftbhqfmgaixqnwked.supabase.co"
SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImtrbWZ0YmhxZm1nYWl4cW53a2VkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzU1NDY1MzQsImV4cCI6MjA5MTEyMjUzNH0.he9kNYN6LwB3iRUTlFdzOYBX-jejbFEUFZOJbw2rmp0"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

# Sign in
res = supabase.auth.sign_in_with_password({
    "email": "mousamrakse99@gmail.com",
    "password": "@Qwerty_123"
})

token = res.session.access_token

# Make request to live API
api_url = "https://convexa-ai1.onrender.com/api/logs/stats"
headers = {"Authorization": f"Bearer {token}"}
response = requests.get(api_url, headers=headers)

print("STATS STATUS:", response.status_code)
print("STATS BODY:", response.text)

# Also test create agent
create_url = "https://convexa-ai1.onrender.com/api/agents/create-agent"
create_res = requests.post(create_url, headers=headers, json={
    "agent_name": "API Test",
    "custom_first_line": "Hello",
    "prompt_text": "Test",
    "stt_language": "en",
    "voice_id": 1,
    "enable_calendar_booking": True
})
print("CREATE STATUS:", create_res.status_code)
print("CREATE BODY:", create_res.text)
