import logging
import re
import time
import statistics

from app.ai.llm_client import generate_answer as generate_gemini_answer
from app.ai.groq_client import generate_answer as generate_groq_answer


logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s | %(name)s | %(message)s",
)

QUESTION = "What is the vehicle registration number?"

CONTEXT = """
[Source 1 | Chunk 11_002]
The vehicle registration number is UA 07 K 5553.
"""

EXPECTED_ANSWER = "UA 07 K 5553"
TEST_RUNS = 3

PROVIDERS = {
    "Gemini": generate_gemini_answer,
    "Groq": generate_groq_answer,
}


def normalize(text):
    return re.sub(r"[^A-Z0-9]", "", text.upper())


def benchmark_provider(provider_name, generate_function):
    results = []

    print(f"\n========== {provider_name} BENCHMARK ==========")

    for run in range(1, TEST_RUNS + 1):
        start_time = time.perf_counter()

        try:
            answer = generate_function(
                question=QUESTION,
                context=CONTEXT,
            )

            elapsed = time.perf_counter() - start_time

            if not isinstance(answer, str) or not answer.strip():
                raise ValueError("Empty or invalid answer received.")

            is_correct = normalize(EXPECTED_ANSWER) in normalize(answer)

            results.append({
                "time": elapsed,
                "correct": is_correct,
                "answer": answer,
            })

            print(f"\nRun {run}")
            print(f"Response time: {elapsed:.3f} seconds")
            print(f"Correct answer: {'YES' if is_correct else 'NO'}")
            print(f"Answer: {answer}")

        except Exception as error:
            print(f"\nRun {run} failed: {error}")

    if not results:
        print(f"\n{provider_name}: All runs failed.")
        return None

    times = [result["time"] for result in results]

    return {
        "provider": provider_name,
        "successful_runs": len(results),
        "average_time": statistics.mean(times),
        "median_time": statistics.median(times),
        "accuracy": (
            sum(result["correct"] for result in results)
            / len(results)
        ) * 100,
    }


def main():

    print("\n========== PROOFPOCKET LLM COMPARISON ==========")
    print("Question:", QUESTION)
    print(f"Test runs per provider: {TEST_RUNS}")

    # Alternate provider order across rounds to reduce ordering bias.
    results = []

    for run in range(TEST_RUNS):
        provider_order = (
            ["Gemini", "Groq"]
            if run % 2 == 0
            else ["Groq", "Gemini"]
        )

        for provider_name in provider_order:
            if run == 0:
                result = benchmark_provider(
                    provider_name,
                    PROVIDERS[provider_name],
                )

                if result:
                    results.append(result)

    print("\n========== FINAL COMPARISON ==========")

    for result in results:
        print(f"\nProvider: {result['provider']}")
        print(f"Successful runs: {result['successful_runs']}/{TEST_RUNS}")
        print(f"Average response time: {result['average_time']:.3f} seconds")
        print(f"Median response time: {result['median_time']:.3f} seconds")
        print(f"Answer accuracy: {result['accuracy']:.1f}%")

    print("\nBenchmark completed.")


if __name__ == "__main__":
    main()