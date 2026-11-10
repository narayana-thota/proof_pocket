
import logging
import time

from app.ai.llm_client import generate_answer


# Configure logging to display INFO messages.
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s | %(name)s | %(message)s",
)


def test_gemini_answer():

    question = "What is the vehicle registration number?"

    context = """
    [Source 1 | Chunk 11_002]
    The vehicle registration number is UA 07 K 5553.
    """

    # Measure the complete function execution time.
    start_time = time.perf_counter()

    answer = generate_answer(
        question=question,
        context=context,
    )

    total_time = time.perf_counter() - start_time

    print("\n========== GEMINI RESPONSE ==========")
    print("Question:", question)
    print("\nAnswer:")
    print(answer)

    print("\n========== PERFORMANCE ==========")
    print(f"Total execution time: {total_time:.3f} seconds")

    assert isinstance(answer, str)
    assert len(answer.strip()) > 0

    print("\nGemini integration successful!")


if __name__ == "__main__":
    test_gemini_answer()
