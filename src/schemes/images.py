from pydantic import BaseModel
from fastapi import UploadFile


class ImageModel(BaseModel):
    user_id: int
    description: str
    origin_path: str
    public_id: str
    transformed_path: str | None
    qr_path: str | None
    rating: int

class FileModel(BaseModel):
    file: UploadFile

class ResponeUploadFile(BaseModel):
    public_id: str

class UpdateImageModel(BaseModel):
    description: str