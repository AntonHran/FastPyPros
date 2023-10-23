import os
import sys
import pytest
from io import BytesIO
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))

from main import app
from src.database.models import Base, User, Image, Tag
from src.database.connection import get_db
from src.schemes.images import ImageResponse

SQLALCHEMY_DATABASE_URL = 'sqlite:///./test.db'

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={'check_same_thread': False}
)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope='module')
def session():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture(scope='module')
def client(session):
    def override_get_db():
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)


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
def user():
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
def tag():
    return 'tag'

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

@pytest.fixture(scope='module')
def mock_cloud_image():
    return MockCloudImage

@pytest.fixture
def in_memory_file():
    image_content = b'some binary image data'
    return BytesIO(image_content)