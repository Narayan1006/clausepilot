"""
Comparison API Router — Phase 4.

POST /api/comparison
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from app.core.logging import get_logger
from app.schemas.answer_schemas import ComparisonRequest, ComparisonResponse
from app.services.rag_pipeline import RagPipeline

logger = get_logger(__name__)

router = APIRouter(prefix="/api/comparison", tags=["comparison"])
_pipeline = RagPipeline()


@router.post(
    "",
    summary="Compare two documents (Phase 4)",
    response_model=ComparisonResponse,
    status_code=status.HTTP_200_OK,
)
async def compare_documents(request: ComparisonRequest) -> ComparisonResponse:
    """
    Compares two contracts (e.g. Doc A vs Doc B, or standard vs modified terms)
    and returns a structured comparison by topic with citations and diff classification.
    """
    if request.document_id_a == request.document_id_b:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Document A and Document B cannot be the same document.",
        )

    try:
        return _pipeline.compare_documents(
            document_id_a=request.document_id_a,
            document_id_b=request.document_id_b,
            focus=request.focus,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except Exception as exc:
        logger.error(
            "Comparison failed between %s and %s: %s",
            request.document_id_a,
            request.document_id_b,
            exc,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate document comparison. Please verify API key configuration and document status.",
        )
