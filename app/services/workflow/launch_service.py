from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.models import Campaign, CampaignStage, JobStatus
from app.services.workflow.stages import advance_to, require_stage


def launch(db: Session, campaign: Campaign) -> Campaign:
    """Finalizes the campaign once review has approved it. Only the
    digital_export fulfillment path is implemented today -- this returns the
    generated page URLs; print/live-publish are out of scope."""
    require_stage(campaign, CampaignStage.launch)

    deliverable = campaign.deliverable
    if not deliverable or deliverable.status != JobStatus.succeeded:
        raise HTTPException(400, "Deliverable is not finished generating yet")
    if not campaign.review.get("final_approved"):
        raise HTTPException(400, "Final WYSIWYG canvas must be saved and approved before launch")

    output_urls = [p.output_url for p in deliverable.pages]
    campaign.launch = {"output_urls": output_urls, "fulfillment": "digital_export"}
    advance_to(campaign, CampaignStage.done)
    db.commit()
    db.refresh(campaign)
    return campaign
