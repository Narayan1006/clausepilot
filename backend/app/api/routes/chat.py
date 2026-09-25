"""
Chat and Evidence Retrieval Router for Phase 2.

POST /api/documents/{document_id}/ask
POST /api/documents/{document_id}/index
POST /api/documents/{document_id}/evidence
"""
from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse

from app.api.dependencies import get_document_service, get_rag_pipeline
from app.core.logging import get_logger
from app.schemas.answer_schemas import ChatRequest, ChatResponse, LegalAnswer
from app.services.document_service import DocumentService
from app.services.rag_pipeline import RagPipeline

logger = get_logger(__name__)
router = APIRouter(prefix="/api/documents", tags=["chat"])


@router.post(
    "/{document_id}/index",
    summary="Index document for semantic search (Phase 2)",
    status_code=status.HTTP_200_OK,
)
def index_document(
    document_id: str,
    doc_service: DocumentService = Depends(get_document_service),
    rag: RagPipeline = Depends(get_rag_pipeline),
) -> JSONResponse:
    """Chunks and creates vector embeddings in ChromaDB for the document."""
    doc = doc_service.get_document(document_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document '{document_id}' not found.",
        )

    # Fetch all pages efficiently in a single query
    all_pages = doc_service.get_all_pages(document_id)
    from app.services.extraction_service import DocumentPage
    pages = [
        DocumentPage(page_number=p.page_number, text=p.text)
        for p in all_pages
        if p.text
    ]

    if not pages:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Document has no extractable text to index.",
        )

    chunk_count = rag.index_document(document_id, pages)
    return JSONResponse(
        content={
            "document_id": document_id,
            "status": "INDEXED",
            "chunks_indexed": chunk_count,
            "message": f"Successfully indexed {chunk_count} chunks.",
        }
    )


@router.post(
    "/{document_id}/ask",
    response_model=LegalAnswer,
    summary="Ask a question about a document (Phase 2)",
    status_code=status.HTTP_200_OK,
)
def ask_question(
    document_id: str,
    request: ChatRequest,
    doc_service: DocumentService = Depends(get_document_service),
    rag: RagPipeline = Depends(get_rag_pipeline),
) -> LegalAnswer:
    """
    RAG-grounded question answering:
    Retrieves evidence → Filters by threshold → Queries Groq → Validates Citations.
    """
    doc = doc_service.get_document(document_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document '{document_id}' not found.",
        )

    try:
        answer = rag.answer_question(
            document_id=document_id,
            question=request.question,
            decision_context=request.decision_context,
        )
        return answer
    except ValueError as exc:
        if "GROQ_API_KEY" in str(exc):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Groq AI reasoning service is not configured with an API key.",
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
    except Exception as exc:
        logger.error("Error answering question for %s: %s", document_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while generating grounded legal information.",
        ) from exc


@router.post(
    "/{document_id}/evidence",
    summary="Retrieve raw evidence chunks for inspection",
    status_code=status.HTTP_200_OK,
)
def get_evidence(
    document_id: str,
    request: ChatRequest,
    doc_service: DocumentService = Depends(get_document_service),
    rag: RagPipeline = Depends(get_rag_pipeline),
) -> JSONResponse:
    doc = doc_service.get_document(document_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document '{document_id}' not found.",
        )

    chunks = rag.retrieval.retrieve(
        document_id=document_id,
        query=request.question,
        decision_context=request.decision_context,
    )
    return JSONResponse(
        content={
            "document_id": document_id,
            "query": request.question,
            "evidence_count": len(chunks),
            "evidence": [
                {
                    "chunk_id": c.chunk_id,
                    "page_number": c.page_number,
                    "relevance_score": round(c.relevance_score, 3),
                    "text": c.text,
                }
                for c in chunks
            ],
        }
    )
