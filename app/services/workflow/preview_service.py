from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.models import Campaign, CampaignStage
from app.services.workflow.stages import advance_to, require_stage


def save_canvas(db: Session, campaign: Campaign, canvas_json: dict) -> Campaign:
    """Stores the fabric.js canvas serialization (objects/layers, positions,
    fonts, image refs) produced by the frontend editor as the user edits the
    composition. Safe to call repeatedly -- each save just overwrites the
    working draft until approved."""
    require_stage(campaign, CampaignStage.preview)
    preview = campaign.preview
    preview["canvas_json"] = canvas_json
    preview["approved"] = False
    campaign.preview = preview
    db.commit()
    db.refresh(campaign)
    return campaign


def approve_preview(db: Session, campaign: Campaign) -> Campaign:
    require_stage(campaign, CampaignStage.preview)
    preview = campaign.preview
    if "canvas_json" not in preview:
        raise HTTPException(400, "Save a canvas draft before approving")
    preview["approved"] = True
    campaign.preview = preview
    advance_to(campaign, CampaignStage.audience)
    db.commit()
    db.refresh(campaign)
    return campaign
