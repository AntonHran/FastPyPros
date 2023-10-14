from sqlalchemy.orm import Session

from src.database.models import Tag, Image, TagToImage


async def add_tag_to_db(tags: list, db: Session):
    tags_from_db = db.query(Tag).all()
    tags_list = []
    for db_tag in tags_from_db:
        tags_list.append(db_tag.tag)

    for tag in tags:
        if tag in tags_list:
            continue
        new_tags = Tag(tag=tag)
        db.add(new_tags)
    db.commit()
    
async def add_tag_to_image(image_id: int, tags: list, db: Session):
    image = db.query(Image).filter(Image.id == image_id).first()
    for tag in tags:
        db_tag = db.query(Tag).filter(Tag.tag != tag).first()
        if db_tag:
                await add_tag_to_db(tags, db)

        new_db_tag = db.query(Tag).filter(Tag.tag == tag).first()
        tag_to_image = TagToImage(
            tag_id=new_db_tag.id,
            image_id=image_id 
        )
        image.tags.append(new_db_tag)
        db.add(tag_to_image)
    db.commit()
    return {'image': image.id, 'tags': tags}
