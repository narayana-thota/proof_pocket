
import logging
import numpy as np

from fastembed import SparseTextEmbedding


logger = logging.getLogger(__name__)

MODEL_NAME = "Qdrant/bm25"
CACHE_DIR = "/root/.cache/huggingface/fastembed"
BATCH_SIZE = 64

_sparse_model = None


def get_sparse_model():
    """Load the sparse embedding model once and reuse it."""

    global _sparse_model

    if _sparse_model is None:
        logger.info("Loading sparse embedding model: %s", MODEL_NAME)

        _sparse_model = SparseTextEmbedding(
            model_name=MODEL_NAME,
            cache_dir=CACHE_DIR
        )

    return _sparse_model


def generate_sparse_embeddings(texts: list[str]) -> list[dict]:
    """Generate BM25 sparse vectors for document chunks."""

    if not isinstance(texts, list):
        raise TypeError("Texts must be a list.")

    if not texts:
        return []

    if not all(
        isinstance(text, str) and text.strip()
        for text in texts
    ):
        raise ValueError("All texts must be non-empty strings.")

    model = get_sparse_model()

    embeddings = list(
        model.embed(
            texts,
            batch_size=BATCH_SIZE
        )
    )

    if len(embeddings) != len(texts):
        raise ValueError(
            "Number of sparse embeddings does not match text count."
        )

    results = []

    for embedding in embeddings:
        indices = embedding.indices.tolist()
        values = embedding.values.tolist()

        if len(indices) != len(values) or not indices:
            raise ValueError("Invalid sparse embedding.")

        if not all(type(index) is int and index >= 0 for index in indices):
            raise ValueError("Sparse indices contain invalid values.")

        if not all(
            isinstance(value, (int, float))
            and np.isfinite(value)
            for value in values
        ):
            raise ValueError("Sparse weights contain invalid values.")

        results.append({
            "indices": indices,
            "values": values
        })

    logger.info(
        "Generated sparse embeddings for %s chunks.",
        len(results)
    )

    return results


def generate_sparse_query_embedding(query: str) -> dict:
    """Generate a BM25 sparse vector for a search query."""

    if not isinstance(query, str) or not query.strip():
        raise ValueError("Query cannot be empty.")

    model = get_sparse_model()

    embeddings = list(model.query_embed(query.strip()))

    if not embeddings:
        raise ValueError("Could not generate query sparse embedding.")

    embedding = embeddings[0]

    indices = embedding.indices.tolist()
    values = embedding.values.tolist()

    if len(indices) != len(values) or not indices:
        raise ValueError("Invalid sparse query embedding.")

    return {
        "indices": indices,
        "values": values
    }
