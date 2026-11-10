from app.ai.evaluation.metrics import (
    precision_at_k,
    recall_at_k,
    reciprocal_rank,
    hit_rate_at_k,
    ndcg_at_k,
)


def test_retrieval_metrics():

    retrieved = ["11_004", "11_002", "11_005"]
    relevant = ["11_002"]

    precision = precision_at_k(retrieved, relevant, k=3)
    recall = recall_at_k(retrieved, relevant, k=3)
    rr = reciprocal_rank(retrieved, relevant)
    hit_rate = hit_rate_at_k(retrieved, relevant, k=3)
    ndcg = ndcg_at_k(retrieved, relevant, k=3)

    print("\n========== RETRIEVAL METRICS ==========")
    print(f"Precision@3: {precision:.4f}")
    print(f"Recall@3:    {recall:.4f}")
    print(f"Reciprocal Rank: {rr:.4f}")
    print(f"Hit Rate@3:  {hit_rate:.4f}")
    print(f"NDCG@3:      {ndcg:.4f}")

    assert abs(precision - (1 / 3)) < 0.0001
    assert recall == 1.0
    assert rr == 0.5
    assert hit_rate == 1.0
    assert abs(ndcg - 0.6309) < 0.001

    print("\nAll retrieval metric tests passed!")


if __name__ == "__main__":
    test_retrieval_metrics()