
from app.ai.chunking import create_chunks
from app.ai.embedding import generate_embeddings
from app.ai.sparse_embedding import generate_sparse_embeddings


def process_document(
    extracted_text: str,
    document_id: int,
    source_type: str
) -> list[dict]:

    """
    Process extracted document text.

    1. Create text chunks.
    2. Generate dense embeddings.
    3. Generate sparse embeddings.
    4. Attach both embeddings to corresponding chunks.
    5. Return processed chunks.
    """

    # Step 1: Validate input
    if not isinstance(extracted_text, str):
        raise TypeError("Extracted text must be a string.")

    if not extracted_text.strip():
        raise ValueError("Extracted text cannot be empty.")

    # Step 2: Generate chunks
    chunks = create_chunks(
        text=extracted_text,
        document_id=document_id,
        source_type=source_type
    )

    if not chunks:
        return []

    # Step 3: Extract chunk text
    chunk_texts = [
        chunk["chunk_text"]
        for chunk in chunks
    ]

    # Step 4: Generate dense embeddings
    dense_vectors = generate_embeddings(chunk_texts)

    # Step 5: Generate sparse embeddings
    sparse_vectors = generate_sparse_embeddings(chunk_texts)

    # Step 6: Validate embedding counts
    if len(dense_vectors) != len(chunks):
        raise ValueError(
            "Dense embedding count does not match chunk count."
        )

    if len(sparse_vectors) != len(chunks):
        raise ValueError(
            "Sparse embedding count does not match chunk count."
        )

    # Step 7: Attach both embeddings to each chunk
    processed_chunks = []

    for chunk, dense_vector, sparse_vector in zip(
        chunks,
        dense_vectors,
        sparse_vectors
    ):

        processed_chunk = {
            **chunk,
            "embedding": dense_vector.tolist(),
            "sparse_embedding": sparse_vector
        }

        processed_chunks.append(processed_chunk)

    return processed_chunks
