import logging
import math

from sentence_transformers import CrossEncoder

logger = logging.getLogger(__name__)

MODEL_NAME = "cross-encoder/ms-marco-MiniLM-L-6-v2"

DEVICE = "cpu"
MAX_SEQUENCE_LENGTH = 512
BATCH_SIZE = 16

_reranker = None


def get_reranker():
    """
    Load the cross-encoder once and reuse it.
    Model files are cached in the existing Hugging Face Docker volume.
    """
    global _reranker

    if _reranker is None:
        logger.info("Loading cross-encoder model: %s", MODEL_NAME)

        _reranker = CrossEncoder(
            MODEL_NAME,
            max_length=MAX_SEQUENCE_LENGTH,
            device=DEVICE,
        )

        logger.info("Cross-encoder model loaded successfully")

    return _reranker


def rerank_results(
    question: str,
    candidate_results: list[dict],
    top_k: int = 5,
) -> list[dict]:
    """
    Rerank retrieved chunks by evaluating each question/chunk pair.

    The cross-encoder score is a relevance score, not a probability.
    """

    if not isinstance(question, str) or not question.strip():
        raise ValueError("Question must be a non-empty string")

    if top_k < 1:
        raise ValueError("top_k must be at least 1")

    if not candidate_results:
        return []

    sentence_pairs = []

    for result in candidate_results:
        chunk_text = result.get("chunk_text")

        if not isinstance(chunk_text, str) or not chunk_text.strip():
            raise ValueError(
                "Every candidate must contain non-empty chunk_text"
            )

        sentence_pairs.append(
            [question.strip(), chunk_text]
        )

    model = get_reranker()

    scores = model.predict(
        sentence_pairs,
        batch_size=BATCH_SIZE,
        show_progress_bar=False,
        convert_to_numpy=True,
    )

    if len(scores) != len(candidate_results):
        raise RuntimeError(
            "Cross-encoder returned an unexpected number of scores"
        )

    reranked_results = []

    for result, score in zip(candidate_results, scores):
        score = float(score)

        if not math.isfinite(score):
            raise ValueError("Cross-encoder produced a non-finite score")

        reranked_result = {
            **result,
            "cross_encoder_score": score,
        }

        reranked_results.append(reranked_result)

    reranked_results.sort(
        key=lambda item: item["cross_encoder_score"],
        reverse=True,
    )

    final_results = reranked_results[:top_k]

    for rank, result in enumerate(final_results, start=1):
        result["rerank_rank"] = rank

    logger.info(
        "Reranked %d candidates and returned top %d",
        len(candidate_results),
        len(final_results),
    )

    return final_results