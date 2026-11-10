import logging

logger = logging.getLogger(__name__)

# Standard RRF constant
RRF_K = 60


def reciprocal_rank_fusion(
    dense_results: list[dict],
    sparse_results: list[dict],
    top_k: int = 5,
    rrf_k: int = RRF_K,
) -> list[dict]:
    """
    Combine dense and sparse search rankings using
    Reciprocal Rank Fusion (RRF).

    Each result must contain either point_id or chunk_id.
    """

    if top_k < 1:
        raise ValueError("top_k must be at least 1")

    if rrf_k < 1:
        raise ValueError("rrf_k must be at least 1")

    fused_results = {}

    def get_result_key(result):
        key = result.get("point_id") or result.get("chunk_id")

        if key is None:
            raise ValueError(
                "Search result must contain point_id or chunk_id"
            )

        return str(key)

    def add_results(results, search_type):
        for rank, result in enumerate(results, start=1):
            key = get_result_key(result)

            if key not in fused_results:
                fused_results[key] = {
                    **result,
                    "rrf_score": 0.0,
                    "dense_rank": None,
                    "sparse_rank": None,
                    "dense_score": None,
                    "sparse_score": None,
                }

            fused_results[key]["rrf_score"] += (
                1.0 / (rrf_k + rank)
            )

            if search_type == "dense":
                fused_results[key]["dense_rank"] = rank
                fused_results[key]["dense_score"] = result.get(
                    "similarity_score"
                )

            elif search_type == "sparse":
                fused_results[key]["sparse_rank"] = rank
                fused_results[key]["sparse_score"] = result.get(
                    "sparse_score"
                )

    add_results(dense_results, "dense")
    add_results(sparse_results, "sparse")

    ranked_results = sorted(
        fused_results.values(),
        key=lambda item: item["rrf_score"],
        reverse=True,
    )

    final_results = ranked_results[:top_k]

    logger.info(
        "RRF combined %d dense and %d sparse results into %d unique results",
        len(dense_results),
        len(sparse_results),
        len(ranked_results),
    )

    return final_results