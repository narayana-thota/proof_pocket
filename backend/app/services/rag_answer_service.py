import logging

from app.ai.rag_pipeline import retrieve_and_build_context
from app.ai.groq_client import generate_answer

logger = logging.getLogger(__name__)

NO_CONTEXT_ANSWER = (
    "I couldn't find relevant information in your uploaded documents "
    "to answer this question. Try asking with a different wording or "
    "selecting the document you want me to search."
)


def generate_rag_answer(
    question: str,
    user_id: int,
    document_id: int | None = None,
) -> dict:
    """
    Retrieve evidence and generate a grounded answer.

    Generic evidence extraction is handled by the answer prompt: it can
    answer field questions (for example, make/model, dates, names, IDs),
    summarize a document, or explain a section without hard-coded
    document-specific regular expressions.
    """
    if not isinstance(question, str) or not question.strip():
        raise ValueError("Question must not be empty.")

    question = question.strip()
    logger.info(
        "Starting RAG answer generation: user_id=%s document_id=%s",
        user_id, document_id,
    )

    retrieval_result = retrieve_and_build_context(
        question=question,
        user_id=user_id,
        document_id=document_id,
    )
    context = retrieval_result.get("context", "")
    sources = retrieval_result.get("sources", [])

    if not isinstance(context, str) or not context.strip():
        logger.warning(
            "No context retrieved: user_id=%s document_id=%s details=%s",
            user_id, document_id, retrieval_result.get("retrieval_details"),
        )
        return {
            "question": question,
            "answer": NO_CONTEXT_ANSWER,
            "sources": [],
            "total_sources": 0,
            "retrieval_details": retrieval_result.get("retrieval_details", {}),
        }

    answer = generate_answer(question=question, context=context)

    logger.info(
        "RAG answer generated: user_id=%s source_count=%d",
        user_id, len(sources),
    )

    return {
        "question": question,
        "answer": answer,
        "sources": sources,
        "total_sources": retrieval_result.get("total_sources", len(sources)),
        "retrieval_details": retrieval_result.get("retrieval_details", {}),
    }

