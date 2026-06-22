from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.models import Organization
from app.schemas.schemas import OrganizationCreate, OrganizationOut

router = APIRouter(prefix="/organizations", tags=["organizations"])


@router.post("", response_model=OrganizationOut)
def create_organization(payload: OrganizationCreate, db: Session = Depends(get_db)):
    org = Organization(name=payload.name)
    db.add(org)
    db.commit()
    db.refresh(org)
    return org


@router.get("/{organization_id}", response_model=OrganizationOut)
def get_organization(organization_id: str, db: Session = Depends(get_db)):
    org = db.get(Organization, organization_id)
    if not org:
        raise HTTPException(404, "Organization not found")
    return org
