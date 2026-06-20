from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.models import Brand, BrandAsset, LoraModel, TrainingStatus
from app.schemas.schemas import LoraTrainingOut
from app.services import storage
from app.services.replicate_client import get_training, start_lora_training

router = APIRouter(prefix="/brands", tags=["training"])


@router.post("/{brand_id}/train", response_model=LoraTrainingOut)
def train_brand_lora(brand_id: str, db: Session = Depends(get_db)):
    brand = db.get(Brand, brand_id)
    if not brand:
        raise HTTPException(404, "Brand not found")
    asset_count = db.query(BrandAsset).filter(BrandAsset.brand_id == brand_id).count()
    if asset_count < 5:
        raise HTTPException(400, "Upload at least 5 reference images before training (15-20 recommended)")

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
