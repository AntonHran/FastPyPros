from sqlalchemy.orm import Session

from src.database.models import User, Rating, Image
from src.schemes.rating import RatingModel


async def get_image_rates(limit: int, offset: int, image_id: int, db: Session):
    result = db.query(Rating).filter_by(image_id=image_id).limit(limit).offset(offset).all()
    return result


async def rate_image(body: RatingModel, user: User, db: Session):
    rate = Rating(**body.model_dump(), user_id=user.id)
    db.add(rate)
    db.commit()
    db.refresh(rate)
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
    return user_rate


"""async def calculate_rating(image_id: int, db: Session):
    query = db.query(
        func.sum(Rating.rate).label('total_rate'),
        func.count(Rating.user_id).label('user_count')
    ).filter(Rating.image_id == image_id)
    result = query.first()
    if result.total_rate and result.user_count:
        rating = result.total_rate / result.user_count
        return rating


async def update_rating(image_id: int, db: Session):
    rating = await calculate_rating(image_id, db)
    image = db.query(Image).filter(Image.id == image_id).first()
    image.rating = rating
    db.commit()
    db.refresh(image)
    return image"""
