from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.content_models import BrandProfile, PolicyConfig


def enforce_banned_terms(body: str, profile: BrandProfile) -> None:
    lowered = body.lower()
    hits = [term for term in profile.banned_list() if term.lower() in lowered]
    if hits:
        raise HTTPException(400, f"Generated content contains banned term(s): {', '.join(hits)}")


def check_restricted_terms(db: Session, body: str) -> list[str]:
    """Returns any platform-wide restricted terms (across all PolicyConfig
    rows) found in `body`; logged by callers rather than raised, so
    Compliance Insights can surface violations instead of silently blocking
    on a config the content author may not see."""
    policies = db.query(PolicyConfig).all()
    lowered = body.lower()
    hits: set[str] = set()
    for policy in policies:
        for term in policy.restricted_term_list():
            if term.lower() in lowered:
                hits.add(term)
    return sorted(hits)
