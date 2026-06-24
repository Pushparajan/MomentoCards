from sqlalchemy.orm import Session

from app.models.content_models import AuditLog


def record(
    db: Session,
    change_type: str,
    content_id: str | None = None,
    stage: str | None = None,
    actor: str = "system",
    source_ip: str | None = None,
    detail: dict | None = None,
) -> AuditLog:
    """Appends one immutable audit event. Callers never update or delete the
    returned row -- there is intentionally no update/delete path on AuditLog
    anywhere in the codebase."""
    entry = AuditLog(content_id=content_id, change_type=change_type, stage=stage, actor=actor, source_ip=source_ip)
    entry.detail = detail or {}
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry
