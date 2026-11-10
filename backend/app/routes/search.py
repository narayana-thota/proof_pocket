import logging

from fastapi import APIRouter, Depends, HTTPException

from app.dependencies import get_current_user
from app.schemas.search import SemanticSearchRequest
from app.services.semantic_search_service import (
    perform_semantic_search
)


logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/search",
    tags=["Semantic Search"]
)


@router.post("/")
def semantic_search(
    request: SemanticSearchRequest,
    current_user: dict = Depends(get_current_user)
):
    try:
        results = perform_semantic_search(
            question=request.question.strip(),
            user_id=current_user["user_id"],
            top_k=request.top_k,
            document_id=request.document_id
        )

        return {
            "success": True,
            "question": request.question,
            "total_results": len(results),
            "results": results
        }

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    except Exception:
        logger.exception("Semantic search failed")

        raise HTTPException(
            status_code=500,
            detail="Semantic search failed. Check backend logs."
        )