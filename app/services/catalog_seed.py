from sqlalchemy.orm import Session

from app.models.models import DocumentType
from app.services.document_catalog import CATALOG


def seed_document_types(db: Session) -> None:
    existing_keys = {row[0] for row in db.query(DocumentType.key).all()}
    for key, name, category, layout_kind, default_page_count, requires_grid, fulfillment in CATALOG:
        if key in existing_keys:
            continue
        db.add(
            DocumentType(
                key=key,
                name=name,
                category=category,
                layout_kind=layout_kind,
                default_page_count=default_page_count,
                requires_grid=int(requires_grid),
                fulfillment_options=fulfillment,
            )
        )
    db.commit()
