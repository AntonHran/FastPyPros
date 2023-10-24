from sqlalchemy.orm import Session
from sqlalchemy import desc, union, select

from src.database.models import Image, TagToImage, Tag, Account
from src.schemes.search import SearchModel


async def search_result(body: SearchModel, db: Session):
    search_data = {key: value for key, value in body.model_dump().items() if value}
    rd, rt = [], []
    if body.description:
        rd = select([await search_by_description(body.description, db)])  # ???
    if body.tags:
        rt = select(await search_by_tag(body.tags, db))
    if rd and rt:
        return union(rd, rt)
    if rd and not rt:
        return rd
    if rt and not rd:
        return rt


filters = {"date": Image.created_at,
           "date_desc": desc(Image.created_at),
           "rate": Image.updated_at,
           "rate_desc": desc(Image.updated_at), }


async def search_by_description(keyword: str, db: Session):
    result_by_description = db.query(Image).filter(Image.description.ilike("%" + keyword + "%")).order_by(filters["date"]).all()
    return result_by_description


async def get_tags(keyword: str, db: Session):
    tag_ids: list = db.query(Tag.id).filter(Tag.tag.ilike("%" + keyword + "%")).all()
    return tag_ids


async def get_image_ids(tag_ids: list[int], db: Session):
    image_ids_by_tag = db.query(TagToImage.image_id).filter(TagToImage.tag_id.in_(tag_ids)).all()
    return image_ids_by_tag


async def search_by_tag(keyword: str, db: Session):
    tag_ids = await get_tags(keyword, db)
    image_ids_by_tag = await get_image_ids(tag_ids, db)
    result_by_tags = db.query(Image).filter(Image.id.in_(image_ids_by_tag)).order_by(filters["rate"]).all()
    return result_by_tags


async def add_image_to_quantity(username: str, db: Session):
    user_account = db.query(Account).filter(Account.username == username).first()
    user_account.images_quantity += 1
    db.commit()
    db.refresh(user_account)
    return user_account
