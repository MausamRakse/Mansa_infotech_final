from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from middleware.auth import get_current_user
import psycopg2
import os

router = APIRouter(prefix="/users", tags=["users"])

DB_URL = os.getenv("SUPABASE_DB_URL")

@router.get("/config")
def get_config():
    """Returns public configuration for the frontend."""
    return {
        "supabase_url": os.getenv("SUPABASE_URL"),
        "supabase_anon_key": os.getenv("SUPABASE_ANON_KEY")
    }

@router.get("/me")
def get_me(user = Depends(get_current_user)):
    """Returns the current authenticated user profile from Supabase."""
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        cur.execute("SELECT id, email, full_name, cal_api_key, cal_event_type_id FROM public.profiles WHERE id = %s", (user.id,))
        profile = cur.fetchone()
        cur.close()
        conn.close()
        
        if not profile:
            return {
                "id": user.id,
                "email": user.email,
                "full_name": "New User",
                "is_new": True,
                "cal_api_key": "",
                "cal_event_type_id": ""
            }
            
        return {
            "id": profile[0],
            "email": profile[1],
            "full_name": profile[2],
            "is_new": False,
            "cal_api_key": profile[3] or "",
            "cal_event_type_id": profile[4] or ""
        }
    except Exception as e:
        # Graceful fallback if columns don't exist yet
        if "column" in str(e).lower() and "does not exist" in str(e).lower():
            return {
                "id": user.id,
                "email": user.email,
                "full_name": "User",
                "is_new": False,
                "cal_api_key": "",
                "cal_event_type_id": "",
                "error": "Please run the SQL command to add cal_api_key to profiles."
            }
        raise HTTPException(status_code=500, detail=str(e))

class CalSettingsRequest(BaseModel):
    cal_api_key: str
    cal_event_type_id: str

@router.post("/me/cal-settings")
def update_cal_settings(req: CalSettingsRequest, user = Depends(get_current_user)):
    """Updates the user's global Cal.com API key and event type ID."""
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        cur.execute(
            "UPDATE public.profiles SET cal_api_key = %s, cal_event_type_id = %s WHERE id = %s",
            (req.cal_api_key, req.cal_event_type_id, user.id)
        )
        conn.commit()
        cur.close()
        conn.close()
        return {"success": True}
    except Exception as e:
        if "column" in str(e).lower() and "does not exist" in str(e).lower():
            raise HTTPException(status_code=400, detail="Database schema missing cal_api_key columns. Please run the SQL command.")
        raise HTTPException(status_code=500, detail=str(e))
