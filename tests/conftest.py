import os
import sys
from datetime import datetime
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from ipaddress import ip_address
from io import BytesIO

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))

from main import app
from src.database.models import Base, User, Image
from src.database.connection import get_db


def mocked_ip_address(ip_str):
    return ip_address(ip_str)


SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# pytest --cov=. --cov-report html tests
class MockCloudImage:
    @staticmethod
    def mock_generate_file_name(username):
        return f'mock_public_id_{username}'

    @staticmethod
    def mock_upload(file, public_id):
        return "uploaded_image_url"

    @staticmethod
    def mock_get_url_for_avatar(public_id, res):
        return f"avatar_url_{public_id}"


@pytest.fixture(scope='module')
def mock_cloud_image():
    return MockCloudImage


@pytest.fixture
def in_memory_file():
    image_content = b'some binary image data'
    return BytesIO(image_content)


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


@pytest.fixture(scope='module')
def user_():
    return User(
        id=1,
        username='Test Name',
        email='example@mail.com',
        password='password123',
    )


@pytest.fixture(scope='module')
def image():
    return Image(
        id=1,
        user_id=1,
        description="Test image description",
        public_id="test_public_id",
        origin_path="test_origin_path",
        transformed_path=None,
        slug=None,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )


@pytest.fixture(scope='module')
def mock_form_answer():
    return Image(
        user_id=1,
        description="mocked_description",
        public_id="mocked_public_id",
        origin_path="mocked_origin_path",
        transformed_path="mocked_transformed_path",
        slug="mocked_qr_path",
        created_at=datetime.now(),
        updated_at=datetime.now()
    )


@pytest.fixture
def mock_image_response():
    return image


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
def image__():
    return {
        # "id": 1,
        "description": "some image",
        "public_id": "public_id",
        "origin_path": "origin_path",
        "transformed_path": "",
        "slug": "",
        "rating": 0
    }


@pytest.fixture(scope='module')
def tag():
    return 'tag'


@pytest.fixture
def token(client, session, user, monkeypatch):
    mock_send_email = MagicMock()
    monkeypatch.setattr("src.routes.auth.send_email", mock_send_email)
    client.post("/api/auth/signup/", json=user)

    current_user = session.query(User).filter(User.email == user.get("email")).first()
    current_user.confirmed = True
    session.commit()
    response = client.post(
        "/api/auth/login/",
        data={"username": user['email'], "password": user['password']},
    )
    data = response.json()
    return data


@pytest.fixture
def token_admin(client, session, admin, monkeypatch):
    mock_send_email = MagicMock()
    monkeypatch.setattr("src.routes.auth.send_email", mock_send_email)
    client.post("/api/auth/signup/", json=admin)

    current_user = session.query(User).filter(User.email == admin.get("email")).first()
    current_user.confirmed = True
    current_user.roles = "admin"
    session.commit()
    response = client.post(
        "/api/auth/login/",
        data={"username": admin['email'], "password": admin['password']},
    )
    data = response.json()
    return data
