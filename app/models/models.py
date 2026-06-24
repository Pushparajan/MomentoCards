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


class CampaignStage(str, enum.Enum):
    goal = "goal"
    layout = "layout"
    content = "content"
    preview = "preview"
    audience = "audience"
    generate = "generate"
    review = "review"
    launch = "launch"
    done = "done"


STAGE_ORDER = [
    CampaignStage.goal,
    CampaignStage.layout,
    CampaignStage.content,
    CampaignStage.preview,
    CampaignStage.audience,
    CampaignStage.generate,
    CampaignStage.review,
    CampaignStage.launch,
    CampaignStage.done,
]


class LoraCategory(str, enum.Enum):
    branding = "branding"        # brand identity (logo/colors/style)
    typography = "typography"    # type/font feel
    locale = "locale"            # regional setting cues
    community = "community"      # cultural/community cues
    subject = "subject"          # subject/character consistency


class MediaType(str, enum.Enum):
    image = "image"
    video = "video"


class Organization(Base):
    """Top-level tenant. Brands belong to an Organization; this is the
    foundation for multi-tenant isolation (auth/membership enforcement is not
    implemented yet -- this only establishes the data boundary)."""

    __tablename__ = "organizations"

    id = Column(String, primary_key=True, default=gen_id)
    name = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    brands = relationship("Brand", back_populates="organization")


