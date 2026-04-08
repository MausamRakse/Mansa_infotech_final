from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services import tabbly

router = APIRouter(prefix="/campaigns", tags=["campaigns"])

class CreateCampaignRequest(BaseModel):
    campaign_name: str
    agent_id: str
    start_time: str
    end_time: str
    time_zone: str
    custom_first_line: str

@router.post("/create")
def create_campaign(req: CreateCampaignRequest):
    """Proxies campaign creation to Tabbly."""
    try:
        # Note: agent_id is handled as int in the service layer
        result = tabbly.create_campaign(
            campaign_name=req.campaign_name,
            agent_id=req.agent_id,
            start_time=req.start_time,
            end_time=req.end_time,
            time_zone=req.time_zone,
            custom_first_line=req.custom_first_line
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
