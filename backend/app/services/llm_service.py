"""
LLM Reasoning Service for Phase 2 & Phase 3.

Calls Groq API to produce structured, JSON-validated:
- LegalAnswer (grounded chat & citations)
- AnalysisResponse (first-pass Attention Map & Obligations)
- SuggestedQuestionsResponse (Counterparty & Legal Professional questions)
- ChecklistResponse (Before You Sign actionable checklist)
"""
from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional

from app.core.config import get_settings
from app.core.logging import get_logger
from app.prompts.analysis_prompt import ANALYSIS_TASK_TEMPLATE as ANALYSIS_TEMPLATE
from app.prompts.analysis_prompt import SYSTEM_PROMPT as ANALYSIS_SYSTEM_PROMPT
from app.prompts.answer_prompt import ANSWER_TASK_TEMPLATE as ANSWER_TEMPLATE
from app.prompts.answer_prompt import SYSTEM_PROMPT as ANSWER_SYSTEM_PROMPT
from app.prompts.comparison_prompt import (
    COMPARISON_TASK_TEMPLATE,
    SYSTEM_PROMPT as COMPARISON_SYSTEM_PROMPT,
)
from app.prompts.question_generation_prompt import (
    QUESTION_GENERATION_TEMPLATE,
    SYSTEM_PROMPT as QUESTION_SYSTEM_PROMPT,
)
from app.schemas.analysis_schemas import (
    AnalysisResponse,
    AttentionItem,
    AttentionLevel,
    ChecklistItem,
    ChecklistResponse,
    SuggestedQuestionsResponse,
)
from app.schemas.answer_schemas import (
    AnswerConfidence,
    AnswerStatus,
    Citation,
    ComparisonRequest,
    ComparisonResponse,
    ComparisonSection,
    LegalAnswer,
)
from app.services.retrieval_service import RetrievedChunk

logger = get_logger(__name__)


