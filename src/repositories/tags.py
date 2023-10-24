from sqlalchemy.orm import Session
from fastapi.exceptions import ValidationException

from src.database.models import Tag, TagToImage


async def make_record(tag: str, image_id: int, db: Session):
    res = await check_image_tags(tag, image_id, db)
    if res:
        record = TagToImage(tag_id=res.id, image_id=image_id)
        db.add(record)
        db.commit()
        db.refresh(record)
        return record


async def get_image_tags(image_id: int, db: Session):
    try:
        tags = db.query(TagToImage.tag_id).filter_by(image_id=image_id).all()
    except ValidationException:
        return None
    return tags


async def get_tag_by_name(tag: str, db: Session):
    try:
        tag = db.query(Tag).filter_by(tag=tag).first()
    except ValidationException:
        return None
    return tag


async def create_tag(tag: str, db: Session) -> Tag | None:
    tag = tag.strip('')
    new_tag = Tag(tag=tag)
    db.add(new_tag)
    db.commit()
    db.refresh(new_tag)
    return new_tag


async def check_image_tags(tag: str, image_id: int, db: Session):
    tag_ = await get_tag_by_name(tag, db)
    tags = await get_image_tags(image_id, db)
    if not tags:
        return tag_
    if tag and tag_.id not in tags and len(tags) < 5:
        return tag_


async def get_tag_by_id(tag_id: int, db: Session):
    tag = db.query(Tag).filter(Tag.id == tag_id).first()
    return tag


class TagServices:
    @staticmethod
    async def add_tag_to_image(image_id: int, tag: str, db: Session):
        res = await get_tag_by_name(tag, db)
        if not res:
            res = await create_tag(tag, db)
        return res if await make_record(res.tag, image_id, db) else None

    @staticmethod
    async def update_tag(tag_id: int, new_tag: str, db: Session) -> Tag | None:
        tag = await get_tag_by_id(tag_id, db)
        if tag:
            tag.name = new_tag
            db.commit()
            db.refresh(tag)
        return tag

    @staticmethod
    async def get_tags(limit: int, offset: int, db: Session):
        tags = db.query(Tag).limit(limit).offset(offset).all()
        print(tags)
        return tags

    @staticmethod
    async def remove_tag(tag_id: int, db: Session) -> Tag | None:
        tag = await get_tag_by_id(tag_id, db)
        if tag:
            db.delete(tag)
            db.commit()
        return tag
