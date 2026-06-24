from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.content_models import ContentTemplate, ContentTemplateVersion, TemplateStatus
from app.schemas.content_schemas import (
    ContentTemplateCreate,
    ContentTemplateOut,
    ContentTemplateUpdate,
    ContentTemplateVersionOut,
    RestoreVersionRequest,
)
from app.services.content.template_service import (
    archive_template,
    create_template,
    restore_template_version,
    update_template,
)

router = APIRouter(prefix="/content-templates", tags=["content-templates"])


def _get_template(db: Session, template_id: str) -> ContentTemplate:
    template = db.get(ContentTemplate, template_id)
    if not template:
        raise HTTPException(404, "Template not found")
    return template


@router.post("", response_model=ContentTemplateOut)
def create(payload: ContentTemplateCreate, db: Session = Depends(get_db)):
    template = create_template(db, payload.name, payload.channel, payload.objective, payload.body, payload.language)
    return ContentTemplateOut.from_orm_model(template)


@router.get("", response_model=list[ContentTemplateOut])
def list_templates(channel: str | None = None, status: str | None = None, db: Session = Depends(get_db)):
    query = db.query(ContentTemplate)
    if channel:
        query = query.filter(ContentTemplate.channel == channel)
    if status:
        query = query.filter(ContentTemplate.status == TemplateStatus(status))
    return [ContentTemplateOut.from_orm_model(t) for t in query.all()]


@router.get("/{template_id}", response_model=ContentTemplateOut)
def get(template_id: str, db: Session = Depends(get_db)):
    return ContentTemplateOut.from_orm_model(_get_template(db, template_id))


@router.put("/{template_id}", response_model=ContentTemplateOut)
def update(template_id: str, payload: ContentTemplateUpdate, db: Session = Depends(get_db)):
    template = _get_template(db, template_id)
    template = update_template(db, template, payload.model_dump())
    return ContentTemplateOut.from_orm_model(template)


@router.post("/{template_id}/archive", response_model=ContentTemplateOut)
def archive(template_id: str, db: Session = Depends(get_db)):
    template = _get_template(db, template_id)
    return ContentTemplateOut.from_orm_model(archive_template(db, template))


@router.get("/{template_id}/versions", response_model=list[ContentTemplateVersionOut])
def versions(template_id: str, db: Session = Depends(get_db)):
    template = _get_template(db, template_id)
    return template.versions


@router.post("/{template_id}/restore", response_model=ContentTemplateOut)
def restore(template_id: str, payload: RestoreVersionRequest, db: Session = Depends(get_db)):
    template = _get_template(db, template_id)
    version = db.get(ContentTemplateVersion, payload.version_id)
    if not version:
        raise HTTPException(404, "Version not found")
    return ContentTemplateOut.from_orm_model(restore_template_version(db, template, version))
