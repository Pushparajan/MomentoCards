from datetime import datetime

from pydantic import BaseModel


# --- Templates & Brand Profiles ---


class ContentTemplateCreate(BaseModel):
    name: str
    channel: str
    objective: str
    body: str
    language: str = "en"


class ContentTemplateUpdate(BaseModel):
    name: str | None = None
    channel: str | None = None
    objective: str | None = None
    body: str | None = None
    language: str | None = None


class ContentTemplateVersionOut(BaseModel):
    id: str
    version_number: int
    body: str
    created_at: datetime

    class Config:
        from_attributes = True


class ContentTemplateOut(BaseModel):
    id: str
    name: str
    channel: str
    objective: str
    body: str
    language: str
    status: str

    class Config:
        from_attributes = True

    @classmethod
    def from_orm_model(cls, t) -> "ContentTemplateOut":
        return cls(
            id=t.id, name=t.name, channel=t.channel, objective=t.objective, body=t.body, language=t.language, status=t.status.value
        )


class BrandProfileCreate(BaseModel):
    name: str
    tone: str | None = None
    preferred_vocabulary: list[str] = []
    banned_terms: list[str] = []
    is_default_for_team: bool = False


class BrandProfileUpdate(BaseModel):
    name: str | None = None
    tone: str | None = None
    preferred_vocabulary: list[str] | None = None
    banned_terms: list[str] | None = None
    is_default_for_team: bool | None = None


class BrandProfileOut(BaseModel):
    id: str
    name: str
    tone: str | None
    preferred_vocabulary: list[str]
    banned_terms: list[str]
    is_default_for_team: bool
    status: str

    class Config:
        from_attributes = True

    @classmethod
    def from_orm_model(cls, p) -> "BrandProfileOut":
        return cls(
            id=p.id,
            name=p.name,
            tone=p.tone,
            preferred_vocabulary=p.vocabulary_list(),
            banned_terms=p.banned_list(),
            is_default_for_team=bool(p.is_default_for_team),
            status=p.status.value,
        )


# --- Generation / Rewrite ---


class GenerateContentRequest(BaseModel):
    template_id: str
    brand_profile_id: str
    campaign_name: str | None = None
    prompt_brief: str
    keywords: list[str] = []
    output_length: str = "medium"


class RewriteContentRequest(BaseModel):
    rewrite_type: str  # tone | length | cta | language
    tone: str | None = None
    output_length: str | None = None
    cta_focus: str | None = None
    language: str | None = None


class ContentVersionOut(BaseModel):
    id: str
    version_number: int
    body: str
    change_type: str
    actor: str
    created_at: datetime

    class Config:
        from_attributes = True


class GeneratedContentOut(BaseModel):
    id: str
    template_id: str
    brand_profile_id: str
    campaign_name: str | None
    prompt_brief: str
    keywords: list[str]
    output_length: str
    status: str
    error: str | None
    versions: list[ContentVersionOut]

    class Config:
        from_attributes = True

    @classmethod
    def from_orm_model(cls, c) -> "GeneratedContentOut":
        return cls(
            id=c.id,
            template_id=c.template_id,
            brand_profile_id=c.brand_profile_id,
            campaign_name=c.campaign_name,
            prompt_brief=c.prompt_brief,
            keywords=[k.strip() for k in (c.keywords or "").split(",") if k.strip()],
            output_length=c.output_length,
            status=c.status.value,
            error=c.error,
            versions=[ContentVersionOut.model_validate(v) for v in c.versions],
        )


# --- Review / Approval ---


class SubmitForReviewRequest(BaseModel):
    review_route: list[str]  # ordered stage names, e.g. ["legal", "marketing_lead"]
    sla_due_date: datetime | None = None


class ReviewDecisionRequest(BaseModel):
    decision: str  # approved | rejected | changes_requested
    comment: str | None = None
    escalate: bool = False
    actor: str = "reviewer"


class ReviewDecisionOut(BaseModel):
    id: str
    stage: str
    decision: str
    comment: str | None
    escalate: bool
    actor: str
    created_at: datetime

    class Config:
        from_attributes = True

    @classmethod
    def from_orm_model(cls, d) -> "ReviewDecisionOut":
        return cls(
            id=d.id, stage=d.stage, decision=d.decision.value, comment=d.comment, escalate=bool(d.escalate), actor=d.actor, created_at=d.created_at
        )


