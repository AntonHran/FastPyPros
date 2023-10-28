from typing import List

from fastapi import Depends, HTTPException, APIRouter, status, UploadFile
from sqlalchemy.orm import Session

from src.database.connection import get_db
from src.repositories.images import ImageServices
from src.repositories.users import AuthServices
from src.database.models import User, UserRole
from src.services.auth import auth_user
from src.schemes.images import ImageResponse
from src.schemes.images import ImageUploadModel
from src.services.cloud_services import TransformImage
from src.conf import allowed_roles
from src.conf import messages


router = APIRouter(prefix="/images", tags=["images"])


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
async def get_image(image_id: int,
                    current_user: User = Depends(auth_user.get_current_user),
                    db: Session = Depends(get_db)):
    baned_access = await AuthServices.check_ban_list(current_user.id, db)
    if baned_access:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=messages.BAN)
    result = await ImageServices.get_image(image_id, db)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=messages.NOT_FOUND)
    return result


@router.get('/', response_model=List[ImageResponse],
            status_code=status.HTTP_200_OK, dependencies=[Depends(allowed_roles.all_users)],
            description=messages.FOR_ALL)
async def get_images(current_user: User = Depends(auth_user.get_current_user), db: Session = Depends(get_db)):
    baned_access = await AuthServices.check_ban_list(current_user.id, db)
    if baned_access:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=messages.BAN)
    images = await ImageServices.get_all_images(current_user.id, db)
    if not images:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=messages.NOT_FOUND)
    return images


@router.patch('/{image_id}', response_model=ImageResponse,
              status_code=status.HTTP_200_OK, dependencies=[Depends(allowed_roles.all_users)],
              description=messages.FOR_ALL)
async def update_description(image_id: int, description: str,
                             current_user: User = Depends(auth_user.get_current_user),
                             db: Session = Depends(get_db)):
    user_image = await ImageServices.check_image_owner(image_id, current_user, db)
    print(current_user.roles)
    if not user_image and current_user.roles == UserRole.admin:
        return await ImageServices.update_description(image_id, description, db)
    if not user_image and current_user.roles != UserRole.admin:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=messages.NOT_YOUR_IMAGE)
    image = await ImageServices.update_description(image_id, description, db)
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


@router.post("/{image_id}/transform/", status_code=status.HTTP_200_OK,
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


@router.post("/{image_id}/qrcode/", status_code=status.HTTP_201_CREATED,
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
