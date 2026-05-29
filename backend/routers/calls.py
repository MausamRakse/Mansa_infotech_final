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

        # Get local mapping to determine if meeting booking is truly enabled
        mappings = supabase_service.get_user_agent_mappings(user_id)
        agent_map = next((m for m in mappings if str(m['agent_id']) == str(req.agent_id)), {})
        
        # Override frontend request based on actual database status
        is_meeting_enabled = agent_map.get('meeting_enabled', False) and req.is_booking_agent

        availability_instruction = ""
        if is_meeting_enabled:
            print(f"[TRIGGER] 📅 Meeting booking is ENABLED for agent {req.agent_id}. Fetching availability...")
            api_key = agent_map.get('cal_api_key')
            event_type_id = agent_map.get('cal_event_type_id')
            
            if not api_key or not event_type_id:
                user_profile = supabase_service.get_user_profile(user_id)
                api_key = api_key or user_profile.get('cal_api_key')
                event_type_id = event_type_id or user_profile.get('cal_event_type_id')
                
            availability_instruction = cal.build_availability_instruction(
                api_key=api_key,
                event_type_id=event_type_id,
                user_id=user_id,
                agent_id=req.agent_id
            )
        else:
            print(f"[TRIGGER] 🔇 Meeting booking is DISABLED for agent {req.agent_id}. Skipping availability.")
            availability_instruction = "IMPORTANT: The meeting booking function is currently OFF. Do NOT suggest any dates or times to the user. Inform them that booking is unavailable if they ask."
            
        result = tabbly.trigger_call(
            agent_id=req.agent_id,
            called_to=req.phone_number,
            custom_instruction=availability_instruction,
            custom_first_line=req.custom_first_line,
            custom_identifiers="booking:enabled" if is_meeting_enabled else "booking:disabled"
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
    """Fetches meeting logs and merges them with agent names and call log metadata."""
    try:
        logs = supabase_service.get_meeting_logs(user_id)
        
        # Fetch tabbly agents to map names
        raw_agents = tabbly.get_agents()
        agent_names = {str(a.get("id")): a.get("agent_name", "Unknown Agent") for a in raw_agents}
        
        # Fetch tabbly call logs for all of the user's agent IDs to build a mapping
        user_agent_ids = supabase_service.get_user_agent_ids(user_id)
        call_logs_map = {}
        for agent_id in user_agent_ids:
            try:
                raw_logs = tabbly.fetch_call_logs(agent_id, limit=100)
                for log in raw_logs:
                    call_id = log.get("participant_identity")
                    if call_id:
                        call_logs_map[str(call_id)] = log
            except Exception as e:
                print(f"Error fetching tabbly logs for agent {agent_id}: {e}")
        
        for log in logs:
            log["agent_name"] = agent_names.get(str(log.get("agent_id")), "Unknown Agent")
            
            # Enrich with Tabbly call log details
            call_id = str(log.get("call_id"))
            if call_id in call_logs_map:
                t_log = call_logs_map[call_id]
                log["phone_number"] = t_log.get("called_to", "")
                log["date"] = t_log.get("called_time", "")
                log["recording_url"] = t_log.get("call_recording_url")
                log["transcript"] = t_log.get("call_transcript")
                log["json_output"] = t_log.get("call_json_output")
            else:
                log["phone_number"] = ""
                log["date"] = log.get("created_at")
                log["recording_url"] = None
                log["transcript"] = None
                log["json_output"] = None
            
        return {"success": True, "logs": logs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
