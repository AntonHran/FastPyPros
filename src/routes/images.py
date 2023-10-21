from typing import List

from fastapi import Depends, HTTPException, Path, Query, APIRouter, status, UploadFile
from sqlalchemy.orm import Session
from fastapi_limiter.depends import RateLimiter

from src.database.connection import get_db
from src.repositories import rating as repository_rating
from src.repositories.images import ImageServices
from src.repositories import search_images as search
from src.repositories.tags import TagServices
from src.repositories.comments import CommentServices
from src.schemes.rating import RatingModel, RatingResponse
from src.database.models import User
from src.services.auth import auth_user
from src.schemes.images import ImageResponse
from src.schemes.tags import TagResponse
from src.schemes.comments import CommentResponse, CommentModel
from src.schemes.images import ImageUploadModel
from src.services.cloud_services import TransformImage
from src.conf import allowed_roles
from src.conf import messages


router = APIRouter(prefix="/images", tags=["images"])


# ----------------------------------------RATING------------------------------------
@router.get("/rating/{image_id}", status_code=status.HTTP_200_OK, response_model=List[RatingResponse],
            dependencies=[Depends(allowed_roles.moderators_admin), Depends(RateLimiter(times=10, seconds=60))],
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


@router.post("/rate/", response_model=RatingResponse,
             status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(allowed_roles.all_users)],  # Depends(RateLimiter(times=4, seconds=60))],
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


@router.delete("/remove_rates/{image_id}", status_code=status.HTTP_204_NO_CONTENT,
               dependencies=[Depends(allowed_roles.moderators_admin)],
               description=messages.FOR_MODERATORS_ADMIN
               )
async def delete_rate(image_id: int = Path(ge=1),
                      user_id: int = Path(ge=1),
                      db: Session = Depends(get_db)):

    rate = await repository_rating.remove_rate(image_id, user_id, db)
    if not rate:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=messages.NOT_FOUND)
    return rate


# -------------------------------------SEARCH---------------------------------------
@router.get("/search/", status_code=status.HTTP_200_OK,
            response_model=List[ImageResponse],
            dependencies=[Depends(allowed_roles.all_users)],
            description=messages.FOR_ALL)
async def search_images(keyword: str, filter_by: str, db: Session = Depends(get_db)):
    images = await search.search_result(keyword, filter_by, db)
    if not images:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=messages.NOT_FOUND)
    return images


# -------------------------------------IMAGES---------------------------------------
@router.post('/', status_code=status.HTTP_201_CREATED,
             response_model=ImageResponse, dependencies=[Depends(allowed_roles.all_users)],
             description=messages.FOR_ALL)
async def upload_file(file: UploadFile, description: str,
                      current_user: User = Depends(auth_user.get_current_user),
                      db: Session = Depends(get_db)):

    image = await ImageServices.upload_file(file, description, current_user, db)
    if image is None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=messages.SOMETHING_WRONG)
    return image


@router.get('/{image_id}', response_model=ImageResponse,
            status_code=status.HTTP_200_OK, dependencies=[Depends(allowed_roles.all_users)],
            description=messages.FOR_ALL)
async def get_image(image_id: int, db: Session = Depends(get_db)):

    result = await ImageServices.get_image(image_id, db)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=messages.NOT_FOUND)
    return result


@router.get('/', response_model=List[ImageResponse],
            status_code=status.HTTP_200_OK, dependencies=[Depends(allowed_roles.all_users)],
            description=messages.FOR_ALL)
async def get_images(current_user: User = Depends(auth_user.get_current_user), db: Session = Depends(get_db)):

    images = await ImageServices.get_all_images(current_user.id, db)
    if images is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=messages.NOT_FOUND)
    return images


@router.patch('/{image_id}', response_model=ImageResponse,
              status_code=status.HTTP_200_OK, dependencies=[Depends(allowed_roles.all_users)],
              description=messages.FOR_ALL)
async def update_description(image_id: int, description: str,
                             current_user: User = Depends(auth_user.get_current_user),
                             db: Session = Depends(get_db)):
    user_image = await ImageServices.check_image_owner(image_id, current_user, db)
    if not user_image and current_user.roles in ("admin", "moderator"):
        return await ImageServices.update_description(image_id, description, db)
    if not user_image and current_user.roles not in ("admin", "moderator"):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=messages.NOT_YOUR_IMAGE)
    image = await ImageServices.update_description(image_id, description, db)
    if not image:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=messages.NOT_FOUND)
    return image


@router.delete('/{image_id}',
               status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(allowed_roles.all_users)],
               description=messages.FOR_ALL)
