from sqlalchemy.orm import Session

from src.database.models import User, Rating, Image
from src.schemes.rating import RatingModel


async def get_image_rates(limit: int, offset: int, image_id: int, db: Session):
    result = db.query(Rating).limit(limit).filter_by(image_id=image_id).offset(offset).all()
    return result


async def rate_image(body: RatingModel, user: User, db: Session):
    rate = Rating(**body.model_dump(), user_id=user.id)
    db.add(rate)
    db.commit()
    db.refresh(rate)
    await update_rating(body.image_id, db)
    return rate


async def check_image(image_id: int, user: User, db: Session):
    user_image = db.query(Image).filter(Image.id == image_id, Image.user_id == int(user.id)).first()
    return user_image


async def check_repeating_rate(image_id: int, user: User, db: Session):
    user_rate = db.query(Rating).filter(Rating.image_id == image_id, Rating.user_id == int(user.id)).first()
    return user_rate


async def remove_rate(image_id: int, user_id: int, db: Session):
    user_rate = db.query(Rating).filter(Rating.image_id == image_id, Rating.user_id == user_id).first()
    if user_rate:
        db.delete(user_rate)
        db.commit()
        await update_rating(image_id, db)
    return user_rate


async def calculate_rating(image_id: int, db: Session):
    rates_query = db.query(Rating).filter(Rating.image_id == image_id).all()
    rates = sum([rate.rate for rate in rates_query])
    users = len([rate.user_id for rate in rates_query])
    rating = rates / users
    return rating


async def update_rating(image_id: int, db: Session):
    rating = await calculate_rating(image_id, db)
    image = db.query(Image).filter(Image.id == image_id).first()
    image.rating = rating
    db.commit()
    db.refresh(image)
    return image
