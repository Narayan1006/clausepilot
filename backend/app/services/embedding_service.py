"""
Embedding service for Phase 2.

Uses sentence-transformers with lazy loading, singleton caching,
and batch generation.
Includes a robust deterministic fallback vectorizer (TF-IDF hashed n-grams)
if local OS application control policies block C/Cython DLLs.
"""
from __future__ import annotations

import hashlib
import math
import re
from typing import List, Optional, Protocol

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class EmbeddingProvider(Protocol):
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        ...

    def embed_query(self, query: str) -> List[float]:
        ...


def _deterministic_hash_vector(text: str, dim: int = 384) -> List[float]:
    """
    Pure Python deterministic embedding generator.
    Creates high-dimensional dense term-frequency vector with cosine normalization.
    Ensures zero external DLL dependencies if OS AppLocker/WDAC blocks Cython BLAS.
    """
    tokens = [w.lower() for w in re.findall(r"\b\w+\b", text)]
    if not tokens:
        return [0.0] * dim

    vec = [0.0] * dim
    for t in tokens:
        # 1-gram
        h = int(hashlib.md5(t.encode("utf-8")).hexdigest(), 16) % dim
        vec[h] += 1.0

    # Bigrams for phrase preservation (e.g. "notice period", "remote work")
    for i in range(len(tokens) - 1):
        bigram = f"{tokens[i]}_{tokens[i+1]}"
        h = int(hashlib.sha256(bigram.encode("utf-8")).hexdigest(), 16) % dim
        vec[h] += 1.5

    # L2 normalize
    norm = math.sqrt(sum(v * v for v in vec))
    if norm > 0:
        vec = [v / norm for v in vec]

    return vec


class SentenceTransformerEmbeddingService:
    """
    Lazy-loading embedding service using sentence-transformers.
    Never downloads or loads models during application startup or import.
    Gracefully falls back to deterministic hash vectors if OS blocks C extensions.
    """

    def __init__(self, model_name: Optional[str] = None) -> None:
        self.model_name = model_name or get_settings().embedding_model
        self._model = None
        self._use_fallback = False
        self._query_cache: dict[str, List[float]] = {}

    def _get_model(self):
        if self._use_fallback:
            return None

        if self._model is None:
            logger.info("Lazy-loading embedding model: %s", self.model_name)
            try:
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer(self.model_name)
            except Exception as exc:
                logger.warning(
                    "Primary embedding model %s unavailable (%s). "
                    "Falling back to built-in pure Python vectorizer.",
                    self.model_name,
                    exc,
                )
                self._use_fallback = True
                return None
        return self._model

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []

        model = self._get_model()
        if model is not None:
            try:
                embeddings = model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
                return embeddings.tolist()
            except Exception as exc:
                logger.warning("Model inference error (%s). Using fallback embeddings.", exc)

        return [_deterministic_hash_vector(t) for t in texts]

    def embed_text(self, text: str) -> List[float]:
        return self.embed_documents([text])[0]

    def embed_query(self, query: str) -> List[float]:
        q_norm = query.strip().lower()
        if q_norm in self._query_cache:
            return self._query_cache[q_norm]
        vec = self.embed_text(query)
        if len(self._query_cache) < 2048:
            self._query_cache[q_norm] = vec
        return vec


_embedding_service_instance: Optional[SentenceTransformerEmbeddingService] = None


def get_embedding_service() -> SentenceTransformerEmbeddingService:
    global _embedding_service_instance
    if _embedding_service_instance is None:
        _embedding_service_instance = SentenceTransformerEmbeddingService()
    return _embedding_service_instance
