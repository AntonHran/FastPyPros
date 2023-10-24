import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock
from sqlalchemy.orm import Session
from src.database.models import User, Image, Comment

from src.repositories.comments import CommentServices


@pytest.fixture
def session():
    return MagicMock(spec=Session)


@pytest.fixture
def test_user():
    return User(id=1, email='someemail@gmail.com', roles=1, username='Somename', confirmed=True, password='secret')


@pytest.fixture
def test_image():
    return Image(id=1, origin_path="http://example.com/photo.jpg")


@pytest.fixture
def client():
    from main import app  # Здесь подставьте правильный импорт вашего FastAPI приложения
    return TestClient(app)


@pytest.mark.asyncio
async def test_get_comment(session):
    expected_comment = Comment(id=1, comment="Test content")
    session.query().filter().first.return_value = expected_comment
    result = await CommentServices.get_comment(comment_id=1, db=session)
    assert result == expected_comment


@pytest.mark.asyncio
async def test_delete_comment(session):
    existing_comment = Comment(id=1, comment="Old content")
    session.query().filter().first.return_value = existing_comment
    deleted_comment = await CommentServices.delete_comment(1, session)
    assert deleted_comment == existing_comment
    session.delete.assert_called_once_with(existing_comment)
    session.commit.assert_called_once()
