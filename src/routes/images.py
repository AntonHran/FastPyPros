from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile

from sqlalchemy.orm import Session

from src.database.connection import get_db
from src.repositories import images as repository_images
from src.repositories import tags as repository_tags
from src.repositories import comments as repository_comments
from src.schemes.images import UpdateImageModel, ImageModel, ResponeUploadFile
from src.schemes.tags import ResponeTagModel, ResponsTagToImageModel
from src.database.models import TagToImage



router = APIRouter(prefix="/images", tags=["images"])

# ---------------images-----------------------------
@router.post('/upload_images/', response_model=ResponeUploadFile)
async def upload_file(file: UploadFile, description: str, db: Session = Depends(get_db)):
    
    result = await repository_images.upload_file(file, description, db)
    if result is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Some problem.')
    
    return result

@router.get('/get_images/{image_id}', response_model=ImageModel)
async def get_images(image_id: int, db: Session = Depends(get_db)):

    result = await repository_images.get_image_by_id(image_id, db)
    if result is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Some problem.')
    
    return result

@router.put('/update_description/{image_id}', response_model=UpdateImageModel)
async def update_description(image_id: int, description: str, db: Session = Depends(get_db)):

    result = await repository_images.update_description(image_id, description, db)

    if result is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Some problem.')
    
    return result

@router.delete('/delete_images/{image_id}')
async def delete_image(image_id: int, db: Session = Depends(get_db)):
    
    result = await repository_images.delete_image(image_id, db)
    if result is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Some problem.')
    
    return result


# ----------- tags ----------------
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
    if result is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Some problem.')
    
    return result