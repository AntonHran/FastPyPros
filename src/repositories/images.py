from typing import List
from fastapi import UploadFile, File
from sqlalchemy import and_
from sqlalchemy.orm import Session

from src.database.models import Image, User
from src.services.cloud_image import CloudImage


async def upload_file(file: UploadFile, description: str, db: Session, user: User):

    public_id = CloudImage.generate_public_id(username=user.username, email=user.email) 
    upload_result = CloudImage.upload(file.file, public_id)
    image_url = upload_result["secure_url"]

    image = Image(user_id=user.id, description=description, origin_path=image_url, public_id=public_id, transformed_path=None, qr_path=None)
    db.add(image)
    db.commit()
    return {"image": image}

async def get_image_by_id(image_id: int, db: Session, user: User) -> Image:
    return db.query(Image).filter(and_(Image.id == image_id, Image.user_id == user.id)).first()

async def get_images(skip: int, limit: int, db: Session, user: User) -> List[Image]:
    return db.query(Image).filter(Image.user_id == user.id).offset(skip).limit(limit).all()

async def update_description(image_id: int, description: str, db: Session, user: User):

    image = await get_image_by_id(image_id, db, user)
    if image:
        image.description = description
        db.commit()
    return image

async def delete_image(image_id: int, db: Session, user: User):

    image = await get_image_by_id(image_id, db, user)
    if image:
        result = CloudImage.delete_image(image.public_id)
        db.delete(image)
        db.commit()
    return result
