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

# ---------------images-----------------------------
@router.post('/upload_images/',status_code=status.HTTP_201_CREATED, response_model=ResponeUploadFile, dependencies=[Depends(allowed_crud_images)],
             description=FOR_ALL)
async def upload_file(file: UploadFile, description: str, db: Session = Depends(get_db), current_user: User = Depends(auth_user.get_current_user)):
    
    result = await repository_images.upload_file(file, description, db, current_user)
    if result is None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='Wrong data.')
    
    return result

@router.get('/get_images', status_code=status.HTTP_200_OK, response_model=List[ResponeImageModel], dependencies=[Depends(allowed_crud_images)],
             description=FOR_ALL)
async def get_images(skip: int = 0, limit: int = 10, db: Session = Depends(get_db), current_user: User = Depends(auth_user.get_current_user)):

    result = await repository_images.get_images(skip, limit, db, current_user)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Images not found.')
    
    return result

@router.get('/get_image_by_id/{image_id}', status_code=status.HTTP_200_OK, response_model=ResponeImageModel, dependencies=[Depends(allowed_crud_images)],
             description=FOR_ALL)
async def get_image_by_id(image_id: int, db: Session = Depends(get_db), current_user: User = Depends(auth_user.get_current_user)):

    result = await repository_images.get_image_by_id(image_id, db, current_user)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Image not found.')
    
    return result

@router.put('/update_description/{image_id}', status_code=status.HTTP_200_OK, response_model=UpdateImageModel, dependencies=[Depends(allowed_crud_images)],
             description=FOR_ALL)
async def update_description(image_id: int, description: str, db: Session = Depends(get_db), current_user: User = Depends(auth_user.get_current_user)):

    result = await repository_images.update_description(image_id, description, db, current_user)

    if result is None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='Wrong data.')
    
    return result

@router.delete('/delete_images/{image_id}', status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(allowed_crud_images)],
             description=FOR_ALL)
async def delete_image(image_id: int, db: Session = Depends(get_db), current_user: User = Depends(auth_user.get_current_user)):
    
    result = await repository_images.delete_image(image_id, db, current_user)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Image not found.')
    
    return result



# ----------- tags ----------------
@router.get('/get_tags')
async def get_tags(skip:int = 0, limit: int = 5, db: Session = Depends(get_db)):
    result = await repository_tags.get_tags(skip, limit, db)
    if result is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Some problem.')
    
    return result

@router.get('/get_tag/{tag}')
async def get_tag(tag: str, db: Session = Depends(get_db)):
    result = await repository_tags.get_tag(tag, db)
    if result is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='No tag in db.')
    
    return result

@router.post('/add_tag_to_db', response_model=ResponeTagModel)
async def add_tag_to_db(tags: str, db: Session = Depends(get_db)):    
    tags = tags.rstrip(' ').split(' ')
    if len(tags) > 5:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='To many tags, max 5 tags.')
    
    result = await repository_tags.add_tag_to_db(tags, db)
    return result

@router.put('/add_tag_to_image/{image_id}', response_model=ResponsTagToImageModel)
async def add_tag_to_image(image_id: int, tags: str, db: Session = Depends(get_db)):
    tags = tags.rstrip(' ').split(' ')
    if len(tags) > 5:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='To many tags, max 5 tags.')
        
    result = await repository_tags.add_tag_to_image(image_id, tags, db)
    return result

