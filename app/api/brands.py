from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.db import get_db
from app.models.models import Brand, BrandAsset, LoraCategory, LoraModel, Organization
from app.schemas.schemas import BrandCreate, BrandOut
from app.services import storage
from app.services.training_service import start_training

router = APIRouter(prefix="/brands", tags=["brands"])


@router.post("", response_model=BrandOut)
def create_brand(payload: BrandCreate, db: Session = Depends(get_db)):
    if payload.organization_id and not db.get(Organization, payload.organization_id):
        raise HTTPException(404, "Organization not found")
    brand = Brand(**payload.model_dump())
    db.add(brand)
    db.commit()
    db.refresh(brand)
    return brand


@router.get("/{brand_id}", response_model=BrandOut)
def get_brand(brand_id: str, db: Session = Depends(get_db)):
    brand = db.get(Brand, brand_id)
    if not brand:
        raise HTTPException(404, "Brand not found")
    return brand


@router.post("/{brand_id}/assets")
async def upload_assets(brand_id: str, files: list[UploadFile], db: Session = Depends(get_db)):
    """Saves reference assets and, once their count crosses
    AUTO_TRAIN_ASSET_THRESHOLD, automatically kicks off a branding-category
    LoRA training run (instead of requiring an explicit POST /train call) --
    skipped if a training run already exists, so re-uploading more assets
    later doesn't keep re-triggering training on every call."""
    brand = db.get(Brand, brand_id)
    if not brand:
        raise HTTPException(404, "Brand not found")
    saved = []
    for file in files:
        content = await file.read()
        path = storage.save_upload(brand_id, file.filename, content)
        asset = BrandAsset(brand_id=brand_id, file_path=path)
        db.add(asset)
        saved.append(path)
    db.commit()

    asset_count = db.query(BrandAsset).filter(BrandAsset.brand_id == brand_id).count()
    auto_triggered = False
    if asset_count >= settings.auto_train_asset_threshold:
        existing = db.query(LoraModel).filter(LoraModel.brand_id == brand_id).first()
        if not existing:
            start_training(db, brand_id, LoraCategory.branding)
            auto_triggered = True

    return {"saved": saved, "auto_train_triggered": auto_triggered}