class ReviewSubmissionOut(BaseModel):
    id: str
    content_id: str
    version_id: str
    review_route: list[str]
    stage: str
    sla_due_date: datetime | None
    status: str
    decisions: list[ReviewDecisionOut]

    class Config:
        from_attributes = True

    @classmethod
    def from_orm_model(cls, s) -> "ReviewSubmissionOut":
        return cls(
            id=s.id,
            content_id=s.content_id,
            version_id=s.version_id,
            review_route=s.route_stages(),
            stage=s.stage,
            sla_due_date=s.sla_due_date,
            status=s.status.value,
            decisions=[ReviewDecisionOut.from_orm_model(d) for d in s.decisions],
        )


# --- Audit ---


class AuditLogOut(BaseModel):
    id: str
    event_id: str
    content_id: str | None
    change_type: str
    stage: str | None
    actor: str
    source_ip: str | None
    detail: dict
    created_at: datetime

    class Config:
        from_attributes = True

    @classmethod
    def from_orm_model(cls, a) -> "AuditLogOut":
        return cls(
            id=a.id,
            event_id=a.event_id,
            content_id=a.content_id,
            change_type=a.change_type,
            stage=a.stage,
            actor=a.actor,
            source_ip=a.source_ip,
            detail=a.detail,
            created_at=a.created_at,
        )


class VersionCompareOut(BaseModel):
    from_version: ContentVersionOut
    to_version: ContentVersionOut


class RestoreVersionRequest(BaseModel):
    version_id: str
    actor: str = "system"


# --- Export ---


class ExportDestinationCreate(BaseModel):
    name: str
    destination_type: str
    workspace: str | None = None


class ExportDestinationOut(BaseModel):
    id: str
    name: str
    destination_type: str
    workspace: str | None
    auth_status: str

    class Config:
        from_attributes = True


class ExportRequest(BaseModel):
    destination_id: str
    content_format: str = "plain_text"
    metadata_mapping: dict = {}
    schedule: str | None = None


class ExportRecordOut(BaseModel):
    id: str
    content_id: str
    destination_id: str
    content_format: str
    metadata_mapping: dict
    schedule: str | None
    status: str
    failure_reason: str | None
    retry_count: int

    class Config:
        from_attributes = True

    @classmethod
    def from_orm_model(cls, e) -> "ExportRecordOut":
        return cls(
            id=e.id,
            content_id=e.content_id,
            destination_id=e.destination_id,
            content_format=e.content_format,
            metadata_mapping=e.metadata_mapping,
            schedule=e.schedule,
            status=e.status.value,
            failure_reason=e.failure_reason,
            retry_count=e.retry_count,
        )


# --- Admin / Governance / Analytics ---


class PlatformUserCreate(BaseModel):
    email: str
    role: str = "creator"
    team: str | None = None


class PlatformUserOut(BaseModel):
    id: str
    email: str
    role: str
    team: str | None

    class Config:
        from_attributes = True

    @classmethod
    def from_orm_model(cls, u) -> "PlatformUserOut":
        return cls(id=u.id, email=u.email, role=u.role.value, team=u.team)


class PolicyConfigCreate(BaseModel):
    name: str
    restricted_terms: list[str] = []
    review_rules: dict = {}
    retention_period_days: int = 365


class PolicyConfigOut(BaseModel):
    id: str
    name: str
    restricted_terms: list[str]
    review_rules: dict
    retention_period_days: int

    class Config:
        from_attributes = True

    @classmethod
    def from_orm_model(cls, p) -> "PolicyConfigOut":
        return cls(
            id=p.id, name=p.name, restricted_terms=p.restricted_term_list(), review_rules=p.review_rules, retention_period_days=p.retention_period_days
        )


class ModelLimitCreate(BaseModel):
    model_config = {"protected_namespaces": ()}

    model_name: str
    daily_limit: int


class ModelLimitOut(BaseModel):
    model_config = {"protected_namespaces": (), "from_attributes": True}

    id: str
    model_name: str
    daily_limit: int


class AnalyticsOut(BaseModel):
    total_generated: int
    approval_rate: float
    rejection_rate: float
    success_rate: float
    rejection_reasons: dict[str, int]
