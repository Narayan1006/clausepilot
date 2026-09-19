"""
ClausePilot Backend Configuration
Reads settings from environment variables / .env file.
Groq API key is optional at startup — Phase 1 does not call the LLM.
"""
from __future__ import annotations

import os
from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ──────────────────────────────
    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    log_level: str = "INFO"

    # ── CORS ─────────────────────────────────────
    # Accepts a comma-separated string or a JSON list via env var
    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    # ── Upload Limits ─────────────────────────────
    max_upload_size_mb: int = 20
    upload_dir: str = "./uploads"

    @property
    def max_upload_size_bytes(self) -> int:
        return self.max_upload_size_mb * 1024 * 1024

    # ── Database ─────────────────────────────────
    database_path: str = "./clausepilot.db"

    # ── Groq LLM (Phase 2+) ──────────────────────
    # Optional — backend starts without this in Phase 1
    groq_api_key: str = ""
    groq_model: str = "openai/gpt-oss-120b"

    # ── Vector Store (Phase 2+) ───────────────────
    chroma_persist_dir: str = "./chroma_db"

    # ── Embeddings (Phase 2+) ─────────────────────
    embedding_model: str = "all-MiniLM-L6-v2"

    # ── Comparison Engine (Phase 4 & 5 Hardening) ──
    comparison_top_k: int = 8
    comparison_max_context_chars: int = 12000
    comparison_min_retrieval_score: float = 0.2


@lru_cache
def get_settings() -> Settings:
    return Settings()
