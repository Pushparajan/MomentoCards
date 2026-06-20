from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.models import Campaign, CampaignStage, DocumentType
from app.services.deliverable_service import (
    create_deliverable,
    resolve_ip_adapter_image_url,
    resolve_lora_weights_url,
)
from app.services.workflow.stages import advance_to, require_stage


def _build_page_context(campaign: Campaign) -> str:
    """Folds the Goal, Content text, and Audience Q&A answers into a single
    prompt-context string injected alongside the structural/style tags."""
    parts = []
    goal = campaign.goal
    if goal.get("goal_text"):
        parts.append(f"goal: {goal['goal_text']}")
    text_fields = campaign.content.get("text_fields", {})
    for key, value in text_fields.items():
        parts.append(f"{key}: {value}")
    for key, value in campaign.audience.get("answers", {}).items():
        parts.append(f"{key.replace('_', ' ')}: {value}")
    return "; ".join(parts)


def run_generate(db: Session, campaign: Campaign) -> Campaign:
    require_stage(campaign, CampaignStage.generate)

    document_type = db.query(DocumentType).filter(DocumentType.key == campaign.layout.get("document_type_key")).first()
    if not document_type:
        raise HTTPException(400, "Campaign layout is missing a valid document_type_key")

    use_brand_lora = bool(campaign.layout.get("style_lora_model_id"))
    lora_weights_url = resolve_lora_weights_url(db, campaign.brand_id, use_brand_lora)
    ip_adapter_image_url = resolve_ip_adapter_image_url(db, campaign.brand_id, campaign.content.get("ip_adapter_asset_id"))

    page_context = _build_page_context(campaign)
    grid_pages = campaign.layout.get("grid_pages") or []
    if document_type.requires_grid:
        page_param_list = [{"context": page_context, **gp} for gp in grid_pages]
    else:
        page_param_list = [{"context": page_context} for _ in range(document_type.default_page_count)]

    deliverable = create_deliverable(
        db,
        campaign.brand,
        document_type,
        title=campaign.goal.get("goal_text"),
        style=campaign.layout.get("style", "vector"),
        page_param_list=page_param_list,
        lora_weights_url=lora_weights_url,
        ip_adapter_image_url=ip_adapter_image_url,
    )

    campaign.deliverable_id = deliverable.id
    advance_to(campaign, CampaignStage.review)
    db.commit()
    db.refresh(campaign)
    return campaign
