
from transformers import AutoTokenizer

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

CHUNK_SIZE = 180
CHUNK_OVERLAP = 30
MAX_SEQUENCE_LENGTH = 256

tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)


def create_chunks(
    text: str,
    document_id: int,
    source_type: str,
    chunk_size: int = CHUNK_SIZE,
    overlap: int = CHUNK_OVERLAP,
    max_sequence_length: int = MAX_SEQUENCE_LENGTH
):
    """
    Create token-based chunks with overlap and metadata.

    end_token is exclusive.
    """

    # Validate inputs
    if not isinstance(text, str):
        raise TypeError("Document text must be a string.")

    if not isinstance(document_id, int) or document_id <= 0:
        raise ValueError("document_id must be a positive integer.")

    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than zero.")

    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("Overlap must be >= 0 and smaller than chunk_size.")

    special_token_count = tokenizer.num_special_tokens_to_add(pair=False)

    if chunk_size + special_token_count > max_sequence_length:
        raise ValueError(
            "Chunk size plus special tokens exceeds model sequence limit."
        )

    if not source_type:
        raise ValueError("source_type cannot be empty.")

    # Empty document: return no chunks
    if not text.strip():
        return []

    # Convert the complete document into token IDs
    token_ids = tokenizer.encode(
        text,
        add_special_tokens=False
    )

    chunks = []

    start = 0
    chunk_index = 0
    step = chunk_size - overlap

    while start < len(token_ids):

        end = min(start + chunk_size, len(token_ids))

        current_tokens = token_ids[start:end]

        chunk_text = tokenizer.decode(
            current_tokens,
            skip_special_tokens=True,
            clean_up_tokenization_spaces=False
        )

        # Count actual model input tokens, including special tokens
        model_input_count = len(
            tokenizer.encode(
                chunk_text,
                add_special_tokens=True
            )
        )

        chunk = {
            "document_id": document_id,
            "chunk_id": f"{document_id}_{chunk_index + 1:03d}",
            "chunk_index": chunk_index,
            "source_type": source_type.lower(),
            "start_token": start,
            "end_token": end,
            "token_count": len(current_tokens),
            "model_input_token_count": model_input_count,
            "chunk_text": chunk_text
        }

        chunks.append(chunk)

        chunk_index += 1
        start += step

    # Validate the generated chunks before returning
    validate_chunks(
        chunks=chunks,
        chunk_size=chunk_size,
        overlap=overlap,
        max_sequence_length=max_sequence_length
    )

    return chunks


def validate_chunks(
    chunks: list,
    chunk_size: int = CHUNK_SIZE,
    overlap: int = CHUNK_OVERLAP,
    max_sequence_length: int = MAX_SEQUENCE_LENGTH
):
    """
    Validate chunk metadata, token limits and overlap.
    """

    if not chunks:
        return True

    for index, chunk in enumerate(chunks):

        # Check chunk sequence
        if chunk["chunk_index"] != index:
            raise ValueError("Invalid chunk index.")

        # Check token range
        actual_range = chunk["end_token"] - chunk["start_token"]

        if actual_range != chunk["token_count"]:
            raise ValueError("Token range does not match token count.")

        if not 0 < chunk["token_count"] <= chunk_size:
            raise ValueError("Chunk token count is outside allowed limits.")

        # Check actual model input length
        if chunk["model_input_token_count"] > max_sequence_length:
            raise ValueError("Chunk exceeds model sequence length.")

        if not chunk["chunk_text"].strip():
            raise ValueError("Chunk text cannot be empty.")

        if index > 0:

            previous = chunks[index - 1]

            # Check continuous chunk progression
            if chunk["start_token"] >= chunk["end_token"]:
                raise ValueError("Invalid token positions.")

            if chunk["start_token"] >= previous["end_token"]:
                raise ValueError("Expected overlap between consecutive chunks.")

            actual_overlap = (
                previous["end_token"] - chunk["start_token"]
            )

            if actual_overlap != overlap:
                raise ValueError("Incorrect overlap between chunks.")

    return True


if __name__ == "__main__":

    sample_text = """
    Insurance policies provide financial protection against
    unexpected medical expenses.

    The policyholder is eligible for coverage up to five lakh rupees.

    The policy remains active until 15 December 2027.

    Renewal must be completed before the expiry date.
    """ * 20

    result = create_chunks(
        text=sample_text,
        document_id=102,
        source_type="txt"
    )

    print("\nTOTAL CHUNKS:", len(result))

    for chunk in result:
        print("\n----------------------------")
        print("CHUNK ID:", chunk["chunk_id"])
        print("CHUNK INDEX:", chunk["chunk_index"])
        print("TOKEN RANGE:", chunk["start_token"], "-", chunk["end_token"])
        print("TOKEN COUNT:", chunk["token_count"])
        print("MODEL INPUT TOKENS:", chunk["model_input_token_count"])
        print("TEXT:", chunk["chunk_text"])

    print("\nVALIDATION:", validate_chunks(result))
