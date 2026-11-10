
from app.ai.groq_client import generate_answer


def test_groq():

    question = "What is the vehicle registration number?"

    context = """
[Source 4 | Chunk 11_002]

The extracted insurance document contains:
ua 07 k 5553

This is the vehicle registration mark.
"""

    print("\n========== QUESTION ==========")
    print(question)

    print("\n========== CONTEXT ==========")
    print(context)

    print("\n========== GROQ ANSWER ==========")

    answer = generate_answer(
        question=question,
        context=context,
    )

    print(answer)

    normalized_answer = "".join(
        char for char in answer.upper()
        if char.isalnum()
    )

    expected_number = "UA07K5553"

    assert expected_number in normalized_answer, (
        f"Expected {expected_number}, but received: {answer}"
    )

    print(
        "\nTEST PASSED: Correct vehicle registration number."
    )


if __name__ == "__main__":
    test_groq()
