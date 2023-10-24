from typing import List

from fastapi import Depends, HTTPException, Query, APIRouter, status
from sqlalchemy.orm import Session

from src.database.connection import get_db
from src.repositories.comments import CommentServices
from src.database.models import User
from src.services.auth import auth_user
from src.schemes.comments import CommentResponse, CommentModel
from src.conf import allowed_roles
from src.conf import messages


router = APIRouter(prefix="/images", tags=["images"])


@router.get("/{image_id}/comments", status_code=status.HTTP_200_OK,
            response_model=List[CommentResponse],
            dependencies=[Depends(allowed_roles.all_users)],
            description=messages.FOR_ALL)
async def read_comments(image_id: int, limit: int = Query(10, le=100),
                        offset: int = 0, db: Session = Depends(get_db)):

    comments = await CommentServices.get_comments(image_id, limit, offset, db)
    if not comments:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=messages.NOT_FOUND)
    return comments


@router.post("/{image_id}/comments/", response_model=CommentResponse, status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(allowed_roles.all_users)], description=messages.FOR_ALL)
async def create_comment(body: CommentModel,
                         current_user: User = Depends(auth_user.get_current_user),
                         db: Session = Depends(get_db)):
    comment = await CommentServices.create_comment(body, current_user, db)
    if not comment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=messages.SOMETHING_WRONG)
    return comment


@router.put("/{image_id}/comments/{comment_id}", response_model=CommentResponse, status_code=status.HTTP_200_OK,
            dependencies=[Depends(allowed_roles.all_users)], description=messages.FOR_ALL)
async def update_comment(comment_id: int, new_comment: str,
                         current_user: User = Depends(auth_user.get_current_user),
                         db: Session = Depends(get_db)):

    comment = await CommentServices.get_comment(comment_id, db)
    if not comment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=messages.NOT_FOUND)
    if comment.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail=messages.NOT_YOUR_COMMENT)
    new_comment = await CommentServices.update_comment(new_comment, comment_id, db)
    return new_comment


@router.delete("/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT,
               dependencies=[Depends(allowed_roles.admin)],
               description=messages.FOR_ADMIN)
async def delete_comment(comment_id: int, db: Session = Depends(get_db)):

    comment = await CommentServices.delete_comment(comment_id, db)
    if not comment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=messages.NOT_FOUND)
    return comment
