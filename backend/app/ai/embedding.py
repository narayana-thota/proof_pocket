
import logging
import numpy as np
from sentence_transformers import SentenceTransformer

# Model configuration
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

EMBEDDING_DIMENSION = 384
BATCH_SIZE = 32
DEVICE = "cpu"

logger = logging.getLogger(__name__)

# Load the model once when the module is initialized.
model = SentenceTransformer(
    MODEL_NAME,
    device=DEVICE
)


def generate_batch_embeddings(texts: list[str]) -> np.ndarray:
    """
    Generate embeddings for a batch of text using local MiniLM inference.
    """

    if not isinstance(texts, list):
        raise TypeError("texts must be a list.")

    if not texts:
        return np.empty((0, EMBEDDING_DIMENSION), dtype=np.float32)

    if not all(isinstance(text, str) and text.strip() for text in texts):
        raise ValueError("Every text must be a non-empty string.")

    embeddings = model.encode(
        texts,
        batch_size=BATCH_SIZE,
        convert_to_numpy=True,
        normalize_embeddings=True,
        show_progress_bar=False
    )

    embeddings = np.asarray(embeddings, dtype=np.float32)

    if embeddings.shape != (len(texts), EMBEDDING_DIMENSION):
        raise ValueError(
            f"Unexpected embedding shape: {embeddings.shape}"
        )

    if not np.isfinite(embeddings).all():
        raise ValueError("Embeddings contain invalid numerical values.")

    logger.info(
        "Generated %s embeddings locally. Vector dimension: %s",
        len(texts),
        EMBEDDING_DIMENSION
    )

    return embeddings


def generate_embeddings(texts: list[str]) -> np.ndarray:
    """
    Generate embeddings in batches of 32.
    """

    if not isinstance(texts, list):
        raise TypeError("texts must be a list.")

    if not texts:
        return np.empty((0, EMBEDDING_DIMENSION), dtype=np.float32)

    all_embeddings = []

    total_batches = (len(texts) + BATCH_SIZE - 1) // BATCH_SIZE

    logger.info(
        "Starting local embedding generation. Texts: %s | Batch size: %s | Batches: %s",
        len(texts),
        BATCH_SIZE,
        total_batches
    )

    for start in range(0, len(texts), BATCH_SIZE):
        batch = texts[start:start + BATCH_SIZE]

        batch_number = (start // BATCH_SIZE) + 1

        logger.info(
            "Processing batch %s/%s",
            batch_number,
            total_batches
        )

        batch_embeddings = generate_batch_embeddings(batch)

        all_embeddings.append(batch_embeddings)

    embeddings = np.vstack(all_embeddings)

    if embeddings.shape != (len(texts), EMBEDDING_DIMENSION):
        raise ValueError("Final embedding count or dimension is incorrect.")

    return embeddings


if __name__ == "__main__":

    sample_texts = [
        "This is a document about insurance policies.",
        "This document contains information about insurance coverage.",
        "The weather is sunny today."
    ]

    vectors = generate_embeddings(sample_texts)

    print("\nEMBEDDING RESULTS")
    print("-------------------------")
    print("Number of texts:", len(sample_texts))
    print("Embedding shape:", vectors.shape)
    print("Vector dimension:", vectors.shape[1])

    similarity_1_2 = np.dot(vectors[0], vectors[1])
    similarity_1_3 = np.dot(vectors[0], vectors[2])

    print("Similarity between sentence 1 and 2:", similarity_1_2)
    print("Similarity between sentence 1 and 3:", similarity_1_3)

def generate_query_embedding(query: str) -> list[float]:
    """
    Generate a normalized embedding for a single user question.
    Uses the same model as document embedding generation.
    """

    if not isinstance(query, str) or not query.strip():
        raise ValueError("Query must be a non-empty string.")

    query = query.strip()

    query_vector = generate_batch_embeddings([query])[0]

    return query_vector.tolist()