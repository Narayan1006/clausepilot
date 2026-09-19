"""
Analysis & Preparation API Router for Phase 2 & Phase 3.

POST /api/analysis/{document_id}                    (Attention Map & Audit)
GET  /api/analysis/{document_id}/checklist          (Before You Sign Checklist)
GET  /api/analysis/{document_id}/suggested-questions (Counterparty & Legal Counsel Questions)
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse

from app.api.dependencies import get_document_service, get_rag_pipeline
from app.core.logging import get_logger
from app.schemas.analysis_schemas import (
    AnalysisRequest,
    AnalysisResponse,
    ChecklistResponse,
    SuggestedQuestionsResponse,
)
from app.services.document_service import DocumentService
from app.services.rag_pipeline import RagPipeline

logger = get_logger(__name__)
router = APIRouter(prefix="/api/analysis", tags=["analysis"])


@router.post(
    "/{document_id}",
    response_model=AnalysisResponse,
    summary="Trigger document analysis (Attention Map)",
    status_code=status.HTTP_200_OK,
)
async def trigger_analysis(
    document_id: str,
    request: Optional[AnalysisRequest] = None,
    doc_service: DocumentService = Depends(get_document_service),
    rag: RagPipeline = Depends(get_rag_pipeline),
) -> AnalysisResponse:
    doc = doc_service.get_document(document_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document '{document_id}' not found.",
        )

    decision_context = request.decision_context if request else "General Contract Review"

    try:
        analysis_result = rag.analyze_document(
            document_id=document_id,
            decision_context=decision_context,
        )
        return analysis_result
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
        logger.error("Analysis failed for document %s: %s", document_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while generating document analysis.",
        ) from exc


@router.get(
    "/{document_id}/checklist",
    response_model=ChecklistResponse,
    summary="Get 'Before You Sign' checklist (Phase 3)",
    status_code=status.HTTP_200_OK,
)
async def get_checklist(
    document_id: str,
    decision_context: str = Query(default="General Contract Review"),
    doc_service: DocumentService = Depends(get_document_service),
    rag: RagPipeline = Depends(get_rag_pipeline),
) -> ChecklistResponse:
    doc = doc_service.get_document(document_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document '{document_id}' not found.",
        )

    try:
        prep = rag.generate_preparation(document_id=document_id, decision_context=decision_context)
        return ChecklistResponse(
            document_id=document_id,
            decision_context=decision_context,
            items=prep.checklist,
        )
    except ValueError as exc:
        if "GROQ_API_KEY" in str(exc):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Groq AI reasoning service is not configured with an API key.",
            )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except Exception as exc:
        logger.error("Checklist generation failed for %s: %s", document_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while generating signing checklist.",
        ) from exc


@router.get(
    "/{document_id}/suggested-questions",
    response_model=SuggestedQuestionsResponse,
    summary="Get targeted questions for HR / legal professional (Phase 3)",
    status_code=status.HTTP_200_OK,
)
async def get_suggested_questions(
    document_id: str,
    decision_context: str = Query(default="General Contract Review"),
    doc_service: DocumentService = Depends(get_document_service),
    rag: RagPipeline = Depends(get_rag_pipeline),
) -> SuggestedQuestionsResponse:
    doc = doc_service.get_document(document_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document '{document_id}' not found.",
        )

    try:
        prep = rag.generate_preparation(document_id=document_id, decision_context=decision_context)
        return prep
    except ValueError as exc:
        if "GROQ_API_KEY" in str(exc):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Groq AI reasoning service is not configured with an API key.",
            )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except Exception as exc:
        logger.error("Question generation failed for %s: %s", document_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while generating suggested questions.",
        ) from exc
