from typing import List

from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile
from sqlalchemy.orm import Session

from src.database.connection import get_db
from src.database.models import User
from src.repositories import images as repository_images
from src.repositories import tags as repository_tags
from src.schemes.images import UpdateImageModel, ResponeImageModel, ResponeUploadFile
from src.schemes.tags import ResponeTagModel, ResponsTagToImageModel
from src.services.auth import auth_user
from src.services.roles import RoleAccess, Role
from src.conf.messages import FOR_ALL

allowed_crud_images = RoleAccess([Role.admin, Role.moderator, Role.user])
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
    """
    Retrieves image ratings with optional pagination parameters.

    :param limit: The maximum number of ratings to return (default 10, max 100).
    :type limit: int
    :param offset: The number of ratings to skip.
    :type offset: int
    :param image_id: The ID of the image for which ratings are retrieved.
    :type image_id: int
    :param db: Database session object.
    :type db: Session

    :return: A list of image ratings.
    :rtype: List[RatingResponse]

    :raises HTTPException: If an error occurs.

    HTTP Response:
    - 404 Not Found: No ratings were found for the specified image.

    - 200 OK: The list of image ratings.
    """
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
    """
    Rates an image and stores the user's rating.

    :param body: The rating details, including image ID and rating value.
    :type body: RatingModel
    :param current_user: The current user rating the image.
    :type current_user: User
    :param db: Database session object.
    :type db: Session

    :return: The user's rating for the image.
    :rtype: RatingResponse

    :raises HTTPException: If an error occurs.

    HTTP Response:
    - 409 Conflict: The user is attempting to rate their own image.

    - 409 Conflict: The user is attempting to rate the same image multiple times.

    - 201 Created: The user's rating for the image.
    """
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
    """
    Removes a user's rating for a specific image.

    :param image_id: The ID of the image for which the rating is removed.
    :type image_id: int
    :param user_id: The ID of the user whose rating is being removed.
    :type user_id: int
    :param db: Database session object.
    :type db: Session

    :return: None

    :raises HTTPException: If an error occurs.

    HTTP Response:
    - 404 Not Found: The specified rating was not found.

    - 204 No Content: The rating has been successfully removed.
    """
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
    """
    Searches for images based on a keyword and optional filters.

    :param keyword: The keyword to search for in images.
    :type keyword: str
    :param filter_by: Optional filter for refining the search.
    :type filter_by: str
    :param db: Database session object.
    :type db: Session

    :return: A list of images matching the search criteria.
    :rtype: List[ImageResponse]

    :raises HTTPException: If an error occurs.

    HTTP Response:
    - 404 Not Found: No images matching the search criteria were found.

    - 200 OK: The search results, a list of images.
    """    
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
    """
    Uploads an image and stores it in the database.

    :param file: The uploaded image file.
    :type file: UploadFile
    :param description: Description of the image.
    :type description: str
    :param current_user: The current user.
    :type current_user: User
    :param db: Database session object.
    :type db: Session

    :return: The response with the public identifier of the uploaded image.
    :rtype: ImageResponse

    :raises HTTPException: If an error occurs.

    HTTP Response:
    - 201 Created: The image was successfully uploaded.
    - 409 Conflict: Occurs if the data provided is incorrect.
    """
    image = await ImageServices.upload_file(file, description, current_user, db)
    if image is None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=messages.SOMETHING_WRONG)
    return image


@router.get('/{image_id}', response_model=ImageResponse,
            status_code=status.HTTP_200_OK, dependencies=[Depends(allowed_roles.all_users)],
            description=messages.FOR_ALL)
async def get_image(image_id: int, db: Session = Depends(get_db)):
    """
    Retrieves an image by its identifier.

    :param image_id: The image identifier.
    :type image_id: int
    :param db: Database session object.
    :type db: Session

    :return: The image.
    :rtype: ImageResponse

    :raises HTTPException: If an error occurs.

    HTTP Response:
    - 200 OK: The image was successfully retrieved.
    - 404 Not Found: The image was not found.
    """
    result = await ImageServices.get_image(image_id, db)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Image not found.')
    
    return result


@router.get('/', response_model=List[ImageResponse],
            status_code=status.HTTP_200_OK, dependencies=[Depends(allowed_roles.all_users)],
            description=messages.FOR_ALL)
