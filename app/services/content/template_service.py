from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.content_models import ContentTemplate, ContentTemplateVersion, TemplateStatus


def _snapshot(db: Session, template: ContentTemplate) -> None:
    next_version = len(template.versions) + 1
    db.add(ContentTemplateVersion(template_id=template.id, version_number=next_version, body=template.body))


def create_template(db: Session, name: str, channel: str, objective: str, body: str, language: str) -> ContentTemplate:
    template = ContentTemplate(name=name, channel=channel, objective=objective, body=body, language=language)
    db.add(template)
    db.commit()
    _snapshot(db, template)
    db.commit()
    db.refresh(template)
    return template


def update_template(db: Session, template: ContentTemplate, updates: dict) -> ContentTemplate:
    if template.status == TemplateStatus.archived:
        raise HTTPException(400, "Cannot edit an archived template")
    body_changed = "body" in updates and updates["body"] is not None and updates["body"] != template.body
    for key, value in updates.items():
        if value is not None:
            setattr(template, key, value)
    db.commit()
    if body_changed:
        _snapshot(db, template)
        db.commit()
    db.refresh(template)
    return template


def archive_template(db: Session, template: ContentTemplate) -> ContentTemplate:
    template.status = TemplateStatus.archived
    db.commit()
    db.refresh(template)
    return template


def restore_template_version(db: Session, template: ContentTemplate, version: ContentTemplateVersion) -> ContentTemplate:
    if version.template_id != template.id:
        raise HTTPException(400, "Version does not belong to this template")
    template.body = version.body
    db.commit()
    _snapshot(db, template)
    db.commit()
    db.refresh(template)
    return template
