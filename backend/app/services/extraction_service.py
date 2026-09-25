"""
PDF text extraction service using PyMuPDF.

CRITICAL: Every extracted page preserves its original page number.
Page numbers are 1-indexed throughout the application.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None

from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class ExtractedPage:
    """A single extracted PDF page with preserved page number."""

    page_number: int  # 1-indexed
    text: str
    character_count: int = field(init=False)

    def __post_init__(self) -> None:
        self.character_count = len(self.text)


# Alias for cross-module compatibility
DocumentPage = ExtractedPage
normalize_text = lambda raw: _normalize_text(raw)


@dataclass
class ExtractionResult:
    """Complete extraction result for a PDF file."""

    pages: List[ExtractedPage]
    page_count: int
    total_characters: int
    has_text: bool

    @property
    def full_text(self) -> str:
        return "\n\n".join(p.text for p in self.pages)


class ExtractionError(Exception):
    """Raised when PDF extraction fails."""


def extract_pdf(file_path: Path) -> ExtractionResult:
    """
    Extract text from a PDF file, preserving page boundaries and numbers.

    Args:
        file_path: Path to the PDF file on the server filesystem.

    Returns:
        ExtractionResult with one ExtractedPage per PDF page.

    Raises:
        ExtractionError: on invalid PDF, empty PDF, encrypted PDF, or I/O error.
    """
    if not file_path.exists():
        raise ExtractionError(f"File not found: {file_path.name}")

    if fitz is None:
        raise ExtractionError("PDF extraction engine (PyMuPDF) is not installed on this system.")

    try:
        doc = fitz.open(str(file_path))
    except fitz.FileDataError as exc:
        raise ExtractionError(
            "The uploaded file is not a valid PDF or is corrupted."
        ) from exc
    except Exception as exc:  # pragma: no cover
        raise ExtractionError(f"Failed to open PDF: {exc}") from exc

    try:
        if doc.is_encrypted:
            raise ExtractionError(
                "The uploaded PDF is password-protected. "
                "Please provide an unencrypted copy."
            )

        page_count = len(doc)
        if page_count == 0:
            raise ExtractionError("The uploaded PDF contains no pages.")

        pages: List[ExtractedPage] = []
        for idx in range(page_count):
            page = doc[idx]
            # get_text("text") preserves layout; strip leading/trailing whitespace
            raw = page.get_text("text") or ""
            normalized = _normalize_text(raw)
            pages.append(
                ExtractedPage(
                    page_number=idx + 1,  # convert 0-indexed → 1-indexed
                    text=normalized,
                )
            )

        total_chars = sum(p.character_count for p in pages)
        has_text = total_chars > 0

        if not has_text:
            # Scanned PDF with no extractable text layer
            logger.warning(
                "PDF appears to be scanned (no extractable text): %s",
                file_path.name,
            )

        logger.info(
            "Extracted %d pages, %d total characters from %s",
            page_count,
            total_chars,
            file_path.name,
        )
        return ExtractionResult(
            pages=pages,
            page_count=page_count,
            total_characters=total_chars,
            has_text=has_text,
        )

    finally:
        doc.close()


def _normalize_text(raw: str) -> str:
    """
    Normalize extracted text:
    - Collapse runs of whitespace within lines
    - Preserve paragraph breaks (double newlines)
    - Strip leading/trailing whitespace per page
    """
    import re

    # Collapse multiple spaces/tabs → single space
    text = re.sub(r"[ \t]+", " ", raw)
    # Collapse 3+ newlines → 2 newlines (paragraph break)
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Strip per-line leading/trailing spaces
    lines = [line.strip() for line in text.splitlines()]
    return "\n".join(lines).strip()
