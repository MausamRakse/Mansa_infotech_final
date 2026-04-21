from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from services import tabbly, supabase_service
from middleware.auth import get_user_id

router = APIRouter(prefix="/campaigns", tags=["campaigns"])

class CreateCampaignRequest(BaseModel):
    campaign_name: str
    agent_id: str
    start_time: str
    end_time: str
    time_zone: str
    custom_first_line: str


@router.post("/create")
def create_campaign(req: CreateCampaignRequest, user_id: str = Depends(get_user_id)):
    """Proxies campaign creation to Tabbly."""
    try:
        # Verify ownership of agent
        user_agent_ids = supabase_service.get_user_agent_ids(user_id)
        if str(req.agent_id) not in user_agent_ids and not str(req.agent_id).startswith("default-"):
            raise HTTPException(status_code=403, detail="Not authorized to use this agent for campaigns")

        return tabbly.create_campaign(
            campaign_name=req.campaign_name,
            agent_id=req.agent_id,
            start_time=req.start_time,
            end_time=req.end_time,
            time_zone=req.time_zone,
            custom_first_line=req.custom_first_line
        )
    except Exception as e:
        print(f"DEBUG: Campaign creation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/update")
def update_campaign(campaign_id: int, current_status: str = None, user_id: str = Depends(get_user_id)):
    try:
        return tabbly.update_campaign(campaign_id, current_status=current_status)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

