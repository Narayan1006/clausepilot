"""
Unit tests for security helpers.
Tests: filename sanitization, UUID filename generation, type/size validation.
"""
from __future__ import annotations

import pytest

from app.core.security import (
    generate_server_filename,
    sanitize_original_filename,
    validate_file_size,
    validate_file_type,
)


class TestSanitizeFilename:
    def test_normal_filename(self):
        assert sanitize_original_filename("contract.pdf") == "contract.pdf"

    def test_strips_path_components(self):
        result = sanitize_original_filename("../../etc/passwd")
        assert ".." not in result
        assert "/" not in result

    def test_strips_path_components_windows(self):
        result = sanitize_original_filename(r"C:\Users\attacker\evil.pdf")
        assert "\\" not in result
        assert ":" not in result

    def test_replaces_unsafe_chars(self):
        result = sanitize_original_filename("my<evil>file?.pdf")
        assert "<" not in result
        assert ">" not in result
        assert "?" not in result

    def test_null_byte_removed(self):
        result = sanitize_original_filename("file\x00.pdf")
        assert "\x00" not in result

    def test_long_filename_truncated(self):
        long_name = "a" * 300 + ".pdf"
        result = sanitize_original_filename(long_name)
        assert len(result) <= 255

    def test_empty_filename_fallback(self):
        result = sanitize_original_filename("")
        assert result == "unnamed_document.pdf"

    def test_unicode_filename_preserved(self):
        result = sanitize_original_filename("contrato_año.pdf")
        assert "contrato" in result


class TestGenerateServerFilename:
    def test_returns_uuid_based_name(self):
        name = generate_server_filename("my_contract.pdf")
        assert name.endswith(".pdf")
        # UUID format: 8-4-4-4-12 hex chars separated by hyphens
        uuid_part = name[:-4]
        assert len(uuid_part) == 36

    def test_different_calls_return_different_names(self):
        a = generate_server_filename("contract.pdf")
        b = generate_server_filename("contract.pdf")
        assert a != b

    def test_preserves_extension_lowercase(self):
        name = generate_server_filename("doc.PDF")
        assert name.endswith(".pdf")

    def test_no_original_name_in_result(self):
        original = "very_secret_filename.pdf"
        server = generate_server_filename(original)
        assert "very_secret_filename" not in server


class TestValidateFileType:
    def test_valid_pdf(self):
        validate_file_type("contract.pdf", "application/pdf")  # Should not raise

    def test_invalid_extension(self):
        with pytest.raises(ValueError, match="Unsupported file type"):
            validate_file_type("contract.docx", "application/pdf")

    def test_invalid_mime(self):
        with pytest.raises(ValueError, match="Unsupported MIME type"):
            validate_file_type("contract.pdf", "text/plain")

    def test_case_insensitive_extension(self):
        validate_file_type("contract.PDF", "application/pdf")  # Should not raise

    def test_path_traversal_in_filename(self):
        # Extension check catches the .php; this tests defense in depth
        with pytest.raises(ValueError):
            validate_file_type("../../evil.php", "application/pdf")


class TestValidateFileSize:
    def test_within_limit(self):
        validate_file_size(1024 * 1024, 20 * 1024 * 1024)  # 1 MB < 20 MB

    def test_at_limit(self):
        validate_file_size(20 * 1024 * 1024, 20 * 1024 * 1024)  # Exactly at limit

    def test_exceeds_limit(self):
        with pytest.raises(ValueError, match="exceeds the maximum"):
            validate_file_size(21 * 1024 * 1024, 20 * 1024 * 1024)

    def test_zero_size(self):
        validate_file_size(0, 20 * 1024 * 1024)  # Should not raise
