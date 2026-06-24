"""Content marketing platform: text-content templates, brand voice profiles,
generation/rewrite drafts, review/approval workflow, audit log, export, and
lightweight admin/governance -- distinct from the visual creative pipeline in
app.models.models (LoraModel/Deliverable/Campaign are for image generation;
these models are for marketing copy)."""

import enum
import json
import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.core.db import Base


def gen_id() -> str:
    return uuid.uuid4().hex


class TemplateStatus(str, enum.Enum):
    active = "active"
    archived = "archived"


class ContentTemplate(Base):
    """A reusable text-content template (channel/objective/body/language).
    Archiving removes it from selection for new generation without deleting
    history (existing GeneratedContent rows keep their template_id)."""

    __tablename__ = "content_templates"

    id = Column(String, primary_key=True, default=gen_id)
    name = Column(String, nullable=False)
    channel = Column(String, nullable=False)  # e.g. email, social, blog, sms
    objective = Column(String, nullable=False)  # e.g. awareness, conversion
    body = Column(Text, nullable=False)
    language = Column(String, default="en")
    status = Column(Enum(TemplateStatus), default=TemplateStatus.active)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    versions = relationship(
        "ContentTemplateVersion", back_populates="template", cascade="all, delete-orphan", order_by="ContentTemplateVersion.version_number"
    )


class ContentTemplateVersion(Base):
    """Immutable snapshot of a ContentTemplate's body, recorded on every save
    so version history can be viewed and restored (restore creates a new
    latest version rather than overwriting)."""

    __tablename__ = "content_template_versions"

    id = Column(String, primary_key=True, default=gen_id)
    template_id = Column(String, ForeignKey("content_templates.id"), nullable=False)
    version_number = Column(Integer, nullable=False)
    body = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    template = relationship("ContentTemplate", back_populates="versions")


class BrandProfile(Base):
    """Brand voice/governance profile for content generation (tone, preferred
    vocabulary, banned terms) -- distinct from app.models.models.Brand, which
    carries visual identity for image generation."""

    __tablename__ = "brand_profiles"

    id = Column(String, primary_key=True, default=gen_id)
    name = Column(String, nullable=False)
    tone = Column(String, nullable=True)
    preferred_vocabulary = Column(String, default="")  # comma-separated
    banned_terms = Column(String, default="")  # comma-separated
    is_default_for_team = Column(Integer, default=0)  # bool
    status = Column(Enum(TemplateStatus), default=TemplateStatus.active)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def vocabulary_list(self) -> list[str]:
        return [v.strip() for v in self.preferred_vocabulary.split(",") if v.strip()]

    def banned_list(self) -> list[str]:
        return [v.strip() for v in self.banned_terms.split(",") if v.strip()]


class ContentStatus(str, enum.Enum):
    draft = "draft"
    in_review = "in_review"
    approved = "approved"
    rejected = "rejected"
    published = "published"


class GeneratedContent(Base):
    """One piece of marketing copy: created from a template+brief, refined
    through rewrite/review cycles, each producing a new ContentVersion."""

    __tablename__ = "generated_contents"

    id = Column(String, primary_key=True, default=gen_id)
    template_id = Column(String, ForeignKey("content_templates.id"), nullable=False)
    brand_profile_id = Column(String, ForeignKey("brand_profiles.id"), nullable=False)
    campaign_name = Column(String, nullable=True)
    prompt_brief = Column(Text, nullable=False)
    keywords = Column(String, default="")  # comma-separated
    output_length = Column(String, default="medium")  # short | medium | long
    status = Column(Enum(ContentStatus), default=ContentStatus.draft)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    template = relationship("ContentTemplate")
    brand_profile = relationship("BrandProfile")
    versions = relationship(
        "ContentVersion", back_populates="content", cascade="all, delete-orphan", order_by="ContentVersion.version_number"
    )
    submissions = relationship("ReviewSubmission", back_populates="content", cascade="all, delete-orphan")

    def latest_version(self) -> "ContentVersion | None":
        return self.versions[-1] if self.versions else None


class ContentVersion(Base):
    """One immutable draft snapshot. `change_type` records why it exists
    (generate/rewrite/restore) for the audit trail."""

    __tablename__ = "content_versions"

    id = Column(String, primary_key=True, default=gen_id)
    content_id = Column(String, ForeignKey("generated_contents.id"), nullable=False)
    version_number = Column(Integer, nullable=False)
    body = Column(Text, nullable=False)
    change_type = Column(String, nullable=False)  # generate | rewrite | restore
    actor = Column(String, default="system")
    created_at = Column(DateTime, default=datetime.utcnow)

    content = relationship("GeneratedContent", back_populates="versions")


