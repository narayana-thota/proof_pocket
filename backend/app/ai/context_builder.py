import logging
from typing import Any

logger = logging.getLogger(__name__)

DEFAULT_MAX_CONTEXT_CHARS = 12000


def build_context(
    retrieved_chunks: list[dict[str, Any]],
    max_context_chars: int = DEFAULT_MAX_CONTEXT_CHARS,
) -> dict[str, Any]:
    """
    Build source-labelled context from retrieved chunks.

    Keeps the supplied ranking order, removes duplicate chunk IDs/text,
    and enforces a maximum context size. Each context section includes a
    stable source label that the answer model can cite.
    """
    if not isinstance(retrieved_chunks, list):
        raise ValueError("retrieved_chunks must be a list.")
    if max_context_chars <= 0:
        raise ValueError("max_context_chars must be greater than zero.")

    sections: list[str] = []
    sources: list[dict[str, Any]] = []
    seen_chunk_ids: set[Any] = set()
    seen_texts: set[str] = set()
    total_chars = 0

    for chunk in retrieved_chunks:
        if not isinstance(chunk, dict):
            continue

        raw_text = chunk.get("chunk_text")
        if not isinstance(raw_text, str) or not raw_text.strip():
            continue

        chunk_text = raw_text.strip()
        chunk_id = chunk.get("chunk_id")

        if chunk_id is not None and chunk_id in seen_chunk_ids:
            continue
        if chunk_text in seen_texts:
            continue

        source_number = len(sources) + 1
        source_label = (
            f"[Source {source_number} | "
            f"Chunk {chunk_id if chunk_id is not None else 'Unknown'}]"
        )
        section = f"{source_label}\n{chunk_text}\n"

        # If this section does not fit, skip it and continue checking later
        # chunks; do not silently truncate evidence-bearing text.
        if total_chars + len(section) > max_context_chars:
            logger.debug(
                "Skipping chunk %s because it exceeds remaining context budget.",
                chunk_id,
            )
            continue

        sections.append(section)
        sources.append({
            "source_number": source_number,
            "chunk_id": chunk_id,
            "document_id": chunk.get("document_id"),
            "chunk_index": chunk.get("chunk_index"),
            "source_type": chunk.get("source_type"),
            "retrieval_score": chunk.get("rrf_score"),
            "dense_score": chunk.get("dense_score"),
            "sparse_score": chunk.get("sparse_score"),
            "cross_encoder_score": chunk.get("cross_encoder_score"),
            "rerank_rank": chunk.get("rerank_rank"),
        })

        if chunk_id is not None:
            seen_chunk_ids.add(chunk_id)
        seen_texts.add(chunk_text)
        total_chars += len(section)

    context = "\n".join(sections)
    logger.info(
        "Context constructed: sources=%d characters=%d limit=%d",
        len(sources), len(context), max_context_chars,
    )

    return {
        "context": context,
        "sources": sources,
        "total_sources": len(sources),
        "total_characters": len(context),
        "max_context_chars": max_context_chars,
    }