async def get_images(current_user: User = Depends(auth_user.get_current_user), db: Session = Depends(get_db)):
    """
    Retrieves a list of images with specified pagination parameters.

    :param current_user: The current user.
    :type current_user: User
    :param db: Database session object.
    :type db: Session

    :return: The list of images.
    :rtype: List[ImageResponse]

    :raises HTTPException: If an error occurs.

    HTTP Response:
    - 200 OK: Images were successfully retrieved.
    - 404 Not Found: No images found.
    """
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
    """
    Updates the description of an image by its identifier.

    :param image_id: The image identifier.
    :type image_id: int
    :param description: The new description of the image.
    :type description: str
    :param current_user: The current user.
    :type current_user: User
    :param db: Database session object.
    :type db: Session

    :return: The updated image.
    :rtype: ImageResponse

    :raises HTTPException: If an error occurs.

    HTTP Response:
    - 200 OK: The description of the image was successfully updated.
    - 404 Not Found: The image was not found.
    - 409 Conflict: The image does not belong to the user.
    """
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
    """
    Deletes an image by its identifier.

    :param image_id: The image identifier.
    :type image_id: int
    :param current_user: The current user.
    :type current_user: User
    :param db: Database session object.
    :type db: Session

    :return: None

    :raises HTTPException: If an error occurs.

    HTTP Response:
    - 204 No Content: The image was successfully deleted.
    - 409 Conflict: The image does not belong to the user, or the user does not have permission to delete it.
    """
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
    """
    Retrieves a list of tags with specified pagination parameters.

    :param limit: The maximum number of tags to return (default: 10, max: 50).
    :type limit: int
    :param offset: The number of tags to skip.
    :type offset: int
    :param db: Database session object.
    :type db: Session

    :return: A list of tags.
    :rtype: List[TagResponse]

    :raises HTTPException: If an error occurs.

    HTTP Response:
    - 200 OK: Tags were successfully retrieved.
    - 404 Not Found: No tags found.
    """ 
    tags = await TagServices.get_tags(limit, offset, db)
    if not tags:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=messages.NOT_FOUND)
    return tags


@router.put('/{tag_id}', response_model=TagResponse, dependencies=[Depends(allowed_roles.moderators_admin)],
            status_code=status.HTTP_200_OK, description=messages.FOR_MODERATORS_ADMIN)
async def update_tag(tag_id: int, new_tag: str, db: Session = Depends(get_db)):
    """
    Updates a tag by its identifier.

    :param tag_id: The tag identifier.
    :type tag_id: int
    :param new_tag: The new tag content.
    :type new_tag: str
    :param db: Database session object.
    :type db: Session

    :return: The updated tag.
    :rtype: TagResponse

    :raises HTTPException: If an error occurs.

    HTTP Response:
    - 200 OK: The tag was successfully updated.
    - 404 Not Found: The tag was not found.
    """ 
    tag = await TagServices.update_tag(tag_id, new_tag, db)
    if tag is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=messages.NOT_FOUND)
    return tag


@router.delete('/{tag_id}', dependencies=[Depends(allowed_roles.admin)],
               status_code=status.HTTP_204_NO_CONTENT, description=messages.FOR_ADMIN)
async def delete_tag(tag_id: int, db: Session = Depends(get_db)):
    """
    Deletes a tag by its identifier.

    :param tag_id: The tag identifier.
    :type tag_id: int
    :param db: Database session object.
    :type db: Session

    :return: None

    :raises HTTPException: If an error occurs.

    HTTP Response:
    - 204 No Content: The tag was successfully deleted.
    - 404 Not Found: The tag was not found.
    """ 
    tag = await TagServices.remove_tag(tag_id, db)
    if tag is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=messages.NOT_FOUND)
    return tag


@router.post('/add_tag_to_image/{image_id}', response_model=TagResponse, status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(allowed_roles.all_users)], description=messages.FOR_ALL)
async def add_tag_to_image(image_id: int, tag: str, db: Session = Depends(get_db)):
    """
    Adds a tag to an image.

    :param image_id: The identifier of the image.
    :type image_id: int
    :param tag: The tag to be added to the image.
    :type tag: str
    :param db: Database session object.
    :type db: Session

    :return: The result of adding the tag to the image.
    :rtype: TagResponse

    :raises HTTPException: If an error occurs.

    HTTP Response:
    - 409 Conflict: The tag limit is exceeded.
    """     
    result = await TagServices.add_tag_to_image(image_id, tag, db)
    if result is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='No tag in db.')
    
    return result


# -------------------------------------COMMENTS-------------------------------------
@router.get("/image_comments/", status_code=status.HTTP_200_OK,
            response_model=List[CommentResponse],
            dependencies=[Depends(allowed_roles.all_users)],
            description=messages.FOR_ALL)
