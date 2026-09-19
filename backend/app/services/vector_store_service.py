"""
Vector store service for Phase 2.

Integrates ChromaDB for persistent document indexing and similarity search.
Uses lazy loading and document_id metadata filtering for complete multi-tenant isolation.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.core.config import get_settings
from app.core.logging import get_logger
from app.services.chunking_service import Chunk
from app.services.embedding_service import EmbeddingProvider, get_embedding_service

logger = get_logger(__name__)

COLLECTION_NAME = "clausepilot_documents"


@dataclass
class VectorSearchResult:
    chunk_id: str
    document_id: str
    page_number: int
    chunk_index: int
    text: str
    similarity_score: float  # Normalized 0.0 to 1.0


class VectorStoreService:
    """ChromaDB Vector Store wrapper with lazy initialization and document isolation."""

    def __init__(
        self,
        persist_dir: Optional[str] = None,
        embedding_provider: Optional[EmbeddingProvider] = None,
    ) -> None:
        self.persist_dir = persist_dir or get_settings().chroma_persist_dir
        self.embedding_provider = embedding_provider or get_embedding_service()
        self._client = None
        self._collection = None

    def _get_client(self):
        if self._client is None:
            logger.info("Lazy-initializing ChromaDB client at %s", self.persist_dir)
            Path(self.persist_dir).mkdir(parents=True, exist_ok=True)
            import chromadb
            from chromadb.config import Settings as ChromaSettings
            self._client = chromadb.PersistentClient(
                path=self.persist_dir,
                settings=ChromaSettings(anonymized_telemetry=False),
            )
        return self._client

    def _get_collection(self):
        if self._collection is None:
            client = self._get_client()
            self._collection = client.get_or_create_collection(
                name=COLLECTION_NAME,
                metadata={"hnsw:space": "cosine"},
            )
        return self._collection

    def add_chunks(self, document_id: str, chunks: List[Chunk]) -> int:
        """Embeds and indexes document chunks in ChromaDB."""
        if not chunks:
            return 0

        collection = self._get_collection()
        texts = [c.text for c in chunks]
        embeddings = self.embedding_provider.embed_documents(texts)

        ids = [c.chunk_id for c in chunks]
        metadatas = [
            {
                "document_id": c.document_id,
                "page_number": c.page_number,
                "chunk_index": c.chunk_index,
                "char_count": c.char_count,
            }
            for c in chunks
        ]

        collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas,
        )
        logger.info("Indexed %d chunks for document %s in ChromaDB", len(chunks), document_id)
        return len(chunks)

    def query_chunks(
        self,
        document_id: str,
        query: str,
        top_k: int = 5,
    ) -> List[VectorSearchResult]:
        """Queries chunks with mandatory document_id filtering."""
        collection = self._get_collection()
        query_embedding = self.embedding_provider.embed_query(query)

        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where={"document_id": document_id},
            include=["documents", "metadatas", "distances"],
        )

        search_results: List[VectorSearchResult] = []
        if not results or not results["ids"] or len(results["ids"][0]) == 0:
            return search_results

        ids = results["ids"][0]
        docs = results["documents"][0] if results.get("documents") else []
        metas = results["metadatas"][0] if results.get("metadatas") else []
        distances = results["distances"][0] if results.get("distances") else []

        for i in range(len(ids)):
            meta = metas[i] if i < len(metas) else {}
            # Cosine distance to similarity: similarity = 1 - distance (or max(0, 1 - dist))
            dist = distances[i] if i < len(distances) else 1.0
            similarity = max(0.0, min(1.0, 1.0 - dist))

            search_results.append(
                VectorSearchResult(
                    chunk_id=ids[i],
                    document_id=meta.get("document_id", document_id),
                    page_number=meta.get("page_number", 1),
                    chunk_index=meta.get("chunk_index", 0),
                    text=docs[i] if i < len(docs) else "",
                    similarity_score=similarity,
                )
            )

        return search_results

    def delete_document(self, document_id: str) -> None:
        """Deletes all indexed vectors belonging to a document."""
        try:
            collection = self._get_collection()
            collection.delete(where={"document_id": document_id})
            logger.info("Deleted ChromaDB vectors for document %s", document_id)
        except Exception as exc:
            logger.warning("Error deleting vectors for document %s: %s", document_id, exc)


_vector_store_instance: Optional[VectorStoreService] = None


def get_vector_store_service() -> VectorStoreService:
    global _vector_store_instance
    if _vector_store_instance is None:
        _vector_store_instance = VectorStoreService()
    return _vector_store_instance
