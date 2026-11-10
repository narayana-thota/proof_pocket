
"""
ProofPocket retrieval evaluation dataset.

Ground truth for the motor insurance document.
Document ID: 11
Owner user ID: 2
"""

EVALUATION_DATASET = [
    {
        "question_id": "Q001",
        "user_id": 2,
        "document_id": 11,
        "question": "What is the vehicle registration number?",
        "expected_answer": "UA 07 K 5553",
        "relevant_chunk_ids": ["11_002"],
    },
    {
        "question_id": "Q002",
        "user_id": 2,
        "document_id": 11,
        "question": "What is the policy start date?",
        "expected_answer": "25/05/2023",
        "relevant_chunk_ids": ["11_001"],
    },
    {
        "question_id": "Q003",
        "user_id": 2,
        "document_id": 11,
        "question": "What is the policy end date?",
        "expected_answer": "24/05/2024",
        "relevant_chunk_ids": ["11_001"],
    },
    {
        "question_id": "Q004",
        "user_id": 2,
        "document_id": 11,
        "question": "Which insurance company issued the policy?",
        "expected_answer": "The Oriental Insurance Company Limited",
        "relevant_chunk_ids": ["11_001"],
    },
]


def validate_dataset(dataset: list[dict]) -> None:
    """Validate the structure and required fields of the dataset."""

    if not dataset:
        raise ValueError("Evaluation dataset cannot be empty")

    required_fields = {
        "question_id",
        "user_id",
        "document_id",
        "question",
        "expected_answer",
        "relevant_chunk_ids",
    }

    question_ids = set()

    for item in dataset:
        missing_fields = required_fields - item.keys()

        if missing_fields:
            raise ValueError(
                f"Missing fields in dataset entry: {missing_fields}"
            )

        if item["question_id"] in question_ids:
            raise ValueError(
                f"Duplicate question ID: {item['question_id']}"
            )

        question_ids.add(item["question_id"])

        if not item["question"].strip():
            raise ValueError("Question cannot be empty")

        if not item["expected_answer"].strip():
            raise ValueError("Expected answer cannot be empty")

        if not item["relevant_chunk_ids"]:
            raise ValueError(
                f"No relevant chunks specified for {item['question_id']}"
            )


if __name__ == "__main__":
    validate_dataset(EVALUATION_DATASET)

    print("Evaluation dataset validation successful!")
    print(f"Total evaluation questions: {len(EVALUATION_DATASET)}")

    for item in EVALUATION_DATASET:
        print(
            f"{item['question_id']} | "
            f"{item['question']} | "
            f"Relevant chunks: {item['relevant_chunk_ids']}"
        )
