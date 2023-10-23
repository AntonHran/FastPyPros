from typing import List

from fastapi import Depends, HTTPException, Query, APIRouter, status
from sqlalchemy.orm import Session

from src.database.connection import get_db
from src.repositories.tags import TagServices
from src.schemes.tags import TagResponse
from src.conf import allowed_roles
from src.conf import messages


router = APIRouter(prefix="/images", tags=["images"])


@router.get("/tags/", response_model=List[TagResponse], dependencies=[Depends(allowed_roles.all_users)],
            status_code=status.HTTP_200_OK, description=messages.FOR_ALL)
async def get_tags(limit: int = Query(10, le=50),
                   offset: int = 0, db: Session = Depends(get_db)):
    tags = await TagServices.get_tags(limit, offset, db)
    if not tags:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=messages.NOT_FOUND)
    return tags


@router.put('/tags/{tag_id}/', response_model=TagResponse, dependencies=[Depends(allowed_roles.moderators_admin)],
            status_code=status.HTTP_200_OK, description=messages.FOR_MODERATORS_ADMIN)
async def update_tag(tag_id: int, new_tag: str, db: Session = Depends(get_db)):
    tag = await TagServices.update_tag(tag_id, new_tag, db)
    if tag is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=messages.NOT_FOUND)
    return tag


@router.delete('/tags/{tag_id}/', dependencies=[Depends(allowed_roles.admin)],
               status_code=status.HTTP_204_NO_CONTENT, description=messages.FOR_ADMIN)
async def delete_tag(tag_id: int, db: Session = Depends(get_db)):
    tag = await TagServices.remove_tag(tag_id, db)
    if tag is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=messages.NOT_FOUND)
    return tag


@router.post('/{image_id}/tags/', response_model=TagResponse, status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(allowed_roles.all_users)], description=messages.FOR_ALL)
async def add_tag_to_image(image_id: int, tag: str, db: Session = Depends(get_db)):
    result = await TagServices.add_tag_to_image(image_id, tag, db)
    if result is None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=messages.LIMIT_EXCEEDED)
    return result
