from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.content_models import ContentStatus, ExportRecord, ExportStatus, GeneratedContent
from app.services.audit_log import record as audit_record


def export_content(
    db: Session, content: GeneratedContent, destination_id: str, content_format: str, metadata_mapping: dict, schedule: str | None
) -> ExportRecord:
    if content.status != ContentStatus.approved:
        raise HTTPException(400, "Only approved content is exportable")

    record = ExportRecord(
        content_id=content.id,
        destination_id=destination_id,
        content_format=content_format,
        schedule=schedule,
        status=ExportStatus.pending,
    )
    record.metadata_mapping = metadata_mapping
    db.add(record)
    db.commit()

    _attempt_export(db, record)
    audit_record(db, "export", content_id=content.id, detail={"destination_id": destination_id, "status": record.status.value})
    return record


def retry_export(db: Session, record: ExportRecord) -> ExportRecord:
    if record.status != ExportStatus.failed:
        raise HTTPException(400, "Only failed exports can be retried")
    record.retry_count += 1
    _attempt_export(db, record)
    audit_record(db, "export_retry", content_id=record.content_id, detail={"retry_count": record.retry_count, "status": record.status.value})
    return record


def _attempt_export(db: Session, record: ExportRecord) -> None:
    """Stands in for the actual downstream API call to the connector; the
    seam (this one function) is where a real CMS/social/email integration
    would plug in per destination_type."""
    destination = record.destination
    if destination.auth_status != "connected":
        record.status = ExportStatus.failed
        record.failure_reason = f"Destination '{destination.name}' is not connected (auth_status={destination.auth_status})"
    else:
        record.status = ExportStatus.succeeded
        record.failure_reason = None
    db.commit()
    db.refresh(record)
