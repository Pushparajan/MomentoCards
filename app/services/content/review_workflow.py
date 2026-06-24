from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.content_models import (
    ContentStatus,
    GeneratedContent,
    ReviewDecision,
    ReviewStageStatus,
    ReviewSubmission,
)
from app.services.audit_log import record as audit_record


def submit_for_review(
    db: Session, content: GeneratedContent, review_route: list[str], sla_due_date: datetime | None
) -> ReviewSubmission:
    if not review_route:
        raise HTTPException(400, "review_route must contain at least one stage")
    latest = content.latest_version()
    if not latest:
        raise HTTPException(400, "Content has no draft version to submit")

    submission = ReviewSubmission(
        content_id=content.id,
        version_id=latest.id,
        review_route=",".join(review_route),
        stage=review_route[0],
        sla_due_date=sla_due_date,
        status=ReviewStageStatus.pending,
    )
    db.add(submission)
    content.status = ContentStatus.in_review
    db.commit()
    db.refresh(submission)
    audit_record(db, "submit", content_id=content.id, stage=submission.stage, detail={"review_route": review_route})
    return submission


def decide(db: Session, submission: ReviewSubmission, decision: str, comment: str | None, escalate: bool, actor: str) -> ReviewSubmission:
    if submission.status != ReviewStageStatus.pending:
        raise HTTPException(409, f"Submission is at status '{submission.status.value}', not pending")
    try:
        decision_status = ReviewStageStatus(decision)
    except ValueError:
        raise HTTPException(400, f"Invalid decision '{decision}'")
    if decision_status not in (ReviewStageStatus.approved, ReviewStageStatus.rejected, ReviewStageStatus.changes_requested):
        raise HTTPException(400, "decision must be one of: approved, rejected, changes_requested")
    if decision_status in (ReviewStageStatus.rejected, ReviewStageStatus.changes_requested) and not comment:
        raise HTTPException(400, "A comment is mandatory when rejecting or requesting changes")

    db.add(
        ReviewDecision(
            submission_id=submission.id,
            stage=submission.stage,
            decision=decision_status,
            comment=comment,
            escalate=1 if escalate else 0,
            actor=actor,
        )
    )

    content = submission.content
    if decision_status == ReviewStageStatus.approved:
        stages = submission.route_stages()
        current_idx = stages.index(submission.stage)
        if current_idx + 1 < len(stages):
            submission.stage = stages[current_idx + 1]
            submission.status = ReviewStageStatus.pending
        else:
            submission.status = ReviewStageStatus.approved
            content.status = ContentStatus.approved
    elif decision_status == ReviewStageStatus.rejected:
        submission.status = ReviewStageStatus.escalated if escalate else ReviewStageStatus.rejected
        content.status = ContentStatus.rejected
    else:  # changes_requested
        submission.status = ReviewStageStatus.changes_requested
        content.status = ContentStatus.draft

    db.commit()
    db.refresh(submission)
    audit_record(
        db,
        "decide",
        content_id=content.id,
        stage=submission.stage,
        actor=actor,
        detail={"decision": decision_status.value, "comment": comment, "escalate": escalate},
    )
    return submission