class ReviewStageStatus(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"
    changes_requested = "changes_requested"
    escalated = "escalated"


class ReviewSubmission(Base):
    """One pass of a content version through a (simple, ordered) review
    route. `stage` is the route's current position (e.g. "legal",
    "marketing_lead"); decisions are recorded as ReviewDecision rows."""

    __tablename__ = "review_submissions"

    id = Column(String, primary_key=True, default=gen_id)
    content_id = Column(String, ForeignKey("generated_contents.id"), nullable=False)
    version_id = Column(String, ForeignKey("content_versions.id"), nullable=False)
    review_route = Column(String, default="")  # comma-separated ordered stage names
    stage = Column(String, nullable=False)
    sla_due_date = Column(DateTime, nullable=True)
    status = Column(Enum(ReviewStageStatus), default=ReviewStageStatus.pending)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    content = relationship("GeneratedContent", back_populates="submissions")
    decisions = relationship("ReviewDecision", back_populates="submission", cascade="all, delete-orphan")

    def route_stages(self) -> list[str]:
        return [s.strip() for s in self.review_route.split(",") if s.strip()]


class ReviewDecision(Base):
    """One reviewer action on a ReviewSubmission. Comment is mandatory for
    reject/changes_requested (enforced in services.review_workflow)."""

    __tablename__ = "review_decisions"

    id = Column(String, primary_key=True, default=gen_id)
    submission_id = Column(String, ForeignKey("review_submissions.id"), nullable=False)
    stage = Column(String, nullable=False)
    decision = Column(Enum(ReviewStageStatus), nullable=False)
    comment = Column(Text, nullable=True)
    escalate = Column(Integer, default=0)  # bool
    actor = Column(String, default="reviewer")
    created_at = Column(DateTime, default=datetime.utcnow)

    submission = relationship("ReviewSubmission", back_populates="decisions")


class AuditLog(Base):
    """Immutable record of every content lifecycle event (generate, rewrite,
    submit, decide, restore, export, ...). Never updated or deleted after
    creation -- only ever queried (services.audit_log enforces append-only
    by not exposing any update/delete path)."""

    __tablename__ = "audit_logs"

    id = Column(String, primary_key=True, default=gen_id)
    event_id = Column(String, unique=True, default=gen_id)
    content_id = Column(String, ForeignKey("generated_contents.id"), nullable=True)
    change_type = Column(String, nullable=False)  # generate | rewrite | submit | approve | reject | restore | export
    stage = Column(String, nullable=True)
    actor = Column(String, default="system")
    source_ip = Column(String, nullable=True)
    detail_json = Column(Text, default="{}")
    created_at = Column(DateTime, default=datetime.utcnow)

    @property
    def detail(self) -> dict:
        return json.loads(self.detail_json or "{}")

    @detail.setter
    def detail(self, value: dict) -> None:
        self.detail_json = json.dumps(value or {})


class ExportStatus(str, enum.Enum):
    pending = "pending"
    succeeded = "succeeded"
    failed = "failed"


class ExportDestination(Base):
    """A downstream connector (CMS, social scheduler, email platform, ...)
    content can be exported to once approved."""

    __tablename__ = "export_destinations"

    id = Column(String, primary_key=True, default=gen_id)
    name = Column(String, nullable=False)
    destination_type = Column(String, nullable=False)  # cms | social | email | webhook
    workspace = Column(String, nullable=True)
    auth_status = Column(String, default="connected")  # connected | disconnected | error
    created_at = Column(DateTime, default=datetime.utcnow)


class ExportRecord(Base):
    """One export attempt of an approved GeneratedContent to a destination.
    Retries increment `retry_count` and re-use the same row rather than
    creating a new one, so history per content item stays linear."""

    __tablename__ = "export_records"

    id = Column(String, primary_key=True, default=gen_id)
    content_id = Column(String, ForeignKey("generated_contents.id"), nullable=False)
    destination_id = Column(String, ForeignKey("export_destinations.id"), nullable=False)
    content_format = Column(String, default="plain_text")  # plain_text | html | markdown
    metadata_json = Column(Text, default="{}")
    schedule = Column(String, nullable=True)  # ISO datetime string, optional
    status = Column(Enum(ExportStatus), default=ExportStatus.pending)
    failure_reason = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    content = relationship("GeneratedContent")
    destination = relationship("ExportDestination")

    @property
    def metadata_mapping(self) -> dict:
        return json.loads(self.metadata_json or "{}")

    @metadata_mapping.setter
    def metadata_mapping(self, value: dict) -> None:
        self.metadata_json = json.dumps(value or {})


class PlatformRole(str, enum.Enum):
    admin = "admin"
    reviewer = "reviewer"
    creator = "creator"
    viewer = "viewer"


class PlatformUser(Base):
    """Minimal user/role record for admin governance (User/Role Management
    story). Not wired to authentication -- this session has none -- it only
    establishes who-can-do-what for policy/limit enforcement and analytics
    attribution."""

    __tablename__ = "platform_users"

    id = Column(String, primary_key=True, default=gen_id)
    email = Column(String, unique=True, nullable=False)
    role = Column(Enum(PlatformRole), default=PlatformRole.creator)
    team = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class PolicyConfig(Base):
    """Platform-wide content policy: restricted terms, review rules,
    retention period. Violations are logged (services.policy_engine) rather
    than silently enforced, so Compliance Insights can surface them."""

    __tablename__ = "policy_configs"

    id = Column(String, primary_key=True, default=gen_id)
    name = Column(String, nullable=False)
    restricted_terms = Column(String, default="")  # comma-separated
    review_rules_json = Column(Text, default="{}")  # e.g. {"min_stages": 2}
    retention_period_days = Column(Integer, default=365)
    created_at = Column(DateTime, default=datetime.utcnow)

    def restricted_term_list(self) -> list[str]:
        return [t.strip() for t in self.restricted_terms.split(",") if t.strip()]

    @property
    def review_rules(self) -> dict:
        return json.loads(self.review_rules_json or "{}")

    @review_rules.setter
    def review_rules(self, value: dict) -> None:
        self.review_rules_json = json.dumps(value or {})


class ModelLimit(Base):
    """Per-model usage limit (e.g. max generations/day) for governance over
    AI spend/usage; enforcement happens in services.policy_engine."""

    __tablename__ = "model_limits"

    id = Column(String, primary_key=True, default=gen_id)
    model_name = Column(String, nullable=False, unique=True)
    daily_limit = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
