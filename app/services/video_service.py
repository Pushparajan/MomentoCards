from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.models import DeliverablePage, JobStatus
from app.services.replicate_client import start_video_from_keyframe


def start_video_for_page(db: Session, page: DeliverablePage, prompt: str | None) -> DeliverablePage:
    """Generates a short video using this page's already-generated image as
    the keyframe (img2vid). Requires the image to have finished successfully,
    and requires APP_BASE_URL to be set so Replicate can fetch our app-served
    image URL back from us."""
    if page.status != JobStatus.succeeded or not page.output_url:
        raise HTTPException(400, "Page must have a successfully generated image before generating a video from it")
    if not settings.app_base_url:
        raise HTTPException(400, "APP_BASE_URL must be configured so Replicate can fetch the keyframe image")

    keyframe_url = f"{settings.app_base_url.rstrip('/')}{page.output_url}"
    try:
        prediction = start_video_from_keyframe(keyframe_url, prompt)
        page.video_replicate_prediction_id = prediction.id
        page.video_status = JobStatus.running
    except Exception as exc:  # noqa: BLE001
        page.video_status = JobStatus.failed
        page.error = str(exc)
    db.commit()
    db.refresh(page)
    return page
