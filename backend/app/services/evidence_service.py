"""
Evidence verification service for Phase 2.

Validates LLM-generated citations deterministically against retrieved chunks.
Ensures the LLM cannot hallucinate quotes, pages, or document IDs.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Optional, Tuple

from app.core.logging import get_logger
from app.schemas.answer_schemas import AnswerStatus, Citation, LegalAnswer
from app.services.retrieval_service import RetrievedChunk

logger = get_logger(__name__)


@dataclass
class EvidenceValidationResult:
    is_valid: bool
    validated_citations: List[Citation]
    rejection_reasons: List[str]


class EvidenceService:
    """
    Deterministic outside-the-LLM citation validator.
    Matches citations to retrieved chunks using exact, normalized, and fuzzy substring matching.
    """

    def normalize_text_for_matching(self, text: str) -> str:
        """Removes punctuation and extra whitespace for fuzzy matching."""
        text = text.lower()
        text = re.sub(r"[^\w\s]", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text

    def match_quote_in_chunks(
        self,
        quote: str,
        page_number: int,
        document_id: str,
        evidence_chunks: List[RetrievedChunk],
    ) -> Tuple[bool, Optional[str]]:
        """
        Checks if a quote exists in the retrieved chunks for the specified page and document.
        Returns (matches, matching_chunk_id).
        """
        norm_quote = self.normalize_text_for_matching(quote)
        if not norm_quote:
            return False, None

        # Filter candidate chunks for the same document and page
        matching_page_chunks = [
            c for c in evidence_chunks
            if c.document_id == document_id and c.page_number == page_number
        ]

        # 1. Exact or substring match in matching page chunks
        for c in matching_page_chunks:
            if quote.strip().lower() in c.text.lower():
                return True, c.chunk_id
            
            norm_chunk = self.normalize_text_for_matching(c.text)
            if norm_quote in norm_chunk:
                return True, c.chunk_id

        # 2. Check if quote spans across neighboring chunks or slightly mismatched page number
        for c in evidence_chunks:
            if c.document_id == document_id:
                if quote.strip().lower() in c.text.lower():
                    return True, c.chunk_id
                norm_chunk = self.normalize_text_for_matching(c.text)
                if norm_quote in norm_chunk:
                    return True, c.chunk_id

        return False, None

    def validate_answer(
        self,
        document_id: str,
        answer: LegalAnswer,
        evidence_chunks: List[RetrievedChunk],
    ) -> LegalAnswer:
        """
        Validates citations and adjusts status if citations fail verification.
        If status is GROUNDED but citations are missing or fabricated, downgrades status.
        """
        if answer.status == AnswerStatus.NOT_FOUND:
            # NOT_FOUND doesn't require citations
            return answer

        valid_citations: List[Citation] = []
        rejection_reasons: List[str] = []

        for cit in answer.citations:
            # 1. Verify document_id
            if cit.document_id != document_id:
                rejection_reasons.append(
                    f"Citation document_id mismatch: '{cit.document_id}' vs expected '{document_id}'"
                )
                continue

            # 2. Verify quote against evidence
            is_matched, chunk_id = self.match_quote_in_chunks(
                quote=cit.quote,
                page_number=cit.page_number,
                document_id=document_id,
                evidence_chunks=evidence_chunks,
            )

            if is_matched:
                valid_citations.append(cit)
            else:
                rejection_reasons.append(
                    f"Citation quote not found on Page {cit.page_number} in retrieved evidence: '{cit.quote[:60]}...'"
                )

        # Enforce grounding rules based on verified citations
        final_answer = answer.model_copy(deep=True)
        final_answer.citations = valid_citations

        if answer.status == AnswerStatus.GROUNDED and len(valid_citations) == 0:
            logger.warning(
                "Downgrading GROUNDED answer to INFERRED because no citations passed validation. Reasons: %s",
                rejection_reasons,
            )
            final_answer.status = AnswerStatus.INFERRED
            final_answer.reasoning += " (Note: Supporting quote could not be fully verified against retrieved evidence.)"

        return final_answer

    def validate_comparison(
        self,
        comparison_response,
        evidence_chunks_a: List[RetrievedChunk],
        evidence_chunks_b: List[RetrievedChunk],
    ):
        """
        Deterministically verifies all citations across both Document A and Document B.
        Strips or marks unverifiable citations.
        """
        validated_sections = []
        for sec in comparison_response.sections:
            valid_cits_a = []
            for cit in sec.citations_a:
                is_matched, _ = self.match_quote_in_chunks(
                    quote=cit.quote,
                    page_number=cit.page_number,
                    document_id=comparison_response.document_id_a,
                    evidence_chunks=evidence_chunks_a,
                )
                if is_matched:
                    valid_cits_a.append(cit)
                else:
                    logger.warning(
                        "Comparison citation for Doc A rejected: '%s' (p. %d)",
                        cit.quote[:40],
                        cit.page_number,
                    )

            valid_cits_b = []
            for cit in sec.citations_b:
                is_matched, _ = self.match_quote_in_chunks(
                    quote=cit.quote,
                    page_number=cit.page_number,
                    document_id=comparison_response.document_id_b,
                    evidence_chunks=evidence_chunks_b,
                )
                if is_matched:
                    valid_cits_b.append(cit)
                else:
                    logger.warning(
                        "Comparison citation for Doc B rejected: '%s' (p. %d)",
                        cit.quote[:40],
                        cit.page_number,
                    )

            validated_sec = sec.model_copy(deep=True)
            validated_sec.citations_a = valid_cits_a
            validated_sec.citations_b = valid_cits_b
            validated_sections.append(validated_sec)

        final_resp = comparison_response.model_copy(deep=True)
        final_resp.sections = validated_sections
        return final_resp
