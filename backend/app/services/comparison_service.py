"""Comparison Service — Multi-contract semantic difference and conflict engine."""
from __future__ import annotations

from typing import Any, Optional
from app.core.logging import get_logger
from app.schemas.answer_schemas import ComparisonResponse

logger = get_logger(__name__)


class ComparisonService:
    """
    Compares two documents using semantic alignment + LLM diff.
    Delegates to the central RagPipeline for evidence-grounded comparison.
    """

    def __init__(self, rag_pipeline: Optional[Any] = None) -> None:
        from app.services.rag_pipeline import RagPipeline
        self.rag = rag_pipeline or RagPipeline()

    def compare(self, document_id_a: str, document_id_b: str, focus: Optional[str] = None) -> ComparisonResponse:
        """Compare two documents."""
        return self.rag.compare_documents(document_id_a=document_id_a, document_id_b=document_id_b, focus=focus)
