
import logging
from statistics import mean

from app.ai.embedding import generate_query_embedding
from app.ai.sparse_embedding import generate_sparse_query_embedding

from app.ai.qdrant_service import (
    search_similar_chunks,
    search_sparse_chunks,
)

from app.ai.hybrid_retrieval import reciprocal_rank_fusion
from app.ai.reranking import rerank_results

from app.ai.evaluation.dataset import (
    EVALUATION_DATASET,
    validate_dataset,
)

from app.ai.evaluation.metrics import (
    precision_at_k,
    recall_at_k,
    reciprocal_rank,
    hit_rate_at_k,
    ndcg_at_k,
)


logger = logging.getLogger(__name__)

# Number of candidates retrieved from each search method.
RETRIEVAL_TOP_K = 20

# Number of final results used to calculate ranking metrics.
EVALUATION_K = 5

# Retrieval strategies being compared.
STRATEGIES = [
    "dense",
    "sparse",
    "hybrid_rrf",
    "hybrid_reranked",
]

METRIC_FUNCTIONS = {
    "precision": precision_at_k,
    "recall": recall_at_k,
    "mrr": reciprocal_rank,
    "hit_rate": hit_rate_at_k,
    "ndcg": ndcg_at_k,
}


def get_chunk_ids(results: list[dict]) -> list[str]:
    """Extract chunk IDs in their retrieval ranking order."""

    chunk_ids = []

    for result in results:
        chunk_id = result.get("chunk_id")

        if chunk_id is None:
            raise ValueError(
                "A retrieval result is missing its chunk_id"
            )

        chunk_ids.append(str(chunk_id))

    return chunk_ids


def retrieve_for_question(
    question: str,
    user_id: int,
    document_id: int,
) -> dict:
    """
    Execute dense, sparse, RRF and cross-encoder retrieval
    for one question.
    """

    # Generate query representations.
    dense_vector = generate_query_embedding(question)
    sparse_vector = generate_sparse_query_embedding(question)

    # 1. Dense retrieval.
    dense_results = search_similar_chunks(
        query_embedding=dense_vector,
        user_id=user_id,
        document_id=document_id,
        top_k=RETRIEVAL_TOP_K,
    )

    # 2. Sparse retrieval.
    sparse_results = search_sparse_chunks(
        query_sparse_embedding=sparse_vector,
        user_id=user_id,
        document_id=document_id,
        top_k=RETRIEVAL_TOP_K,
    )

    # 3. Hybrid retrieval using RRF.
    hybrid_results = reciprocal_rank_fusion(
        dense_results=dense_results,
        sparse_results=sparse_results,
        top_k=RETRIEVAL_TOP_K,
    )

    # 4. Cross-encoder reranking of hybrid candidates.
    reranked_results = rerank_results(
        question=question,
        candidate_results=hybrid_results,
        top_k=RETRIEVAL_TOP_K,
    )

    return {
        "dense": dense_results,
        "sparse": sparse_results,
        "hybrid_rrf": hybrid_results,
        "hybrid_reranked": reranked_results,
    }


def calculate_metrics(
    retrieved_chunk_ids: list[str],
    relevant_chunk_ids: list[str],
) -> dict:
    """Calculate all retrieval metrics for one question."""

    return {
        "precision": precision_at_k(
            retrieved_chunk_ids,
            relevant_chunk_ids,
            k=EVALUATION_K,
        ),
        "recall": recall_at_k(
            retrieved_chunk_ids,
            relevant_chunk_ids,
            k=EVALUATION_K,
        ),
        "mrr": reciprocal_rank(
            retrieved_chunk_ids,
            relevant_chunk_ids,
        ),
        "hit_rate": hit_rate_at_k(
            retrieved_chunk_ids,
            relevant_chunk_ids,
            k=EVALUATION_K,
        ),
        "ndcg": ndcg_at_k(
            retrieved_chunk_ids,
            relevant_chunk_ids,
            k=EVALUATION_K,
        ),
    }


