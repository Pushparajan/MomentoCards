from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.models import DocumentType
from app.schemas.schemas import DocumentTypeOut

router = APIRouter(prefix="/document-types", tags=["document-types"])


@router.get("", response_model=list[DocumentTypeOut])
def list_document_types(category: str | None = None, db: Session = Depends(get_db)):
    query = db.query(DocumentType)
    if category:
        query = query.filter(DocumentType.category == category)
    return [DocumentTypeOut.from_orm_model(dt) for dt in query.order_by(DocumentType.category, DocumentType.name).all()]
