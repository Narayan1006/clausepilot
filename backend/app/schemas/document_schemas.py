"""Pydantic schemas for Document API request/response."""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class DocumentUploadResponse(BaseModel):
    """Returned immediately after a successful PDF upload and extraction."""

    document_id: str
    original_filename: str
    file_size_bytes: int
    page_count: int
    upload_timestamp: datetime
    processing_status: str  # "extracted" | "error"
    message: str


class DocumentPageResponse(BaseModel):
    """Text content of a single document page."""

    document_id: str
    page_number: int  # 1-indexed
    text: str
    character_count: int


class DocumentMetadataResponse(BaseModel):
    """Document metadata without page text."""

    document_id: str
    original_filename: str
    file_size_bytes: int
    page_count: int
    upload_timestamp: datetime
    processing_status: str
    error_message: Optional[str] = None


class DocumentListResponse(BaseModel):
    """Paginated list of documents."""

    documents: List[DocumentMetadataResponse]
    total: int


class DocumentDeleteResponse(BaseModel):
    document_id: str
    deleted: bool
    message: str
