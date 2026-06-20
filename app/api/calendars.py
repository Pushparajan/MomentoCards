from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.models import Brand, BrandAsset, CalendarJob, JobStatus, LoraModel, TrainingStatus
from app.schemas.schemas import CalendarGenerateRequest, CalendarJobOut
from app.services import storage
from app.services.grid_generator import draw_blank_grid, to_canny
from app.services.prompt_builder import build_negative_prompt, build_prompt
from app.services.replicate_client import generate_calendar_page, get_prediction

router = APIRouter(prefix="/calendars", tags=["calendars"])


@router.post("/generate", response_model=CalendarJobOut)
def generate_calendar(payload: CalendarGenerateRequest, db: Session = Depends(get_db)):
    brand = db.get(Brand, payload.brand_id)
    if not brand:
        raise HTTPException(404, "Brand not found")

    job = CalendarJob(
        brand_id=brand.id,
        month=payload.month,
        year=payload.year,
        style=payload.style,
        status=JobStatus.running,
    )
    db.add(job)
    db.commit()

    grid_path, canny_path = storage.grid_paths(job.id)
    draw_blank_grid(payload.year, payload.month, grid_path)
    to_canny(grid_path, canny_path)
    job.grid_path = grid_path
    job.canny_path = canny_path
    db.commit()

    lora_weights_url = None
    if payload.use_brand_lora:
        lora = (
            db.query(LoraModel)
            .filter(LoraModel.brand_id == brand.id, LoraModel.status == TrainingStatus.succeeded)
            .order_by(LoraModel.created_at.desc())
            .first()
        )
        if not lora:
            job.status = JobStatus.failed
            job.error = "No trained LoRA available for this brand; train one first or set use_brand_lora=false"
            db.commit()
            return job
        lora_weights_url = lora.weights_url

    ip_adapter_image_url = None
    if payload.ip_adapter_asset_id:
        asset = db.get(BrandAsset, payload.ip_adapter_asset_id)
        if not asset or asset.brand_id != brand.id:
            raise HTTPException(404, "IP-Adapter reference asset not found for this brand")
        ip_adapter_image_url = asset.file_path

    prompt = build_prompt(payload.style, brand.mood_keywords, brand.primary_color, brand.secondary_color)
    negative_prompt = build_negative_prompt()

    try:
        with open(canny_path, "rb") as canny_file:
            prediction = generate_calendar_page(
                canny_image_url=canny_file,
                ip_adapter_image_url=ip_adapter_image_url,
                lora_weights_url=lora_weights_url,
                prompt=prompt,
                negative_prompt=negative_prompt,
            )
        job.replicate_prediction_id = prediction.id
    except Exception as exc:  # noqa: BLE001
        job.status = JobStatus.failed
        job.error = str(exc)
    db.commit()
    db.refresh(job)
    return job


@router.get("/{job_id}", response_model=CalendarJobOut)
def get_job(job_id: str, db: Session = Depends(get_db)):
    job = db.get(CalendarJob, job_id)
    if not job:
        raise HTTPException(404, "Job not found")

    if job.replicate_prediction_id and job.status == JobStatus.running:
        prediction = get_prediction(job.replicate_prediction_id)
        if prediction.status == "succeeded":
            job.status = JobStatus.succeeded
            output = prediction.output
            job.output_url = output[0] if isinstance(output, list) else output
        elif prediction.status == "failed":
            job.status = JobStatus.failed
            job.error = prediction.error
        db.commit()
        db.refresh(job)
    return job
