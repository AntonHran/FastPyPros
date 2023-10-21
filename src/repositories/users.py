from typing import Type

from sqlalchemy.orm import Session
from fastapi.exceptions import ValidationException
from libgravatar import Gravatar

from src.database.models import User, Account, BanList
from src.schemes.users import UserModel
from src.schemes.account import AccountModel, AccountResponse
from src.services.cloud_image import CloudImage


class AccountServices:
    @staticmethod
    async def create_user_account(body: AccountModel, username: str, db: Session):
        gr = Gravatar(body.email)
        avatar = gr.get_image()
        new_account = Account(**body.model_dump(), username=username, avatar=avatar)
        db.add(new_account)
        db.commit()
        db.refresh(new_account)
        res = await form_response(new_account)
        return res

    @staticmethod
    async def update_user_account(username: str, body: AccountModel, db: Session):
        account_data = {key: value for key, value in body.model_dump().items() if value}
        if account_data:
            db.query(Account).filter(Account.username == username).update(account_data)
            db.commit()
            account = await get_account(username, db)
            res = await form_response(account)
            return res

    @staticmethod
    async def remove_account(username: str, db: Session):
        account = db.query(Account).filter_by(username=username).first()
        if account:
            db.delete(account)
            db.commit()
            res = await form_response(account)
            return res

    @staticmethod
    async def get_account_by_username(username: str, db: Session):
        try:
            account = await get_account(username, db)
            res = await form_response(account)
            return res
        except ValidationException:
            return

    @staticmethod
    async def update_avatar(user: User, url: str, db: Session):
        user_account = await get_account(user.username, db)
        if user_account:
            user_account.avatar = url
            db.commit()
            db.refresh(user_account)
            res = await form_response(user_account)
            return res


async def form_response(account: Type[Account] | Account):
    if account:
        res = AccountResponse.model_validate(account)
        res.images_quantity = account.images_quantity
        return res


async def get_account(username: str, db: Session):
    return db.query(Account).filter_by(username=username).first()


class UserServices:
    @staticmethod
    async def get_all_users(limit: int, offset: int, db: Session):
        return db.query(User).limit(limit).offset(offset).all()

    @staticmethod
    async def get_user_by_id(user_id: int, db: Session):
        return db.query(User).filter_by(id=user_id).first()

    @staticmethod
    async def create_user(body: UserModel, db: Session):
        new_user = User(**body.model_dump())
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user

    @staticmethod
    async def remove_user(user_id: int, db: Session):
        user = db.query(User).filter_by(id=user_id).first()
        if user:
            db.delete(user)
            db.commit()
            CloudImage.remove_folder(user.username)
        return user

    @staticmethod
    async def add_to_ban_list(user_id: int, reason: str, db: Session):
        user = db.query(User).filter_by(id=user_id).first()
        if reason != "logout":
            CloudImage.remove_folder(user.username)
        new_record = BanList(access_token=user.access_token, reason=reason)
        db.add(new_record)
        db.commit()

    @staticmethod
    async def search(filter_by: str, db: Session):
        result = db.query(Account.username).filter(Account.images_quantity != 0).distinct().all()
        users = db.query(User).filter(User.username.in_(result)).order_by(getattr(User, filter_by)).all()
        return users


class AuthServices:
    @staticmethod
    async def check_ban_list(user_id: int, db: Session):
        user = db.query(User).filter_by(id=user_id).first()
        return db.query(BanList).filter_by(access_token=user.access_token).first()

    @staticmethod
    async def get_user_by_email(email: str, db: Session) -> User | None:
        return db.query(User).filter_by(email=email).first()

    @staticmethod
    async def update_token(user: User, access_token: str | None,
                           refresh_token: str | None, db: Session):
        user.refresh_token = refresh_token
        user.access_token = access_token
        db.commit()
        db.refresh(user)

    @staticmethod
    async def confirm_email(email: str, db: Session):
        user = db.query(User).filter_by(email=email).first()
        user.confirmed = True
        db.commit()

    @staticmethod
    async def reset_password(user: User, new_password: str, db: Session):
        user.password = new_password
        db.commit()



