from datetime import datetime

from pydantic import BaseModel, Field, EmailStr, ConfigDict

from src.database.models import UserRole
from src.conf.messages import TOKEN_TYPE


class UserModel(BaseModel):
    username: str = Field(min_length=3, max_length=15)
    email: EmailStr
    password: str = Field(min_length=6, max_length=12)


class UserResponse(BaseModel):
    id: int
    username: str
    email: EmailStr
    roles: UserRole
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class TokenModel(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = TOKEN_TYPE
