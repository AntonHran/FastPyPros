from pydantic import BaseModel, ConfigDict
from typing import Optional
from fastapi_filter.contrib.sqlalchemy import Filter


class SearchModel(Filter):
    tags: Optional[str]
    description: Optional[str] | None
    date: Optional[str] | None
    rate: Optional[float] | None


class SearchResponse(BaseModel):
    id: int
    tag: str
    model_config = ConfigDict(from_attributes=True)
