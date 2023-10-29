import pickle

import redis
from sqlalchemy.orm import Session
# from fastapi import Depends

from src.database.connection import SessionLocal
from src.database.models import BanList
from src.conf.config import settings


class CurrentBanList:
    '''SECRET_KEY_A = settings.secret_key_a
    ALGORITHM = settings.algorithm
    oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")'''
    red = redis.Redis(host=settings.redis_host,
                      port=settings.redis_port,
                      password=settings.redis_password,
                      db=1)
    db: Session = SessionLocal()  # = Depends(get_db)

    async def get_ban_list(self):
        ban_list = self.red.get(f"ban_list")
        if not ban_list:
            ban_list = self.db.query(BanList).all()
            self.red.set("ban_list", pickle.dumps(ban_list))
            self.red.expire("ban_list", 1500)
        else:
            ban_list = pickle.loads(ban_list)
        return ban_list

    async def set_ban_list(self, ban_list: BanList):
        self.red.set("ban_list", pickle.dumps(ban_list))
        self.red.expire("ban_list", 1500)


auth_ban_list = CurrentBanList()
