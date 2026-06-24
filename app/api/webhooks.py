from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.models import DeliverablePage, WebhookEvent
from app.services.deliverable_service import apply_completed_prediction, apply_completed_video_prediction

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


class _PredictionView:
    """Adapts a raw Replicate webhook JSON payload to the shape expected by
    deliverable_service (which normally consumes the SDK's Prediction
    object), so we don't need a network round-trip back to Replicate just to
    process its own push notification."""

    def __init__(self, payload: dict):
        self.status = payload.get("status")
        self.output = payload.get("output")
        self.error = payload.get("error")


@router.post("/replicate")
async def replicate_webhook(request: Request, db: Session = Depends(get_db)):
    payload = await request.json()
    prediction_id = payload.get("id")
    if not prediction_id:
        return {"ok": True}

    # Idempotency: Replicate may deliver the same webhook more than once.
    if db.query(WebhookEvent).filter(WebhookEvent.provider_prediction_id == prediction_id).first():
        return {"ok": True}

    prediction = _PredictionView(payload)
    if prediction.status in ("succeeded", "failed"):
        page = db.query(DeliverablePage).filter(DeliverablePage.replicate_prediction_id == prediction_id).first()
        if page:
            apply_completed_prediction(db, page, prediction)
        else:
            page = (
                db.query(DeliverablePage)
                .filter(DeliverablePage.video_replicate_prediction_id == prediction_id)
                .first()
            )
            if page:
                apply_completed_video_prediction(db, page, prediction)

    db.add(WebhookEvent(provider_prediction_id=prediction_id))
    db.commit()
    return {"ok": True}