def evaluate_question(item: dict) -> dict:
    """Evaluate all retrieval strategies for one dataset question."""

    question_id = item["question_id"]
    question = item["question"]
    user_id = item["user_id"]
    document_id = item["document_id"]

    relevant_chunk_ids = [
        str(chunk_id)
        for chunk_id in item["relevant_chunk_ids"]
    ]

    logger.info("Evaluating question %s", question_id)

    retrieval_results = retrieve_for_question(
        question=question,
        user_id=user_id,
        document_id=document_id,
    )

    question_report = {
        "question_id": question_id,
        "question": question,
        "expected_answer": item["expected_answer"],
        "relevant_chunk_ids": relevant_chunk_ids,
        "strategies": {},
    }

    for strategy in STRATEGIES:
        retrieved_ids = get_chunk_ids(
            retrieval_results[strategy]
        )

        metrics = calculate_metrics(
            retrieved_chunk_ids=retrieved_ids,
            relevant_chunk_ids=relevant_chunk_ids,
        )

        question_report["strategies"][strategy] = {
            "retrieved_chunk_ids": retrieved_ids,
            "metrics": metrics,
        }

    return question_report


def calculate_average_metrics(
    question_reports: list[dict],
) -> dict:
    """Calculate average metric scores across all questions."""

    if not question_reports:
        raise ValueError("No question reports available")

    averages = {}

    for strategy in STRATEGIES:
        averages[strategy] = {}

        for metric_name in METRIC_FUNCTIONS:
            scores = [
                report["strategies"][strategy]["metrics"][metric_name]
                for report in question_reports
            ]

            averages[strategy][metric_name] = mean(scores)

    return averages


def print_evaluation_report(
    question_reports: list[dict],
    average_metrics: dict,
) -> None:
    """Print per-question results and overall strategy comparison."""

    print("\n" + "=" * 75)
    print("PROOFPOCKET RETRIEVAL EVALUATION REPORT")
    print("=" * 75)

    print(f"Total questions: {len(question_reports)}")
    print(f"Evaluation cutoff: K={EVALUATION_K}")

    for report in question_reports:
        print("\n" + "-" * 75)
        print(f"{report['question_id']}: {report['question']}")
        print(
            "Expected relevant chunks:",
            report["relevant_chunk_ids"],
        )

        for strategy in STRATEGIES:
            strategy_result = report["strategies"][strategy]

            print(f"\n{strategy.upper()}")
            print(
                "Retrieved:",
                strategy_result["retrieved_chunk_ids"][:EVALUATION_K],
            )

            for metric_name, score in strategy_result["metrics"].items():
                print(f"  {metric_name}: {score:.4f}")

    print("\n" + "=" * 75)
    print("OVERALL STRATEGY COMPARISON")
    print("=" * 75)

    metric_names = list(METRIC_FUNCTIONS.keys())

    header = f"{'Strategy':<22}"

    for metric_name in metric_names:
        header += f"{metric_name.upper():>12}"

    print(header)
    print("-" * len(header))

    for strategy in STRATEGIES:
        row = f"{strategy:<22}"

        for metric_name in metric_names:
            score = average_metrics[strategy][metric_name]
            row += f"{score:>12.4f}"

        print(row)

    print("=" * 75)


def run_evaluation() -> dict:
    """Run the complete retrieval evaluation framework."""

    validate_dataset(EVALUATION_DATASET)

    question_reports = []

    for item in EVALUATION_DATASET:
        report = evaluate_question(item)
        question_reports.append(report)

    average_metrics = calculate_average_metrics(
        question_reports
    )

    print_evaluation_report(
        question_reports=question_reports,
        average_metrics=average_metrics,
    )

    return {
        "total_questions": len(question_reports),
        "evaluation_k": EVALUATION_K,
        "question_reports": question_reports,
        "average_metrics": average_metrics,
    }


if __name__ == "__main__":
    run_evaluation()
