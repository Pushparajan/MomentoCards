import enum
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


class CalendarJob(Base):
    __tablename__ = "calendar_jobs"

    id = Column(String, primary_key=True, default=gen_id)
    brand_id = Column(String, ForeignKey("brands.id"), nullable=False)
    month = Column(Integer, nullable=False)
    year = Column(Integer, nullable=False)
    style = Column(String, default="vector")  # vector | photographic | minimal
    grid_path = Column(String, nullable=True)
    canny_path = Column(String, nullable=True)
    replicate_prediction_id = Column(String, nullable=True)
    status = Column(Enum(JobStatus), default=JobStatus.pending)
    output_url = Column(String, nullable=True)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
