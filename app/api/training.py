from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.models import Brand, BrandAsset, LoraModel, TrainingStatus
from app.schemas.schemas import LoraTrainingOut
from app.services import storage
from app.services.replicate_client import get_training, start_lora_training

router = APIRouter(prefix="/brands", tags=["training"])

MIN_TRAINING_IMAGES = 10


def _start_training(db: Session, brand_id: str) -> LoraModel:
    zip_path = storage.zip_brand_assets(brand_id)
    trigger_word = f"brand{brand_id[:8]}"

    lora = LoraModel(brand_id=brand_id, status=TrainingStatus.training)
    db.add(lora)
    db.commit()

    try:
        with open(zip_path, "rb") as f:
            training = start_lora_training(zip_url=f, trigger_word=trigger_word)
        lora.replicate_training_id = training.id
    except Exception as exc:  # noqa: BLE001
        lora.status = TrainingStatus.failed
        lora.error = str(exc)
    db.commit()
    db.refresh(lora)
    return lora


@router.post("/{brand_id}/lora/train-from-upload", response_model=LoraTrainingOut)
async def upload_images_and_train(brand_id: str, files: list[UploadFile], db: Session = Depends(get_db)):
    """One-call flow: user uploads their reference photos (10+) and a custom
    LoRA training run is kicked off immediately on Replicate. Once it
    succeeds (poll via GET .../train/{lora_id}), the resulting weights can be
    selected as `style_lora_model_id` in the campaign Layout stage to brand
    any card/flyer/etc. generated for this brand."""
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

    return _start_training(db, brand_id)


@router.post("/{brand_id}/train", response_model=LoraTrainingOut)
def train_brand_lora(brand_id: str, db: Session = Depends(get_db)):
    """Trains on whatever images were previously uploaded via POST /assets."""
    brand = db.get(Brand, brand_id)
    if not brand:
        raise HTTPException(404, "Brand not found")
    asset_count = db.query(BrandAsset).filter(BrandAsset.brand_id == brand_id).count()
    if asset_count < MIN_TRAINING_IMAGES:
        raise HTTPException(400, f"Upload at least {MIN_TRAINING_IMAGES} reference images before training")

    return _start_training(db, brand_id)


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
    return lora


@router.get("/{brand_id}/loras", response_model=list[LoraTrainingOut])
def list_loras(brand_id: str, db: Session = Depends(get_db)):
    """Lists all LoRAs trained for this brand, so the user can pick one
    (status == 'succeeded') when generating a card."""
    return db.query(LoraModel).filter(LoraModel.brand_id == brand_id).order_by(LoraModel.created_at.desc()).all()
