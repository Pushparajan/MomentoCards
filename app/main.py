import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api import (
    audit,
    brand_profiles,
    brand_rules,
    brands,
    campaigns,
    content_admin,
    content_templates,
    dashboard,
    deliverables,
    document_types,
    exports,
    generated_content,
    lora_presets,
    organizations,
    profile,
    review,
    templates,
    training,
    webhooks,
)
from app.core.config import settings
from app.core.db import Base, SessionLocal, engine
from app.models import content_models  # noqa: F401  (registers content tables on Base)
from app.services.catalog_seed import seed_document_types

Base.metadata.create_all(bind=engine)

with SessionLocal() as db:
    seed_document_types(db)

os.makedirs(settings.storage_dir, exist_ok=True)

app = FastAPI(title="MomentoCards Multi-LoRA Deliverable Engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/storage", StaticFiles(directory=settings.storage_dir), name="storage")

app.include_router(organizations.router)
app.include_router(brands.router)
app.include_router(brand_rules.router)
app.include_router(training.router)
app.include_router(document_types.router)
app.include_router(templates.router)
app.include_router(deliverables.router)
app.include_router(campaigns.router)
app.include_router(lora_presets.router)
app.include_router(webhooks.router)
app.include_router(content_templates.router)
app.include_router(brand_profiles.router)
app.include_router(generated_content.router)
app.include_router(review.router)
app.include_router(audit.router)
app.include_router(exports.router)
app.include_router(content_admin.router)
app.include_router(profile.router)
app.include_router(dashboard.router)


@app.get("/health")
def health():
    return {"status": "ok"}
