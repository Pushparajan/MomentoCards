from sqlalchemy.orm import Session

from app.models.models import Brand, BrandRule


def validate_brand_rules(db: Session, brand: Brand) -> list[str]:
    """Brand Governance: runs every BrandRule for this brand and returns a
    list of human-readable violations (empty list == compliant). Called
    before launch so a campaign can't ship something that breaks the
    brand's own rules (e.g. missing logo, forbidden font, under-using the
    primary brand color)."""
    rules = db.query(BrandRule).filter(BrandRule.brand_id == brand.id).all()
    violations: list[str] = []

    for rule in rules:
        if rule.rule_type == "logo_mandatory":
            if rule.value.get("required", True) and not brand.logo_asset_id:
                violations.append("Brand rule violated: a logo asset is mandatory but none is set on this brand")

        elif rule.rule_type == "forbidden_fonts":
            forbidden = {f.lower() for f in rule.value.get("fonts", [])}
            used = {f.lower() for f in brand.font_list()}
            hit = used & forbidden
            if hit:
                violations.append(f"Brand rule violated: forbidden font(s) in use: {', '.join(sorted(hit))}")

        elif rule.rule_type == "min_primary_color_usage":
            min_pct = rule.value.get("min_pct")
            actual_pct = rule.value.get("actual_pct")
            if min_pct is not None and actual_pct is not None and actual_pct < min_pct:
                violations.append(
                    f"Brand rule violated: primary color usage {actual_pct}% is below required minimum {min_pct}%"
                )

    return violations
