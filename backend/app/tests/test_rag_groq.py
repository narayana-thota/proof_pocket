
from app.ai.rag_pipeline import retrieve_and_build_context
from app.ai.groq_client import generate_answer


def test_rag_groq():

    question = "What is the vehicle registration number?"

    result = retrieve_and_build_context(
        question=question,
        user_id=2,
        document_id=11,
    )

    context = result["context"]

    print("\n========== ACTUAL RAG CONTEXT ==========")
    print(context)

    print("\n========== CONTEXT VALIDATION ==========")

    print(
        "Registration number present:",
        "ua 07 k 5553" in context.lower()
    )

    print(
        "Chunk 11_002 present:",
        "11_002" in context
    )

    print("\n========== GROQ ANSWER ==========")

    answer = generate_answer(
        question=question,
        context=context,
    )

    print(answer)


if __name__ == "__main__":
    test_rag_groq()
