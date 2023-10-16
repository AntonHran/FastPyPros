from typing import List, Type

from sqlalchemy.orm import Session

from src.database.models import Comment, CommentToImage
from src.database.models import User
from src.schemes.comments import CommentModel
from images import get_all_images


async def get_comments(image_id: int, limit: int, offset: int, db: Session) -> List[Type[Comment]]:
    comment_ids = await get_image_comments_ids(image_id, db)
    comments = db.query(Comment).filter(Comment.id.in_(comment_ids)).limit(limit).offset(offset).all()
    return comments


async def get_comment(comment_id: int, db: Session) -> Type[Comment] | None:
    return db.query(Comment).filter(Comment.id == comment_id).first()


async def create_comment(body: CommentModel, user: User, db: Session) -> Comment:
    user_images = await get_all_images(user, db)
    if body.image_id not in [user_image.id for user_image in user_images]:
        comment = Comment(comment=body.content, user_id=user.id)
        db.add(comment)
        db.commit()
        db.refresh(comment)
        await create_record(user, comment.id, body.image_id, db)
        return comment


async def update_comment(new_comment: str, comment_id: int, db: Session) -> Type[Comment] | None:
    comment = await get_comment(comment_id, db)
    if len(new_comment) > 2:
        comment.comment = new_comment
        db.commit()
        db.refresh(comment)
        return comment


async def delete_comment(comment_id: int, db: Session) -> Type[Comment] | None:
    comment = await get_comment(comment_id, db)
    if comment:
        db.delete(comment)
        db.commit()
    return comment


async def create_record(user: User, comment_id: int, image_id: int, db: Session):
    new_record = CommentToImage(user_id=user.id, image_id=image_id, comment_id=comment_id)
    db.add(new_record)
    db.commit()
    db.refresh(new_record)
    return new_record


async def get_image_comments_ids(image_id: int, db: Session):
    comment_ids = db.query(CommentToImage.comment_id).filter_by(image_id=image_id).all()
    return comment_ids
