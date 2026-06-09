"""FastAPI entry point for the Nexora backend."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI

from backend.app.api.routes_agents import router as agents_router
from backend.app.api.routes_deployment import router as deployment_router
from backend.app.api.routes_health import router as health_router
from backend.app.api.routes_explainability import router as explainability_router
from backend.app.api.routes_inference import router as inference_router
from backend.app.api.routes_ingestion import router as ingestion_router
from backend.app.api.routes_models import router as models_router
from backend.app.api.routes_performance import router as performance_router
from backend.app.api.routes_processing import router as processing_router
from backend.app.api.routes_rag import router as rag_router
from backend.app.api.routes_reasoning import router as reasoning_router
from backend.app.api.routes_retrieval import router as retrieval_router
from backend.app.api.routes_risk import router as risk_router
from backend.app.core.config import get_settings
from backend.app.core.logging_config import setup_logging


setup_logging()
settings = get_settings()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    logger.info(
        "Nexora API startup complete | environment=%s | local_first=%s",
        settings.environment,
        settings.local_first,
    )
    yield


app = FastAPI(
    title="Nexora API",
    version="0.1.0",
    description="Local-first backend for the Nexora Financial Scenario Intelligence Engine.",
    lifespan=lifespan,
)

app.include_router(health_router)
app.include_router(models_router)
app.include_router(inference_router)
app.include_router(ingestion_router)
app.include_router(processing_router)
app.include_router(retrieval_router)
app.include_router(rag_router)
app.include_router(reasoning_router)
app.include_router(risk_router)
app.include_router(explainability_router)
app.include_router(agents_router)
app.include_router(performance_router)
app.include_router(deployment_router)


@app.get("/")
def root() -> dict[str, str]:
    return {
        "app": "Nexora",
        "status": "running",
        "message": "Financial Scenario Intelligence Engine backend is active.",
    }
