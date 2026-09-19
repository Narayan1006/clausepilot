"""Pydantic schemas for Analysis & Preparation API — Phase 3."""
from __future__ import annotations

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class AttentionLevel(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    MISSING = "MISSING"
    CONFLICT = "CONFLICT"


class AttentionItem(BaseModel):
    category: str
    level: AttentionLevel
    summary: str
    clause_ids: List[str] = Field(default_factory=list)


class AnalysisRequest(BaseModel):
    decision_context: str
    decision_category: Optional[str] = None


class AnalysisResponse(BaseModel):
    document_id: str
    decision_context: str
    processing_status: str
    attention_items: List[AttentionItem] = Field(default_factory=list)
    obligations: List[str] = Field(default_factory=list)
    risks: List[str] = Field(default_factory=list)
    missing_information: List[str] = Field(default_factory=list)
    possible_conflicts: List[str] = Field(default_factory=list)
    message: str


class ChecklistItem(BaseModel):
    item: str
    priority: str = "MEDIUM"  # HIGH | MEDIUM | LOW
    clause_reference: Optional[str] = None


class ChecklistResponse(BaseModel):
    document_id: str
    decision_context: str
    items: List[ChecklistItem] = Field(default_factory=list)


class SuggestedQuestionsResponse(BaseModel):
    document_id: str
    decision_context: str
    questions_for_counterparty: List[str] = Field(default_factory=list)
    questions_for_legal_professional: List[str] = Field(default_factory=list)
    checklist: List[ChecklistItem] = Field(default_factory=list)
