
from transformers import AutoTokenizer

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

# Sentence Transformers uses a maximum sequence length of 256
MAX_SEQUENCE_LENGTH = 256

# Load the tokenizer
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)


def tokenize_text(text: str):
    """
    Convert text into tokens and token IDs.
    """

    tokens = tokenizer.tokenize(text)

    token_ids = tokenizer.convert_tokens_to_ids(tokens)

    return {
        "original_text": text,
        "tokens": tokens,
        "token_ids": token_ids,
        "token_count": len(token_ids)
    }


def encode_text(text: str):
    """
    Convert text into model-ready token IDs,
    including special tokens and attention mask.
    """

    encoded = tokenizer(
        text,
        add_special_tokens=True,
        truncation=True,
        max_length=MAX_SEQUENCE_LENGTH,
        padding=False,
        return_attention_mask=True
    )

    return {
        "input_ids": encoded["input_ids"],
        "attention_mask": encoded["attention_mask"],
        "token_count": len(encoded["input_ids"]),
        "was_truncated": len(
            tokenizer(text, add_special_tokens=True)["input_ids"]
        ) > MAX_SEQUENCE_LENGTH
    }


if __name__ == "__main__":

    sample_text = (
        "The warranty expires on 15 December 2027. "
        "Please renew the policy before the expiry date."
    )

    result = tokenize_text(sample_text)

    print("\nORIGINAL TEXT:")
    print(result["original_text"])

    print("\nTOKENS:")
    print(result["tokens"])

    print("\nTOKEN IDs:")
    print(result["token_ids"])

    print("\nTOKEN COUNT:")
    print(result["token_count"])

    encoded = encode_text(sample_text)

    print("\nMODEL INPUT:")
    print(encoded)
