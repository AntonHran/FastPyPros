from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict


class ImageResponse(BaseModel):
    id: int
    user_id: int
    description: str
    public_id: str  # ?!?
    origin_path: str
    transformed_path: str | None
    slug: str | None
    rating: float | None = Field(default=0)
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class ImageUploadModel(BaseModel):
    image_id: int
    folder: str = None
    effect: str = None
    border: str = None
    radius: str = None


class ImageUploadResponse(BaseModel):
    transformed_image: str
    model_config = ConfigDict(from_attributes=True)
