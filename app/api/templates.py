import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.models import DocumentType, Template
from app.schemas.schemas import TemplateCreate, TemplateOut

router = APIRouter(prefix="/templates", tags=["templates"])


@router.post("", response_model=TemplateOut)
def create_template(payload: TemplateCreate, db: Session = Depends(get_db)):
    document_type = db.query(DocumentType).filter(DocumentType.key == payload.document_type_key).first()
    if not document_type:
        raise HTTPException(404, f"Unknown document_type_key '{payload.document_type_key}'")
    template = Template(
        document_type_id=document_type.id,
        name=payload.name,
        category=payload.category,
        tags=",".join(payload.tags),
        canvas_json=json.dumps(payload.canvas_json or {}),
        preview_url=payload.preview_url,
    )
    db.add(template)
    db.commit()
    db.refresh(template)
    return TemplateOut.from_orm_model(template)


@router.get("", response_model=list[TemplateOut])
def list_templates(category: str | None = None, document_type_key: str | None = None, db: Session = Depends(get_db)):
    query = db.query(Template)
    if category:
        query = query.filter(Template.category == category)
    if document_type_key:
        document_type = db.query(DocumentType).filter(DocumentType.key == document_type_key).first()
        if not document_type:
            return []
        query = query.filter(Template.document_type_id == document_type.id)
    return [TemplateOut.from_orm_model(t) for t in query.all()]