class LLMService:
    """Orchestrates Groq inference for structured legal reasoning."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
    ) -> None:
        self.api_key = api_key or get_settings().groq_api_key
        self.model_name = model_name or get_settings().groq_model
        self._client = None

    def _get_client(self):
        if self._client is None:
            if not self.api_key:
                raise ValueError(
                    "GROQ_API_KEY is not configured. Please set the environment variable."
                )
            from groq import Groq
            self._client = Groq(api_key=self.api_key)
        return self._client

    def format_evidence_block(self, evidence: List[RetrievedChunk]) -> str:
        """Formats evidence chunks with clear page markers and injection defense tags."""
        if not evidence:
            return "No document evidence retrieved."

        lines = []
        for i, chunk in enumerate(evidence, 1):
            lines.append(f"--- Evidence Item {i} [Page {chunk.page_number}] ---")
            lines.append(chunk.text.strip())
            lines.append("")
        return "\n".join(lines)

    def generate_legal_answer(
        self,
        document_id: str,
        question: str,
        evidence: List[RetrievedChunk],
        decision_context: Optional[str] = None,
    ) -> LegalAnswer:
        """Sends formatted evidence to Groq and extracts structured LegalAnswer."""
        if not evidence:
            return LegalAnswer(
                answer=None,
                status=AnswerStatus.NOT_FOUND,
                confidence=AnswerConfidence.LOW,
                citations=[],
                reasoning="No relevant document sections were found matching your question.",
                missing_information=[f"Information regarding '{question}' in this document"],
                suggested_questions=[
                    f"Does the document specify terms for {question}?",
                    "Can you provide an addendum or clarification for this clause?",
                ],
            )

        client = self._get_client()
        evidence_text = self.format_evidence_block(evidence)
        user_prompt = ANSWER_TEMPLATE.format(
            decision_context=decision_context or "General Document Review",
            question=question,
            evidence=evidence_text,
        )

        try:
            chat_completion = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": ANSWER_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                model=self.model_name,
                temperature=0.1,
                response_format={"type": "json_object"},
            )
            raw_content = chat_completion.choices[0].message.content or "{}"
            data = json.loads(raw_content)

            # Ensure correct document_id is always assigned to citations
            citations_raw = data.get("citations", [])
            citations = []
            for c in citations_raw:
                page_raw = c.get("page_number", 1)
                try:
                    page_num = int(re.sub(r"\D", "", str(page_raw)) or "1")
                except Exception:
                    page_num = 1

                citations.append(
                    Citation(
                        document_id=document_id,
                        page_number=page_num,
                        clause_number=str(c.get("clause_number")) if c.get("clause_number") is not None else None,
                        quote=c.get("quote", ""),
                    )
                )

            status_str = data.get("status", "NOT_FOUND").upper()
            if status_str not in AnswerStatus._value2member_map_:
                status_str = "NOT_FOUND"

            conf_str = data.get("confidence", "MEDIUM").upper()
            if conf_str not in AnswerConfidence._value2member_map_:
                conf_str = "MEDIUM"

            return LegalAnswer(
                answer=data.get("answer"),
                status=AnswerStatus(status_str),
                confidence=AnswerConfidence(conf_str),
                citations=citations,
                reasoning=data.get("reasoning", "Derived from document evidence."),
                missing_information=data.get("missing_information", []),
                suggested_questions=data.get("suggested_questions", []),
            )
        except Exception as exc:
            logger.error("LLM reasoning error for document %s: %s", document_id, exc)
            raise

    def analyze_document_text(
        self,
        document_id: str,
        document_text: str,
        decision_context: Optional[str] = None,
    ) -> AnalysisResponse:
        """Runs comprehensive first-pass document audit with categorized attention items."""
        client = self._get_client()
        truncated_text = document_text[:50000]

        user_prompt = ANALYSIS_TEMPLATE.format(
            decision_context=decision_context or "General Contract Review",
            document_text=truncated_text,
        )

        try:
            chat_completion = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": ANALYSIS_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                model=self.model_name,
                temperature=0.1,
                response_format={"type": "json_object"},
            )
            raw_content = chat_completion.choices[0].message.content or "{}"
            data = json.loads(raw_content)

            attention_items = []
            for item in data.get("attention_items", []):
                lvl_str = item.get("level", "MEDIUM").upper()
                if lvl_str not in AttentionLevel._value2member_map_:
                    lvl_str = "MEDIUM"
                attention_items.append(
                    AttentionItem(
                        category=item.get("category", "General"),
                        level=AttentionLevel(lvl_str),
                        summary=item.get("summary", ""),
                        clause_ids=item.get("clause_ids", []),
                    )
                )

            return AnalysisResponse(
                document_id=document_id,
                decision_context=decision_context or "General Contract Review",
                processing_status="completed",
                attention_items=attention_items,
                obligations=data.get("obligations", []),
                risks=data.get("risks", []),
                missing_information=data.get("missing_information", []),
                possible_conflicts=data.get("possible_conflicts", []),
                message="Document analysis completed successfully.",
            )
        except Exception as exc:
            logger.error("Document analysis error for %s: %s", document_id, exc)
            raise

    def generate_questions_and_checklist(
        self,
        document_id: str,
        document_text: str,
        attention_summary: str,
        decision_context: Optional[str] = None,
    ) -> SuggestedQuestionsResponse:
        """Generates targeted questions for HR/landlord/lawyer and an actionable checklist."""
        client = self._get_client()
        truncated_text = document_text[:50000]

        user_prompt = QUESTION_GENERATION_TEMPLATE.format(
            decision_context=decision_context or "General Document Review",
            attention_summary=attention_summary or "None specified",
            evidence=truncated_text,
        )

        try:
            chat_completion = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": QUESTION_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                model=self.model_name,
                temperature=0.1,
                response_format={"type": "json_object"},
            )
            raw_content = chat_completion.choices[0].message.content or "{}"
            data = json.loads(raw_content)

            checklist_items = []
            for item in data.get("checklist", []):
                checklist_items.append(
                    ChecklistItem(
                        item=item.get("item", ""),
                        priority=item.get("priority", "MEDIUM").upper(),
                        clause_reference=item.get("clause_reference"),
                    )
                )

            return SuggestedQuestionsResponse(
                document_id=document_id,
                decision_context=decision_context or "General Document Review",
                questions_for_counterparty=data.get("questions_for_counterparty", []),
                questions_for_legal_professional=data.get("questions_for_legal_professional", []),
                checklist=checklist_items,
            )
        except Exception as exc:
            logger.error("Question & checklist generation error for %s: %s", document_id, exc)
            raise

    def compare_documents_text(
        self,
        doc_id_a: str,
        text_a: str,
        doc_id_b: str,
        text_b: str,
        focus: Optional[str] = None,
    ) -> ComparisonResponse:
        """Compares two contracts clause-by-clause, noting ADDED, REMOVED, CHANGED, and SAME with citations."""
        client = self._get_client()
        trunc_a = text_a[:35000]
        trunc_b = text_b[:35000]

        user_prompt = COMPARISON_TASK_TEMPLATE.format(
            focus=focus or "Comprehensive clause comparison",
            doc_id_a=doc_id_a,
            text_a=trunc_a,
            doc_id_b=doc_id_b,
            text_b=trunc_b,
        )

        try:
            chat_completion = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": COMPARISON_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                model=self.model_name,
                temperature=0.1,
                response_format={"type": "json_object"},
            )
            raw_content = chat_completion.choices[0].message.content or "{}"
            data = json.loads(raw_content)

            sections = []
            for sec in data.get("sections", []):
                diff_type = sec.get("difference_type", "CHANGED").upper()
                if diff_type not in {"ADDED", "REMOVED", "CHANGED", "SAME"}:
                    diff_type = "CHANGED"

                cits_a = []
                for c in sec.get("citations_a", []):
                    cits_a.append(
                        Citation(
                            document_id=doc_id_a,
                            page_number=int(c.get("page_number", 1)),
                            clause_number=str(c.get("clause_number")) if c.get("clause_number") is not None else None,
                            quote=c.get("quote", ""),
                        )
                    )

                cits_b = []
                for c in sec.get("citations_b", []):
                    cits_b.append(
                        Citation(
                            document_id=doc_id_b,
                            page_number=int(c.get("page_number", 1)),
                            clause_number=str(c.get("clause_number")) if c.get("clause_number") is not None else None,
                            quote=c.get("quote", ""),
                        )
                    )

                sections.append(
                    ComparisonSection(
                        topic=sec.get("topic", "General Terms"),
                        document_a_summary=sec.get("document_a_summary"),
                        document_b_summary=sec.get("document_b_summary"),
                        difference_type=diff_type,
                        citations_a=cits_a,
                        citations_b=cits_b,
                    )
                )

            return ComparisonResponse(
                document_id_a=doc_id_a,
                document_id_b=doc_id_b,
                sections=sections,
                overall_summary=data.get("overall_summary", "Comparison completed."),
                message="Documents compared successfully.",
            )
        except Exception as exc:
            logger.error("Comparison error between %s and %s: %s", doc_id_a, doc_id_b, exc)
            raise
