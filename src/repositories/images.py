from sqlalchemy import func
from sqlalchemy.orm import Session

from src.services.cloud_image import CloudImage
from src.database.models import User, Image


async def upload_file(file, description: str, user: User, db: Session):
    public_id = CloudImage.generate_file_name(user.username)
    res = CloudImage.upload(file.file, public_id)
    scr_url = CloudImage.get_url_for_avatar(public_id, res)
    image = Image(user_id=user.id, description=description, public_id=public_id, origin_path=scr_url)
    db.add(image)
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


async def check_image_owner_(image_id: int, user: User, db: Session):
    user_images = await get_all_images(user.id, db)
    if image_id in [record.id for record in user_images]:
        return image_id


async def check_image_owner(image_id: int, user: User, db: Session):
    user_image = db.query(Image).filter(Image.id == image_id, Image.user_id == int(user.id)).first()
    return user_image


async def calculate_user_images(user_id: int, db: Session):
    quantity = db.query(func.count(Image.user_id)).filter(Image.user_id == user_id)
    return quantity.scalar()


# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
async def get_image_from_cloud(image_id: int, db: Session):
    image = await get_image_by_id(image_id, db)
    if image:
        file = CloudImage.get_file_by_url(image.public_id)
        return file if file else None


async def transform_image_to_db(transformed_url, image_id: int, db: Session):
    image = await get_image_by_id(image_id, db)
    image.transformed_path = transformed_url["url"]
    db.commit()
    db.refresh(image)


async def add_qrcode_to_db(image_id: int, qr_code: str, db: Session):
    image = await get_image_by_id(image_id, db)
    if image:
        image.slug = qr_code
        db.commit()
        db.refresh(image)
    return image