async def read_comments(image_id: int, limit: int = Query(10, le=100),
                        offset: int = 0, db: Session = Depends(get_db)):
    """
    Retrieves comments for a specific image with specified pagination parameters.

    :param image_id: The identifier of the image.
    :type image_id: int
    :param limit: The maximum number of comments to return.
    :type limit: int
    :param offset: The number of comments to skip.
    :type offset: int
    :param db: Database session object.
    :type db: Session

    :return: A list of comments.
    :rtype: List[CommentResponse]

    :raises HTTPException: If an error occurs.

    HTTP Response:
    - 404 Not Found: No comments found for the image.
    """
    comments = await CommentServices.get_comments(image_id, limit, offset, db)
    if not comments:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=messages.NOT_FOUND)
    return comments


@router.post("/comment/", response_model=CommentResponse, status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(allowed_roles.all_users)], description=messages.FOR_ALL)
async def create_comment(body: CommentModel,
                         current_user: User = Depends(auth_user.get_current_user),
                         db: Session = Depends(get_db)):
    """
    Creates a new comment for an image.

    :param body: The comment data to be created.
    :type body: CommentModel
    :param current_user: The current user creating the comment.
    :type current_user: User
    :param db: Database session object.
    :type db: Session

    :return: The created comment.
    :rtype: CommentResponse

    :raises HTTPException: If an error occurs.

    HTTP Response:
    - 404 Not Found: An error occurred while creating the comment.

    - 403 Forbidden: The user is not allowed to create this comment.
    """
    comment = await CommentServices.create_comment(body, current_user, db)
    if not comment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=messages.SOMETHING_WRONG)
    return comment


@router.put("/{comment_id}/", response_model=CommentResponse, status_code=status.HTTP_200_OK,
            dependencies=[Depends(allowed_roles.all_users)], description=messages.FOR_ALL)
async def update_comment(comment_id: int, new_comment: str,
                         current_user: User = Depends(auth_user.get_current_user),
                         db: Session = Depends(get_db)):
    """
    Updates an existing comment.

    :param comment_id: The identifier of the comment to be updated.
    :type comment_id: int
    :param new_comment: The updated comment content.
    :type new_comment: str
    :param current_user: The current user making the update.
    :type current_user: User
    :param db: Database session object.
    :type db: Session

    :return: The updated comment.
    :rtype: CommentResponse

    :raises HTTPException: If an error occurs.

    HTTP Response:
    - 404 Not Found: The specified comment was not found.

    - 403 Forbidden: The user is not allowed to update this comment.
    """
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
    """
    Deletes an existing comment.

    :param comment_id: The identifier of the comment to be deleted.
    :type comment_id: int
    :param db: Database session object.
    :type db: Session

    :raises HTTPException: If an error occurs.

    HTTP Response:
    - 404 Not Found: The specified comment was not found.

    - 403 Forbidden: The user is not allowed to delete this comment.

    - 204 No Content: The comment has been successfully deleted.
    """
    comment = CommentServices.delete_comment(comment_id, db)
    if not comment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=messages.NOT_FOUND)
    return comment


# -----------------------------------CLOUD_SERVICES----------------------------------response_model=ImageUploadResponse,
@router.post("/transform/", status_code=status.HTTP_200_OK,
             dependencies=[Depends(allowed_roles.all_users)], description=messages.FOR_ALL)
async def transform_image(body: ImageUploadModel,
                          db: Session = Depends(get_db)):
    """
    Transforms an image based on provided parameters.

    :param body: The image transformation data.
    :type body: ImageUploadModel
    :param db: Database session object.
    :type db: Session

    :return: The URL of the transformed image.
    :rtype: str

    :raises HTTPException: If an error occurs.

    HTTP Response:
    - 404 Not Found: The specified image was not found.

    - 409 Conflict: An error occurred during the transformation.

    - 200 OK: The image has been successfully transformed.
    """
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
    """
    Generates a QR code for an image and adds it to the image.

    :param image_id: The identifier of the image to add the QR code.
    :type image_id: int
    :param db: Database session object.
    :type db: Session

    :return: The updated image with the QR code.
    :rtype: ImageResponse

    :raises HTTPException: If an error occurs.

    HTTP Response:
    - 404 Not Found: The specified image was not found.

    - 404 Not Found: The image's transformed version does not exist.

    - 201 Created: The QR code has been successfully added to the image.
    """
    image = await ImageServices.get_image(image_id, db)
    if not image.transformed_path:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=messages.NOT_FOUND)
    qr_code = await TransformImage.qrcode_image(image.transformed_path)
    image = await ImageServices.add_qrcode_to_db(image_id, qr_code, db)
    return image
