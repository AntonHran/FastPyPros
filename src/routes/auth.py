from fastapi import Depends, HTTPException, status, APIRouter, Security, BackgroundTasks, Request
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
    OAuth2PasswordRequestForm,
)
from sqlalchemy.orm import Session
# from fastapi_limiter.depends import RateLimiter

from src.database.connection import get_db
from src.schemes.users import UserModel, UserResponse, TokenModel
from src.schemes.email import RequestEmail, PasswordResetModel
from src.services.auth import auth_token, auth_password, auth_user
from src.services.email import send_email
from src.database.models import User
from src.repositories.users import AuthServices, UserServices
from src.conf import messages


router = APIRouter(prefix="/auth", tags=["auth"])
security = HTTPBearer()


@router.post("/signup", response_model=UserResponse,
             # dependencies=[Depends(RateLimiter(times=3, seconds=60))],
             status_code=status.HTTP_201_CREATED,
             description=messages.FOR_ALL)
async def signup(body: UserModel, background_task: BackgroundTasks, request: Request,
                 db: Session = Depends(get_db)):
    """
    The signup function creates a new user in the database.
        It takes in a UserModel object, which is validated by pydantic.
        The password is hashed using the auth_password module and then stored in the database.

    :param body: UserModel: Get the request body
    :param background_task: BackgroundTasks: Add a task to the background queue
    :param request: Request: Get the base_url of the server
    :param db: Session: Get the database session
    :return: A user object, which is then serialized and returned as a response
    :doc-author: Trelent
    """
    exist_user = await AuthServices.get_user_by_email(body.email, db)
    if exist_user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=messages.ACCOUNT_EXISTS)
    body.password = auth_password.get_password_hash(body.password)
    new_user = await UserServices.create_user(body, db)
    background_task.add_task(send_email, new_user.email, new_user.username, str(request.base_url))
    return new_user


