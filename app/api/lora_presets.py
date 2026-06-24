from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.models import LoraCategory, SharedLoraPreset
from app.schemas.schemas import SharedLoraPresetCreate, SharedLoraPresetOut

router = APIRouter(prefix="/presets", tags=["presets"])


@router.post("", response_model=SharedLoraPresetOut)
def create_preset(payload: SharedLoraPresetCreate, db: Session = Depends(get_db)):
    """Platform-owned LoRA presets (e.g. seasonal/typography/locale styles)
    selectable across brands. weights_url is stored server-side only and
    never returned to the client."""
    preset = SharedLoraPreset(
        key=payload.key,
        name=payload.name,
        category=LoraCategory(payload.category),
        weights_url=payload.weights_url,
        default_weight=str(payload.default_weight),
    )
    db.add(preset)
    db.commit()
    db.refresh(preset)
    return preset


@router.get("", response_model=list[SharedLoraPresetOut])
def list_presets(category: LoraCategory | None = None, db: Session = Depends(get_db)):
    query = db.query(SharedLoraPreset)
    if category:
        query = query.filter(SharedLoraPreset.category == category)
    return query.order_by(SharedLoraPreset.name).all()
