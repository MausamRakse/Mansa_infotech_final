from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from services import tabbly, cal, supabase_service
from middleware.auth import get_user_id
import os

router = APIRouter(prefix="/calls", tags=["calls"])

class TriggerCallRequest(BaseModel):
    agent_id: str
    phone_number: str
    custom_first_line: str = ""

@router.post("/trigger-call")
def trigger_call(req: TriggerCallRequest, user_id: str = Depends(get_user_id)):
    """
    1. Fetches Cal.com availability for next 5 days
    2. Builds custom_instruction string
    3. Triggers outbound call via Tabbly
    """
    try:
        # Verify ownership
        user_agent_ids = supabase_service.get_user_agent_ids(user_id)
        if str(req.agent_id) not in user_agent_ids and not str(req.agent_id).startswith("default-"):
            raise HTTPException(status_code=403, detail="Not authorized to use this agent")

        availability_instruction = cal.build_availability_instruction()
        result = tabbly.trigger_call(
            agent_id=req.agent_id,
            called_to=req.phone_number,
            custom_instruction=availability_instruction,
            custom_first_line=req.custom_first_line,
        )
        return {"success": True, "call_id": result.get("participant_identity"), "raw": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
