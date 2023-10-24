from typing import List

from fastapi import APIRouter, Depends, Path, status, Query
from fastapi.exceptions import HTTPException
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session

from src.database.connection import get_db
from src.repositories.users import UserServices
from src.schemes.users import UserResponse
from src.conf.allowed_roles import *
from src.conf import messages


router = APIRouter(prefix="/users", tags=["users"])
security = HTTPBearer()


@router.get("/", response_model=List[UserResponse], status_code=status.HTTP_200_OK,
            dependencies=[Depends(moderators_admin)],
            description=messages.FOR_MODERATORS_ADMIN)
async def get_users(limit: int = Query(10, le=100),
                    offset: int = 0,
                    db: Session = Depends(get_db)):
    """
    The get_users function returns a list of users.

    :param limit: int: Limit the number of users returned; le: Limit the maximum
    number of users that can be returned
    :param offset: int: Skip a number of records
    :param db: Session: Pass the database session to the function
    :return: A list of users
    :doc-author: Trelent
    """
    return await UserServices.get_all_users(limit, offset, db)


@router.get("/{user_id}", response_model=UserResponse, status_code=status.HTTP_200_OK,
            dependencies=[Depends(moderators_admin)],
            description=messages.FOR_MODERATORS_ADMIN)
async def get_user(user_id: int = Path(ge=1), db: Session = Depends(get_db)):

    """
    The get_user function returns a user by id.
        Args:
            user_id (int): The id of the user to return.
            db (Session, optional): SQLAlchemy Session. Defaults to Depends(get_db).

    :param user_id: int: Specify the type of data that is expected to be passed in
    :param db: Session: Pass the database session to the function
    :return: A user object
    :doc-author: Trelent
    """
    return await UserServices.get_user_by_id(user_id, db)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT,
               dependencies=[Depends(admin)],
               description=messages.FOR_ADMIN)
async def remove_user(user_id: int = Path(ge=1),
                      db: Session = Depends(get_db)):

    """
    The remove_user function removes a user from the database.

    :param user_id: int: Specify the user id of the user to be deleted
    :param db: Session: Pass the database session to the repository function
    :return: The user that was removed
    :doc-author: Trelent
    """
    user = await UserServices.remove_user(user_id, db)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=messages.NOT_FOUND)
    return user


@router.post("/{user_id}", status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(admin)], description=messages.FOR_ADMIN)
async def ban(user_id: int, reason: str, db: Session = Depends(get_db)):

    user = await UserServices.add_to_ban_list(user_id, reason, db)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=messages.NOT_FOUND)
    return user


@router.get("/search/", dependencies=[Depends(moderators_admin)], status_code=status.HTTP_200_OK,
            response_model=List[UserResponse],
            description=messages.FOR_MODERATORS_ADMIN)
async def search_users(filter_by: str, db: Session = Depends(get_db)):
    users = await UserServices.search(filter_by, db)
    if not users:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=messages.NOT_FOUND)
    return users
