"""
Retrieval service for Phase 2.

Retrieves and filters candidate chunks with confidence scores and minimum threshold filtering.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from app.core.config import get_settings
from app.core.logging import get_logger
from app.services.vector_store_service import VectorSearchResult, VectorStoreService, get_vector_store_service

logger = get_logger(__name__)


@dataclass
class RetrievedChunk:
    chunk_id: str
    document_id: str
    page_number: int
    text: str
    relevance_score: float


class RetrievalService:
    """Orchestrates semantic retrieval with score filtering and document isolation."""

    def __init__(
        self,
        vector_store: Optional[VectorStoreService] = None,
        min_retrieval_score: float = 0.25,
    ) -> None:
        self.vector_store = vector_store or get_vector_store_service()
        self.min_retrieval_score = min_retrieval_score

    def retrieve(
        self,
        document_id: str,
        query: str,
        top_k: int = 5,
        decision_context: Optional[str] = None,
    ) -> List[RetrievedChunk]:
        """
        Retrieves top relevant chunks for a specific document.
        Applies minimum relevance threshold.
        """
        # Augment query with decision context if present to improve semantic matching
        effective_query = query
        if decision_context:
            effective_query = f"{query} (Context: {decision_context})"

        results = self.vector_store.query_chunks(
            document_id=document_id,
            query=effective_query,
            top_k=top_k,
        )

        # Filter by threshold
        filtered_chunks: List[RetrievedChunk] = []
        for r in results:
            if r.similarity_score >= self.min_retrieval_score:
                filtered_chunks.append(
                    RetrievedChunk(
                        chunk_id=r.chunk_id,
                        document_id=r.document_id,
                        page_number=r.page_number,
                        text=r.text,
                        relevance_score=r.similarity_score,
                    )
                )

        logger.info(
            "Retrieved %d/%d chunks above threshold %.2f for document %s (query='%s')",
            len(filtered_chunks),
            len(results),
            self.min_retrieval_score,
            document_id,
            query[:50],
        )
        return filtered_chunks
