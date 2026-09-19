"""
Pydantic schemas for structured LegalAnswer.

Every AI-generated answer MUST conform to this schema.
This is the core evidence model for ClausePilot.
"""
from __future__ import annotations

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class AnswerStatus(str, Enum):
    """
    Grounding status of a legal answer.

    GROUNDED    — The document directly supports the answer.
    INFERRED    — The document provides sufficient context for a reasonable
                  interpretation, but the answer is not explicitly stated.
    NOT_FOUND   — The document does not contain enough information to answer.
    CONFLICT    — Two or more document sections appear inconsistent.
    """

    GROUNDED = "GROUNDED"
    INFERRED = "INFERRED"
    NOT_FOUND = "NOT_FOUND"
    CONFLICT = "CONFLICT"


class AnswerConfidence(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class Citation(BaseModel):
    """A verifiable reference to a specific location in a document."""

    document_id: str
    page_number: int
    clause_number: Optional[str] = None
    quote: str = Field(..., min_length=1, description="Exact verbatim quote from the document")


class LegalAnswer(BaseModel):
    """
    Structured output for every AI-generated answer.

    Rules enforced by the LLM service (Phase 2):
    1. Never invent clauses, pages, or legal facts.
    2. If evidence is insufficient, status MUST be NOT_FOUND.
    3. Citations must contain exact quotes — no paraphrasing.
    4. Conflicts must be flagged, not silently resolved.
    5. This schema is NOT legal advice.
    """

    answer: Optional[str] = Field(
        None,
        description="The answer text, or null when status is NOT_FOUND.",
    )
    status: AnswerStatus
    confidence: AnswerConfidence
    citations: List[Citation] = Field(
        default_factory=list,
        description="Exact document evidence supporting the answer.",
    )
    reasoning: str = Field(
        ...,
        description="Brief explanation of how the answer was derived.",
    )
    missing_information: List[str] = Field(
        default_factory=list,
        description="Information absent from the document that would clarify the answer.",
    )
    suggested_questions: List[str] = Field(
        default_factory=list,
        description="Follow-up questions the user should ask HR or a legal professional.",
    )


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)
    decision_context: Optional[str] = None


class ChatResponse(BaseModel):
    document_id: str
    question: str
    legal_answer: LegalAnswer


class ComparisonRequest(BaseModel):
    document_id_a: str
    document_id_b: str
    focus: Optional[str] = None


class ComparisonSection(BaseModel):
    topic: str
    document_a_summary: Optional[str] = None
    document_b_summary: Optional[str] = None
    difference_type: str  # ADDED | REMOVED | CHANGED | SAME
    citations_a: List[Citation] = []
    citations_b: List[Citation] = []


class ComparisonResponse(BaseModel):
    document_id_a: str
    document_id_b: str
    sections: List[ComparisonSection] = []
    overall_summary: str
    message: str
