from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.content_models import AuditLog
from app.schemas.content_schemas import AuditLogOut

router = APIRouter(prefix="/audit-logs", tags=["audit"])


@router.get("", response_model=list[AuditLogOut])
def list_logs(
    content_id: str | None = None,
    change_type: str | None = None,
    start: datetime | None = None,
    end: datetime | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(AuditLog)
    if content_id:
        query = query.filter(AuditLog.content_id == content_id)
    if change_type:
        query = query.filter(AuditLog.change_type == change_type)
    if start:
        query = query.filter(AuditLog.created_at >= start)
    if end:
        query = query.filter(AuditLog.created_at <= end)
    logs = query.order_by(AuditLog.created_at.desc()).all()
    return [AuditLogOut.from_orm_model(a) for a in logs]
