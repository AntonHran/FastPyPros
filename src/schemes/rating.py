from datetime import datetime

from pydantic import BaseModel, ConfigDict, conint


class RatingModel(BaseModel):
    image_id: int
    rate: conint(ge=1, le=5)


class RatingResponse(BaseModel):
    id: int
    image_id: int
    rate: int
    user_id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
