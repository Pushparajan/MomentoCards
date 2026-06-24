from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.content_models import ModelLimit, PlatformUser, PolicyConfig
from app.schemas.content_schemas import (
    AnalyticsOut,
    ModelLimitCreate,
    ModelLimitOut,
    PlatformUserCreate,
    PlatformUserOut,
    PolicyConfigCreate,
    PolicyConfigOut,
)
from app.services.content.analytics_service import compute_analytics

router = APIRouter(tags=["content-admin"])


@router.post("/platform-users", response_model=PlatformUserOut)
def create_user(payload: PlatformUserCreate, db: Session = Depends(get_db)):
    if db.query(PlatformUser).filter(PlatformUser.email == payload.email).first():
        raise HTTPException(400, "A user with this email already exists")
    user = PlatformUser(email=payload.email, role=payload.role, team=payload.team)
    db.add(user)
    db.commit()
    db.refresh(user)
    return PlatformUserOut.from_orm_model(user)


@router.get("/platform-users", response_model=list[PlatformUserOut])
def list_users(db: Session = Depends(get_db)):
    return [PlatformUserOut.from_orm_model(u) for u in db.query(PlatformUser).all()]


@router.post("/policy-configs", response_model=PolicyConfigOut)
def create_policy(payload: PolicyConfigCreate, db: Session = Depends(get_db)):
    policy = PolicyConfig(
        name=payload.name,
        restricted_terms=",".join(payload.restricted_terms),
        retention_period_days=payload.retention_period_days,
    )
    policy.review_rules = payload.review_rules
    db.add(policy)
    db.commit()
    db.refresh(policy)
    return PolicyConfigOut.from_orm_model(policy)


@router.get("/policy-configs", response_model=list[PolicyConfigOut])
def list_policies(db: Session = Depends(get_db)):
    return [PolicyConfigOut.from_orm_model(p) for p in db.query(PolicyConfig).all()]


@router.post("/model-limits", response_model=ModelLimitOut)
def create_limit(payload: ModelLimitCreate, db: Session = Depends(get_db)):
    if db.query(ModelLimit).filter(ModelLimit.model_name == payload.model_name).first():
        raise HTTPException(400, "A limit for this model already exists")
    limit = ModelLimit(model_name=payload.model_name, daily_limit=payload.daily_limit)
    db.add(limit)
    db.commit()
    db.refresh(limit)
    return limit


@router.get("/model-limits", response_model=list[ModelLimitOut])
def list_limits(db: Session = Depends(get_db)):
    return db.query(ModelLimit).all()


@router.get("/analytics/content", response_model=AnalyticsOut)
def analytics(start: datetime | None = None, end: datetime | None = None, db: Session = Depends(get_db)):
    return compute_analytics(db, start, end)
