from fastapi import FastAPI

from app.api import brands, deliverables, document_types, training
from app.core.db import Base, SessionLocal, engine
from app.services.catalog_seed import seed_document_types

Base.metadata.create_all(bind=engine)

with SessionLocal() as db:
    seed_document_types(db)

app = FastAPI(title="MomentoCards Multi-LoRA Deliverable Engine")

app.include_router(brands.router)
app.include_router(training.router)
app.include_router(document_types.router)
app.include_router(deliverables.router)


@app.get("/health")
def health():
    return {"status": "ok"}
