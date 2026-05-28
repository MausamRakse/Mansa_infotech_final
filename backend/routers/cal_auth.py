from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.responses import HTMLResponse
import os
import requests
from datetime import datetime, timedelta
from middleware.auth import get_user_id, supabase
from typing import Optional

router = APIRouter(prefix="/auth/cal", tags=["cal-auth"])

from dotenv import load_dotenv


# ---------------------------------------------------------------------------
# Internal helper: resolve event type ID via the correct Cal.com v2 endpoint
# ---------------------------------------------------------------------------

def _resolve_cal_event_type_id(access_token: str) -> Optional[int]:
    """
    Fetch the first available event type ID for the authenticated user.

    Endpoint:  GET /v2/event-types
    Version:   cal-api-version: 2024-06-14   ← required for this endpoint
    Auth:      Bearer <oauth_access_token>

    Official docs: https://cal.com/docs/api-reference/v2/event-types/get-all-event-types

    Response shape (flat array, NOT eventTypeGroups):
        {
            "status": "success",
            "data": [
                { "id": 123456, "title": "30 Min Meeting", ... },
                ...
            ]
        }
    """
    url = "https://api.cal.com/v2/event-types"

    headers = {
        # CRITICAL: this endpoint requires 2024-06-14, NOT 2024-08-13
        # Using the wrong version causes a 404 "Cannot GET /v2/event-types"
        "cal-api-version": "2024-06-14",
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    print(f"[CAL] 🔄 Querying Cal.com v2: {url}")

    try:
        response = requests.get(url, headers=headers, timeout=10)
    except requests.RequestException as exc:
        print(f"[CAL] ❌ Network error contacting Cal.com: {exc}")
        return None

    print(f"[CAL] Status: {response.status_code}")
    print(f"[CAL] Response: {response.text[:500]}")   # cap log length

    if response.status_code != 200:
        print(f"[CAL] ❌ Failed to fetch event types. Status: {response.status_code}")
        return None

    try:
        data = response.json()
        if data.get("status") == "success":
            event_list = data.get("data", [])
            if isinstance(event_list, list) and len(event_list) > 0:
                for et in event_list:
                    if et.get("active") is not False:
                        return int(et.get("id"))
                return int(event_list[0].get("id"))
    except Exception as e:
        print(f"[CAL] ❌ Error parsing event types response: {e}")
        
    return None


@router.get("/url")
def get_auth_url(agent_id: str = None, user_id: str = Depends(get_user_id)):
    """
    Generates and returns the Cal.com OAuth URL.
    Passes user_id (and optional agent_id) in the state parameter to verify/identify during the callback.
    """
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
    load_dotenv(dotenv_path=env_path, override=True)
    client_id = os.getenv("CAL_CLIENT_ID")
    redirect_uri = os.getenv("CAL_REDIRECT_URI", "http://localhost:8000/api/auth/cal/callback")
    
    if not client_id:
        raise HTTPException(status_code=500, detail="CAL_CLIENT_ID is not configured in backend .env")
        
    state_val = f"{user_id}:{agent_id}" if agent_id else user_id
    
    auth_url = (
        f"https://app.cal.com/auth/oauth2/authorize"
        f"?client_id={client_id}"
        f"&redirect_uri={redirect_uri}"
        f"&response_type=code"
        f"&state={state_val}"
        f"&scope=BOOKING_READ%20BOOKING_WRITE"
    )
    return {"url": auth_url}


@router.get("/callback", response_class=HTMLResponse)
def oauth_callback(code: str = Query(...), state: str = Query(...)):
    """
    Handles redirect from Cal.com. Receives code and exchanges it for tokens,
    saves tokens to public.profiles matching user_id in state, and serves success HTML.
    """
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
    load_dotenv(dotenv_path=env_path, override=True)
    client_id = os.getenv("CAL_CLIENT_ID")
    client_secret = os.getenv("CAL_CLIENT_SECRET")
    redirect_uri = os.getenv("CAL_REDIRECT_URI", "http://localhost:8000/api/auth/cal/callback")
    
    if not client_id or not client_secret:
        return error_html("Cal.com client credentials are not configured in the backend environment.")
        
    user_id = state
    agent_id = None
    if ":" in state:
        user_id, agent_id = state.split(":", 1)
    
    # Exchange auth code for tokens
    token_url = "https://api.cal.com/v2/auth/oauth2/token"
    payload = {
        "client_id": client_id,
        "client_secret": client_secret,
        "code": code,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code"
    }
    
    try:
        r = requests.post(token_url, json=payload, headers={"Content-Type": "application/json"})
        if r.status_code != 200:
            return error_html(f"OAuth Token Exchange failed ({r.status_code}): {r.text}")
            
        data = r.json()
        access_token = data.get("access_token")
        refresh_token = data.get("refresh_token")
        expires_in = data.get("expires_in", 3600)  # default to 1 hr if missing
        
        if not access_token:
            return error_html("No access_token returned by Cal.com.")
            
        # Calculate token expiry time
        expiry_time = datetime.utcnow() + timedelta(seconds=expires_in)
        
        # Save credentials to public.profiles in Supabase
        update_data = {
            "cal_access_token": access_token,
            "cal_refresh_token": refresh_token,
            "cal_token_expiry": expiry_time.isoformat()
        }
        
        # Resolve dynamic event type ID using access_token
        resolved_eid = None
        try:
            resolved_eid = _resolve_cal_event_type_id(access_token)
            if resolved_eid:
                update_data["cal_event_type_id"] = str(resolved_eid)
                print(f"[CAL_CALLBACK] Dynamic event type ID resolved: {resolved_eid}")
        except Exception as e:
            print(f"[CAL_CALLBACK] Error auto-resolving event type id: {e}")
        
        db_res = supabase.table("profiles").update(update_data).eq("id", user_id).execute()
        if not db_res.data:
            return error_html("Failed to update user profile in Supabase database.")
            
        # If agent_id was passed, dynamically map the Event Type ID to agent_mappings
        if agent_id:
            try:
                from services import supabase_service
                supabase_service.update_agent_mapping(
                    agent_id=agent_id,
                    user_id=user_id,
                    cal_event_type_id=str(resolved_eid) if resolved_eid else ""
                )
                print(f"[CAL_CALLBACK] Updated agent {agent_id} mapping with event type ID {resolved_eid}")
            except Exception as e:
                print(f"[CAL_CALLBACK] Error updating agent mapping: {e}")
            
        return success_html()
        
    except Exception as e:
        return error_html(f"An unexpected error occurred during OAuth callback: {str(e)}")


def success_html():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Authentication Successful</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
                background-color: #0d0e12;
                color: #ffffff;
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                height: 100vh;
                margin: 0;
                text-align: center;
            }
            .container {
                padding: 40px;
                background-color: #15171e;
                border-radius: 20px;
                box-shadow: 0 12px 40px rgba(0,0,0,0.5);
                border: 1px solid rgba(255, 255, 255, 0.08);
                max-width: 440px;
                animation: zoomIn 0.3s ease-out;
            }
            @keyframes zoomIn {
                from { opacity: 0; transform: scale(0.95); }
                to { opacity: 1; transform: scale(1); }
            }
            h1 { font-size: 26px; font-weight: 800; margin-top: 15px; margin-bottom: 10px; color: #10b981; }
            p { color: #9ca3af; font-size: 15px; line-height: 1.6; margin-bottom: 25px; }
            .spinner {
                border: 3px solid rgba(255,255,255,0.05);
                width: 48px;
                height: 48px;
                border-radius: 50%;
                border-left-color: #10b981;
                animation: spin 0.8s linear infinite;
                margin: 0 auto;
            }
            @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="spinner"></div>
            <h1>Connection Successful!</h1>
            <p>Your Cal.com calendar is now securely connected to the Mansa Dashboard. This window will close automatically.</p>
        </div>
        <script>
            try {
                if (window.opener) {
                    window.opener.postMessage({ type: "CAL_AUTH_SUCCESS" }, "*");
                }
            } catch (e) {
                console.error("Failed to notify parent window:", e);
            }
            setTimeout(() => {
                window.close();
            }, 2000);
        </script>
    </body>
    </html>
    """

def error_html(details: str):
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Authentication Failed</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
                background-color: #0d0e12;
                color: #ffffff;
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                height: 100vh;
                margin: 0;
                text-align: center;
            }}
            .container {{
                padding: 40px;
                background-color: #15171e;
                border-radius: 20px;
                box-shadow: 0 12px 40px rgba(0,0,0,0.5);
                border: 1px solid rgba(239, 68, 68, 0.2);
                max-width: 440px;
            }}
            h1 {{ font-size: 26px; font-weight: 800; margin-top: 15px; margin-bottom: 10px; color: #ef4444; }}
            p {{ color: #9ca3af; font-size: 15px; line-height: 1.6; margin-bottom: 25px; }}
            .details {{
                font-family: monospace;
                background-color: #1f222c;
                padding: 12px;
                border-radius: 8px;
                border: 1px solid rgba(255,255,255,0.05);
                color: #f87171;
                font-size: 13px;
                text-align: left;
                word-break: break-all;
                max-height: 120px;
                overflow-y: auto;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <span style="font-size: 48px;">❌</span>
            <h1>Connection Failed</h1>
            <p>We encountered an issue during the Cal.com OAuth process. Please check your credentials and try again.</p>
            <div class="details">Error: {details}</div>
        </div>
    </body>
    </html>
    """
