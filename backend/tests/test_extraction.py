"""
Unit tests for PDF extraction service.
Uses synthetic in-memory PDFs created with reportlab.
"""
from __future__ import annotations

import io
import os
import tempfile
from pathlib import Path

import pytest
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

from app.services.extraction_service import (
    ExtractionError,
    ExtractionResult,
    ExtractedPage,
    extract_pdf,
    _normalize_text,
)


def _make_pdf(pages: list[str]) -> Path:
    """Create a synthetic PDF with given text per page, return temp file path."""
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    for page_text in pages:
        c.setFont("Helvetica", 12)
        # Write text line by line
        y = 750
        for line in page_text.splitlines():
            c.drawString(50, y, line[:100])  # truncate very long lines
            y -= 20
        c.showPage()
    c.save()
    buf.seek(0)

    tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
    tmp.write(buf.read())
    tmp.flush()
    tmp.close()
    return Path(tmp.name)


class TestExtractPdf:
    def test_single_page_extraction(self):
        path = _make_pdf(["Hello, this is page one of the contract."])
        try:
            result = extract_pdf(path)
            assert result.page_count == 1
            assert len(result.pages) == 1
            assert result.pages[0].page_number == 1
            assert "Hello" in result.pages[0].text or result.has_text
        finally:
            path.unlink(missing_ok=True)

    def test_multi_page_preserves_page_numbers(self):
        path = _make_pdf([
            "Page one: Introduction",
            "Page two: Terms and Conditions",
            "Page three: Signatures",
        ])
        try:
            result = extract_pdf(path)
            assert result.page_count == 3
            assert len(result.pages) == 3
            # Page numbers must be 1-indexed
            assert result.pages[0].page_number == 1
            assert result.pages[1].page_number == 2
            assert result.pages[2].page_number == 3
        finally:
            path.unlink(missing_ok=True)

    def test_page_numbers_are_one_indexed(self):
        path = _make_pdf(["Content"])
        try:
            result = extract_pdf(path)
            for page in result.pages:
                assert page.page_number >= 1
        finally:
            path.unlink(missing_ok=True)

    def test_nonexistent_file_raises(self):
        with pytest.raises(ExtractionError, match="File not found"):
            extract_pdf(Path("/nonexistent/path/document.pdf"))

    def test_invalid_pdf_raises(self):
        tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
        tmp.write(b"This is not a valid PDF file content")
        tmp.close()
        try:
            with pytest.raises(ExtractionError):
                extract_pdf(Path(tmp.name))
        finally:
            Path(tmp.name).unlink(missing_ok=True)

    def test_has_text_flag(self):
        path = _make_pdf(["Some text content on this page"])
        try:
            result = extract_pdf(path)
            assert isinstance(result.has_text, bool)
        finally:
            path.unlink(missing_ok=True)

    def test_extraction_result_fields(self):
        path = _make_pdf(["Test content"])
        try:
            result = extract_pdf(path)
            assert isinstance(result, ExtractionResult)
            assert result.page_count > 0
            assert isinstance(result.total_characters, int)
            assert isinstance(result.pages, list)
            assert all(isinstance(p, ExtractedPage) for p in result.pages)
        finally:
            path.unlink(missing_ok=True)

    def test_character_count_on_page(self):
        path = _make_pdf(["Short text"])
        try:
            result = extract_pdf(path)
            for page in result.pages:
                assert page.character_count == len(page.text)
        finally:
            path.unlink(missing_ok=True)


class TestNormalizeText:
    def test_collapses_multiple_spaces(self):
        result = _normalize_text("hello    world")
        assert "  " not in result

    def test_preserves_paragraph_break(self):
        result = _normalize_text("paragraph one\n\nparagraph two")
        assert "\n\n" in result

    def test_collapses_triple_newlines(self):
        result = _normalize_text("a\n\n\n\nb")
        assert "\n\n\n" not in result

    def test_strips_leading_trailing_whitespace(self):
        result = _normalize_text("   hello   ")
        assert result == "hello"

    def test_empty_string(self):
        result = _normalize_text("")
        assert result == ""
