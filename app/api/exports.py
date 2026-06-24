from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.content_models import ExportDestination, ExportRecord, GeneratedContent
from app.schemas.content_schemas import (
    ExportDestinationCreate,
    ExportDestinationOut,
    ExportRecordOut,
    ExportRequest,
)
from app.services.content.export_service import export_content, retry_export

router = APIRouter(tags=["exports"])


@router.post("/export-destinations", response_model=ExportDestinationOut)
def create_destination(payload: ExportDestinationCreate, db: Session = Depends(get_db)):
    destination = ExportDestination(name=payload.name, destination_type=payload.destination_type, workspace=payload.workspace)
    db.add(destination)
    db.commit()
    db.refresh(destination)
    return destination


@router.get("/export-destinations", response_model=list[ExportDestinationOut])
def list_destinations(db: Session = Depends(get_db)):
    return db.query(ExportDestination).all()


@router.post("/content/{content_id}/export", response_model=ExportRecordOut)
def export(content_id: str, payload: ExportRequest, db: Session = Depends(get_db)):
    content = db.get(GeneratedContent, content_id)
    if not content:
        raise HTTPException(404, "Content not found")
    record = export_content(db, content, payload.destination_id, payload.content_format, payload.metadata_mapping, payload.schedule)
    return ExportRecordOut.from_orm_model(record)


@router.post("/exports/{export_id}/retry", response_model=ExportRecordOut)
def retry(export_id: str, db: Session = Depends(get_db)):
    record = db.get(ExportRecord, export_id)
    if not record:
        raise HTTPException(404, "Export record not found")
    record = retry_export(db, record)
    return ExportRecordOut.from_orm_model(record)


@router.get("/content/{content_id}/exports", response_model=list[ExportRecordOut])
def list_exports(content_id: str, db: Session = Depends(get_db)):
    records = db.query(ExportRecord).filter(ExportRecord.content_id == content_id).all()
    return [ExportRecordOut.from_orm_model(r) for r in records]
