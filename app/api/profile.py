from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.models import Profile
from app.schemas.schemas import ProfileOut, ProfileUpdate

router = APIRouter(prefix="/profile", tags=["profile"])

DEFAULT_EMAIL = "pushparajanr@gmail.com"


def _get_or_create_profile(db: Session) -> Profile:
    """No auth system exists yet, so the Profile screen operates on a single
    singleton row rather than a per-session user."""
    profile = db.query(Profile).first()
    if not profile:
        profile = Profile(email=DEFAULT_EMAIL)
        db.add(profile)
        db.commit()
        db.refresh(profile)
    return profile


@router.get("", response_model=ProfileOut)
def get_profile(db: Session = Depends(get_db)):
    return _get_or_create_profile(db)


@router.put("", response_model=ProfileOut)
def update_profile(payload: ProfileUpdate, db: Session = Depends(get_db)):
    profile = _get_or_create_profile(db)
    if payload.display_name is not None:
        profile.display_name = payload.display_name
    db.commit()
    db.refresh(profile)
    return profile
