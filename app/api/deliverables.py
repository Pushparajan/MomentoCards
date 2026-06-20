from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db
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
from app.schemas.schemas import DeliverableCreate, DeliverableOut
from app.services import storage
from app.services.grid_generator import draw_blank_grid, to_canny
from app.services.prompt_builder import build_negative_prompt, build_prompt
from app.services.replicate_client import generate_calendar_page, get_prediction

router = APIRouter(prefix="/deliverables", tags=["deliverables"])


def _generate_page(db: Session, deliverable: Deliverable, page: DeliverablePage, lora_weights_url: str | None, ip_adapter_image_url: str | None):
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


@router.post("", response_model=DeliverableOut)
def create_deliverable(payload: DeliverableCreate, db: Session = Depends(get_db)):
    brand = db.get(Brand, payload.brand_id)
    if not brand:
        raise HTTPException(404, "Brand not found")
    document_type = db.query(DocumentType).filter(DocumentType.key == payload.document_type_key).first()
    if not document_type:
        raise HTTPException(404, f"Unknown document_type_key '{payload.document_type_key}'")

    lora_weights_url = None
    if payload.use_brand_lora:
        lora = (
            db.query(LoraModel)
            .filter(LoraModel.brand_id == brand.id, LoraModel.status == TrainingStatus.succeeded)
            .order_by(LoraModel.created_at.desc())
            .first()
        )
        if not lora:
            raise HTTPException(400, "No trained LoRA available for this brand; train one first or set use_brand_lora=false")
        lora_weights_url = lora.weights_url

    ip_adapter_image_url = None
    if payload.ip_adapter_asset_id:
        asset = db.get(BrandAsset, payload.ip_adapter_asset_id)
        if not asset or asset.brand_id != brand.id:
            raise HTTPException(404, "IP-Adapter reference asset not found for this brand")
        ip_adapter_image_url = asset.file_path

    deliverable = Deliverable(
        brand_id=brand.id,
        document_type_id=document_type.id,
        title=payload.title,
        style=payload.style,
        status=JobStatus.running,
    )
    db.add(deliverable)
    db.commit()

    page_specs = payload.pages or [{"params": {}} for _ in range(document_type.default_page_count)]
    for idx, spec in enumerate(page_specs, start=1):
        params = spec.params if hasattr(spec, "params") else spec.get("params", {})
        page = DeliverablePage(deliverable_id=deliverable.id, page_number=idx, status=JobStatus.pending)
        page.params = params
        db.add(page)
    db.commit()
    db.refresh(deliverable)

    for page in deliverable.pages:
        _generate_page(db, deliverable, page, lora_weights_url, ip_adapter_image_url)

    db.refresh(deliverable)
    if any(p.status == JobStatus.failed for p in deliverable.pages):
        deliverable.status = JobStatus.failed
    db.commit()
    db.refresh(deliverable)
    return deliverable


@router.get("/{deliverable_id}", response_model=DeliverableOut)
def get_deliverable(deliverable_id: str, db: Session = Depends(get_db)):
    deliverable = db.get(Deliverable, deliverable_id)
    if not deliverable:
        raise HTTPException(404, "Deliverable not found")

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