async def delete_image(image_id: int, current_user: User = Depends(auth_user.get_current_user),
                       db: Session = Depends(get_db)):
    user_image = await ImageServices.check_image_owner(image_id, current_user, db)
    if not user_image and current_user.roles == "admin":
        result = await ImageServices.delete_image(image_id, current_user.username, db)
        return result
    if not user_image and current_user.roles != "admin":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=messages.NOT_YOUR_IMAGE)
    result = await ImageServices.delete_image(image_id, current_user.username, db)
    return result


# ----------------------------------------TAGS--------------------------------------
@router.get("/tags/", response_model=List[TagResponse], dependencies=[Depends(allowed_roles.all_users)],
            status_code=status.HTTP_200_OK, description=messages.FOR_ALL)
async def get_tags(limit: int = Query(10, le=50),
                   offset: int = 0, db: Session = Depends(get_db)):
    tags = await TagServices.get_tags(limit, offset, db)
    if not tags:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=messages.NOT_FOUND)
    return tags


@router.put('/{tag_id}', response_model=TagResponse, dependencies=[Depends(allowed_roles.moderators_admin)],
            status_code=status.HTTP_200_OK, description=messages.FOR_MODERATORS_ADMIN)
async def update_tag(tag_id: int, new_tag: str, db: Session = Depends(get_db)):
    tag = await TagServices.update_tag(tag_id, new_tag, db)
    if tag is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=messages.NOT_FOUND)
    return tag


@router.delete('/{tag_id}', dependencies=[Depends(allowed_roles.admin)],
               status_code=status.HTTP_204_NO_CONTENT, description=messages.FOR_ADMIN)
async def delete_tag(tag_id: int, db: Session = Depends(get_db)):
    tag = await TagServices.remove_tag(tag_id, db)
    if tag is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=messages.NOT_FOUND)
    return tag


@router.post('/add_tag_to_image/{image_id}', response_model=TagResponse, status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(allowed_roles.all_users)], description=messages.FOR_ALL)
async def add_tag_to_image(image_id: int, tag: str, db: Session = Depends(get_db)):
    result = await TagServices.add_tag_to_image(image_id, tag, db)
    if result is None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=messages.LIMIT_EXCEEDED)
    return result


# -------------------------------------COMMENTS-------------------------------------
@router.get("/image_comments/", status_code=status.HTTP_200_OK,
            response_model=List[CommentResponse],
            dependencies=[Depends(allowed_roles.all_users)],
            description=messages.FOR_ALL)
async def read_comments(image_id: int, limit: int = Query(10, le=100),
                        offset: int = 0, db: Session = Depends(get_db)):

    comments = await CommentServices.get_comments(image_id, limit, offset, db)
    if not comments:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=messages.NOT_FOUND)
    return comments


@router.post("/comment/", response_model=CommentResponse, status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(allowed_roles.all_users)], description=messages.FOR_ALL)
async def create_comment(body: CommentModel,
                         current_user: User = Depends(auth_user.get_current_user),
                         db: Session = Depends(get_db)):
    comment = await CommentServices.create_comment(body, current_user, db)
    if not comment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=messages.SOMETHING_WRONG)
    return comment


@router.put("/{comment_id}/", response_model=CommentResponse, status_code=status.HTTP_200_OK,
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


@router.delete("/{comment_id}", status_code=status.HTTP_204_NO_CONTENT,
               dependencies=[Depends(allowed_roles.admin)],
               description=messages.FOR_ADMIN)
async def delete_comment(comment_id: int, db: Session = Depends(get_db)):

    comment = CommentServices.delete_comment(comment_id, db)
    if not comment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=messages.NOT_FOUND)
    return comment


# -----------------------------------CLOUD_SERVICES----------------------------------response_model=ImageUploadResponse,
@router.post("/transform/", status_code=status.HTTP_200_OK,
             dependencies=[Depends(allowed_roles.all_users)], description=messages.FOR_ALL)
async def transform_image(body: ImageUploadModel,
                          db: Session = Depends(get_db)):
    file = await ImageServices.get_image_from_cloud(body.image_id, db)
    if not file:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=messages.NOT_FOUND)
    transform_image_url = await TransformImage.upload_image(file=file,
                                                            folder=body.folder,
                                                            effect=body.effect,
                                                            border=body.border,
                                                            radius=body.radius)
    if not transform_image_url:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=messages.SOMETHING_WRONG)
    await ImageServices.transform_image_to_db(transform_image_url, body.image_id, db)
    return transform_image_url


@router.get("/qrcode/{image_id}", status_code=status.HTTP_201_CREATED,
            response_model=ImageResponse,
            dependencies=[Depends(allowed_roles.all_users)],
            description=messages.FOR_ALL)
async def qr_base64(image_id: int,
                    db: Session = Depends(get_db)):
    image = await ImageServices.get_image(image_id, db)
    if not image.transformed_path:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=messages.NOT_FOUND)
    qr_code = await TransformImage.qrcode_image(image.transformed_path)
    image = await ImageServices.add_qrcode_to_db(image_id, qr_code, db)
    return image
