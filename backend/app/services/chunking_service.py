"""
Chunking service for Phase 2.

Takes DocumentPage objects and produces text Chunks preserving:
- chunk_id (deterministic or uuid)
- document_id
- page_number
- chunk_index
- text (normalized)
- character/token boundaries
"""
from __future__ import annotations

import re
import uuid
from dataclasses import dataclass
from typing import List, Sequence

from app.core.logging import get_logger
from app.services.extraction_service import DocumentPage, normalize_text

logger = get_logger(__name__)


@dataclass
class Chunk:
    chunk_id: str
    document_id: str
    page_number: int
    chunk_index: int
    text: str
    char_count: int


class ChunkingService:
    """
    Intelligent page-aware text chunking.
    Preserves page boundaries and splits on paragraphs/sentences.
    """

    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 150,
        min_chunk_size: int = 50,
    ) -> None:
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.min_chunk_size = min_chunk_size

    def chunk_pages(
        self,
        document_id: str,
        pages: Sequence[DocumentPage],
    ) -> List[Chunk]:
        """
        Chunks pages into manageable text pieces.
        Preserves original 1-indexed page numbers.
        """
        chunks: List[Chunk] = []
        global_chunk_idx = 0

        for page in pages:
            page_text = normalize_text(page.text)
            if not page_text or len(page_text.strip()) == 0:
                continue

            page_chunks = self._chunk_single_page(
                document_id=document_id,
                page_number=page.page_number,
                text=page_text,
                start_index=global_chunk_idx,
            )
            chunks.extend(page_chunks)
            global_chunk_idx += len(page_chunks)

        logger.info(
            "Chunked document %s into %d chunks across %d pages",
            document_id,
            len(chunks),
            len(pages),
        )
        return chunks

    def _chunk_single_page(
        self,
        document_id: str,
        page_number: int,
        text: str,
        start_index: int,
    ) -> List[Chunk]:
        """Splits a single page's text into overlapping chunks along paragraph/sentence lines."""
        if len(text) <= self.chunk_size:
            return [
                Chunk(
                    chunk_id=f"{document_id}_p{page_number}_c0",
                    document_id=document_id,
                    page_number=page_number,
                    chunk_index=start_index,
                    text=text,
                    char_count=len(text),
                )
            ]

        # Break text by double newlines or paragraph breaks first
        paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
        chunks: List[Chunk] = []
        current_text = ""
        chunk_local_idx = 0

        for p in paragraphs:
            # If the paragraph itself exceeds chunk_size, split by sentences first
            if len(p) > self.chunk_size:
                if current_text and len(current_text) >= self.min_chunk_size:
                    chunks.append(
                        Chunk(
                            chunk_id=f"{document_id}_p{page_number}_c{chunk_local_idx}",
                            document_id=document_id,
                            page_number=page_number,
                            chunk_index=start_index + len(chunks),
                            text=current_text,
                            char_count=len(current_text),
                        )
                    )
                    chunk_local_idx += 1
                    current_text = ""
                
                sub_chunks = self._split_large_text(p)
                for sc in sub_chunks:
                    chunks.append(
                        Chunk(
                            chunk_id=f"{document_id}_p{page_number}_c{chunk_local_idx}",
                            document_id=document_id,
                            page_number=page_number,
                            chunk_index=start_index + len(chunks),
                            text=sc,
                            char_count=len(sc),
                        )
                    )
                    chunk_local_idx += 1
                continue

            if not current_text:
                current_text = p
            elif len(current_text) + len(p) + 2 <= self.chunk_size:
                current_text += "\n\n" + p
            else:
                if len(current_text) >= self.min_chunk_size:
                    chunks.append(
                        Chunk(
                            chunk_id=f"{document_id}_p{page_number}_c{chunk_local_idx}",
                            document_id=document_id,
                            page_number=page_number,
                            chunk_index=start_index + len(chunks),
                            text=current_text,
                            char_count=len(current_text),
                        )
                    )
                    chunk_local_idx += 1
                
                overlap_prefix = ""
                if self.chunk_overlap > 0 and len(current_text) > self.chunk_overlap:
                    overlap_prefix = current_text[-self.chunk_overlap:].strip() + " "
                current_text = overlap_prefix + p

        if current_text and len(current_text.strip()) >= self.min_chunk_size:
            chunks.append(
                Chunk(
                    chunk_id=f"{document_id}_p{page_number}_c{chunk_local_idx}",
                    document_id=document_id,
                    page_number=page_number,
                    chunk_index=start_index + len(chunks),
                    text=current_text,
                    char_count=len(current_text),
                )
            )

        return chunks

    def _split_large_text(self, text: str) -> List[str]:
        """Splits long paragraphs into sentence-aware blocks."""
        sentences = re.split(r"(?<=[.!?])\s+", text)
        results: List[str] = []
        current = ""

        for s in sentences:
            if not current:
                current = s
            elif len(current) + len(s) + 1 <= self.chunk_size:
                current += " " + s
            else:
                if current:
                    results.append(current)
                current = s

        if current:
            results.append(current)

        return results
