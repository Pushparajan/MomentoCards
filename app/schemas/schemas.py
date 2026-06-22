from datetime import datetime

from pydantic import BaseModel


class OrganizationCreate(BaseModel):
    name: str


class OrganizationOut(BaseModel):
    id: str
    name: str
    created_at: datetime

    class Config:
        from_attributes = True


class BrandCreate(BaseModel):
    name: str
    organization_id: str | None = None
    primary_color: str | None = None
    secondary_color: str | None = None
    mood_keywords: str | None = None
    industry: str | None = None
    voice: str | None = None
    fonts: str | None = None  # comma-separated
    logo_asset_id: str | None = None


class BrandOut(BaseModel):
    id: str
    name: str
    organization_id: str | None
    primary_color: str | None
    secondary_color: str | None
    mood_keywords: str | None
    industry: str | None
    voice: str | None
    fonts: str | None
    logo_asset_id: str | None
    created_at: datetime

    class Config:
        from_attributes = True


class BrandRuleCreate(BaseModel):
    rule_type: str  # logo_mandatory | forbidden_fonts | min_primary_color_usage
    value: dict = {}


class BrandRuleOut(BaseModel):
    id: str
    brand_id: str
    rule_type: str
    value: dict

    class Config:
        from_attributes = True

    @classmethod
    def from_orm_model(cls, rule) -> "BrandRuleOut":
        return cls(id=rule.id, brand_id=rule.brand_id, rule_type=rule.rule_type, value=rule.value)


class TemplateCreate(BaseModel):
    document_type_key: str
    name: str
    category: str
    tags: list[str] = []
    canvas_json: dict = {}
    preview_url: str | None = None


class TemplateOut(BaseModel):
    id: str
    document_type_id: str
    name: str
    category: str
    tags: list[str]
    canvas_json: dict
    preview_url: str | None

    class Config:
        from_attributes = True

    @classmethod
    def from_orm_model(cls, template) -> "TemplateOut":
        import json

        return cls(
            id=template.id,
            document_type_id=template.document_type_id,
            name=template.name,
            category=template.category,
            tags=template.tag_list(),
            canvas_json=json.loads(template.canvas_json or "{}"),
            preview_url=template.preview_url,
        )


class LoraTrainingOut(BaseModel):
    """Never exposes weights_url/file paths to the client -- only enough to
    select this LoRA by id (e.g. as style_lora_model_id) once it's ready."""

    id: str
    brand_id: str
    category: str
    status: str
    is_ready: bool
    error: str | None

    class Config:
        from_attributes = True

    @classmethod
    def from_orm_model(cls, lora) -> "LoraTrainingOut":
        return cls(
            id=lora.id,
            brand_id=lora.brand_id,
            category=lora.category.value,
            status=lora.status.value,
            is_ready=lora.status.value == "succeeded",
            error=lora.error,
        )


class SharedLoraPresetCreate(BaseModel):
    key: str
    name: str
    category: str
    weights_url: str
    default_weight: float = 0.5


class SharedLoraPresetOut(BaseModel):
    id: str
    key: str
    name: str
    category: str

    class Config:
        from_attributes = True


class VideoGenerateRequest(BaseModel):
    prompt: str | None = None


class DocumentTypeOut(BaseModel):
    id: str
    key: str
    name: str
    category: str
    layout_kind: str
    default_page_count: int
    requires_grid: bool
    fulfillment_options: list[str]

    class Config:
        from_attributes = True

    @classmethod
    def from_orm_model(cls, dt) -> "DocumentTypeOut":
        return cls(
            id=dt.id,
            key=dt.key,
            name=dt.name,
            category=dt.category,
            layout_kind=dt.layout_kind.value,
            default_page_count=dt.default_page_count,
            requires_grid=bool(dt.requires_grid),
            fulfillment_options=dt.fulfillment_list(),
        )


class DeliverablePageCreate(BaseModel):
    params: dict = {}


class DeliverableCreate(BaseModel):
    brand_id: str
    document_type_key: str
    title: str | None = None
    style: str = "vector"
    use_brand_lora: bool = False
    ip_adapter_asset_id: str | None = None
    pages: list[DeliverablePageCreate] | None = None  # defaults to document_type.default_page_count blank pages


class DeliverablePageOut(BaseModel):
    id: str
    page_number: int
    status: str
    output_url: str | None
    error: str | None

    class Config:
        from_attributes = True


class DeliverableOut(BaseModel):
    id: str
    brand_id: str
    document_type_id: str
    title: str | None
    style: str
    status: str
    error: str | None
    pages: list[DeliverablePageOut] = []

    class Config:
        from_attributes = True


# --- Campaign workflow (Goal -> Layout -> Content -> Preview -> Audience -> Generate -> Review -> Launch) ---


class CampaignCreate(BaseModel):
    brand_id: str


class GoalRequest(BaseModel):
    goal_text: str
    intent: str  # e.g. "promotion", "event", "announcement"


class LayoutRequest(BaseModel):
    document_type_key: str
    style_lora_model_id: str | None = None
    canvas_width: int = 1024
    canvas_height: int = 1024
    grid_pages: list[dict] | None = None  # e.g. [{"month": 6, "year": 2026}]


class ContentTextRequest(BaseModel):
    text_fields: dict


class PreviewSaveRequest(BaseModel):
    canvas_json: dict


class AudienceAnswerRequest(BaseModel):
    key: str
    answer: str


class AudienceQuestionOut(BaseModel):
    key: str
    question: str


class FinalCanvasSaveRequest(BaseModel):
    canvas_json: dict


class ReviewRequest(BaseModel):
    approved: bool
    comments: str | None = None


class CampaignOut(BaseModel):
    id: str
    brand_id: str
    deliverable_id: str | None
    stage: str
    goal: dict
    layout: dict
    content: dict
    preview: dict
    audience: dict
    review: dict
    launch: dict

    class Config:
        from_attributes = True
