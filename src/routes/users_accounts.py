from fastapi import APIRouter, Depends, UploadFile, File, status
from fastapi.exceptions import HTTPException
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session

from src.database.connection import get_db
from src.database.models import User
from src.repositories.users import AccountServices
from src.services.auth import auth_user
from src.schemes.account import AccountResponse, AccountModel
from src.services.cloud_image import CloudImage
from src.conf.allowed_roles import *
from src.conf import messages


router = APIRouter(prefix="/users", tags=["users"])
security = HTTPBearer()


@router.get("/accounts/{username}/", response_model=AccountResponse, status_code=status.HTTP_200_OK,
            dependencies=[Depends(all_users)],
            description=messages.FOR_ALL)
async def read_users_me(username: str,
                        db: Session = Depends(get_db)):
    """
    The read_users_me function will return the user object for a given username.

    :param username: str: Specify the username of the user we want to get
    :param db: Session: Pass the database session to the function
    :return: The user object for the given username
    :doc-author: Trelent
    """
    account = await AccountServices.get_account_by_username(username, db)
    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=messages.ACCOUNT_NOT_FOUND)
    return account


@router.post("/accounts/", response_model=AccountResponse, status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(all_users)],
             description=messages.FOR_ALL)
async def create_account(body: AccountModel,
                         current_user: User = Depends(auth_user.get_current_user),
                         db: Session = Depends(get_db)):
    """
    The create_account function creates a new account for the user.
        The function takes in an AccountModel object, which contains the following fields:
            - name (str): The name of the account.
            - balance (float): The starting balance of the account.

    :param body: AccountModel: Pass the account model to the function
    :param current_user: User: Get the current user
    :param db: Session: Get the database session
    :return: A new account object
    :doc-author: Trelent
    """
    account = await AccountServices.create_user_account(body, current_user.username, db)
    if not account:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=messages.SOMETHING_WRONG
        )
    return account


@router.patch('/accounts/', response_model=AccountResponse, status_code=status.HTTP_200_OK,
              dependencies=[Depends(only_users)],
              description="For all users")
async def update_account_avatar(file: UploadFile = File(),
                                current_user: User = Depends(auth_user.get_current_user),
                                db: Session = Depends(get_db)):

    public_id = CloudImage.generate_file_name(current_user.username)
    r = CloudImage.upload(file.file, public_id)
    src_url = CloudImage.get_url_for_avatar(public_id, r)
    user_account = await AccountServices.update_avatar(current_user, src_url, db)
    if not user_account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=messages.ACCOUNT_NOT_FOUND
        )
    return user_account


@router.put("/accounts/{username}/", response_model=AccountResponse, status_code=status.HTTP_200_OK,
            dependencies=[Depends(only_users)],
            description=messages.FOR_ALL)
async def update_account(body: AccountModel,
                         username: str,
                         db: Session = Depends(get_db)):
    account = await AccountServices.update_user_account(username, body, db)
    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=messages.ACCOUNT_NOT_FOUND)
    return account


@router.delete("/accounts/", status_code=status.HTTP_204_NO_CONTENT,
               dependencies=[Depends(all_users)],
               description=messages.FOR_ALL)
async def remove_account(current_user: User = Depends(auth_user.get_current_user),
                         db: Session = Depends(get_db)):
    account = await AccountServices.remove_account(current_user.username, db)
    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=messages.ACCOUNT_NOT_FOUND)
    return account
