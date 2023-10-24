from typing import List, Type

from sqlalchemy.orm import Session

from src.database.models import Comment, CommentToImage
from src.database.models import User
from src.schemes.comments import CommentModel
from src.repositories.images import ImageServices


class CommentServices:
    @staticmethod
    async def get_comments(image_id: int, limit: int, offset: int, db: Session) -> List[Type[Comment]]:
        comment_ids = await get_image_comments_ids(image_id, db)
        comment_ids = [comm.comment_id for comm in comment_ids]
        comments = db.query(Comment).filter(Comment.id.in_(comment_ids)).limit(limit).offset(offset).all()
        return comments

    @staticmethod
    async def get_comment(comment_id: int, db: Session) -> Type[Comment] | None:
        return db.query(Comment).filter(Comment.id == comment_id).first()

    @staticmethod
    async def create_comment(body: CommentModel, user: User, db: Session) -> Comment:
        user_images = await ImageServices.get_all_images(user.id, db)
        if user_images and body.image_id not in [user_image.id for user_image in user_images]:
            comment = Comment(comment=body.content, user_id=user.id)
            db.add(comment)
            db.commit()
            db.refresh(comment)
            await create_record(comment.id, body.image_id, db)
            return comment
        if not user_images:
            comment = Comment(comment=body.content, user_id=user.id)
            db.add(comment)
            db.commit()
            db.refresh(comment)
            await create_record(comment.id, body.image_id, db)
            return comment

    @staticmethod
    async def update_comment(new_comment: str, comment_id: int, db: Session) -> Type[Comment] | None:
        comment = db.query(Comment).filter(Comment.id == comment_id).first()
        if len(new_comment) > 2:
            comment.comment = new_comment
            db.commit()
            db.refresh(comment)
            return comment

    @staticmethod
    async def delete_comment(comment_id: int, db: Session) -> Type[Comment] | None:
        comment = db.query(Comment).filter(Comment.id == comment_id).first()
        if comment:
            db.delete(comment)
            db.commit()
        return comment


async def create_record(comment_id: int, image_id: int, db: Session):
    new_record = CommentToImage(image_id=image_id, comment_id=comment_id)
    db.add(new_record)
    db.commit()
    db.refresh(new_record)
    return new_record


async def get_image_comments_ids(image_id: int, db: Session):
    comment_ids = db.query(CommentToImage).filter_by(image_id=image_id).all()
    return comment_ids
