from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.content_models import BrandProfile, TemplateStatus
from app.schemas.content_schemas import BrandProfileCreate, BrandProfileOut, BrandProfileUpdate

router = APIRouter(prefix="/brand-profiles", tags=["brand-profiles"])


def _get_profile(db: Session, profile_id: str) -> BrandProfile:
    profile = db.get(BrandProfile, profile_id)
    if not profile:
        raise HTTPException(404, "Brand profile not found")
    return profile


@router.post("", response_model=BrandProfileOut)
def create(payload: BrandProfileCreate, db: Session = Depends(get_db)):
    profile = BrandProfile(
        name=payload.name,
        tone=payload.tone,
        preferred_vocabulary=",".join(payload.preferred_vocabulary),
        banned_terms=",".join(payload.banned_terms),
        is_default_for_team=1 if payload.is_default_for_team else 0,
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return BrandProfileOut.from_orm_model(profile)


@router.get("", response_model=list[BrandProfileOut])
def list_profiles(db: Session = Depends(get_db)):
    return [BrandProfileOut.from_orm_model(p) for p in db.query(BrandProfile).all()]


@router.get("/{profile_id}", response_model=BrandProfileOut)
def get(profile_id: str, db: Session = Depends(get_db)):
    return BrandProfileOut.from_orm_model(_get_profile(db, profile_id))


@router.put("/{profile_id}", response_model=BrandProfileOut)
def update(profile_id: str, payload: BrandProfileUpdate, db: Session = Depends(get_db)):
    profile = _get_profile(db, profile_id)
    if profile.status == TemplateStatus.archived:
        raise HTTPException(400, "Cannot edit an archived brand profile")
    data = payload.model_dump(exclude_unset=True)
    if "preferred_vocabulary" in data and data["preferred_vocabulary"] is not None:
        profile.preferred_vocabulary = ",".join(data.pop("preferred_vocabulary"))
    if "banned_terms" in data and data["banned_terms"] is not None:
        profile.banned_terms = ",".join(data.pop("banned_terms"))
    if "is_default_for_team" in data and data["is_default_for_team"] is not None:
        profile.is_default_for_team = 1 if data.pop("is_default_for_team") else 0
    for key, value in data.items():
        if value is not None:
            setattr(profile, key, value)
    db.commit()
    db.refresh(profile)
    return BrandProfileOut.from_orm_model(profile)


@router.post("/{profile_id}/archive", response_model=BrandProfileOut)
def archive(profile_id: str, db: Session = Depends(get_db)):
    profile = _get_profile(db, profile_id)
    profile.status = TemplateStatus.archived
    db.commit()
    db.refresh(profile)
    return BrandProfileOut.from_orm_model(profile)
