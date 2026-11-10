
from uuid import UUID

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):

    question: str = Field(
        min_length=1,
        max_length=2000,
    )

    document_id: int | None = Field(
        default=None,
        gt=0,
    )

    conversation_id: UUID | None = None
