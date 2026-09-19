"""FastAPI dependencies — shared across routes."""
from __future__ import annotations

from functools import lru_cache

from fastapi import Request

from app.core.config import get_settings
from app.services.chunking_service import ChunkingService
from app.services.document_service import DocumentService
from app.services.evidence_service import EvidenceService
from app.services.llm_service import LLMService
from app.services.rag_pipeline import RagPipeline
from app.services.retrieval_service import RetrievalService
from app.services.vector_store_service import get_vector_store_service


@lru_cache
def get_document_service() -> DocumentService:
    settings = get_settings()
    return DocumentService(max_upload_size_bytes=settings.max_upload_size_bytes)


@lru_cache
def get_rag_pipeline() -> RagPipeline:
    return RagPipeline(
        chunking_service=ChunkingService(),
        vector_store_service=get_vector_store_service(),
        retrieval_service=RetrievalService(vector_store=get_vector_store_service()),
        llm_service=LLMService(),
        evidence_service=EvidenceService(),
    )
