from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.models import (
    Brand,
    BrandAsset,
    Deliverable,
    DeliverablePage,
    DocumentType,
    JobStatus,
    LayoutKind,
    LoraModel,
    TrainingStatus,
)
from app.services import storage
from app.services.grid_generator import draw_blank_grid, to_canny
from app.services.prompt_builder import build_negative_prompt, build_prompt
from app.services.replicate_client import generate_calendar_page, get_prediction


def generate_page(
    db: Session,
    deliverable: Deliverable,
    page: DeliverablePage,
    lora_weights_url: str | None,
    ip_adapter_image_url: str | None,
) -> None:
    document_type: DocumentType = deliverable.document_type
    brand: Brand = deliverable.brand

    canny_path = None
    if document_type.requires_grid:
        params = page.params
        year, month = params.get("year"), params.get("month")
        if not year or not month:
            page.status = JobStatus.failed
            page.error = "Grid layouts require 'year' and 'month' in page params"
            db.commit()
            return
        grid_path, canny_path = storage.grid_paths(page.id)
        draw_blank_grid(year, month, grid_path)
        to_canny(grid_path, canny_path)
        page.grid_path = grid_path
        page.canny_path = canny_path
        db.commit()

    page_context = page.params.get("panel") or page.params.get("context")
    prompt = build_prompt(
        layout_kind=LayoutKind(document_type.layout_kind),
        style=deliverable.style,
        mood_keywords=brand.mood_keywords,
        primary_color=brand.primary_color,
        secondary_color=brand.secondary_color,
        page_context=page_context,
    )
    negative_prompt = build_negative_prompt()

    try:
        canny_file = open(canny_path, "rb") if canny_path else None
        try:
            prediction = generate_calendar_page(
                canny_image_url=canny_file,
                ip_adapter_image_url=ip_adapter_image_url,
                lora_weights_url=lora_weights_url,
                prompt=prompt,
                negative_prompt=negative_prompt,
            )
        finally:
            if canny_file:
                canny_file.close()
        page.replicate_prediction_id = prediction.id
        page.status = JobStatus.running
    except Exception as exc:  # noqa: BLE001
        page.status = JobStatus.failed
        page.error = str(exc)
    db.commit()


def resolve_lora_weights_url(db: Session, brand_id: str, use_brand_lora: bool) -> str | None:
    if not use_brand_lora:
        return None
    lora = (
        db.query(LoraModel)
        .filter(LoraModel.brand_id == brand_id, LoraModel.status == TrainingStatus.succeeded)
        .order_by(LoraModel.created_at.desc())
        .first()
    )
    if not lora:
        raise HTTPException(400, "No trained LoRA available for this brand; train one first or set use_brand_lora=false")
    return lora.weights_url


def resolve_ip_adapter_image_url(db: Session, brand_id: str, asset_id: str | None) -> str | None:
    if not asset_id:
        return None
    asset = db.get(BrandAsset, asset_id)
    if not asset or asset.brand_id != brand_id:
        raise HTTPException(404, "IP-Adapter reference asset not found for this brand")
    return asset.file_path


def create_deliverable(
    db: Session,
    brand: Brand,
    document_type: DocumentType,
    title: str | None,
    style: str,
    page_param_list: list[dict],
    lora_weights_url: str | None,
    ip_adapter_image_url: str | None,
) -> Deliverable:
    """Creates a Deliverable with N pages and immediately kicks off generation
    for each. Shared by the standalone /deliverables API and the campaign
    workflow's Generate stage."""
    deliverable = Deliverable(
        brand_id=brand.id,
        document_type_id=document_type.id,
        title=title,
        style=style,
        status=JobStatus.running,
    )
    db.add(deliverable)
    db.commit()

    for idx, params in enumerate(page_param_list, start=1):
        page = DeliverablePage(deliverable_id=deliverable.id, page_number=idx, status=JobStatus.pending)
        page.params = params
        db.add(page)
    db.commit()
    db.refresh(deliverable)

    for page in deliverable.pages:
        generate_page(db, deliverable, page, lora_weights_url, ip_adapter_image_url)

    db.refresh(deliverable)
    if any(p.status == JobStatus.failed for p in deliverable.pages):
        deliverable.status = JobStatus.failed
    db.commit()
    db.refresh(deliverable)
    return deliverable


def refresh_deliverable_status(db: Session, deliverable: Deliverable) -> Deliverable:
    for page in deliverable.pages:
        if page.replicate_prediction_id and page.status == JobStatus.running:
            prediction = get_prediction(page.replicate_prediction_id)
            if prediction.status == "succeeded":
                page.status = JobStatus.succeeded
                output = prediction.output
                page.output_url = output[0] if isinstance(output, list) else output
            elif prediction.status == "failed":
                page.status = JobStatus.failed
                page.error = prediction.error
    db.commit()

    if deliverable.pages and all(p.status == JobStatus.succeeded for p in deliverable.pages):
        deliverable.status = JobStatus.succeeded
    elif any(p.status == JobStatus.failed for p in deliverable.pages):
        deliverable.status = JobStatus.failed
    db.commit()
    db.refresh(deliverable)
    return deliverable
