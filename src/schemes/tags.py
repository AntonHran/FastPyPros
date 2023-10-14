from pydantic import BaseModel
from datetime import datetime


class TagModel(BaseModel):
    tag: str
    created_at: datetime

class ResponeTagModel(BaseModel):
    tags: list

class ResponsTagToImageModel(BaseModel):
    image: int
    tags: list
    