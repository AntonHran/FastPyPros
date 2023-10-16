from sqlalchemy.orm import Session

from src.database.models import Tag, TagToImage


async def add_tag_to_image(image_id: int, tag: str, db: Session):
    tag_check = await create_tag(tag, db)
    if tag_check:
        return await make_record(tag_check, image_id, db)
    return await make_record(tag, image_id, db)


async def make_record(tag: str, image_id: int, db: Session):
    tag = await get_tag_by_name(tag, db)
    tags = await get_image_tags(image_id, db)
    if len(tags) < 5:
        record = TagToImage(tag_id=tag.id, image_id=image_id)
        db.add(record)
        db.commit()
        db.refresh(record)
        return record


async def get_image_tags(image_id: int, db: Session):
    tags = db.query(TagToImage.tag_id).filter_by(image_id=image_id).all()
    return tags


async def get_tags(limit: int, offset: int, db: Session):

    tags = db.query(Tag).offset(offset).limit(limit).all()
    return tags


async def get_tag_by_name(tag: str, db: Session):

    tag = db.query(Tag).filter_by(tag=tag).first()
    return tag


async def create_tag(tag: str, db: Session) -> Tag | None:
    tag = tag.rstrip(' ')
    tag = await get_tag_by_name(tag, db)
    if tag is None:
        tag = Tag(tag=tag)
        db.add(tag)
        db.commit()
        db.refresh(tag)
    return tag


async def update_tag(tag_id: int, new_tag: str, db: Session) -> Tag | None:

    tag = db.query(Tag).filter(Tag.id == tag_id).first()
    if tag:
        tag.name = new_tag
        db.commit()
        db.refresh(tag)
    return tag


async def remove_tag(tag_id: int, db: Session) -> Tag | None:
    tag = db.query(Tag).filter(Tag.id == tag_id).first()
    if tag:
        db.delete(tag)
        db.commit()
    return tag
