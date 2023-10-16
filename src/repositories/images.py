from sqlalchemy.orm import Session

from src.schemes.images import ImageModel
from src.services.cloud_image import CloudImage
from src.database.models import User, Image


async def upload_file(body: ImageModel, user: User, db: Session):
    public_id = CloudImage.generate_name_avatar(user.username)
    res = CloudImage.upload(body.file.file, public_id)
    scr_url = CloudImage.get_url_for_avatar(public_id, res)
    image = Image(user_id=user.id, description=body.description, public_id=public_id, origin_path=scr_url)
    db.commit()
    db.refresh(image)
    return image


async def get_image_by_id(image_id: int, db: Session):
    return db.query(Image).filter(Image.id == image_id).first()


async def get_all_images(user_id: int, db: Session):
    return db.query(Image).filter(Image.user_id == user_id).all()


async def update_description(image_id: int, description: str, db: Session):
    image = await get_image_by_id(image_id, db)
    if image:
        image.description = description
        db.commit()
        db.refresh(image)
    return image


async def delete_image(image_id: int, username: str, db: Session):
    image = await get_image_by_id(image_id, db)
    if image:
        CloudImage.remove_image(username, image.public_id)
        db.delete(image)
        db.commit()
    return image
