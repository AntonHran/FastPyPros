from datetime import datetime

from fastapi.exceptions import HTTPException
from fastapi import status
from jose import jwt
from sqlalchemy.orm import Session

from src.database.models import BanList
from src.conf.config import settings


async def get_token_data(token: str):
    try:
        token_data = jwt.decode(token, settings.secret_key_a, algorithms=settings.algorithm)
        return token_data
    except HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="") as exc:
        raise exc


async def check_token(db: Session):
    tokens = await get_all_tokens(db)
    result = []
    for token in tokens:
        token_data = await get_token_data(token.access_token)
        if datetime.fromtimestamp(token_data["exp"]) <= datetime.now() and token.reason == "logout":
            removed_token = await remove_token(token.access_token, db)
            result.append(removed_token)
    return result


async def remove_token(token: str, db: Session):
    token_from = await get_token(token, db)
    if token_from:
        db.delete(token_from)
        db.commit()
    return token_from


async def get_token(token: str, db: Session):
    return db.query(BanList).filter_by(access_token=token)


async def get_all_tokens(db: Session):
    return db.query(BanList).all()
