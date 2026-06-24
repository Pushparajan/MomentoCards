from collections import Counter

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.models import Deliverable, DocumentType, LoraModel, TrainingStatus

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/overview")
def overview(brand_id: str, db: Session = Depends(get_db)):
    """Backs the Overview screen: total creations, brand-model readiness,
    and the most-made deliverable type for this brand."""
    deliverables = db.query(Deliverable).filter(Deliverable.brand_id == brand_id).all()
    loras = db.query(LoraModel).filter(LoraModel.brand_id == brand_id).all()

    type_counts = Counter(d.document_type_id for d in deliverables)
    most_made = None
    if type_counts:
        top_id, _ = type_counts.most_common(1)[0]
        document_type = db.get(DocumentType, top_id)
        most_made = document_type.name if document_type else None

    return {
        "total_creations": len(deliverables),
        "favorites_count": sum(1 for d in deliverables if d.is_favorite),
        "brand_models_total": len(loras),
        "brand_models_ready": sum(1 for l in loras if l.status == TrainingStatus.succeeded),
        "most_made_document_type": most_made,
        "recent": [
            {"id": d.id, "title": d.title, "status": d.status.value, "document_type_id": d.document_type_id}
            for d in sorted(deliverables, key=lambda d: d.created_at, reverse=True)[:8]
        ],
    }
