"""
Document orchestration service.
Handles the full upload pipeline for Phase 1:
  validate → save → extract → persist metadata + pages → ready
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from app.core.logging import get_logger
from app.core.security import (
    generate_server_filename,
    sanitize_original_filename,
    validate_file_size,
    validate_file_type,
)
from app.schemas.document_schemas import (
    DocumentDeleteResponse,
    DocumentMetadataResponse,
    DocumentPageResponse,
    DocumentUploadResponse,
)
from app.services.extraction_service import ExtractionError, extract_pdf
from app.utils.db import get_connection
from app.utils.file_utils import delete_document_file, get_document_path, get_upload_dir

logger = get_logger(__name__)


class DocumentService:
    """Orchestrates document upload, extraction, and retrieval."""

    def __init__(self, max_upload_size_bytes: int) -> None:
        self._max_size = max_upload_size_bytes

    # ─────────────────────────────────────────────
    # Upload
    # ─────────────────────────────────────────────

    def upload_document(
        self,
        file_content: bytes,
        original_filename: str,
        content_type: str,
    ) -> DocumentUploadResponse:
        """
        Full upload pipeline:
        1. Validate file type and size
        2. Generate UUID-based server filename
        3. Write file to disk
        4. Extract text (PyMuPDF)
        5. Persist document metadata + pages to SQLite
        6. Return response
        """
        # Step 1 — Validate
        validate_file_type(original_filename, content_type)
        validate_file_size(len(file_content), self._max_size)

        # Step 2 — Generate safe filenames
        safe_original = sanitize_original_filename(original_filename)
        server_filename = generate_server_filename(original_filename)
        document_id = str(uuid.uuid4())
        upload_ts = datetime.now(timezone.utc)

        # Step 3 — Write to disk
        upload_dir = get_upload_dir()
        dest_path = upload_dir / server_filename
        dest_path.write_bytes(file_content)
        logger.info("Saved upload: %s → %s", safe_original, server_filename)

        # Step 4 — Extract
        processing_status = "extracted"
        error_message: Optional[str] = None
        page_count = 0
        extracted_pages = []

        try:
            result = extract_pdf(dest_path)
            page_count = result.page_count
            extracted_pages = result.pages

            if not result.has_text:
                processing_status = "extracted_no_text"
                error_message = (
                    "PDF appears to be a scanned image with no extractable text. "
                    "OCR is not yet supported."
                )
        except ExtractionError as exc:
            processing_status = "error"
            error_message = str(exc)
            logger.error("Extraction failed for %s: %s", server_filename, exc)

        # Step 5 — Persist
        self._persist_document(
            document_id=document_id,
            original_filename=safe_original,
            server_filename=server_filename,
            file_size_bytes=len(file_content),
            page_count=page_count,
            upload_ts=upload_ts,
            processing_status=processing_status,
            error_message=error_message,
        )

        if extracted_pages:
            self._persist_pages(document_id, extracted_pages)

        return DocumentUploadResponse(
            document_id=document_id,
            original_filename=safe_original,
            file_size_bytes=len(file_content),
            page_count=page_count,
            upload_timestamp=upload_ts,
            processing_status=processing_status,
            message=(
                error_message
                or f"Document uploaded and extracted successfully. {page_count} pages processed."
            ),
        )

    # ─────────────────────────────────────────────
    # Read
    # ─────────────────────────────────────────────

    def get_document(self, document_id: str) -> Optional[DocumentMetadataResponse]:
        with get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM documents WHERE id = ?", (document_id,)
            ).fetchone()
        if row is None:
            return None
        return DocumentMetadataResponse(
            document_id=row["id"],
            original_filename=row["original_filename"],
            file_size_bytes=row["file_size_bytes"],
            page_count=row["page_count"],
            upload_timestamp=datetime.fromisoformat(row["upload_timestamp"]),
            processing_status=row["processing_status"],
            error_message=row["error_message"],
        )

    def get_page(self, document_id: str, page_number: int) -> Optional[DocumentPageResponse]:
        with get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM document_pages WHERE document_id = ? AND page_number = ?",
                (document_id, page_number),
            ).fetchone()
        if row is None:
            return None
        text = row["text"]
        return DocumentPageResponse(
            document_id=document_id,
            page_number=page_number,
            text=text,
            character_count=len(text),
        )

    def get_all_pages(self, document_id: str) -> List[DocumentPageResponse]:
        """Fetch all pages for a document in a single batched query to eliminate N+1 roundtrips."""
        with get_connection() as conn:
            rows = conn.execute(
                "SELECT document_id, page_number, text FROM document_pages WHERE document_id = ? ORDER BY page_number ASC",
                (document_id,),
            ).fetchall()
        return [
            DocumentPageResponse(
                document_id=row["document_id"],
                page_number=row["page_number"],
                text=row["text"],
                character_count=len(row["text"] or ""),
            )
            for row in rows
        ]

    # ─────────────────────────────────────────────
    # Delete
    # ─────────────────────────────────────────────

    def delete_document(self, document_id: str) -> DocumentDeleteResponse:
        with get_connection() as conn:
            row = conn.execute(
                "SELECT server_filename FROM documents WHERE id = ?",
                (document_id,),
            ).fetchone()

        if row is None:
            return DocumentDeleteResponse(
                document_id=document_id,
                deleted=False,
                message="Document not found.",
            )

        server_filename = row["server_filename"]
        # Delete file from disk
        delete_document_file(server_filename)
        # Delete from database (cascades to pages, chunks, clauses)
        with get_connection() as conn:
            conn.execute("DELETE FROM documents WHERE id = ?", (document_id,))

        logger.info("Deleted document %s", document_id)
        return DocumentDeleteResponse(
            document_id=document_id,
            deleted=True,
            message="Document and all associated data deleted.",
        )

    # ─────────────────────────────────────────────
    # Private helpers
    # ─────────────────────────────────────────────

    def _persist_document(
        self,
        *,
        document_id: str,
        original_filename: str,
        server_filename: str,
        file_size_bytes: int,
        page_count: int,
        upload_ts: datetime,
        processing_status: str,
        error_message: Optional[str],
    ) -> None:
        with get_connection() as conn:
            conn.execute(
                """
                INSERT INTO documents
                    (id, original_filename, server_filename, file_size_bytes,
                     page_count, upload_timestamp, processing_status, error_message)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    document_id,
                    original_filename,
                    server_filename,
                    file_size_bytes,
                    page_count,
                    upload_ts.isoformat(),
                    processing_status,
                    error_message,
                ),
            )

    def _persist_pages(self, document_id: str, pages: list) -> None:
        with get_connection() as conn:
            conn.executemany(
                """
                INSERT OR REPLACE INTO document_pages (document_id, page_number, text)
                VALUES (?, ?, ?)
                """,
                [(document_id, p.page_number, p.text) for p in pages],
            )
