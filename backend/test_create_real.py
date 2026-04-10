import uuid
from fastapi.testclient import TestClient
from main import app
from middleware.auth import get_current_user

class MockUser:
    id = "6e72317c-bb9b-4eee-9fcc-c873423a8d29" # mousamrakse99@gmail.com
    email = "mousamrakse99@gmail.com"

app.dependency_overrides[get_current_user] = lambda: MockUser()

client = TestClient(app)

response = client.post("/api/agents/create-agent", json={
    "agent_name": "Test Agent Via Script",
    "custom_first_line": "Hello",
    "prompt_text": "Be helpful",
    "stt_language": "en",
    "voice_id": 1,
    "enable_calendar_booking": True
})
print("STATUS CODE:", response.status_code)
print("RESPONSE:", response.json())
