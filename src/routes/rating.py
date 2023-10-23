from typing import List

from fastapi import Depends, HTTPException, Path, Query, APIRouter, status
from sqlalchemy.orm import Session

from src.database.connection import get_db
from src.repositories import rating as repository_rating
from src.repositories.images import ImageServices

from src.schemes.rating import RatingModel, RatingResponse
from src.database.models import User
from src.services.auth import auth_user
from src.conf import allowed_roles
from src.conf import messages


router = APIRouter(prefix="/images", tags=["images"])


@router.get("/{image_id}/rating/", status_code=status.HTTP_200_OK, response_model=List[RatingResponse],
            dependencies=[Depends(allowed_roles.moderators_admin)],
            description=messages.FOR_MODERATORS_ADMIN
            )
async def get_rates(
        limit: int = Query(10, le=100),
        offset: int = 0,
        image_id: int = Path(ge=1),
        db: Session = Depends(get_db)):
    image_rates = await repository_rating.get_image_rates(limit, offset, image_id, db)
    if not image_rates:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=messages.NOT_FOUND)
    return image_rates


@router.post("/{image_id}/rating/", response_model=RatingResponse,
             status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(allowed_roles.all_users)],
             description=messages.FOR_ALL
             )
async def make_rate(body: RatingModel,
                    current_user: User = Depends(auth_user.get_current_user),
                    db: Session = Depends(get_db)):

    user_image = await ImageServices.check_image_owner(body.image_id, current_user, db)
    if user_image:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=messages.RATE_OWN_IMAGE)
    repeat_rate = await repository_rating.check_repeating_rate(body.image_id, current_user, db)
    if repeat_rate:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=messages.REPEAT_RATE)
    rate = await repository_rating.rate_image(body, current_user, db)
    return rate


@router.delete("/{image_id}/rating/", status_code=status.HTTP_204_NO_CONTENT,
               dependencies=[Depends(allowed_roles.moderators_admin)],
               description=messages.FOR_MODERATORS_ADMIN
               )
async def delete_rate(image_id: int,
                      user_id: int,
                      db: Session = Depends(get_db)):

    rate = await repository_rating.remove_rate(image_id, user_id, db)
    if not rate:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=messages.NOT_FOUND)
    return rate
