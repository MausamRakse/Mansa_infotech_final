from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel
from services import tabbly, cal, supabase_service, post_call_service
from middleware.auth import get_user_id
import os

router = APIRouter(prefix="/calls", tags=["calls"])

class TriggerCallRequest(BaseModel):
    agent_id: str
    phone_number: str
    custom_first_line: str = ""
    is_booking_agent: bool = False

@router.post("/trigger-call")
def trigger_call(req: TriggerCallRequest, background_tasks: BackgroundTasks, user_id: str = Depends(get_user_id)):
    """
    1. Fetches Cal.com availability 
    2. Triggers outbound call via Tabbly
    3. PROACTIVE: Instead of waiting for a Webhook, we schedule a 
       check for the JSON Output results directly.
    """
    try:
        # Verify ownership
        user_agent_ids = supabase_service.get_user_agent_ids(user_id)
        if str(req.agent_id) not in user_agent_ids:
            raise HTTPException(status_code=403, detail="Not authorized to use this agent")

        availability_instruction = ""
        if req.is_booking_agent:
            # Fetch agent specific credentials
            mappings = supabase_service.get_user_agent_mappings(user_id)
            agent_map = next((m for m in mappings if str(m['agent_id']) == str(req.agent_id)), {})
            
            availability_instruction = cal.build_availability_instruction(
                api_key=agent_map.get('cal_api_key'),
                event_type_id=agent_map.get('cal_event_type_id')
            )
        else:
            availability_instruction = "IMPORTANT: The meeting booking function is currently OFF. Do NOT suggest any dates or times to the user. Inform them that booking is unavailable if they ask."
            
        result = tabbly.trigger_call(
            agent_id=req.agent_id,
            called_to=req.phone_number,
            custom_instruction=availability_instruction,
            custom_first_line=req.custom_first_line,
            custom_identifiers="booking:enabled" if req.is_booking_agent else "booking:disabled"
        )
        
        call_id = result.get("participant_identity")
        
        if call_id and req.is_booking_agent:
            # We schedule the processing proactively. No webhook needed.
            # It will wait internally for the call to finish and JSON to generate.
            print(f"[TRIGGER] ⚡ Scheduling proactive outcome check for {call_id}...")
            background_tasks.add_task(post_call_service.process_call_results, call_id, agent_id=req.agent_id, user_id=user_id)
            
        return {"success": True, "call_id": call_id, "raw": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/meeting-logs")
def get_meeting_logs_endpoint(user_id: str = Depends(get_user_id)):
    """Fetches meeting logs and merges them with agent names."""
    try:
        logs = supabase_service.get_meeting_logs(user_id)
        
        # We need agent names. We'll fetch them from tabbly or agent_mappings but we don't store names in agent_mappings currently.
        # Actually a quick way is to just fetch tabbly agents and build a map.
        raw_agents = tabbly.get_agents()
        agent_names = {str(a.get("id")): a.get("agent_name", "Unknown Agent") for a in raw_agents}
        
        for log in logs:
            log["agent_name"] = agent_names.get(str(log.get("agent_id")), "Unknown Agent")
            
        return {"success": True, "logs": logs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
