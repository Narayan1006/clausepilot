"""
Central RAG Orchestration Pipeline for Phase 2.

Connects Document Ingestion → Chunking → ChromaDB Embedding → Retrieval → LLM Reasoning → Citation Verification.
"""
from __future__ import annotations

from typing import List, Optional

from app.core.config import get_settings
from app.core.logging import get_logger
from app.schemas.analysis_schemas import AnalysisResponse
from app.schemas.answer_schemas import AnswerConfidence, AnswerStatus, LegalAnswer
from app.services.chunking_service import ChunkingService
from app.services.evidence_service import EvidenceService
from app.services.extraction_service import DocumentPage
from app.services.llm_service import LLMService
from app.services.retrieval_service import RetrievalService
from app.services.vector_store_service import VectorStoreService, get_vector_store_service
from app.utils.db import get_connection

logger = get_logger(__name__)


class RagPipeline:
    """Orchestrates indexing, retrieval, and evidence-grounded reasoning."""

    def __init__(
        self,
        chunking_service: Optional[ChunkingService] = None,
        vector_store_service: Optional[VectorStoreService] = None,
        retrieval_service: Optional[RetrievalService] = None,
        llm_service: Optional[LLMService] = None,
        evidence_service: Optional[EvidenceService] = None,
    ) -> None:
        self.chunking = chunking_service or ChunkingService()
        self.vector_store = vector_store_service or get_vector_store_service()
        self.retrieval = retrieval_service or RetrievalService(vector_store=self.vector_store)
        self.llm = llm_service or LLMService()
        self.evidence = evidence_service or EvidenceService()

    def index_document(
        self,
        document_id: str,
        pages: List[DocumentPage],
    ) -> int:
        """
        Executes semantic indexing:
        1. Breaks pages into overlapping sentence-aware chunks.
        2. Persists chunks into SQLite.
        3. Generates vector embeddings and stores in ChromaDB.
        4. Updates document status to 'INDEXED'.
        """
        if not pages:
            logger.warning("No pages provided for document %s indexing", document_id)
            return 0

        # Update status to INDEXING
        self._update_status(document_id, "INDEXING")

        try:
            # 1. Chunk pages
            chunks = self.chunking.chunk_pages(document_id, pages)

            # 2. Store chunks in SQLite
            with get_connection() as conn:
                conn.executemany(
                    """
                    INSERT OR REPLACE INTO chunks (id, document_id, page_number, chunk_index, text)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    [(c.chunk_id, c.document_id, c.page_number, c.chunk_index, c.text) for c in chunks],
                )

            # 3. Store vectors in ChromaDB
            self.vector_store.add_chunks(document_id, chunks)

            # 4. Update status to INDEXED
            self._update_status(document_id, "INDEXED")
            logger.info("Document %s indexed successfully (%d chunks)", document_id, len(chunks))
            return len(chunks)
        except Exception as exc:
            self._update_status(document_id, "FAILED", error_message=str(exc))
            logger.error("Failed to index document %s: %s", document_id, exc)
            raise

    def answer_question(
        self,
        document_id: str,
        question: str,
        decision_context: Optional[str] = None,
    ) -> LegalAnswer:
        """
        Full Evidence Pipeline:
        1. Retrieve top matching chunks from ChromaDB.
        2. Apply minimum relevance score filter.
        3. If no evidence exceeds threshold, return NOT_FOUND directly.
        4. Pass evidence to Groq for structured legal answer.
        5. Validate citations deterministically against retrieved chunks.
        """
        # 1. Retrieve
        retrieved_chunks = self.retrieval.retrieve(
            document_id=document_id,
            query=question,
            top_k=5,
            decision_context=decision_context,
        )

        # 2 & 3. Threshold check
        if not retrieved_chunks:
            return LegalAnswer(
                answer=None,
                status=AnswerStatus.NOT_FOUND,
                confidence=AnswerConfidence.LOW,
                citations=[],
                reasoning="The document does not contain relevant clauses or sufficient evidence addressing this question.",
                missing_information=[f"Specific terms regarding '{question}'"],
                suggested_questions=[
                    f"What specific provisions govern {question}?",
                    "Are there supplementary policies or attachments addressing this topic?",
                ],
            )

        # 4. Generate answer via LLM
        raw_answer = self.llm.generate_legal_answer(
            document_id=document_id,
            question=question,
            evidence=retrieved_chunks,
            decision_context=decision_context,
        )

        # 5. Deterministic evidence validation
        validated_answer = self.evidence.validate_answer(
            document_id=document_id,
            answer=raw_answer,
            evidence_chunks=retrieved_chunks,
        )

        return validated_answer

    def analyze_document(
        self,
        document_id: str,
        decision_context: Optional[str] = None,
    ) -> AnalysisResponse:
        """Assembles all document text and performs comprehensive analysis."""
        with get_connection() as conn:
            rows = conn.execute(
                "SELECT page_number, text FROM document_pages WHERE document_id = ? ORDER BY page_number ASC",
                (document_id,),
            ).fetchall()

        if not rows:
            raise ValueError(f"No pages found for document {document_id}")

        full_text = "\n\n".join([f"--- Page {r['page_number']} ---\n{r['text']}" for r in rows])
        return self.llm.analyze_document_text(
            document_id=document_id,
            document_text=full_text,
            decision_context=decision_context,
        )

    def generate_preparation(
        self,
        document_id: str,
        decision_context: Optional[str] = None,
    ):
        """Generates targeted counterparty/lawyer questions and signing checklist."""
        with get_connection() as conn:
            rows = conn.execute(
                "SELECT page_number, text FROM document_pages WHERE document_id = ? ORDER BY page_number ASC",
                (document_id,),
            ).fetchall()

        if not rows:
            raise ValueError(f"No pages found for document {document_id}")

        full_text = "\n\n".join([f"--- Page {r['page_number']} ---\n{r['text']}" for r in rows])
        return self.llm.generate_questions_and_checklist(
            document_id=document_id,
            document_text=full_text,
            attention_summary=f"Decision context: {decision_context}",
            decision_context=decision_context,
        )

    def compare_documents(
        self,
        document_id_a: str,
        document_id_b: str,
        focus: Optional[str] = None,
    ) -> ComparisonResponse:
        """
        Compares two documents at the clause and section level.
        Hardened for long documents:
        1. Checks total text length against comparison_max_context_chars.
        2. If within limits, uses full page text preserving complete clause context.
        3. If long document, uses focused semantic retrieval across both ChromaDB indices.
        4. Invokes LLM reasoning with prompt injection boundaries.
        5. Validates citations deterministically using EvidenceService.
        """
        settings = get_settings()
        with get_connection() as conn:
            rows_a = conn.execute(
                "SELECT page_number, text FROM document_pages WHERE document_id = ? ORDER BY page_number ASC",
                (document_id_a,),
            ).fetchall()
            rows_b = conn.execute(
                "SELECT page_number, text FROM document_pages WHERE document_id = ? ORDER BY page_number ASC",
                (document_id_b,),
            ).fetchall()

        if not rows_a:
            raise ValueError(f"No pages found for document A ({document_id_a})")
        if not rows_b:
            raise ValueError(f"No pages found for document B ({document_id_b})")

        text_a_full = "\n\n".join([f"--- Page {r['page_number']} ---\n{r['text']}" for r in rows_a])
        text_b_full = "\n\n".join([f"--- Page {r['page_number']} ---\n{r['text']}" for r in rows_b])

        # Prepare evidence representations for deterministic verification
        from app.services.retrieval_service import RetrievedChunk
        evidence_chunks_a: List[RetrievedChunk] = []
        evidence_chunks_b: List[RetrievedChunk] = []

        total_length = len(text_a_full) + len(text_b_full)
        if total_length <= settings.comparison_max_context_chars:
            # Document fits in configured bounded context window
            text_a = text_a_full
            text_b = text_b_full

            for r in rows_a:
                evidence_chunks_a.append(
                    RetrievedChunk(
                        chunk_id=f"{document_id_a}_p{r['page_number']}",
                        document_id=document_id_a,
                        page_number=r["page_number"],
                        text=r["text"],
                        relevance_score=1.0,
                    )
                )
            for r in rows_b:
                evidence_chunks_b.append(
                    RetrievedChunk(
                        chunk_id=f"{document_id_b}_p{r['page_number']}",
                        document_id=document_id_b,
                        page_number=r["page_number"],
                        text=r["text"],
                        relevance_score=1.0,
                    )
                )
        else:
            # Long document: bounded semantic retrieval for each document
            logger.info(
                "Long documents detected (%d chars > %d max). Using semantic retrieval for comparison.",
                total_length,
                settings.comparison_max_context_chars,
            )
            query_focus = focus or "Key legal terms, obligations, notice period, non-compete, compensation, termination, liabilities"
            retrieved_a = self.retrieval.retrieve(
                document_id=document_id_a,
                query=query_focus,
                top_k=settings.comparison_top_k,
                decision_context=focus,
            )
            retrieved_b = self.retrieval.retrieve(
                document_id=document_id_b,
                query=query_focus,
                top_k=settings.comparison_top_k,
                decision_context=focus,
            )

            # Fallback to initial pages if retrieval returned nothing
            if not retrieved_a:
                retrieved_a = [
                    RetrievedChunk(
                        chunk_id=f"{document_id_a}_p{r['page_number']}",
                        document_id=document_id_a,
                        page_number=r["page_number"],
                        text=r["text"],
                        relevance_score=0.5,
                    )
                    for r in rows_a[:3]
                ]
            if not retrieved_b:
                retrieved_b = [
                    RetrievedChunk(
                        chunk_id=f"{document_id_b}_p{r['page_number']}",
                        document_id=document_id_b,
                        page_number=r["page_number"],
                        text=r["text"],
                        relevance_score=0.5,
                    )
                    for r in rows_b[:3]
                ]

            evidence_chunks_a = retrieved_a
            evidence_chunks_b = retrieved_b

            text_a = "\n\n".join([f"--- Page {c.page_number} ---\n{c.text}" for c in retrieved_a])
            text_b = "\n\n".join([f"--- Page {c.page_number} ---\n{c.text}" for c in retrieved_b])

        # Generate comparison with LLM
        raw_comparison = self.llm.compare_documents_text(
            doc_id_a=document_id_a,
            text_a=text_a,
            doc_id_b=document_id_b,
            text_b=text_b,
            focus=focus,
        )

        # Deterministic citation validation
        validated_comparison = self.evidence.validate_comparison(
            comparison_response=raw_comparison,
            evidence_chunks_a=evidence_chunks_a,
            evidence_chunks_b=evidence_chunks_b,
        )

        return validated_comparison

    def _update_status(self, document_id: str, status: str, error_message: Optional[str] = None) -> None:
        with get_connection() as conn:
            conn.execute(
                "UPDATE documents SET processing_status = ?, error_message = ? WHERE id = ?",
                (status, error_message, document_id),
            )
