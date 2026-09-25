"""Conflict Detection Service — Identifies contradictory terms across clauses."""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from app.core.logging import get_logger

logger = get_logger(__name__)


class ConflictService:
    """
    Detects semantic and procedural conflicts within contract clauses.
    Delegates to the central RagPipeline for evidence-grounded risk and conflict extraction.
    """

    def __init__(self, rag_pipeline: Optional[Any] = None) -> None:
        from app.services.rag_pipeline import RagPipeline
        self.rag = rag_pipeline or RagPipeline()

    def detect_conflicts(self, document_id: str) -> List[Dict[str, Any]]:
        """Detect clause conflicts and mutually exclusive obligations."""
        analysis = self.rag.analyze_document(document_id=document_id)
        conflicts: List[Dict[str, Any]] = []
        for item in analysis.possible_conflicts:
            conflicts.append({
                "document_id": document_id,
                "conflict_description": item,
                "severity": "HIGH",
            })
        return conflicts
