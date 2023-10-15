from datetime import datetime

from pydantic import BaseModel, ConfigDict, conint


class RatingModel(BaseModel):
    image_id: int
    rate: conint(ge=1, le=5)


class RatingResponse(BaseModel):
    id: int
    rates: int
    users: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
