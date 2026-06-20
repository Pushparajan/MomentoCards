from sqlalchemy.orm import Session

from app.models.models import Campaign, CampaignAsset, CampaignStage
from app.services import storage
from app.services.workflow.stages import advance_to, require_stage


def set_text_content(db: Session, campaign: Campaign, text_fields: dict) -> Campaign:
    """Fills in free-form copy for the chosen template, e.g. {"headline": ...,
    "body": ..., "cta": ...}. Can be called multiple times while still in the
    content stage to iterate before moving on."""
    require_stage(campaign, CampaignStage.content)
    content = campaign.content
    content["text_fields"] = text_fields
    campaign.content = content
    db.commit()
    db.refresh(campaign)
    return campaign


async def add_photo(db: Session, campaign: Campaign, filename: str, content_bytes: bytes, label: str | None) -> CampaignAsset:
    require_stage(campaign, CampaignStage.content)
    path = storage.save_upload(f"campaign_{campaign.id}", filename, content_bytes)
    asset = CampaignAsset(campaign_id=campaign.id, file_path=path, label=label)
    db.add(asset)
    db.commit()
    db.refresh(asset)
    return asset


def complete_content(db: Session, campaign: Campaign) -> Campaign:
    advance_to(campaign, CampaignStage.preview)
    db.commit()
    db.refresh(campaign)
    return campaign
