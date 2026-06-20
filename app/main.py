from fastapi import FastAPI

from app.api import brands, calendars, training
from app.core.db import Base, engine

Base.metadata.create_all(bind=engine)

app = FastAPI(title="MomentoCards Multi-LoRA Calendar Engine")

app.include_router(brands.router)
app.include_router(training.router)
app.include_router(calendars.router)


@app.get("/health")
def health():
    return {"status": "ok"}
