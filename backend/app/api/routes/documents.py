"""
Documents API Router.

Endpoints:
  POST /api/documents/upload
  GET  /api/documents/{document_id}
  GET  /api/documents/{document_id}/pages/{page_number}
  DELETE /api/documents/{document_id}
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from app.api.dependencies import get_document_service
from app.core.logging import get_logger
from app.core.security import validate_file_size, validate_file_type
from app.schemas.document_schemas import (
    DocumentDeleteResponse,
    DocumentMetadataResponse,
    DocumentPageResponse,
    DocumentUploadResponse,
)
from app.services.document_service import DocumentService

logger = get_logger(__name__)
router = APIRouter(prefix="/api/documents", tags=["documents"])


@router.post(
    "/upload",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a PDF document",
    description=(
        "Validates, saves, and extracts text from an uploaded PDF. "
        "Returns a document ID and page count. "
        "The original filename is stored as metadata only — "
        "server-side UUID filename is used for storage."
    ),
)
async def upload_document(
    file: UploadFile = File(..., description="PDF file to upload"),
    service: DocumentService = Depends(get_document_service),
) -> DocumentUploadResponse:
    # Read file content
    try:
        content = await file.read()
    except Exception as exc:
        logger.error("Failed to read uploaded file: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to read uploaded file.",
        ) from exc

    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty.",
        )

    original_filename = file.filename or "unknown.pdf"
    from starlette.concurrency import run_in_threadpool

    try:
        result = await run_in_threadpool(
            service.upload_document,
            file_content=content,
            original_filename=original_filename,
            content_type=content_type,
        )
    except ValueError as exc:
        # Validation errors (file type, size)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        logger.error("Unexpected error during document upload: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while processing the document.",
        ) from exc

    return result


@router.get(
    "/{document_id}",
    response_model=DocumentMetadataResponse,
    summary="Get document metadata",
)
def get_document(
    document_id: str,
    service: DocumentService = Depends(get_document_service),
) -> DocumentMetadataResponse:
    doc = service.get_document(document_id)
    if doc is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document '{document_id}' not found.",
        )
    return doc


@router.get(
    "/{document_id}/pages/{page_number}",
    response_model=DocumentPageResponse,
    summary="Get page text",
    description="Returns the extracted text for a specific page (1-indexed).",
)
def get_document_page(
    document_id: str,
    page_number: int,
    service: DocumentService = Depends(get_document_service),
) -> DocumentPageResponse:
    if page_number < 1:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Page number must be 1 or greater.",
        )

    # Verify document exists first
    doc = service.get_document(document_id)
    if doc is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document '{document_id}' not found.",
        )

    if page_number > doc.page_count:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"Page {page_number} does not exist. "
                f"Document has {doc.page_count} pages."
            ),
        )

    page = service.get_page(document_id, page_number)
    if page is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Page {page_number} not found in document '{document_id}'.",
        )
    return page


@router.delete(
    "/{document_id}",
    response_model=DocumentDeleteResponse,
    summary="Delete a document",
    description="Deletes the document, all pages, and all associated data.",
)
def delete_document(
    document_id: str,
    service: DocumentService = Depends(get_document_service),
) -> DocumentDeleteResponse:
    result = service.delete_document(document_id)
    if not result.deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document '{document_id}' not found.",
        )
    return result
