from sqlalchemy.orm import Session

from app.models.models import LoraCategory, LoraModel, TrainingStatus
from app.services import storage
from app.services.replicate_client import start_lora_training


def start_training(
    db: Session,
    brand_id: str,
    category: LoraCategory,
    subject_type: str = "style",
    name: str | None = None,
    description: str | None = None,
    existing: LoraModel | None = None,
) -> LoraModel:
    """Kicks off a custom LoRA training run on whatever reference assets the
    brand has uploaded so far. Shared by the manual /train endpoints and the
    automatic-trigger path (asset count crossing AUTO_TRAIN_ASSET_THRESHOLD).
    Pass `existing` to retry a previously-failed run in place."""
    zip_path = storage.zip_brand_assets(brand_id)
    trigger_word = f"brand{brand_id[:8]}{category.value}"

    if existing is not None:
        lora = existing
    else:
        lora = LoraModel(
            brand_id=brand_id, category=category, subject_type=subject_type, name=name, description=description, status=TrainingStatus.training
        )
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
