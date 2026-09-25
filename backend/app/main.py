"""
ClausePilot FastAPI Application Entry Point.

Design decisions:
- Database is initialized at startup via lifespan context manager.
- Heavy AI services (embeddings, vector store, Groq) are NOT initialized here.
- CORS origins are configurable via environment variable.
- /health endpoint requires NO external services.
- Backend starts successfully even when GROQ_API_KEY is absent.
"""
from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import analysis, chat, comparison, documents
from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger
from app.utils.db import init_db

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan: startup → yield → shutdown."""
    settings = get_settings()
    configure_logging(settings.log_level)
    logger.info("ClausePilot backend starting up (env=%s)", settings.app_env)

    # Initialize SQLite database (creates tables if they don't exist)
    init_db()

    # Ensure upload directory exists
    from app.utils.file_utils import get_upload_dir
    get_upload_dir()
    logger.info("Upload directory ready: %s", settings.upload_dir)

    if not settings.groq_api_key:
        logger.warning(
            "GROQ_API_KEY is not set. "
            "LLM endpoints will return 501 until Phase 2 is configured."
        )

    logger.info("ClausePilot Phase 1 ready — health endpoint and document upload active")
    yield
    logger.info("ClausePilot backend shutting down")


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="ClausePilot API",
        description=(
            "Legal Decision & Evidence Workspace — "
            "understand contracts, verify evidence, know what to ask next.\n\n"
            "**Phase 1**: Document upload, extraction, and metadata. "
            "RAG pipeline (Phase 2) is not yet implemented."
        ),
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # ── CORS ─────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_origin_regex=r"https://.*\.vercel\.app",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Routes ───────────────────────────────────
    app.include_router(documents.router)
    app.include_router(analysis.router)
    app.include_router(chat.router)
    app.include_router(comparison.router)

    # ── Safe Exception Handling ──────────────────
    @app.exception_handler(Exception)
    async def global_exception_handler(request, exc: Exception) -> JSONResponse:
        logger.error("Unhandled exception for %s: %s", request.url.path, exc, exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "detail": "An internal server error occurred. Please try again or check system logs.",
                "type": "server_error",
            },
        )

    # ── Health ───────────────────────────────────
    @app.get("/health", tags=["system"], summary="Health check")
    async def health() -> JSONResponse:
        """
        Lightweight health check.
        Does NOT depend on Groq, ChromaDB, embeddings, or any external service.
        Returns 200 as long as the application is running.
        """
        settings = get_settings()
        return JSONResponse(
            content={
                "status": "ok",
                "service": "ClausePilot API",
                "version": "1.0.0",
                "phase": "Phase 5 — Production Ready Workspace",
                "capabilities": {
                    "document_upload": True,
                    "pdf_extraction": True,
                    "rag_pipeline": True,
                    "llm_analysis": bool(settings.groq_api_key),
                    "document_comparison": True,
                },
            }
        )

    @app.get("/", tags=["system"], include_in_schema=False)
    async def root() -> JSONResponse:
        return JSONResponse(
            content={
                "message": "ClausePilot API is running. See /docs for API documentation.",
                "docs": "/docs",
                "health": "/health",
            }
        )

    return app


app = create_app()
