from typing import List

from fastapi import Depends, HTTPException, APIRouter, status
from sqlalchemy.orm import Session
from fastapi_filter import FilterDepends

from src.database.connection import get_db
from src.repositories import search_images as search
from src.schemes.images import ImageResponse
from src.schemes.search import SearchModel
from src.conf import allowed_roles
from src.conf import messages


router = APIRouter(prefix="/images", tags=["images"])


@router.get("/search/", status_code=status.HTTP_200_OK,
            response_model=List[ImageResponse],
            dependencies=[Depends(allowed_roles.all_users)],
            description=messages.FOR_ALL)
async def search_images(body: SearchModel = FilterDepends(SearchModel), db: Session = Depends(get_db)):
    images = await search.search_result(body, db)
    if not images:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=messages.NOT_FOUND)
    return images
