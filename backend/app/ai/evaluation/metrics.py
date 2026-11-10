import math


def _validate_inputs(
    retrieved_chunk_ids: list[str],
    relevant_chunk_ids: list[str],
    k: int,
):
    if k < 1:
        raise ValueError("k must be at least 1")

    if not isinstance(retrieved_chunk_ids, list):
        raise TypeError("retrieved_chunk_ids must be a list")

    if not isinstance(relevant_chunk_ids, list):
        raise TypeError("relevant_chunk_ids must be a list")

    if not relevant_chunk_ids:
        raise ValueError("relevant_chunk_ids cannot be empty")

    if len(retrieved_chunk_ids) != len(set(retrieved_chunk_ids)):
        raise ValueError("Retrieved chunk IDs must be unique")

    if len(relevant_chunk_ids) != len(set(relevant_chunk_ids)):
        raise ValueError("Relevant chunk IDs must be unique")


def precision_at_k(
    retrieved_chunk_ids: list[str],
    relevant_chunk_ids: list[str],
    k: int = 5,
) -> float:
    """Calculate the proportion of top-K results that are relevant."""

    _validate_inputs(retrieved_chunk_ids, relevant_chunk_ids, k)

    retrieved = retrieved_chunk_ids[:k]
    relevant = set(relevant_chunk_ids)

    if not retrieved:
        return 0.0

    relevant_count = sum(
        1 for chunk_id in retrieved if chunk_id in relevant
    )

    return relevant_count / len(retrieved)


def recall_at_k(
    retrieved_chunk_ids: list[str],
    relevant_chunk_ids: list[str],
    k: int = 5,
) -> float:
    """Calculate the proportion of all relevant chunks found in top K."""

    _validate_inputs(retrieved_chunk_ids, relevant_chunk_ids, k)

    retrieved = set(retrieved_chunk_ids[:k])
    relevant = set(relevant_chunk_ids)

    relevant_found = len(retrieved.intersection(relevant))

    return relevant_found / len(relevant)


def reciprocal_rank(
    retrieved_chunk_ids: list[str],
    relevant_chunk_ids: list[str],
    k: int = 5,
) -> float:
    """Calculate reciprocal rank of the first relevant result within top K."""

    _validate_inputs(retrieved_chunk_ids, relevant_chunk_ids, k)

    relevant = set(relevant_chunk_ids)

    for rank, chunk_id in enumerate(retrieved_chunk_ids[:k], start=1):
        if chunk_id in relevant:
            return 1.0 / rank

    return 0.0


def hit_rate_at_k(
    retrieved_chunk_ids: list[str],
    relevant_chunk_ids: list[str],
    k: int = 5,
) -> float:
    """Return 1 if at least one relevant chunk appears in top K."""

    _validate_inputs(retrieved_chunk_ids, relevant_chunk_ids, k)

    retrieved = set(retrieved_chunk_ids[:k])
    relevant = set(relevant_chunk_ids)

    return float(bool(retrieved.intersection(relevant)))


def ndcg_at_k(
    retrieved_chunk_ids: list[str],
    relevant_chunk_ids: list[str],
    k: int = 5,
) -> float:
    """
    Calculate binary NDCG@K.

    Relevant chunks have gain 1.
    Non-relevant chunks have gain 0.
    """

    _validate_inputs(retrieved_chunk_ids, relevant_chunk_ids, k)

    relevant = set(relevant_chunk_ids)
    retrieved = retrieved_chunk_ids[:k]

    dcg = 0.0

    for rank, chunk_id in enumerate(retrieved, start=1):
        if chunk_id in relevant:
            dcg += 1.0 / math.log2(rank + 1)

    ideal_relevant_count = min(len(relevant), k)

    if ideal_relevant_count == 0:
        return 0.0

    ideal_dcg = sum(
        1.0 / math.log2(rank + 1)
        for rank in range(1, ideal_relevant_count + 1)
    )

    return dcg / ideal_dcg