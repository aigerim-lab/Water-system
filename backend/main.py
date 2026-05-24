"""FastAPI application entry point.

Run from project root:
  python3 -m uvicorn backend.main:app --reload --port 8000

Architecture:
  React frontend  →  REST API (this app)  →  data/ + analytics/
  Streamlit app.py remains available as standalone analytical UI.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.routes.dashboard import router as dashboard_router
from config.logging_config import get_logger

logger = get_logger(__name__)

app = FastAPI(
    title="Kazakhstan Water Quality API",
    description=(
        "REST backend for water pollution monitoring. "
        "Business logic lives in backend/services and analytics/ modules."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(dashboard_router)


@app.get("/api/health")
def health():
    meta = dashboard_service_meta_safe()
    return {"status": "ok", "dataset_exists": meta.get("dataset_exists", False)}


def dashboard_service_meta_safe():
    try:
        from backend.services.dashboard_service import dashboard_service
        return dashboard_service.meta()
    except Exception as exc:
        logger.warning("Health check meta failed: %s", exc)
        return {}


@app.on_event("startup")
def startup():
    from backend.services.dashboard_service import dashboard_service
    if dashboard_service.meta()["dataset_exists"]:
        dashboard_service.load_dataset()
        logger.info("Backend startup: dataset preloaded")
    else:
        logger.warning("Backend startup: dataset missing — run python3 -m data.build_dataset")