@router.post("/login", status_code=status.HTTP_201_CREATED, response_model=TokenModel)
async def login(body: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    The login function is used to authenticate a user.
        It takes the email and password of the user, verifies them against
        those stored in the database, and returns an access token if they match.

    :param body: OAuth2PasswordRequestForm: Get the username and password from the request body
    :param db: Session: Get a database session
    :return: An access token and a refresh token
    :doc-author: Trelent
    """
    user = await AuthServices.get_user_by_email(body.username, db)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=messages.INVALID_EMAIL)
    if not user.confirmed:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=messages.EMAIL_NOT_CONFIRMED)
    if not auth_password.verify_password(body.password, user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=messages.INVALID_PASSWORD)
    baned_access = await AuthServices.check_ban_list(user.id, db)
    if baned_access:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=messages.BAN)
    # generate JWT
    access_token = await auth_token.create_access_token(data={"sub": user.email})
    refresh_token_ = await auth_token.create_refresh_token(data={"sub": user.email})
    await AuthServices.update_token(user, access_token, refresh_token_, db)
    return {"access_token": access_token,
            "refresh_token": refresh_token_,
            "token_type": messages.TOKEN_TYPE}


@router.get("/refresh_token", status_code=status.HTTP_200_OK, response_model=TokenModel)
async def refresh_token(credentials: HTTPAuthorizationCredentials = Security(security),
                        db: Session = Depends(get_db)):
    """
    The refresh_token function is used to refresh the access token.
        The function will check if the user has a valid refresh token and then create
        a new access token for them. If they do not have a valid refresh_token,
        it will return an error.

    :param credentials: HTTPAuthorizationCredentials: Get the credentials from the
    request header
    :param db: Session: Pass the database session to the function
    :return: A new access token and refresh token
    :doc-author: Trelent
    """
    token = credentials.credentials
    email = await auth_token.decode_refresh_token(token)
    user = await AuthServices.get_user_by_email(email, db)
    if user.refresh_token != token:
        await AuthServices.update_token(user, None, None, db)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=messages.COULD_NOT_VALIDATE_CREDENTIALS)

    access_token = await auth_token.create_access_token(data={"sub": email})
    refresh_token_ = await auth_token.create_refresh_token(data={"sub": user.email})
    await AuthServices.update_token(user, access_token, refresh_token_, db)
    return {
        "access_token": access_token,
        "refresh_token": refresh_token_,
        "token_type": messages.TOKEN_TYPE,
    }


@router.get('/confirmed_email/{token}', status_code=status.HTTP_200_OK, )
async def confirmed_email(token: str, db: Session = Depends(get_db)):
    """
    The confirmed_email function is used to confirm a user's email address.
    It takes the token from the URL and uses it to get the user's email address.
    Then, it checks if that user exists in our database, and if they do not exist,
    we return an error message. If they do exist but their account has already been
    confirmed, we return a message saying so. If neither of these are true
    (i.e., the account exists and hasn't been confirmed yet), then we call
    repository_users' confirm_email function with that email address as its argument.

    :param token: str: Get the email from the token
    :param db: Session: Get the database session
    :return: A dictionary with a message
    :doc-author: Trelent"""
    
    email = auth_token.get_email_from_token(token)
    user = await AuthServices.get_user_by_email(email, db)
    if user is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=messages.VERIFICATION_ERROR)
    if user.confirmed:
        return {messages.MESSAGE: messages.EMAIL_ALREADY_CONFIRMED}
    await AuthServices.confirm_email(email, db)
    return {messages.MESSAGE: messages.EMAIL_CONFIRMED}


@router.post('/request_email', status_code=status.HTTP_201_CREATED, )
async def request_email(body: RequestEmail, background_tasks: BackgroundTasks,
                        request: Request,  # !!!
                        db: Session = Depends(get_db)):
    """
    The request_email function is used to send an email the user with a link
    that will confirm their email address. The function takes in a RequestEmail
    object, which contains the user's email address. The function then checks if
    the user exists and if they are already confirmed. If they do exist and are
    not yet confirmed, it sends them an email using the send_email() function
    from utils/mailgun_api.

    :param body: RequestEmail: Receive the email from the user
    :param background_tasks: BackgroundTasks: Add a task to the background tasks queue
    :param request: Request: Get the base url of the request
    :param db: Session: Access the database
    :return: A dictionary with a message
    :doc-author: Trelent"""
    
    user = await AuthServices.get_user_by_email(body.email, db)

    if user and user.confirmed:
        return {"message": "Your email is already confirmed"}
    if user:
        background_tasks.add_task(send_email, user.email, user.username, str(request.base_url))
    return {"message": "Check your email for confirmation."}


@router.post('/reset_password')
async def reset_password(body: PasswordResetModel, db: Session = Depends(get_db)):
    """
    The reset_password function is used to reset a user's password.
        It takes in the email of the user and their new password, which must be
        confirmed by entering it again. If the email does not exist or if the
        passwords do not match, an error will be thrown.

    :param body: PasswordResetModel: Get the data from the request body
    :param db: Session: Get the database session
    :return: A dictionary with the message &quot;password reset complete!&quot;
    :doc-author: Trelent"""
    
    user = await AuthServices.get_user_by_email(body.email, db)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=messages.INVALID_EMAIL)
    if body.new_password != body.confirm_password:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail=messages.PASSWORDS_NOT_EQUAL)
    new_password = auth_password.get_password_hash(body.new_password)
    await AuthServices.reset_password(user, new_password, db)
    return {"message": messages.RESET_COMPLETE}


@router.post("/logout", status_code=status.HTTP_201_CREATED)
async def logout(
        current_user: User = Depends(auth_user.get_current_user), db: Session = Depends(get_db)
):
    """
    The logout function is used to logout a user.
        It takes in the current_user and db as parameters, which are both optional.
        The current_user parameter is obtained from the auth_user module's get_current_user function,
            which returns an object of type User if there exists a valid token in the request header.

    :param current_user: User: Get the current user's information
    :param db: Session: Get the database session
    :return: A message
    :doc-author: Trelent
    """
    await UserServices.add_to_ban_list(current_user.id, reason="logout", db=db)
    return {"message": messages.LOGOUT}
