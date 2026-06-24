from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.models import Campaign, CampaignStage, DocumentType, LoraModel, TrainingStatus
from app.services import storage
from app.services.template_service import find_best_template
from app.services.workflow.stages import advance_to, require_stage


def upload_background(db: Session, campaign: Campaign, filename: str, content_bytes: bytes) -> str:
    """Stores a user-supplied image to seed the Preview canvas as a background
    layer. This is a straight upload + URL-seeding step, not AI layer
    separation -- the user still builds/arranges layers themselves in the
    canvas editor on top of this image."""
    require_stage(campaign, CampaignStage.layout)
    path = storage.save_upload(f"campaign_{campaign.id}", filename, content_bytes)
    url = storage.to_url(path)
    layout = campaign.layout
    layout["custom_background_url"] = url
    campaign.layout = layout
    db.commit()
    db.refresh(campaign)
    return url


def set_layout(
    db: Session,
    campaign: Campaign,
    document_type_key: str,
    style_lora_model_id: str | None,
    canvas_width: int,
    canvas_height: int,
    grid_pages: list[dict] | None = None,
) -> Campaign:
    """Picks the structural template (DocumentType, i.e. its layout_kind/grid
    rules) and, optionally, a trained brand LoRA to use as the visual identity
    for this campaign -- the 'upload template/lora' step."""
    require_stage(campaign, CampaignStage.layout)

    document_type = db.query(DocumentType).filter(DocumentType.key == document_type_key).first()
    if not document_type:
        raise HTTPException(404, f"Unknown document_type_key '{document_type_key}'")

    if style_lora_model_id:
        lora = db.get(LoraModel, style_lora_model_id)
        if not lora or lora.brand_id != campaign.brand_id:
            raise HTTPException(404, "LoRA model not found for this brand")
        if lora.status != TrainingStatus.succeeded:
            raise HTTPException(400, "Selected LoRA has not finished training")

    if document_type.requires_grid and not grid_pages:
        raise HTTPException(400, "This document type requires 'grid_pages' (e.g. [{'month': 6, 'year': 2026}])")

    # Template Intelligence layer: best-effort suggestion based on the Goal
    # stage's intent + goal_text; purely advisory -- the layout/canvas stages
    # don't require a match, they just get one offered if available.
    intent = campaign.goal.get("intent")
    goal_text = campaign.goal.get("goal_text", "")
    matched_template = find_best_template(db, document_type.id, intent, goal_text)

    campaign.layout = {
        "document_type_key": document_type_key,
        "style_lora_model_id": style_lora_model_id,
        "canvas_width": canvas_width,
        "canvas_height": canvas_height,
        "grid_pages": grid_pages or [],
        "suggested_template_id": matched_template.id if matched_template else None,
    }
    advance_to(campaign, CampaignStage.content)
    db.commit()
    db.refresh(campaign)
    return campaign
