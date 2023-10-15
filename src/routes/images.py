from typing import List
# from datetime import date

from fastapi import Depends, HTTPException, Path, Query, APIRouter, status
from sqlalchemy.orm import Session
from fastapi_limiter.depends import RateLimiter

from src.database.connection import get_db
from src.repositories import rating as repository_rating
from src.schemes.rating import RatingModel, RatingResponse
from src.database.models import User, Role
from src.services.auth import auth_user
from src.services.roles import RoleAccess
from src.conf import messages


router = APIRouter(prefix="/images", tags=["images"])

allowed_rate = RoleAccess([Role.admin, Role.moderator, Role.user])
allowed_get = RoleAccess([Role.admin, Role.moderator])
allowed_remove = RoleAccess([Role.admin, Role.moderator])


@router.get("/rating/{image_id}", status_code=status.HTTP_200_OK, response_model=List[RatingResponse],
            dependencies=[Depends(allowed_get), Depends(RateLimiter(times=10, seconds=60))],
            description=messages.FOR_MODERATORS_ADMIN
            )
async def get_rate(
        limit: int = Query(10, le=100),
        offset: int = 0,
        image_id: int = Path(ge=1),
        db: Session = Depends(get_db)):
    image_rates = await repository_rating.get_image_rates(limit, offset, image_id, db)
    if not image_rates:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=messages.NOT_FOUND)
    return image_rates


@router.post("/rate", response_model=RatingResponse,
             status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(allowed_rate)],  # Depends(RateLimiter(times=4, seconds=60))],
             description=messages.FOR_ALL
             )
async def make_rate(body: RatingModel,
                    current_user: User = Depends(auth_user.get_current_user),
                    db: Session = Depends(get_db)):

    user_image = await repository_rating.check_image(body.image_id, current_user, db)
    if user_image:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=messages.RATE_OWN_IMAGE)
    repeat_rate = await repository_rating.check_repeating_rate(body.image_id, current_user, db)
    if repeat_rate:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=messages.REPEAT_RATE)
    rate = await repository_rating.rate_image(body, current_user, db)
    return rate


@router.delete("/rating/{image_id}", status_code=status.HTTP_204_NO_CONTENT,
               response_model=RatingResponse,
               dependencies=[Depends(allowed_remove)],
               description=messages.FOR_MODERATORS_ADMIN
               )
async def delete_rate(image_id: int = Path(ge=1),
                      user_id: int = Path(ge=1),
                      db: Session = Depends(get_db)):

    rate = await repository_rating.remove_rate(image_id, user_id, db)
    if not rate:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=messages.NOT_FOUND)
    return rate
