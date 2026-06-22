from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.models import Brand, BrandAsset, LoraCategory, LoraModel, TrainingStatus
from app.schemas.schemas import LoraTrainingOut
from app.services import storage
from app.services.replicate_client import get_training
from app.services.training_service import start_training as _start_training

router = APIRouter(prefix="/brands", tags=["training"])

MIN_TRAINING_IMAGES = 10


@router.post("/{brand_id}/lora/train-from-upload", response_model=LoraTrainingOut)
async def upload_images_and_train(
    brand_id: str, files: list[UploadFile], category: LoraCategory = LoraCategory.branding, db: Session = Depends(get_db)
):
    """One-call flow: user uploads their reference photos (10+) and a custom
    LoRA training run is kicked off immediately on Replicate. Once it
    succeeds (poll via GET .../train/{lora_id}), the resulting weights can be
    selected as `style_lora_model_id` in the campaign Layout stage to brand
    any card/flyer/etc. generated for this brand. `category` slots the LoRA
    into the branding/typography/locale/community/subject preset matrix."""
    brand = db.get(Brand, brand_id)
    if not brand:
        raise HTTPException(404, "Brand not found")
    if len(files) < MIN_TRAINING_IMAGES:
        raise HTTPException(400, f"Upload at least {MIN_TRAINING_IMAGES} reference images to train a custom LoRA")

    for file in files:
        content = await file.read()
        asset = BrandAsset(brand_id=brand_id, file_path=storage.save_upload(brand_id, file.filename, content))
        db.add(asset)
    db.commit()

    return LoraTrainingOut.from_orm_model(_start_training(db, brand_id, category))


@router.post("/{brand_id}/train", response_model=LoraTrainingOut)
def train_brand_lora(brand_id: str, category: LoraCategory = LoraCategory.branding, db: Session = Depends(get_db)):
    """Trains on whatever images were previously uploaded via POST /assets."""
    brand = db.get(Brand, brand_id)
    if not brand:
        raise HTTPException(404, "Brand not found")
    asset_count = db.query(BrandAsset).filter(BrandAsset.brand_id == brand_id).count()
    if asset_count < MIN_TRAINING_IMAGES:
        raise HTTPException(400, f"Upload at least {MIN_TRAINING_IMAGES} reference images before training")

    return LoraTrainingOut.from_orm_model(_start_training(db, brand_id, category))


@router.get("/{brand_id}/train/{lora_id}", response_model=LoraTrainingOut)
def get_training_status(brand_id: str, lora_id: str, db: Session = Depends(get_db)):
    lora = db.get(LoraModel, lora_id)
    if not lora or lora.brand_id != brand_id:
        raise HTTPException(404, "Training job not found")

    if lora.replicate_training_id and lora.status == TrainingStatus.training:
        training = get_training(lora.replicate_training_id)
        if training.status == "succeeded":
            lora.status = TrainingStatus.succeeded
            output = training.output or {}
            lora.weights_url = output.get("weights") if isinstance(output, dict) else str(output)
        elif training.status == "failed":
            lora.status = TrainingStatus.failed
            lora.error = training.error
        db.commit()
        db.refresh(lora)
    return LoraTrainingOut.from_orm_model(lora)


@router.get("/{brand_id}/loras", response_model=list[LoraTrainingOut])
def list_loras(brand_id: str, db: Session = Depends(get_db)):
    """Lists all LoRAs trained for this brand, so the user can pick one
    (status == 'succeeded') when generating a card."""
    loras = db.query(LoraModel).filter(LoraModel.brand_id == brand_id).order_by(LoraModel.created_at.desc()).all()
    return [LoraTrainingOut.from_orm_model(lora) for lora in loras]