class Brand(Base):
    __tablename__ = "brands"

    id = Column(String, primary_key=True, default=gen_id)
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=True)
    name = Column(String, nullable=False)
    primary_color = Column(String, nullable=True)
    secondary_color = Column(String, nullable=True)
    mood_keywords = Column(String, nullable=True)
    industry = Column(String, nullable=True)  # e.g. "Education", "Wedding", "Political", "Temple/Religious"
    voice = Column(String, nullable=True)  # e.g. "Inspirational", "Formal", "Playful"
    fonts = Column(String, nullable=True)  # comma-separated font family names
    logo_asset_id = Column(String, ForeignKey("brand_assets.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    organization = relationship("Organization", back_populates="brands")
    assets = relationship(
        "BrandAsset", back_populates="brand", cascade="all, delete-orphan", foreign_keys="BrandAsset.brand_id"
    )
    lora_models = relationship("LoraModel", back_populates="brand", cascade="all, delete-orphan")
    rules = relationship("BrandRule", back_populates="brand", cascade="all, delete-orphan")
    logo_asset = relationship("BrandAsset", foreign_keys=[logo_asset_id], post_update=True)

    def font_list(self) -> list[str]:
        return [f.strip() for f in self.fonts.split(",") if f.strip()] if self.fonts else []


class BrandAsset(Base):
    __tablename__ = "brand_assets"

    id = Column(String, primary_key=True, default=gen_id)
    brand_id = Column(String, ForeignKey("brands.id"), nullable=False)
    file_path = Column(String, nullable=False)
    kind = Column(String, default="reference")  # reference | logo
    created_at = Column(DateTime, default=datetime.utcnow)

    brand = relationship("Brand", back_populates="assets", foreign_keys=[brand_id])


class LoraModel(Base):
    """A privately-trained, brand-owned LoRA. `category` slots it into the
    branding/typography/locale/community/subject preset matrix; weights_url
    is never returned to the client directly (see schemas.LoraTrainingOut)."""

    __tablename__ = "lora_models"

    id = Column(String, primary_key=True, default=gen_id)
    brand_id = Column(String, ForeignKey("brands.id"), nullable=False)
    category = Column(Enum(LoraCategory), default=LoraCategory.branding)
    name = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    subject_type = Column(String, default="style")  # style | subject (mock wizard's step-1 choice)
    replicate_training_id = Column(String, nullable=True)
    status = Column(Enum(TrainingStatus), default=TrainingStatus.pending)
    weights_url = Column(String, nullable=True)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    brand = relationship("Brand", back_populates="lora_models")


class BrandRule(Base):
    """One Brand Governance constraint, validated before launch (Brand
    Governance layer: e.g. logo_mandatory, primary_color_usage_min_pct,
    forbidden_fonts). `rule_type` selects which validator in
    services.governance applies; `value_json` carries its parameters."""

    __tablename__ = "brand_rules"

    id = Column(String, primary_key=True, default=gen_id)
    brand_id = Column(String, ForeignKey("brands.id"), nullable=False)
    rule_type = Column(String, nullable=False)  # logo_mandatory | forbidden_fonts | min_primary_color_usage
    value_json = Column(Text, default="{}")
    created_at = Column(DateTime, default=datetime.utcnow)

    brand = relationship("Brand", back_populates="rules")

    @property
    def value(self) -> dict:
        return json.loads(self.value_json or "{}")

    @value.setter
    def value(self, v: dict) -> None:
        self.value_json = json.dumps(v or {})


class Template(Base):
    """A reusable design template the Template Intelligence layer can match
    a campaign's goal/intent against (category-based retrieval today;
    embedding-based vector search is a deferred upgrade -- see
    services.template_service). Not the same as DocumentType, which is the
    structural taxonomy (flyer/brochure/calendar/...); a Template is a
    specific pre-built layout within one of those document types."""

    __tablename__ = "templates"

    id = Column(String, primary_key=True, default=gen_id)
    document_type_id = Column(String, ForeignKey("document_types.id"), nullable=False)
    name = Column(String, nullable=False)
    category = Column(String, nullable=False)  # wedding | birthday | political | religious | educational | retail | real_estate
    tags = Column(String, default="")  # comma-separated keyword tags used for retrieval
    canvas_json = Column(Text, default="{}")  # seed fabric.js layout
    preview_url = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    document_type = relationship("DocumentType")

    def tag_list(self) -> list[str]:
        return [t.strip() for t in self.tags.split(",") if t.strip()] if self.tags else []


class SharedLoraPreset(Base):
    """A platform-owned LoRA usable across tenants for a given category (e.g.
    a 'Tamil Nadu locale' or 'urban family community' preset), as opposed to a
    brand's own private LoraModel. Selected the same way in generation params,
    just sourced from this table instead of LoraModel."""

    __tablename__ = "shared_lora_presets"

    id = Column(String, primary_key=True, default=gen_id)
    key = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    category = Column(Enum(LoraCategory), nullable=False)
    weights_url = Column(String, nullable=False)
    default_weight = Column(String, default="0.5")
    created_at = Column(DateTime, default=datetime.utcnow)


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
    media_type = Column(Enum(MediaType), default=MediaType.image)
    status = Column(Enum(JobStatus), default=JobStatus.pending)
    error = Column(Text, nullable=True)
    is_favorite = Column(Integer, default=0)  # bool: Library "favorite" heart toggle
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
    output_url = Column(String, nullable=True)  # app-owned storage URL, never the raw provider URL
    video_replicate_prediction_id = Column(String, nullable=True)
    video_status = Column(Enum(JobStatus), nullable=True)
    video_url = Column(String, nullable=True)
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


def _json_property(attr: str):
    def getter(self):
        return json.loads(getattr(self, attr) or "{}")

    def setter(self, value: dict):
        setattr(self, attr, json.dumps(value or {}))

    return property(getter, setter)


class Campaign(Base):
    """End-to-end workflow instance: Goal -> Layout -> Content -> Preview ->
    Audience -> Generate -> Review -> Launch. Each stage's working data is kept
    in its own JSON blob so the workflow doesn't need a table per stage; the
    `deliverable_id` link is set once Generate has run."""

    __tablename__ = "campaigns"

    id = Column(String, primary_key=True, default=gen_id)
    brand_id = Column(String, ForeignKey("brands.id"), nullable=False)
    deliverable_id = Column(String, ForeignKey("deliverables.id"), nullable=True)
    stage = Column(Enum(CampaignStage), default=CampaignStage.goal)

    goal_json = Column(Text, default="{}")
    layout_json = Column(Text, default="{}")
    content_json = Column(Text, default="{}")
    preview_json = Column(Text, default="{}")
    audience_json = Column(Text, default="{}")
    review_json = Column(Text, default="{}")
    launch_json = Column(Text, default="{}")

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    brand = relationship("Brand")
    deliverable = relationship("Deliverable")
    assets = relationship("CampaignAsset", back_populates="campaign", cascade="all, delete-orphan")

    goal = _json_property("goal_json")
    layout = _json_property("layout_json")
    content = _json_property("content_json")
    preview = _json_property("preview_json")
    audience = _json_property("audience_json")
    review = _json_property("review_json")
    launch = _json_property("launch_json")


class CampaignAsset(Base):
    """A content-stage photo upload (distinct from BrandAsset, which feeds LoRA
    training/IP-Adapter), e.g. product shots dropped into the layout by the user."""

    __tablename__ = "campaign_assets"

    id = Column(String, primary_key=True, default=gen_id)
    campaign_id = Column(String, ForeignKey("campaigns.id"), nullable=False)
    file_path = Column(String, nullable=False)
    label = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    campaign = relationship("Campaign", back_populates="assets")


class Profile(Base):
    """Single-tenant placeholder for the Profile settings screen. No auth
    system exists yet, so this is a singleton row rather than a per-session
    user; email is set once and never edited (matches the mock's disabled
    Email field with the "Email can't be changed." caption)."""

    __tablename__ = "profiles"

    id = Column(String, primary_key=True, default=gen_id)
    email = Column(String, nullable=False)
    display_name = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class WebhookEvent(Base):
    """Records every Replicate webhook delivery by provider prediction id so
    handling stays idempotent under at-least-once delivery -- a duplicate
    webhook for a prediction we've already processed is a no-op."""

    __tablename__ = "webhook_events"

    id = Column(String, primary_key=True, default=gen_id)
    provider_prediction_id = Column(String, unique=True, nullable=False)
    payload_json = Column(Text, default="{}")
    processed_at = Column(DateTime, default=datetime.utcnow)
