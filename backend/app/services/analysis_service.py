"""Analysis Service — Phase 2 stub."""
from __future__ import annotations
from app.core.logging import get_logger
logger = get_logger(__name__)

class AnalysisService:
    """
    Generates attention map, obligations, risks, and missing information.
    Phase 2 implementation pending.
    """
    def analyze(self, document_id: str, decision_context: str) -> dict:
        """Run full analysis pipeline. Phase 2."""
        raise NotImplementedError("AnalysisService.analyze: Phase 2.")

    def get_checklist(self, document_id: str) -> list:
        """Generate 'Before You Sign' checklist. Phase 2."""
        raise NotImplementedError("AnalysisService.get_checklist: Phase 2.")

    def get_suggested_questions(self, document_id: str) -> list:
        """Generate questions for HR / legal professional. Phase 2."""
        raise NotImplementedError("AnalysisService.get_suggested_questions: Phase 2.")
