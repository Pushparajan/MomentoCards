from fastapi import HTTPException

from app.models.models import STAGE_ORDER, Campaign, CampaignStage


def require_stage(campaign: Campaign, *allowed: CampaignStage) -> None:
    if campaign.stage not in allowed:
        raise HTTPException(
            409,
            f"Campaign is at stage '{campaign.stage.value}'; expected one of {[s.value for s in allowed]}",
        )


def advance_to(campaign: Campaign, stage: CampaignStage) -> None:
    current_idx = STAGE_ORDER.index(campaign.stage)
    target_idx = STAGE_ORDER.index(stage)
    if target_idx < current_idx:
        raise HTTPException(409, f"Cannot move backward from '{campaign.stage.value}' to '{stage.value}'")
    campaign.stage = stage
