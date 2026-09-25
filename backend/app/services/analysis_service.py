"""Analysis Service — Orchestrates contract risk analysis and signing checklists."""
from __future__ import annotations

from typing import Any, Optional
from app.core.logging import get_logger
from app.schemas.analysis_schemas import AnalysisResponse, ChecklistResponse, SuggestedQuestionsResponse

logger = get_logger(__name__)


class AnalysisService:
    """
    Generates attention map, obligations, risks, and missing information.
    Delegates to the central RagPipeline for evidence-grounded analysis.
    """

    def __init__(self, rag_pipeline: Optional[Any] = None) -> None:
        from app.services.rag_pipeline import RagPipeline
        self.rag = rag_pipeline or RagPipeline()

    def analyze(self, document_id: str, decision_context: str = "General Contract Review") -> AnalysisResponse:
        """Run full analysis pipeline."""
        return self.rag.analyze_document(document_id=document_id, decision_context=decision_context)

    def get_checklist(self, document_id: str, decision_context: str = "General Contract Review") -> ChecklistResponse:
        """Generate 'Before You Sign' checklist."""
        return self.rag.generate_checklist(document_id=document_id, decision_context=decision_context)

    def get_suggested_questions(self, document_id: str, decision_context: str = "General Contract Review") -> SuggestedQuestionsResponse:
        """Generate questions for HR / legal professional."""
        return self.rag.generate_suggested_questions(document_id=document_id, decision_context=decision_context)
