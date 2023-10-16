from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict


class CommentModel(BaseModel):
    image_id: int
    content: str = Field(max_length=265)


class CommentResponse(CommentModel):
    id: int
    created_at: datetime
    updated_at: datetime
    user_id: int
    model_config = ConfigDict(from_attributes=True)
