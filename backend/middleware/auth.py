from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from supabase import create_client, Client
import os
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL") or "https://kkmftbhqfmgaixqnwked.supabase.co"
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY") or "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImtrbWZ0YmhxZm1nYWl4cW53a2VkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzU1NDY1MzQsImV4cCI6MjA5MTEyMjUzNH0.he9kNYN6LwB3iRUTlFdzOYBX-jejbFEUFZOJbw2rmp0"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verifies the Supabase JWT and returns the user object."""
    token = credentials.credentials
    try:
        # Verify the token with Supabase Auth
        user_response = supabase.auth.get_user(token)
        if not user_response.user:
            raise HTTPException(status_code=401, detail="Invalid or expired token")
        return user_response.user
    except Exception as e:
        print(f"Auth error: {e}")
        raise HTTPException(status_code=401, detail=f"Authentication failed: {str(e)}")

def get_user_id(user = Depends(get_current_user)):
    return user.id
