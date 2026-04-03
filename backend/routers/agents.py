from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services import tabbly
import os

router = APIRouter(prefix="/agents", tags=["agents"])

# In-memory store (replace with MongoDB in production)
_agents_db = {}

class CreateAgentRequest(BaseModel):
    agent_name: str
    custom_first_line: str
    prompt_text: str
    stt_language: str = "en"
    voice_id: int = 1
    enable_calendar_booking: bool = True

@router.post("/create-agent")
def create_agent(req: CreateAgentRequest):
    """Creates agent via Tabbly (hidden). Returns internal agent object."""
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
        }
        _agents_db[str(agent_id)] = agent
        return {"success": True, "agent": agent}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/")
def list_agents():
    """Returns all created agents."""
    return {"agents": list(_agents_db.values())}
