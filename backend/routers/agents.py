from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services import tabbly
import os

router = APIRouter(prefix="/agents", tags=["agents"])

class CreateAgentRequest(BaseModel):
    agent_name: str
    custom_first_line: str
    prompt_text: str
    stt_language: str = "en"
    voice_id: int = 1
    enable_calendar_booking: bool = True

@router.post("/create-agent")
def create_agent(req: CreateAgentRequest):
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
        }
        return {"success": True, "agent": agent}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/")
def list_agents():
    """Returns all created agents from Tabbly."""
    try:
        raw_agents = tabbly.get_agents()
        agents = []
        for raw in raw_agents:
            agents.append({
                "id": str(raw.get("id")),
                "name": raw.get("agent_name", ""),
                "greeting": raw.get("custom_first_line", ""),
                "prompt": raw.get("prompt_text", ""),
                "language": "en", # Fallback default
                "voice_id": 1,    # Fallback default
                "meeting_enabled": True # Fallback default
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

class DeleteAgentRequest(BaseModel):
    agent_id: str

@router.post("/update-agent")
def update_agent(req: UpdateAgentRequest):
    """Updates agent via Tabbly. Returns success."""
    try:
        if not str(req.agent_id).startswith("default-"):
            tabbly.update_agent(
                agent_id=req.agent_id,
                agent_name=req.agent_name,
                prompt_text=req.prompt_text,
                voice_id=req.voice_id
            )
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/delete-agent")
def delete_agent(req: DeleteAgentRequest):
    """Deletes agent via Tabbly. Returns success."""
    try:
        if not str(req.agent_id).startswith("default-"):
            tabbly.delete_agent(req.agent_id)
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
