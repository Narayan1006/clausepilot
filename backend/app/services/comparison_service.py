"""Comparison Service — Phase 4 stub."""
from __future__ import annotations
from app.core.logging import get_logger
logger = get_logger(__name__)

class ComparisonService:
    """
    Compares two documents using semantic alignment + LLM diff.
    Phase 4 implementation pending.
    """
    def compare(self, document_id_a: str, document_id_b: str, focus: str | None = None) -> dict:
        """Compare two documents. Phase 4."""
        raise NotImplementedError("ComparisonService.compare: Phase 4.")
