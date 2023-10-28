from sqlalchemy.orm import Session
from sqlalchemy import desc

from src.database.models import Image, TagToImage, Tag
from src.schemes.search import SearchModel, SortModel


async def search_result(body_search: SearchModel, body_sort: SortModel, db: Session):
    search_data = {key: value for key, value in body_search.model_dump().items() if value}
    sort_data = {key: value for key, value in body_sort.model_dump().items() if value}
    rd, rt = None, None
    for parameter, value in body_search.model_dump().items():
        if parameter in func.keys() and value:
            res = await func[parameter](value, db)
            return await sorting_by(body_sort, res) if res else None
        '''if parameter == "description" and value:
            rd = await search_by_description(value, db)
        if parameter == "tags" and value:
            rt = await search_by_tag(value, db)
    return await sorting_by(body_sort, rd) if rd else await sorting_by(body_sort, rt) if rt else None'''


async def search_by_description(keyword: str, db: Session):
    result_by_description = db.query(Image).filter(Image.description.ilike("%" + keyword + "%")).all()
    return result_by_description


async def get_tags(keyword: str, db: Session) -> list[int]:
    tag_ids: list = db.query(Tag.id).filter(Tag.tag.ilike("%" + keyword + "%")).all()
    return [tag[0] for tag in tag_ids]


async def get_image_ids(tag_ids: list[int], db: Session) -> list[int]:
    image_ids_by_tag = db.query(TagToImage.image_id).filter(TagToImage.tag_id.in_(tag_ids)).all()
    return [image_id[0] for image_id in image_ids_by_tag]


async def search_by_tag(keyword: str, db: Session):
    tag_ids = await get_tags(keyword, db)
    image_ids_by_tag = await get_image_ids(tag_ids, db)
    result_by_tags = db.query(Image).filter(Image.id.in_(image_ids_by_tag)).all()
    return result_by_tags


async def sorting_by(body: SortModel, query):
    for par, val in body.model_dump().items():
        if getattr(body, par) and val:
            res = sorted(query, key=lambda image: getattr(image, par), reverse=True)
            # select(query).order_by(filters.get(par))
            return res
    return query


func = {"description": search_by_description,
        "tags": search_by_tag, }
