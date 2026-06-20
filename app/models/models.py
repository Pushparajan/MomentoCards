import enum
import json
import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.core.db import Base


def gen_id() -> str:
    return uuid.uuid4().hex


class TrainingStatus(str, enum.Enum):
    pending = "pending"
    training = "training"
    succeeded = "succeeded"
    failed = "failed"


class JobStatus(str, enum.Enum):
    pending = "pending"
    running = "running"
    succeeded = "succeeded"
    failed = "failed"


class LayoutKind(str, enum.Enum):
    single_sheet = "single_sheet"       # flyers, posters, certificates, web banners
    folded = "folded"                   # bi-fold/tri-fold brochures, greeting cards
    multi_page = "multi_page"           # catalogs, annual reports, magazines, books
    grid = "grid"                       # wall/desk/pocket calendars, planner pages
    micro = "micro"                     # business cards, tags, bookmarks, tickets
    live = "live"                       # websites, social posts, presentations


class FulfillmentType(str, enum.Enum):
    digital_export = "digital_export"     # PNG/PDF/SVG download (only path implemented today)
    print_fulfillment = "print_fulfillment"  # Canva-Print-style pack & ship (not implemented)
    live_publish = "live_publish"         # hosted site / scheduled social post (not implemented)


class Brand(Base):
    __tablename__ = "brands"

    id = Column(String, primary_key=True, default=gen_id)
    name = Column(String, nullable=False)
    primary_color = Column(String, nullable=True)
    secondary_color = Column(String, nullable=True)
    mood_keywords = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    assets = relationship("BrandAsset", back_populates="brand", cascade="all, delete-orphan")
    lora_models = relationship("LoraModel", back_populates="brand", cascade="all, delete-orphan")


class BrandAsset(Base):
    __tablename__ = "brand_assets"

    id = Column(String, primary_key=True, default=gen_id)
    brand_id = Column(String, ForeignKey("brands.id"), nullable=False)
    file_path = Column(String, nullable=False)
    kind = Column(String, default="reference")  # reference | logo
    created_at = Column(DateTime, default=datetime.utcnow)

    brand = relationship("Brand", back_populates="assets")


class LoraModel(Base):
    __tablename__ = "lora_models"

    id = Column(String, primary_key=True, default=gen_id)
    brand_id = Column(String, ForeignKey("brands.id"), nullable=False)
    replicate_training_id = Column(String, nullable=True)
    status = Column(Enum(TrainingStatus), default=TrainingStatus.pending)
    weights_url = Column(String, nullable=True)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    brand = relationship("Brand", back_populates="lora_models")


class DocumentType(Base):
    """Catalog entry for one deliverable kind (flyer, brochure, wall calendar, ...).
    Seeded once at startup from app.services.document_catalog; not user-created."""

    __tablename__ = "document_types"

    id = Column(String, primary_key=True, default=gen_id)
    key = Column(String, unique=True, nullable=False)  # e.g. "wall_calendar", "tri_fold_brochure"
    name = Column(String, nullable=False)
    category = Column(String, nullable=False)  # e.g. "Marketing & Promotional Materials"
    layout_kind = Column(Enum(LayoutKind), nullable=False)
    default_page_count = Column(Integer, default=1)
    requires_grid = Column(Integer, default=0)  # bool: render a code-generated grid for ControlNet
    fulfillment_options = Column(String, default=FulfillmentType.digital_export.value)  # comma-separated
    description = Column(Text, nullable=True)

    def fulfillment_list(self) -> list[str]:
        return self.fulfillment_options.split(",") if self.fulfillment_options else []


class Deliverable(Base):
    """A generic generation job for any document type (replaces the calendar-only job).
    One Deliverable owns N DeliverablePages (e.g. 12 for a wall calendar, 1 for a flyer)."""

    __tablename__ = "deliverables"

    id = Column(String, primary_key=True, default=gen_id)
    brand_id = Column(String, ForeignKey("brands.id"), nullable=False)
    document_type_id = Column(String, ForeignKey("document_types.id"), nullable=False)
    title = Column(String, nullable=True)
    style = Column(String, default="vector")  # vector | photographic | minimal
    status = Column(Enum(JobStatus), default=JobStatus.pending)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    brand = relationship("Brand")
    document_type = relationship("DocumentType")
    pages = relationship(
        "DeliverablePage", back_populates="deliverable", cascade="all, delete-orphan", order_by="DeliverablePage.page_number"
    )


class DeliverablePage(Base):
    """One generated page/panel within a Deliverable. For grid layouts (calendars,
    planners) `params` carries {"month": 6, "year": 2026}; for other layouts it
    carries free-form per-page prompt context (e.g. {"panel": "front cover"})."""

    __tablename__ = "deliverable_pages"

    id = Column(String, primary_key=True, default=gen_id)
    deliverable_id = Column(String, ForeignKey("deliverables.id"), nullable=False)
    page_number = Column(Integer, nullable=False)
    params_json = Column(Text, default="{}")
    grid_path = Column(String, nullable=True)
    canny_path = Column(String, nullable=True)
    replicate_prediction_id = Column(String, nullable=True)
    status = Column(Enum(JobStatus), default=JobStatus.pending)
    output_url = Column(String, nullable=True)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    deliverable = relationship("Deliverable", back_populates="pages")

    @property
    def params(self) -> dict:
        return json.loads(self.params_json or "{}")

    @params.setter
    def params(self, value: dict) -> None:
        self.params_json = json.dumps(value or {})
