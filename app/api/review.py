from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.content_models import GeneratedContent, ReviewSubmission
from app.schemas.content_schemas import ReviewDecisionRequest, ReviewSubmissionOut, SubmitForReviewRequest
from app.services.content.review_workflow import decide, submit_for_review

router = APIRouter(tags=["review"])


@router.post("/content/{content_id}/submit", response_model=ReviewSubmissionOut)
def submit(content_id: str, payload: SubmitForReviewRequest, db: Session = Depends(get_db)):
    content = db.get(GeneratedContent, content_id)
    if not content:
        raise HTTPException(404, "Content not found")
    submission = submit_for_review(db, content, payload.review_route, payload.sla_due_date)
    return ReviewSubmissionOut.from_orm_model(submission)


@router.get("/content/{content_id}/submissions", response_model=list[ReviewSubmissionOut])
def list_submissions(content_id: str, db: Session = Depends(get_db)):
    content = db.get(GeneratedContent, content_id)
    if not content:
        raise HTTPException(404, "Content not found")
    return [ReviewSubmissionOut.from_orm_model(s) for s in content.submissions]


@router.post("/submissions/{submission_id}/decide", response_model=ReviewSubmissionOut)
def decide_submission(submission_id: str, payload: ReviewDecisionRequest, db: Session = Depends(get_db)):
    submission = db.get(ReviewSubmission, submission_id)
    if not submission:
        raise HTTPException(404, "Submission not found")
    submission = decide(db, submission, payload.decision, payload.comment, payload.escalate, payload.actor)
    return ReviewSubmissionOut.from_orm_model(submission)
