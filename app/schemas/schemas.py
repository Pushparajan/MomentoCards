from datetime import datetime

from pydantic import BaseModel


class BrandCreate(BaseModel):
    name: str
    primary_color: str | None = None
    secondary_color: str | None = None
    mood_keywords: str | None = None


class BrandOut(BaseModel):
    id: str
    name: str
    primary_color: str | None
    secondary_color: str | None
    mood_keywords: str | None
    created_at: datetime

    class Config:
        from_attributes = True


class LoraTrainingOut(BaseModel):
    id: str
    brand_id: str
    status: str
    weights_url: str | None
    error: str | None

    class Config:
        from_attributes = True


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
