from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.content_models import ContentVersion, GeneratedContent
from app.services.audit_log import record as audit_record


def get_version(db: Session, content: GeneratedContent, version_id: str) -> ContentVersion:
    version = db.get(ContentVersion, version_id)
    if not version or version.content_id != content.id:
        raise HTTPException(404, "Version not found for this content")
    return version


def restore(db: Session, content: GeneratedContent, version_id: str, actor: str) -> ContentVersion:
    """Restoring a prior version creates a brand-new latest version with that
    version's body -- it never overwrites or deletes history."""
    source = get_version(db, content, version_id)
    next_version_number = content.latest_version().version_number + 1
    restored = ContentVersion(content_id=content.id, version_number=next_version_number, body=source.body, change_type="restore", actor=actor)
    db.add(restored)
    db.commit()
    db.refresh(restored)
    audit_record(db, "restore", content_id=content.id, actor=actor, detail={"restored_from_version": source.version_number})
    return restored
