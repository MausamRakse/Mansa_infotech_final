from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from services import tabbly, supabase_service
from middleware.auth import get_user_id
import os

router = APIRouter(prefix="/agents", tags=["agents"])

class CreateAgentRequest(BaseModel):
    agent_name: str
    custom_first_line: str
    prompt_text: str
    stt_language: str = "en"
    voice_id: int = 1
    enable_calendar_booking: bool = True
    cal_api_key: str = ""
    cal_event_type_id: str = ""

@router.post("/create-agent")
def create_agent(req: CreateAgentRequest, user_id: str = Depends(get_user_id)):
    """Creates agent via Tabbly. Returns formatted agent object."""
    try:
        agent_id = tabbly.create_agent(
            agent_name=req.agent_name,
            custom_first_line=req.custom_first_line,
            prompt_text=req.prompt_text,
            stt_language=req.stt_language,
            voice_id=req.voice_id,
            enable_calendar_booking=1 if req.enable_calendar_booking else 0,
        )
        agent = {
            "id": str(agent_id),
            "name": req.agent_name,
            "greeting": req.custom_first_line,
            "prompt": req.prompt_text,
            "language": req.stt_language,
            "voice_id": req.voice_id,
            "meeting_enabled": req.enable_calendar_booking,
            "cal_api_key": req.cal_api_key,
            "cal_event_type_id": req.cal_event_type_id
        }
        # Map agent to user in Supabase with extra config
        supabase_service.add_agent_mapping(
            str(agent_id), 
            user_id, 
            cal_api_key=req.cal_api_key, 
            cal_event_type_id=req.cal_event_type_id
        )

        return {"success": True, "agent": agent}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/")
def list_agents(user_id: str = Depends(get_user_id)):
    """Returns user-specific agents filtered from Tabbly."""
    try:
        raw_agents = tabbly.get_agents()
        
        # Get mapped agent IDs and their config for this user
        agent_mappings = supabase_service.get_user_agent_mappings(user_id)
        # Create a lookup dict: {agent_id: mapping_data}
        mapping_dict = {m['agent_id']: m for m in agent_mappings}
        
        agents = []
        for raw in raw_agents:
            agent_id_str = str(raw.get("id"))
            if agent_id_str not in mapping_dict:
                continue

            mapping = mapping_dict[agent_id_str]
            # An agent is considered "cal_connected" if it has its own OAuth token or API key
            agent_cal_connected = bool(
                mapping.get('cal_access_token') or mapping.get('cal_api_key')
            )
            agents.append({
                "id": agent_id_str,
                "name": raw.get("agent_name", ""),
                "greeting": raw.get("custom_first_line", ""),
                "prompt": raw.get("prompt_text", ""),
                "language": "en", 
                "voice_id": 1,    
                "meeting_enabled": mapping.get('meeting_enabled', True),
                "cal_api_key": mapping.get('cal_api_key'),
                "cal_event_type_id": mapping.get('cal_event_type_id'),
                "cal_connected": agent_cal_connected,
            })
        return {"agents": agents}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class UpdateAgentRequest(BaseModel):
    agent_id: str
    agent_name: str
    custom_first_line: str
    prompt_text: str
    stt_language: str = "en"
    voice_id: int = 1
    enable_calendar_booking: bool = True
    cal_api_key: str = ""
    cal_event_type_id: str = ""
    status: str = "active"


class DeleteAgentRequest(BaseModel):
    agent_id: str

@router.post("/update-agent")
def update_agent(req: UpdateAgentRequest, user_id: str = Depends(get_user_id)):
    """Updates agent via Tabbly. Returns success."""
    try:
        if not str(req.agent_id).startswith("default-"):
            tabbly.update_agent(
                agent_id=req.agent_id,
                agent_name=req.agent_name,
                prompt_text=req.prompt_text,
                voice_id=req.voice_id,
                custom_first_line=req.custom_first_line,
                stt_language=req.stt_language,
                enable_calendar_booking="yes" if req.enable_calendar_booking else "no",
                status=req.status
            )
            # Update Supabase mapping with new config
            supabase_service.update_agent_mapping(
                req.agent_id, 
                user_id,
                cal_api_key=req.cal_api_key,
                cal_event_type_id=req.cal_event_type_id,
                meeting_enabled=req.enable_calendar_booking
            )
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/delete-agent")
def delete_agent(req: DeleteAgentRequest, user_id: str = Depends(get_user_id)):
    """Deletes agent via Tabbly. Returns success."""
    try:
        if not str(req.agent_id).startswith("default-"):
            # Check if user owns the agent before deleting
            user_agent_ids = supabase_service.get_user_agent_ids(user_id)
            if str(req.agent_id) not in user_agent_ids:
                raise HTTPException(status_code=403, detail="Not authorized to delete this agent")

            tabbly.delete_agent(req.agent_id)
            supabase_service.delete_agent_mapping(str(req.agent_id))
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class DisconnectAgentCalRequest(BaseModel):
    agent_id: str

@router.post("/disconnect-agent-cal")
def disconnect_agent_cal(req: DisconnectAgentCalRequest, user_id: str = Depends(get_user_id)):
    """Clears Cal.com OAuth tokens and API key from a specific agent's mapping. Disables booking for that agent only."""
    try:
        from middleware.auth import supabase
        # Verify ownership
        user_agent_ids = supabase_service.get_user_agent_ids(user_id)
        if str(req.agent_id) not in user_agent_ids:
            raise HTTPException(status_code=403, detail="Not authorized to modify this agent")

        supabase.table("agent_mappings").update({
            "cal_access_token": None,
            "cal_refresh_token": None,
            "cal_token_expiry": None,
            "cal_api_key": None,
            "cal_event_type_id": None,
        }).eq("agent_id", str(req.agent_id)).eq("user_id", user_id).execute()

        return {"success": True, "message": "Cal.com disconnected from this agent."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cal-status/{agent_id}")
def get_agent_cal_status(agent_id: str, user_id: str = Depends(get_user_id)):
    """
    Diagnostic endpoint: returns the Cal.com connection state for a specific agent.
    Useful for debugging the OAuth persistence issue.
    """
    try:
        from middleware.auth import supabase
        resp = supabase.table("agent_mappings").select("*").eq("agent_id", agent_id).eq("user_id", user_id).execute()
        if not resp.data:
            return {"cal_connected": False, "reason": "No agent mapping found"}

        mapping = resp.data[0]
        columns = list(mapping.keys())
        has_token_column = "cal_access_token" in columns

        return {
            "agent_id": agent_id,
            "columns_present": columns,
            "has_oauth_columns": has_token_column,
            "cal_access_token_present": bool(mapping.get("cal_access_token")),
            "cal_api_key_present": bool(mapping.get("cal_api_key")),
            "cal_event_type_id": mapping.get("cal_event_type_id"),
            "cal_connected": bool(mapping.get("cal_access_token") or mapping.get("cal_api_key")),
            "migration_needed": not has_token_column,
            "migration_sql": (
                "ALTER TABLE public.agent_mappings "
                "ADD COLUMN IF NOT EXISTS cal_access_token TEXT, "
                "ADD COLUMN IF NOT EXISTS cal_refresh_token TEXT, "
                "ADD COLUMN IF NOT EXISTS cal_token_expiry TIMESTAMP WITH TIME ZONE;"
                if not has_token_column else None
            )
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
