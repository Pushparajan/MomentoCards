from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.models import Brand, Campaign
from app.schemas.schemas import (
    AudienceAnswerRequest,
    AudienceQuestionOut,
    CampaignCreate,
    CampaignOut,
    ContentTextRequest,
    FinalCanvasSaveRequest,
    GoalRequest,
    LayoutRequest,
    PreviewSaveRequest,
    ReviewRequest,
)
from app.services.workflow import (
    audience_service,
    content_service,
    generate_service,
    goal_service,
    launch_service,
    layout_service,
    preview_service,
    review_service,
)

router = APIRouter(prefix="/campaigns", tags=["campaigns"])


def _get_campaign(db: Session, campaign_id: str) -> Campaign:
    campaign = db.get(Campaign, campaign_id)
    if not campaign:
        raise HTTPException(404, "Campaign not found")
    return campaign


@router.post("", response_model=CampaignOut)
def create_campaign(payload: CampaignCreate, db: Session = Depends(get_db)):
    brand = db.get(Brand, payload.brand_id)
    if not brand:
        raise HTTPException(404, "Brand not found")
    campaign = Campaign(brand_id=brand.id)
    db.add(campaign)
    db.commit()
    db.refresh(campaign)
    return campaign


@router.get("/{campaign_id}", response_model=CampaignOut)
def get_campaign(campaign_id: str, db: Session = Depends(get_db)):
    return _get_campaign(db, campaign_id)


@router.post("/{campaign_id}/goal", response_model=CampaignOut)
def set_goal(campaign_id: str, payload: GoalRequest, db: Session = Depends(get_db)):
    campaign = _get_campaign(db, campaign_id)
    return goal_service.set_goal(db, campaign, payload.goal_text, payload.intent)


@router.post("/{campaign_id}/layout", response_model=CampaignOut)
def set_layout(campaign_id: str, payload: LayoutRequest, db: Session = Depends(get_db)):
    campaign = _get_campaign(db, campaign_id)
    return layout_service.set_layout(
        db,
        campaign,
        payload.document_type_key,
        payload.style_lora_model_id,
        payload.canvas_width,
        payload.canvas_height,
        payload.grid_pages,
    )


@router.post("/{campaign_id}/content/text", response_model=CampaignOut)
def set_content_text(campaign_id: str, payload: ContentTextRequest, db: Session = Depends(get_db)):
    campaign = _get_campaign(db, campaign_id)
    return content_service.set_text_content(db, campaign, payload.text_fields)


@router.post("/{campaign_id}/content/photos")
async def upload_content_photos(campaign_id: str, files: list[UploadFile], db: Session = Depends(get_db)):
    campaign = _get_campaign(db, campaign_id)
    saved = []
    for file in files:
        content_bytes = await file.read()
        asset = await content_service.add_photo(db, campaign, file.filename, content_bytes, label=None)
        saved.append(asset.id)
    return {"saved_asset_ids": saved}


@router.post("/{campaign_id}/content/complete", response_model=CampaignOut)
def complete_content(campaign_id: str, db: Session = Depends(get_db)):
    campaign = _get_campaign(db, campaign_id)
    return content_service.complete_content(db, campaign)


@router.put("/{campaign_id}/preview", response_model=CampaignOut)
def save_preview(campaign_id: str, payload: PreviewSaveRequest, db: Session = Depends(get_db)):
    campaign = _get_campaign(db, campaign_id)
    return preview_service.save_canvas(db, campaign, payload.canvas_json)


@router.post("/{campaign_id}/preview/approve", response_model=CampaignOut)
def approve_preview(campaign_id: str, db: Session = Depends(get_db)):
    campaign = _get_campaign(db, campaign_id)
    return preview_service.approve_preview(db, campaign)


@router.get("/{campaign_id}/audience/next-question", response_model=AudienceQuestionOut | None)
def get_next_question(campaign_id: str, db: Session = Depends(get_db)):
    campaign = _get_campaign(db, campaign_id)
    question = audience_service.next_question(campaign)
    return question


@router.post("/{campaign_id}/audience/answer", response_model=CampaignOut)
def answer_question(campaign_id: str, payload: AudienceAnswerRequest, db: Session = Depends(get_db)):
    campaign = _get_campaign(db, campaign_id)
    return audience_service.answer_question(db, campaign, payload.key, payload.answer)


@router.post("/{campaign_id}/audience/complete", response_model=CampaignOut)
def complete_audience(campaign_id: str, db: Session = Depends(get_db)):
    campaign = _get_campaign(db, campaign_id)
    return audience_service.complete_audience(db, campaign)


@router.post("/{campaign_id}/generate", response_model=CampaignOut)
def generate(campaign_id: str, db: Session = Depends(get_db)):
    campaign = _get_campaign(db, campaign_id)
    return generate_service.run_generate(db, campaign)


@router.put("/{campaign_id}/review/final-canvas", response_model=CampaignOut)
def save_final_canvas(campaign_id: str, payload: FinalCanvasSaveRequest, db: Session = Depends(get_db)):
    campaign = _get_campaign(db, campaign_id)
    return review_service.save_final_canvas(db, campaign, payload.canvas_json)


@router.post("/{campaign_id}/review", response_model=CampaignOut)
def review(campaign_id: str, payload: ReviewRequest, db: Session = Depends(get_db)):
    campaign = _get_campaign(db, campaign_id)
    return review_service.submit_review(db, campaign, payload.approved, payload.comments)


@router.post("/{campaign_id}/launch", response_model=CampaignOut)
def launch(campaign_id: str, db: Session = Depends(get_db)):
    campaign = _get_campaign(db, campaign_id)
    return launch_service.launch(db, campaign)
