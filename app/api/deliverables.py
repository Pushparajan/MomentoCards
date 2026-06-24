from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.models import Brand, Deliverable, DeliverablePage, DocumentType
from app.schemas.schemas import DeliverableOut, DeliverablePageOut, DeliverableCreate, FavoriteToggleRequest, VideoGenerateRequest
from app.services.deliverable_service import (
    create_deliverable,
    refresh_deliverable_status,
    resolve_ip_adapter_image_url,
    resolve_lora_weights_url,
)
from app.services.video_service import start_video_for_page

router = APIRouter(prefix="/deliverables", tags=["deliverables"])


@router.post("", response_model=DeliverableOut)
def create_deliverable_endpoint(payload: DeliverableCreate, db: Session = Depends(get_db)):
    brand = db.get(Brand, payload.brand_id)
    if not brand:
        raise HTTPException(404, "Brand not found")
    document_type = db.query(DocumentType).filter(DocumentType.key == payload.document_type_key).first()
    if not document_type:
        raise HTTPException(404, f"Unknown document_type_key '{payload.document_type_key}'")

    lora_weights_url = resolve_lora_weights_url(db, brand.id, payload.use_brand_lora)
    ip_adapter_image_url = resolve_ip_adapter_image_url(db, brand.id, payload.ip_adapter_asset_id)

    page_specs = payload.pages or [{} for _ in range(document_type.default_page_count)]
    page_param_list = [spec.params if hasattr(spec, "params") else spec.get("params", {}) for spec in page_specs]

    return create_deliverable(
        db, brand, document_type, payload.title, payload.style, page_param_list, lora_weights_url, ip_adapter_image_url
    )


@router.get("/{deliverable_id}", response_model=DeliverableOut)
def get_deliverable(deliverable_id: str, db: Session = Depends(get_db)):
    deliverable = db.get(Deliverable, deliverable_id)
    if not deliverable:
        raise HTTPException(404, "Deliverable not found")
    return refresh_deliverable_status(db, deliverable)


@router.get("", response_model=list[DeliverableOut])
def list_deliverables(
    brand_id: str | None = None,
    document_type_key: str | None = None,
    favorites_only: bool = False,
    db: Session = Depends(get_db),
):
    """Backs the Library screen: All/Favorites/by-deliverable-type filters."""
    query = db.query(Deliverable)
    if brand_id:
        query = query.filter(Deliverable.brand_id == brand_id)
    if favorites_only:
        query = query.filter(Deliverable.is_favorite == 1)
    if document_type_key:
        document_type = db.query(DocumentType).filter(DocumentType.key == document_type_key).first()
        if not document_type:
            raise HTTPException(404, f"Unknown document_type_key '{document_type_key}'")
        query = query.filter(Deliverable.document_type_id == document_type.id)
    deliverables = query.order_by(Deliverable.created_at.desc()).all()
    return [DeliverableOut.from_orm_model(d) for d in deliverables]


@router.put("/{deliverable_id}/favorite", response_model=DeliverableOut)
def set_favorite(deliverable_id: str, payload: FavoriteToggleRequest, db: Session = Depends(get_db)):
    deliverable = db.get(Deliverable, deliverable_id)
    if not deliverable:
        raise HTTPException(404, "Deliverable not found")
    deliverable.is_favorite = 1 if payload.is_favorite else 0
    db.commit()
    db.refresh(deliverable)
    return DeliverableOut.from_orm_model(deliverable)


@router.post("/pages/{page_id}/video", response_model=DeliverablePageOut)
def generate_video(page_id: str, payload: VideoGenerateRequest, db: Session = Depends(get_db)):
    page = db.get(DeliverablePage, page_id)
    if not page:
        raise HTTPException(404, "Deliverable page not found")
    return start_video_for_page(db, page, payload.prompt)
