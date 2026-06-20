from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.models import Brand, Deliverable, DocumentType
from app.schemas.schemas import DeliverableCreate, DeliverableOut
from app.services.deliverable_service import (
    create_deliverable,
    refresh_deliverable_status,
    resolve_ip_adapter_image_url,
    resolve_lora_weights_url,
)

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
