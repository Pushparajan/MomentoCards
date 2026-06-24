from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.models import Brand, BrandRule
from app.schemas.schemas import BrandRuleCreate, BrandRuleOut

router = APIRouter(prefix="/brands/{brand_id}/rules", tags=["brand-governance"])


@router.post("", response_model=BrandRuleOut)
def create_rule(brand_id: str, payload: BrandRuleCreate, db: Session = Depends(get_db)):
    """Brand Governance: defines a constraint (e.g. logo_mandatory,
    forbidden_fonts, min_primary_color_usage) validated by
    services.governance before a campaign can launch."""
    if not db.get(Brand, brand_id):
        raise HTTPException(404, "Brand not found")
    rule = BrandRule(brand_id=brand_id, rule_type=payload.rule_type)
    rule.value = payload.value
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return BrandRuleOut.from_orm_model(rule)


@router.get("", response_model=list[BrandRuleOut])
def list_rules(brand_id: str, db: Session = Depends(get_db)):
    rules = db.query(BrandRule).filter(BrandRule.brand_id == brand_id).all()
    return [BrandRuleOut.from_orm_model(rule) for rule in rules]


@router.delete("/{rule_id}", status_code=204)
def delete_rule(brand_id: str, rule_id: str, db: Session = Depends(get_db)):
    rule = db.get(BrandRule, rule_id)
    if not rule or rule.brand_id != brand_id:
        raise HTTPException(404, "Brand rule not found")
    db.delete(rule)
    db.commit()
