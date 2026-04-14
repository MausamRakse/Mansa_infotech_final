from fastapi import APIRouter, Request, BackgroundTasks
from services import post_call_service
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks", tags=["webhooks"])

@router.post("/tabbly")
async def tabbly_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    Webhook received when a Tabbly call finishes.
    """
    try:
        data = await request.json()
        logger.info(f"Webhook received from Tabbly: {data}")
        
        # Tabbly webhook format might vary, but we expect participant_identity (call_id)
        call_id = data.get("participant_identity") or data.get("call_id")
        
        if call_id:
            # Process results in the background so we can respond to the webhook immediately
            background_tasks.add_task(post_call_service.process_call_results, call_id)
            return {"success": True, "message": f"Processing started for {call_id}"}
        else:
            return {"success": False, "message": "No call_id found in webhook payload"}
            
    except Exception as e:
        logger.error(f"Error handling Tabbly webhook: {e}")
        return {"success": False, "error": str(e)}
