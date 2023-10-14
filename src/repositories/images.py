import cloudinary
from fastapi import UploadFile, File
from sqlalchemy.orm import Session

from src.database.models import Image, User
from src.schemes.images import ImageModel


async def upload_file(file: UploadFile, description: str, db: Session):

    upload_result = cloudinary.uploader.upload(file.file, folder='project_file')
    image_url = upload_result["secure_url"]
    public_id = upload_result["public_id"]
    user_id = 1
    image = Image(user_id=user_id, description=description, origin_path=image_url, public_id=public_id, transformed_path=None, qr_path=None, rating=0)
    db.add(image)
    db.commit()

    return {"public_id": public_id}

async def get_image_by_id(image_id: int, db: Session):

    return db.query(Image).filter(Image.id == image_id).first()

async def update_description(image_id: int, description: str, db: Session):

    image = db.query(Image).filter(Image.id == image_id).first()
    if image:
        image.description = description
        db.commit()
    return image

async def delete_image(image_id: int, db: Session):

    image = db.query(Image).filter(Image.id == image_id).first()
    if image:
        result = cloudinary.uploader.destroy(image.public_id, invalidate=True)
        db.delete(image)
        db.commit()
    return result
