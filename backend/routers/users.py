from fastapi import APIRouter, HTTPException, Depends
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
        cur.execute("SELECT id, email, full_name FROM public.profiles WHERE id = %s", (user.id,))
        profile = cur.fetchone()
        cur.close()
        conn.close()
        
        if not profile:
            return {
                "id": user.id,
                "email": user.email,
                "full_name": "New User",
                "is_new": True
            }
            
        return {
            "id": profile[0],
            "email": profile[1],
            "full_name": profile[2],
            "is_new": False
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
