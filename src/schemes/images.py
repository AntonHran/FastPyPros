from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict
from fastapi import UploadFile


class ImageModel(BaseModel):
    description: str = Field(min_length=3, max_length=60)
    file: UploadFile


class ImageResponse(BaseModel):
    id: int
    user_id: int
    description: str
    public_id: str  # ?!?
    origin_path: str
    transformed_path: str | None
    qr_path: str | None
    rating: float = Field(default=0)
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
