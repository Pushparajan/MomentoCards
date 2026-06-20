from sqlalchemy.orm import Session

from app.models.models import Campaign, CampaignStage
from app.services.deliverable_service import refresh_deliverable_status
from app.services.workflow.stages import advance_to, require_stage


def submit_review(db: Session, campaign: Campaign, approved: bool, comments: str | None) -> Campaign:
    """Refreshes generation status from Replicate, then either advances to
    Launch (approved) or sends the campaign back to Content for another pass
    at copy/photos before regenerating."""
    require_stage(campaign, CampaignStage.review)

    if campaign.deliverable:
        refresh_deliverable_status(db, campaign.deliverable)

    campaign.review = {"approved": approved, "comments": comments}

    if approved:
        advance_to(campaign, CampaignStage.launch)
    else:
        campaign.stage = CampaignStage.content  # explicit revert, not advance_to (which forbids going backward)

    db.commit()
    db.refresh(campaign)
    return campaign
