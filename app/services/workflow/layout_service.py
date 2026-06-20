from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.models import Campaign, CampaignStage, DocumentType, LoraModel, TrainingStatus
from app.services.workflow.stages import advance_to, require_stage


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

    campaign.layout = {
        "document_type_key": document_type_key,
        "style_lora_model_id": style_lora_model_id,
        "canvas_width": canvas_width,
        "canvas_height": canvas_height,
        "grid_pages": grid_pages or [],
    }
    advance_to(campaign, CampaignStage.content)
    db.commit()
    db.refresh(campaign)
    return campaign
