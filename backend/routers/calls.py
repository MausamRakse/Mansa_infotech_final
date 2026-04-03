from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services import tabbly, cal
import os

router = APIRouter(prefix="/calls", tags=["calls"])

class TriggerCallRequest(BaseModel):
    agent_id: str
    phone_number: str
    custom_first_line: str = ""

@router.post("/trigger-call")
def trigger_call(req: TriggerCallRequest):
    """
    1. Fetches Cal.com availability for next 5 days
    2. Builds custom_instruction string
    3. Triggers outbound call via Tabbly
    """
    try:
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
