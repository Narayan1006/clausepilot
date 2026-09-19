"""
Unit tests for Pydantic schemas.
Tests: LegalAnswer, Citation, AnswerStatus, DocumentUploadResponse.
"""
from __future__ import annotations

import pytest
from pydantic import ValidationError
from datetime import datetime, timezone

from app.schemas.answer_schemas import (
    AnswerConfidence,
    AnswerStatus,
    Citation,
    LegalAnswer,
)
from app.schemas.document_schemas import DocumentUploadResponse


class TestCitation:
    def test_valid_citation(self):
        c = Citation(
            document_id="doc-123",
            page_number=5,
            clause_number="8.2",
            quote="The notice period shall be sixty (60) days.",
        )
        assert c.page_number == 5
        assert c.quote == "The notice period shall be sixty (60) days."

    def test_optional_clause_number(self):
        c = Citation(
            document_id="doc-123",
            page_number=1,
            quote="Some text",
        )
        assert c.clause_number is None

    def test_empty_quote_rejected(self):
        with pytest.raises(ValidationError):
            Citation(
                document_id="doc-123",
                page_number=1,
                quote="",
            )


class TestLegalAnswer:
    def test_grounded_answer(self):
        answer = LegalAnswer(
            answer="Your notice period is 60 days.",
            status=AnswerStatus.GROUNDED,
            confidence=AnswerConfidence.HIGH,
            citations=[
                Citation(
                    document_id="doc-1",
                    page_number=14,
                    clause_number="8.2",
                    quote="Notice period shall be sixty (60) calendar days.",
                )
            ],
            reasoning="Clause 8.2 explicitly states the notice period.",
        )
        assert answer.status == AnswerStatus.GROUNDED
        assert len(answer.citations) == 1

    def test_not_found_answer(self):
        answer = LegalAnswer(
            answer=None,
            status=AnswerStatus.NOT_FOUND,
            confidence=AnswerConfidence.LOW,
            reasoning="The document does not address stock option treatment.",
            missing_information=[
                "vesting schedule",
                "post-termination exercise period",
            ],
        )
        assert answer.answer is None
        assert answer.status == AnswerStatus.NOT_FOUND
        assert len(answer.missing_information) == 2

    def test_conflict_status(self):
        answer = LegalAnswer(
            answer=None,
            status=AnswerStatus.CONFLICT,
            confidence=AnswerConfidence.MEDIUM,
            reasoning="Clauses 4.2 and 9.1 appear to conflict on remote work.",
            citations=[
                Citation(document_id="doc-1", page_number=3, quote="Remote work permitted."),
                Citation(document_id="doc-1", page_number=8, quote="Office attendance required M-F."),
            ],
        )
        assert answer.status == AnswerStatus.CONFLICT
        assert len(answer.citations) == 2

    def test_default_empty_lists(self):
        answer = LegalAnswer(
            status=AnswerStatus.NOT_FOUND,
            confidence=AnswerConfidence.LOW,
            reasoning="Not found.",
        )
        assert answer.citations == []
        assert answer.missing_information == []
        assert answer.suggested_questions == []

    def test_invalid_status_rejected(self):
        with pytest.raises(ValidationError):
            LegalAnswer(
                status="FABRICATED",  # type: ignore
                confidence=AnswerConfidence.HIGH,
                reasoning="test",
            )


class TestDocumentUploadResponse:
    def test_valid_response(self):
        resp = DocumentUploadResponse(
            document_id="uuid-1234",
            original_filename="contract.pdf",
            file_size_bytes=50000,
            page_count=10,
            upload_timestamp=datetime.now(timezone.utc),
            processing_status="extracted",
            message="Document uploaded successfully.",
        )
        assert resp.page_count == 10
        assert resp.processing_status == "extracted"
