# import os
# import sys
# import base64
# import binascii
import time
from ipaddress import ip_address
from typing import Callable

import redis.asyncio as redis
import uvicorn
from fastapi import FastAPI, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse, HTMLResponse
# from starlette.authentication import AuthenticationBackend, AuthenticationError, AuthCredentials, SimpleUser
from sqlalchemy import text
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
# from starlette.authentication import AuthenticationBackend
# from starlette.middleware.authentication import AuthenticationMiddleware
from starlette.middleware.cors import CORSMiddleware
from fastapi_limiter import FastAPILimiter
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

# SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# sys.path.append(os.path.dirname(SCRIPT_DIR))
# from src.repositories.users import AuthServices
from src.database.connection import get_db
# from src.database.models import BanList
from src.routes import images, auth, users, rating, images_tags, images_comments, images_search, users_accounts
from src.conf.config import settings
from src.services.tasks import remove_tokens
# from src.conf import messages


app = FastAPI()


@app.on_event("startup")
async def startup():
    db = next(get_db())
    r_t = await remove_tokens(db)
    print(r_t)
    red = await redis.Redis(host=settings.redis_host, port=settings.redis_port,
                            password=settings.redis_password,
                            db=0, encoding="utf-8", decode_responses=True)
    await FastAPILimiter.init(red)


origins = [
    "http://127.0.0.1:5500",
    "http://localhost:5500",
    "https://app.koyeb.com/",
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

ALLOWED_IPS = [
    ip_address('192.168.1.0'),
    ip_address('172.28.192.1'),
    ip_address('172.16.0.0'),
    ip_address("127.0.0.1"),
    ]

templates = Jinja2Templates(directory="src/services/templates")
app.mount("/src/services/static", StaticFiles(directory="src/services/static"), name="static")


def get_client_ip(request):
    return ip_address(request.client.host)


'''@app.middleware("http")
async def limit_access_by_ip(request: Request, call_next: Callable):
    """
    The limit_access_by_ip function is a middleware function that limits access to the API by IP address.
    It checks if the client's IP address is in ALLOWED_IPS, and if not, returns a 403 Forbidden response.

    :param request: Request: Access the request object
    :param call_next: Callable: Pass the next function in the pipeline
    :return: A jsonresponse object with a status code of 403
    :doc-author: Trelent
    """
    # ip = ip_address(request.client.host)
    ip = get_client_ip(request)
    if ip not in ALLOWED_IPS:
        return JSONResponse(status_code=status.HTTP_403_FORBIDDEN, content={"detail": "Not allowed IP address"})
    response = await call_next(request)
    return response'''


@app.middleware("http")
async def custom_middleware(request: Request, call_next: Callable):
    """
    The custom_middleware function is a middleware function that will be called before the request
    is passed to the route handler. It will catch any SQLAlchemy errors and return them as JSON responses,
    and it will add a performance header to every response.

    :param request: Request: Access the request object
    :param call_next: Callable: Pass the request to the next middleware in line
    :return: A response object
    :doc-author: Trelent
    """
    start = time.time()
    try:
        response = await call_next(request)
    except SQLAlchemyError as error:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"message": str(error)})
    duration = time.time() - start
    response.headers["performance"] = str(duration)
    return response


'''class BasicAuthBackend(AuthenticationBackend):
    async def authenticate(self, conn):
        if "Authorization" not in conn.headers:
            return

        auth = conn.headers["Authorization"]
        try:
            scheme, credentials = auth.split()
            if scheme.lower() != 'basic':
                return
            decoded = base64.b64decode(credentials).decode("ascii")
        except (ValueError, UnicodeDecodeError, binascii.Error) as exc:
            raise AuthenticationError('Invalid basic auth credentials')

        username, _, password = decoded.partition(":")
        # TODO: You'd want to verify the username and password here.
        return AuthCredentials(["authenticated"]), SimpleUser(username)
        async def authenticate(self, request):
            # This function is inherited from the base class and called by some other class
            if "Authorization" not in request.headers:
                return
        
            auth = request.headers["Authorization"]
            try:
                scheme, token = auth.split()
                if scheme.lower() != "bearer":
                    return
                decoded = jwt.decode(
                    token,
                    settings.JWT_SECRET,
                    algorithms=[settings.JWT_ALGORITHM],
                    options={"verify_aud": False},
                )
            except (ValueError, UnicodeDecodeError, JWTError) as exc:
                raise AuthenticationError("Invalid JWT Token.")
        
            username: str = decoded.get("sub")
            token_data = TokenData(username=username)
            # This is little hack rather making a generator function for get_db
            db = LocalSession()
            user = User.objects(db).filter(User.id == token_data.username).first()
            # We must close the connection
            db.close()
            if user is None:
                raise AuthenticationError("Invalid JWT Token.")
            return auth, user


@app.middleware("http")
async def check_user_ban_status(request: Request, call_next: Callable):
    # Отримайте поточного користувача, наприклад, за допомогою вашої функції get_current_user.
    # Переконайтеся, що ця функція повертає об'єкт користувача із полем "is_banned".
    db = next(get_db())
    ac_l = request.user
    # baned_access = await AuthServices.check_ban_list(request.user.a, db)
    if ac_l:
        return JSONResponse(status_code=status.HTTP_403_FORBIDDEN, content=messages.BAN)
    # if request.user.is_banned:
        # raise HTTPException(status_code=403, detail="Ваш обліковий запис заблоковано.")
    response = await call_next(request)
    return response


app.add_middleware(AuthenticationMiddleware, backend=BasicAuthBackend)
'''


@app.get("/", response_class=HTMLResponse, description="Main Page")
async def root(request: Request):
    """
    The root function is a simple HTTP endpoint that returns a JSON object
    containing the message &quot;Here your contacts!&quot;.

    :return: A dict, so we can use the json() middleware
    :doc-author: Trelent
    """
    # return {"message": "Here your images!"}
    return templates.TemplateResponse(
        "index.html", {"request": request, "title": "PhotoShare App"}
    )


@app.get("/api/healthchecker")
def healthchecker(db: Session = Depends(get_db)):
    """
    The healthchecker function is a simple function that checks the database connection.
    It returns a JSON object with the message &quot;Welcome to FastAPI&quot; if everything is working correctly.

    :param db: Session: Get the database session from the dependency
    :return: A dictionary with a message
    :doc-author: Trelent
    """
    try:
        result = db.execute(text("SELECT 1")).fetchone()
        if not result:
            raise HTTPException(status_code=500, detail="Database is not configured correctly")
        return {"message": "Welcome to FastAPI"}
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Error connecting to the database")


app.include_router(images.router, prefix="/api")
app.include_router(auth.router, prefix="/api")
app.include_router(users.router, prefix="/api")
app.include_router(users_accounts.router, prefix="/api")
app.include_router(images_comments.router, prefix="/api")
app.include_router(images_tags.router, prefix="/api")
app.include_router(rating.router, prefix="/api")
app.include_router(images_search.router, prefix="/api")


if __name__ == '__main__':
    uvicorn.run("main:app", reload=True)
