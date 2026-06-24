from datetime import datetime

from sqlalchemy.orm import Session

from app.models.content_models import ContentStatus, GeneratedContent, ReviewDecision, ReviewStageStatus


def compute_analytics(db: Session, start: datetime | None, end: datetime | None) -> dict:
    query = db.query(GeneratedContent)
    if start:
        query = query.filter(GeneratedContent.created_at >= start)
    if end:
        query = query.filter(GeneratedContent.created_at <= end)
    contents = query.all()

    total = len(contents)
    approved = sum(1 for c in contents if c.status == ContentStatus.approved)
    rejected = sum(1 for c in contents if c.status == ContentStatus.rejected)
    failed = sum(1 for c in contents if c.error)

    rejection_reasons: dict[str, int] = {}
    content_ids = [c.id for c in contents]
    if content_ids:
        decisions = (
            db.query(ReviewDecision)
            .join(ReviewDecision.submission)
            .filter(ReviewDecision.decision == ReviewStageStatus.rejected)
            .all()
        )
        for decision in decisions:
            if decision.submission.content_id in content_ids and decision.comment:
                rejection_reasons[decision.comment] = rejection_reasons.get(decision.comment, 0) + 1

    return {
        "total_generated": total,
        "approval_rate": round(approved / total, 4) if total else 0.0,
        "rejection_rate": round(rejected / total, 4) if total else 0.0,
        "success_rate": round((total - failed) / total, 4) if total else 0.0,
        "rejection_reasons": rejection_reasons,
    }
