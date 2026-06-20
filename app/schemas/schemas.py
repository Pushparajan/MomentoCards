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


class CalendarGenerateRequest(BaseModel):
    brand_id: str
    month: int
    year: int
    style: str = "vector"
    use_brand_lora: bool = False
    ip_adapter_asset_id: str | None = None


class CalendarJobOut(BaseModel):
    id: str
    brand_id: str
    month: int
    year: int
    status: str
    output_url: str | None
    error: str | None

    class Config:
        from_attributes = True
