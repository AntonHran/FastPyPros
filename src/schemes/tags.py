from datetime import datetime

from pydantic import BaseModel, ConfigDict


class TagModel(BaseModel):
    tag: str


class TagResponse(BaseModel):
    tags: list
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
