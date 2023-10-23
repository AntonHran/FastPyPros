import os
import sys
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from ipaddress import ip_address

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))

from main import app
from src.database.models import Base
from src.database.connection import get_db


def mocked_ip_address(ip_str):
    return ip_address(ip_str)


SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# pytest --cov=. --cov-report html tests
# pytest --cov=. --cov-report html tests/test_route_images_rating.py
# pytest --cov=. --cov-report html tests/test_route_auth.py
@pytest.fixture(scope="module")
def session():
    # Create the database
    Base.metadata.create_all(bind=engine)
    #
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="module")
def client(session):
    # Dependency override
    def override_get_db():
        try:
            yield session
        finally:
            session.close()
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)


@pytest.fixture(scope="module")
def user():
    return {"username": "user",
            "email": "user@example.com",
            "password": "123456789",
            "access_token": "a_t"}


@pytest.fixture(scope="module")
def admin():
    return {"username": "_admin_",
            "email": "admin@example.com",
            "password": "9876543210",
            "access_token": "a_t_a"}


@pytest.fixture(scope="module")
def account():
    return {"first_name": "User_1",
            "last_name": "Test_1",
            "email": "user@example.com",
            "phone_number": "+380501234567",
            "location": "city_1"}


@pytest.fixture(scope="module")
def image():
    return {
        # "user_id": 1,
        "description": "some image",
        "public_id": "public_id",
        "origin_path": "origin_path",
        "transformed_path": "",
        "slug": "",
        "rating": 0
    }
