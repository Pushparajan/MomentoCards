from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.content_models import BrandProfile, ContentTemplate, ContentVersion, GeneratedContent
from app.schemas.content_schemas import (
    GenerateContentRequest,
    GeneratedContentOut,
    RestoreVersionRequest,
    RewriteContentRequest,
    VersionCompareOut,
)
from app.services.content.generation_service import generate, rewrite
from app.services.content.version_service import get_version, restore

router = APIRouter(prefix="/content", tags=["generated-content"])


def _get_content(db: Session, content_id: str) -> GeneratedContent:
    content = db.get(GeneratedContent, content_id)
    if not content:
        raise HTTPException(404, "Content not found")
    return content


@router.post("", response_model=GeneratedContentOut)
def create(payload: GenerateContentRequest, db: Session = Depends(get_db)):
    template = db.get(ContentTemplate, payload.template_id)
    if not template:
        raise HTTPException(404, "Template not found")
    profile = db.get(BrandProfile, payload.brand_profile_id)
    if not profile:
        raise HTTPException(404, "Brand profile not found")
    content = generate(
        db, template, profile, payload.campaign_name, payload.prompt_brief, payload.keywords, payload.output_length
    )
    return GeneratedContentOut.from_orm_model(content)


@router.get("", response_model=list[GeneratedContentOut])
def list_content(db: Session = Depends(get_db)):
    return [GeneratedContentOut.from_orm_model(c) for c in db.query(GeneratedContent).all()]


@router.get("/{content_id}", response_model=GeneratedContentOut)
def get(content_id: str, db: Session = Depends(get_db)):
    return GeneratedContentOut.from_orm_model(_get_content(db, content_id))


@router.post("/{content_id}/rewrite", response_model=GeneratedContentOut)
def rewrite_content(content_id: str, payload: RewriteContentRequest, db: Session = Depends(get_db)):
    content = _get_content(db, content_id)
    params = payload.model_dump(exclude={"rewrite_type"})
    content = rewrite(db, content, payload.rewrite_type, params)
    return GeneratedContentOut.from_orm_model(content)


@router.get("/{content_id}/versions/{version_id}", response_model=VersionCompareOut)
def compare_version(content_id: str, version_id: str, against: str, db: Session = Depends(get_db)):
    content = _get_content(db, content_id)
    from_version = get_version(db, content, version_id)
    to_version = get_version(db, content, against)
    return VersionCompareOut(from_version=from_version, to_version=to_version)


@router.post("/{content_id}/versions/restore", response_model=GeneratedContentOut)
def restore_version(content_id: str, payload: RestoreVersionRequest, db: Session = Depends(get_db)):
    content = _get_content(db, content_id)
    restore(db, content, payload.version_id, payload.actor)
    db.refresh(content)
    return GeneratedContentOut.from_orm_model(content)
