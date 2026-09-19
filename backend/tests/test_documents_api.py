"""
Integration tests for the Documents API.
Uses FastAPI TestClient with a temporary SQLite database and upload directory.
"""
from __future__ import annotations

import io
import os
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter


def _make_pdf_bytes(pages: list[str]) -> bytes:
    """Create a synthetic multi-page PDF and return as bytes."""
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    for page_text in pages:
        c.setFont("Helvetica", 12)
        y = 750
        for line in page_text.splitlines():
            c.drawString(50, y, line[:100])
            y -= 20
        c.showPage()
    c.save()
    buf.seek(0)
    return buf.read()


@pytest.fixture
def client(tmp_path):
    """
    FastAPI TestClient with isolated temporary database and upload dir.
    Resets environment for each test.
    """
    db_path = str(tmp_path / "test.db")
    upload_dir = str(tmp_path / "uploads")
    Path(upload_dir).mkdir()

    os.environ["DATABASE_PATH"] = db_path
    os.environ["UPLOAD_DIR"] = upload_dir

    # Clear lru_cache so settings reload with test values
    from app.core.config import get_settings
    from app.api.dependencies import get_document_service
    from app.utils.db import init_db

    get_settings.cache_clear()
    get_document_service.cache_clear()

    # Re-initialize DB with fresh settings
    init_db()

    from app.main import create_app
    test_app = create_app()

    with TestClient(test_app, raise_server_exceptions=True) as c:
        yield c


class TestHealthEndpoint:
    def test_health_returns_ok(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["capabilities"]["document_upload"] is True
        assert data["capabilities"]["rag_pipeline"] is True

    def test_root_endpoint(self, client):
        resp = client.get("/")
        assert resp.status_code == 200
        assert "docs" in resp.json()


class TestDocumentUpload:
    def test_upload_valid_pdf(self, client):
        pdf_bytes = _make_pdf_bytes([
            "Employment Agreement\n\nThis Agreement is entered into on January 1, 2025.",
            "Clause 1. Compensation\nBase salary: $120,000 per annum.",
        ])
        resp = client.post(
            "/api/documents/upload",
            files={"file": ("employment-contract.pdf", pdf_bytes, "application/pdf")},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert "document_id" in data
        assert data["page_count"] == 2
        assert data["processing_status"] == "extracted"
        assert data["original_filename"] == "employment-contract.pdf"

    def test_upload_returns_uuid_not_original_filename(self, client, tmp_path):
        """The server_filename (stored on disk) must be a UUID, not the original name."""
        pdf_bytes = _make_pdf_bytes(["Test page"])
        resp = client.post(
            "/api/documents/upload",
            files={"file": ("secret_name.pdf", pdf_bytes, "application/pdf")},
        )
        assert resp.status_code == 201
        doc_id = resp.json()["document_id"]

        # Verify the file on disk is not named after the original file
        upload_dir = Path(os.environ["UPLOAD_DIR"])
        files_on_disk = list(upload_dir.iterdir())
        assert len(files_on_disk) == 1
        assert "secret_name" not in files_on_disk[0].name

    def test_upload_non_pdf_rejected(self, client):
        resp = client.post(
            "/api/documents/upload",
            files={"file": ("document.docx", b"fake docx content", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
        )
        assert resp.status_code == 422

    def test_upload_wrong_mime_rejected(self, client):
        resp = client.post(
            "/api/documents/upload",
            files={"file": ("document.pdf", b"some content", "text/plain")},
        )
        assert resp.status_code == 422

    def test_upload_empty_file_rejected(self, client):
        resp = client.post(
            "/api/documents/upload",
            files={"file": ("empty.pdf", b"", "application/pdf")},
        )
        assert resp.status_code == 400

    def test_upload_invalid_pdf_content(self, client):
        resp = client.post(
            "/api/documents/upload",
            files={"file": ("fake.pdf", b"not a real pdf", "application/pdf")},
        )
        # Should succeed at upload but processing_status should be "error"
        assert resp.status_code == 201
        data = resp.json()
        assert data["processing_status"] == "error"

    def test_malicious_filename_sanitized(self, client):
        pdf_bytes = _make_pdf_bytes(["Content"])
        resp = client.post(
            "/api/documents/upload",
            files={"file": ("../../etc/passwd.pdf", pdf_bytes, "application/pdf")},
        )
        assert resp.status_code == 201
        data = resp.json()
        # Original filename in metadata must not contain path traversal
        assert ".." not in data["original_filename"]
        assert "/" not in data["original_filename"]


class TestDocumentRetrieval:
    def test_get_document_metadata(self, client):
        pdf_bytes = _make_pdf_bytes(["Page one content"])
        upload_resp = client.post(
            "/api/documents/upload",
            files={"file": ("contract.pdf", pdf_bytes, "application/pdf")},
        )
        doc_id = upload_resp.json()["document_id"]

        resp = client.get(f"/api/documents/{doc_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["document_id"] == doc_id
        assert data["page_count"] == 1

    def test_get_nonexistent_document_returns_404(self, client):
        resp = client.get("/api/documents/nonexistent-id-xyz")
        assert resp.status_code == 404

    def test_get_page_content(self, client):
        pdf_bytes = _make_pdf_bytes(["First page text here", "Second page text here"])
        upload_resp = client.post(
            "/api/documents/upload",
            files={"file": ("contract.pdf", pdf_bytes, "application/pdf")},
        )
        doc_id = upload_resp.json()["document_id"]

        resp = client.get(f"/api/documents/{doc_id}/pages/1")
        assert resp.status_code == 200
        data = resp.json()
        assert data["page_number"] == 1
        assert data["document_id"] == doc_id

    def test_get_page_out_of_range_returns_404(self, client):
        pdf_bytes = _make_pdf_bytes(["Only one page"])
        upload_resp = client.post(
            "/api/documents/upload",
            files={"file": ("contract.pdf", pdf_bytes, "application/pdf")},
        )
        doc_id = upload_resp.json()["document_id"]

        resp = client.get(f"/api/documents/{doc_id}/pages/99")
        assert resp.status_code == 404

    def test_get_page_zero_rejected(self, client):
        pdf_bytes = _make_pdf_bytes(["Content"])
        upload_resp = client.post(
            "/api/documents/upload",
            files={"file": ("contract.pdf", pdf_bytes, "application/pdf")},
        )
        doc_id = upload_resp.json()["document_id"]

        resp = client.get(f"/api/documents/{doc_id}/pages/0")
        assert resp.status_code == 422


class TestDocumentDeletion:
    def test_delete_document(self, client):
        pdf_bytes = _make_pdf_bytes(["Delete me"])
        upload_resp = client.post(
            "/api/documents/upload",
            files={"file": ("to_delete.pdf", pdf_bytes, "application/pdf")},
        )
        doc_id = upload_resp.json()["document_id"]

        del_resp = client.delete(f"/api/documents/{doc_id}")
        assert del_resp.status_code == 200
        assert del_resp.json()["deleted"] is True

        # Verify it's gone
        get_resp = client.get(f"/api/documents/{doc_id}")
        assert get_resp.status_code == 404

    def test_delete_nonexistent_returns_404(self, client):
        resp = client.delete("/api/documents/nonexistent-id")
        assert resp.status_code == 404


class TestStubEndpoints:
    def test_comparison_requires_payload(self, client):
        resp = client.post("/api/comparison", json={})
        assert resp.status_code == 422
