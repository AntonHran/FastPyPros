from sqlalchemy.orm import Session
from libgravatar import Gravatar

from src.database.models import User, Account
from src.schemes.users import UserModel
from src.schemes.account import AccountModel


async def get_user_by_email(email: str, db: Session) -> User | None:
    """
    The get_user_by_email function takes in an email and a database session,
    and returns the user with that email if it exists. If no such user exists,
    it returns None.

    :param email: str: Pass the email address of a user to the function
    :param db: Session: Pass the database session to the function
    :return: A user object if the user exists, or none if it doesn't
    :doc-author: Trelent
    """
    return db.query(User).filter_by(email=email).first()


async def create_user(body: UserModel, db: Session):
    """
    The create_user function creates a new user in the database.
        Args:
            body (UserModel): The UserModel object to be created.
            db (Session): The SQLAlchemy session object used for querying the database.

    :param body: UserModel: Pass the user data to the function
    :param db: Session: Pass the database session to the function
    :return: A user object
    :doc-author: Trelent
    """
    new_user = User(**body.model_dump())
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


async def create_user_account(body: AccountModel, username: str, db: Session):
    """
    The create_user function creates a new user in the database.
        Args:
            body (UserModel): The UserModel object to be created.
            db (Session): The SQLAlchemy session object used for querying the database.

    :param body: UserModel: Pass the user data to the function
    :param username: Create relation in table
    :param db: Session: Pass the database session to the function
    :return: A user object
    :doc-author: Trelent
    """
    gr = Gravatar(body.email)
    avatar = gr.get_image()
    new_account = Account(**body.model_dump(), username=username, avatar=avatar)
    db.add(new_account)
    db.commit()
    db.refresh(new_account)
    return new_account


async def update_token(user: User, refresh_token, db: Session):
    """
    The update_token function updates the refresh token for a user in the database.
        Args:
            user (User): The User object to update.
            refresh_token (str): The new refresh token to store in the database.
            db (Session): A connection to our Postgres database.

    :param user: User: Identify the user that is being updated
    :param refresh_token: Update the user's refresh_token in the database
    :param db: Session: Pass the database session to the function
    :return: A user object
    :doc-author: Trelent
    """
    user.refresh_token = refresh_token
    db.commit()


async def confirm_email(email: str, db: Session):
    """
    The confirm_email function takes an email and a database session as arguments.
    It then uses the get_user_by_email function to retrieve the user with that email address,
    and sets their confirmed field to True. It then commits this change to the database.

    :param email: str: Get the email of the user
    :param db: Session: Access the database
    :return: Nothing, so the return type is none
    :doc-author: Trelent
    """
    user = await get_user_by_email(email, db)
    user.confirmed = True
    db.commit()


async def reset_password(user: User, new_password: str, db: Session):
    """
    The reset_password function takes a user and new_password as arguments,
    and updates the password of the user in the database.


    :param user: User: Get the user object from the database
    :param new_password: str: Pass in the new password
    :param db: Session: Access the database
    :return: Nothing
    :doc-author: Trelent
    """
    user.password = new_password
    db.commit()


async def update_avatar(email: str, url: str, db: Session):
    """
    The update_avatar function updates the avatar of a user.

    :param email: str: Specify the email of the user that is being updated
    :param url: str: Update the avatar of a user
    :param db: Session: Access the database
    :return: The user object
    :doc-author: Trelent
    """
    user = await get_user_by_email(email, db)
    user.avatar = url
    db.commit()
    return user


async def get_all_users(limit: int, offset: int, db: Session):

    """
    The get_all_users function returns a list of all users in the database.

    :param limit: int: Limit the number of results returned
    :param offset: int: Specify the number of records to skip
    :param db: Session: Pass the database session to the function
    :return: A list of all the users in the database
    :doc-author: Trelent
    """
    return db.query(User).limit(limit).offset(offset).all()


async def get_user_by_id(user_id: int, db: Session):

    """
    The get_user_by_id function takes in a user_id and db Session object,
    and returns the User object with that id. If no such user exists, it returns None.

    :param user_id: int: Specify the type of parameter that is expected
    :param db: Session: Pass the database session to the function
    :return: The user with the given id
    :doc-author: Trelent
    """
    return db.query(User).filter_by(id=user_id).first()


async def get_account_by_username(username: str, db: Session):

    """
    The get_user_by_username function takes in a username and returns the user object associated with that username.
        If no such user exists, it returns None.

    :param username: str: Specify the username of the user we want to get from our database
    :param db: Session: Pass the database session to the function
    :return: The first user with the username specified in the function call
    :doc-author: Trelent
    """
    return db.query(Account).filter_by(username=username).first()


async def remove_user(user_id: int, db: Session):

    """
    The remove_user function removes a user from the database.
        Args:
            user_id (int): The id of the user to be removed.
            db (Session): A connection to the database.

    :param user_id: int: Specify the user_id of the user to be deleted
    :param db: Session: Pass the database session to the function
    :return: The user that was deleted
    :doc-author: Trelent
    """
    user = await get_user_by_id(user_id, db)
    if user:
        db.delete(user)
        db.commit()
    return user


async def invalidate_tokens(user: User, db: Session):  # required to be done!!!!
    """
    Invalidate a user's access and refresh tokens.

    :param user: User: The user for whom to invalidate tokens
    :param db: Session: The database session
    """
    user.refresh_token = "invalid"
    db.commit()
