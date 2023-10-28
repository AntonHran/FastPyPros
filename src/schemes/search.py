from pydantic import BaseModel, ConfigDict
from typing import Optional
from fastapi_filter.contrib.sqlalchemy import Filter


class SearchModel(Filter):
    tags: Optional[str] | None = None
    description: Optional[str] | None = None


class SortModel(Filter):
    created_at: Optional[bool] = False
    # date_desc: Optional[bool] | None = False
    rating: Optional[bool] | None = False
    # rate_desc: Optional[float] | None = None


class SearchResponse(BaseModel):
    id: int
    tag: str
    model_config = ConfigDict(from_attributes=True)
