from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.models import Campaign, CampaignStage
from app.services.deliverable_service import refresh_deliverable_status
from app.services.workflow.stages import advance_to, require_stage


def save_final_canvas(db: Session, campaign: Campaign, canvas_json: dict) -> Campaign:
    """The Review-stage WYSIWYG pass: the user edits the AI-generated card
    in-place (fabric.js canvas seeded with the generated output_url as
    background) and saves their final composition before it can be approved
    for Launch. Refreshes generation status first so the canvas can reference
    the finished output."""
    require_stage(campaign, CampaignStage.review)
    if campaign.deliverable:
        refresh_deliverable_status(db, campaign.deliverable)

    review = campaign.review
    review["final_canvas_json"] = canvas_json
    review["final_approved"] = False
    campaign.review = review
    db.commit()
    db.refresh(campaign)
    return campaign


def submit_review(db: Session, campaign: Campaign, approved: bool, comments: str | None) -> Campaign:
    """Approve -> advances to Launch (only once the final canvas has been
    saved). Reject -> sends the campaign back to Content for another pass at
    copy/photos before regenerating."""
    require_stage(campaign, CampaignStage.review)

    review = campaign.review
    if approved and "final_canvas_json" not in review:
        raise HTTPException(400, "Save the final WYSIWYG canvas (PUT .../review/final-canvas) before approving")

    review["approved"] = approved
    review["comments"] = comments
    if approved:
        review["final_approved"] = True
    campaign.review = review

    if approved:
        advance_to(campaign, CampaignStage.launch)
    else:
        campaign.stage = CampaignStage.content  # explicit revert, not advance_to (which forbids going backward)

    db.commit()
    db.refresh(campaign)
    return campaign
