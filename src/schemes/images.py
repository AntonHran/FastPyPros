from pydantic import BaseModel, ConfigDict
from fastapi import UploadFile
from datetime import datetime


class ImageModel(BaseModel):
    id: int
    user_id: int
    description: str
    origin_path: str
    public_id: str
    transformed_path: str | None
    qr_path: str | None
    rating: float
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class FileModel(BaseModel):
    file: UploadFile

class ResponeUploadFile(BaseModel):
    public_id: str

class UpdateImageModel(BaseModel):
    description: str

