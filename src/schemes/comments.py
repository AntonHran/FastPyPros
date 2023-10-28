from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict


class CommentModel(BaseModel):
    image_id: int
    content: str = Field(min_length=2, max_length=265)


class CommentResponse(BaseModel):
    id: int
    user_id: int
    comment: str
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)
