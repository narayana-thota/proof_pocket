
import logging
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException

from app.dependencies import get_current_user
from app.schemas.chat import ChatRequest
from app.services.rag_answer_service import generate_rag_answer
from app.services.chat_history_service import (
    save_chat_exchange,
    get_chat_history,
    get_user_conversations,
)


logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/chat",
    tags=["AI Document Assistant"],
)


@router.post("/ask")
def ask_question(
    request: ChatRequest,
    current_user: dict = Depends(get_current_user),
):
    try:
        user_id = current_user["user_id"]

        question = request.question.strip()

        if not question:
            raise HTTPException(
                status_code=400,
                detail="Question cannot be empty.",
            )

        # Reuse an existing conversation or create a new one.
        conversation_id = (
            request.conversation_id or uuid4()
        )

        # Generate the answer using the existing RAG service.
        result = generate_rag_answer(
            question=question,
            user_id=user_id,
            document_id=request.document_id,
        )

        # Persist the question and answer together.
        save_chat_exchange(
            conversation_id=conversation_id,
            user_id=user_id,
            document_id=request.document_id,
            question=question,
            answer=result["answer"],
        )

        return {
            "success": True,
            "conversation_id": str(conversation_id),
            **result,
        }

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )

    except PermissionError as error:
        raise HTTPException(
            status_code=403,
            detail=str(error),
        )

    except HTTPException:
        raise

    except Exception:
        logger.exception("Chat request failed")

        raise HTTPException(
            status_code=500,
            detail="Unable to process chat request. Check backend logs.",
        )


@router.get("/conversations")
def list_conversations(
    current_user: dict = Depends(get_current_user),
):
    try:
        conversations = get_user_conversations(
            user_id=current_user["user_id"]
        )

        return {
            "success": True,
            "conversations": conversations,
        }

    except Exception:
        logger.exception("Failed to retrieve conversations")

        raise HTTPException(
            status_code=500,
            detail="Unable to retrieve conversations.",
        )


@router.get("/history/{conversation_id}")
def retrieve_chat_history(
    conversation_id: UUID,
    current_user: dict = Depends(get_current_user),
):
    try:
        messages = get_chat_history(
            conversation_id=conversation_id,
            user_id=current_user["user_id"],
        )

        if not messages:
            raise HTTPException(
                status_code=404,
                detail="Conversation not found.",
            )

        return {
            "success": True,
            "conversation_id": str(conversation_id),
            "messages": messages,
        }

    except HTTPException:
        raise

    except Exception:
        logger.exception("Failed to retrieve chat history")

        raise HTTPException(
            status_code=500,
            detail="Unable to retrieve chat history.",
        )
