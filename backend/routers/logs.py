from fastapi import APIRouter, HTTPException, Query, BackgroundTasks, Depends
from services import tabbly, supabase_service
from middleware.auth import get_user_id
import os
import requests

router = APIRouter(prefix="/logs", tags=["logs"])

DEFAULT_AGENT_ID = os.getenv("TABBLY_AGENT_ID")

RECORDINGS_DIR = "recordings"
TRANSCRIPTS_DIR = "transcripts"
os.makedirs(RECORDINGS_DIR, exist_ok=True)
os.makedirs(TRANSCRIPTS_DIR, exist_ok=True)

def sync_call_data_offline(log: dict):
    """Downloads transcript and recording to local directories if they don't exist."""
    call_id = log.get("participant_identity", "unknown")
    called_to = log.get("called_to", "unknown").replace("+", "")
    recording_url = log.get("call_recording_url")
    transcript = log.get("call_transcript")
    created_at = str(log.get("called_time", "unknown")).replace(" ", "_").replace(":", "-")
    
    base_name = f"call_{call_id}_{called_to}_{created_at}"
    
    # Save Transcript
    if transcript:
        transcript_path = os.path.join(TRANSCRIPTS_DIR, f"{base_name}.txt")
        if not os.path.exists(transcript_path):
            try:
                with open(transcript_path, "w", encoding="utf-8") as f:
                    f.write(transcript)
            except Exception as e:
                print(f"Error saving transcript for {call_id}: {e}")

    # Downlad Recording
    if recording_url and recording_url != "N/A":
        recording_path = os.path.join(RECORDINGS_DIR, f"{base_name}.mp3")
        if not os.path.exists(recording_path):
            try:
                rec_res = requests.get(recording_url)
                if rec_res.status_code == 200:
                    with open(recording_path, "wb") as f:
                        f.write(rec_res.content)
            except Exception as e:
                print(f"Error downloading recording for {call_id}: {e}")

@router.get("/call-logs")
def get_call_logs(background_tasks: BackgroundTasks, limit: int = Query(50, le=100), user_id: str = Depends(get_user_id)):
    """Fetches call logs from all agents and automatically saves recordings offline."""
    try:
        # Build agent map
        agents_map = {}
        if DEFAULT_AGENT_ID:
            agents_map[str(DEFAULT_AGENT_ID)] = "Support Hub"
        
        try:
            raw_agents = tabbly.get_agents()
            user_agent_ids = supabase_service.get_user_agent_ids(user_id)
            
            for raw in raw_agents:
                a_id = str(raw.get("id"))
                if a_id in user_agent_ids:
                    agents_map[a_id] = raw.get("agent_name", f"Agent {a_id}")
        except Exception as e:
            print(f"Error fetching agent map for logs: {e}")

        all_logs = []
        for agent_id, agent_name in agents_map.items():
            try:
                raw_logs = tabbly.fetch_call_logs(agent_id, limit=limit)
                for log in raw_logs:
                    # Sync files to disk locally via background task so we don't slow down response
                    background_tasks.add_task(sync_call_data_offline, log)
                    
                    all_logs.append({
                        "call_id":       log.get("participant_identity", ""),
                        "phone_number":  log.get("called_to", ""),
                        "date":          log.get("called_time", ""),
                        "status":        "Completed" if log.get("call_transcript") else "Processing",
                        "recording_url": log.get("call_recording_url"),
                        "transcript":    log.get("call_transcript"),
                        "json_output":   log.get("call_json_output"),
                        "agent_name":    agent_name,
                    })
            except Exception as e:
                print(f"Error fetching logs for agent {agent_id}: {e}")
                continue

        # Sort logs by date descending
        all_logs.sort(key=lambda x: x["date"], reverse=True)
        return {"logs": all_logs[:limit]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats")
def get_dashboard_stats(user_id: str = Depends(get_user_id)):
    """Aggregates stats for the user's dashboard."""
    try:
        user_agent_ids = supabase_service.get_user_agent_ids(user_id)
        total_calls = 0
        total_completed = 0
        
        for agent_id in user_agent_ids:
            try:
                # We fetch a larger sample to calculate aggregate stats
                raw_logs = tabbly.fetch_call_logs(agent_id, limit=100)
                total_calls += len(raw_logs)
                total_completed += sum(1 for log in raw_logs if log.get("call_transcript"))
                # You could add more like avg duration here
            except Exception as e:
                print(f"Error fetching stats for agent {agent_id}: {e}")
                continue

        return {
            "total_calls": total_calls,
            "total_completed": total_completed,
            "active_agents": len(user_agent_ids)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
