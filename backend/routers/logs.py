from fastapi import APIRouter, HTTPException, Query
from services import tabbly
import os

router = APIRouter(prefix="/logs", tags=["logs"])

AGENT_ID = os.getenv("TABBLY_AGENT_ID")

@router.get("/call-logs")
def get_call_logs(limit: int = Query(50, le=100)):
    """Fetches call logs, transcripts, and recording URLs from Tabbly."""
    try:
        raw_logs = tabbly.fetch_call_logs(AGENT_ID, limit=limit)
        logs = []
        for log in raw_logs:
            logs.append({
                "call_id":       log.get("participant_identity", ""),
                "phone_number":  log.get("called_to", ""),
                "date":          log.get("called_time", ""),
                "status":        "Completed" if log.get("call_transcript") else "Processing",
                "recording_url": log.get("call_recording_url"),
                "transcript":    log.get("call_transcript"),
                "json_output":   log.get("call_json_output"),
            })
        return {"logs": logs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
