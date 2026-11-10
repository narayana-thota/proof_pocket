from pydantic import BaseModel, Field


class SemanticSearchRequest(BaseModel):
    question: str = Field(
        ...,
        min_length=3,
        max_length=2000
    )

    top_k: int = Field(
        default=5,
        ge=1,
        le=20
    )

    document_id: int | None = Field(
        default=None,
        gt=0
    )