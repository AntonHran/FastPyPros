import pytest
import asyncio
import io

from unittest.mock import MagicMock, AsyncMock
from src.database.models import Image
from src.services.cloud_image import CloudImage
from tests.conftest import MockCloudImage
from src.repositories.images import ImageServices, get_image_by_id, form_answer


class TestImageServices:
    
    @pytest.mark.asyncio
    async def test_upload_file(self, image, user, session, monkeypatch, mock_image_response):
        monkeypatch.setattr(CloudImage, 'generate_file_name', MockCloudImage.mock_generate_file_name)
        monkeypatch.setattr(CloudImage, 'upload', MockCloudImage.mock_upload)
        monkeypatch.setattr(CloudImage, 'get_url_for_avatar', MockCloudImage.mock_get_url_for_avatar)

        fake_file = MagicMock()
        fake_file.filename = 'test.jpg'
        fake_file.file = io.BytesIO(b'some file content')

        response = await ImageServices.upload_file(file=fake_file, description=image.description, user=user, db=session)

        assert response.model_dump() == mock_image_response.dict()

    @pytest.mark.asyncio
    async def test_upload_file_format_not_found(self, image, user, session, monkeypatch):
        monkeypatch.setattr(CloudImage, 'generate_file_name', MockCloudImage.mock_generate_file_name)
        monkeypatch.setattr(CloudImage, 'upload', MockCloudImage.mock_upload)
        monkeypatch.setattr(CloudImage, 'get_url_for_avatar', MockCloudImage.mock_get_url_for_avatar)

        fake_file = MagicMock()
        fake_file.filename = 'test.unknown' 
        fake_file.file = io.BytesIO(b'some file content')

        response = await ImageServices.upload_file(file=fake_file, description=image.description, user=user, db=session)
        
        assert response is None

    @pytest.mark.asyncio
    async def test_get_image(self, image, mock_form_answer, session, monkeypatch):
        async_get_image_by_id = AsyncMock(return_value=image)
        async_form_answer = AsyncMock(return_value=mock_form_answer)
        monkeypatch.setattr('src.repositories.images.get_image_by_id', async_get_image_by_id)
        monkeypatch.setattr('src.repositories.images.form_answer', async_form_answer)

        result = await ImageServices.get_image(image.id, session)
        expected_result = mock_form_answer
        assert result == expected_result

        async_get_image_by_id.assert_awaited_once_with(image.id, session)
        async_form_answer.assert_awaited_once_with(image)

    @pytest.mark.asyncio
    async def test_get_all_images(self, image, mock_form_answer, user, session, monkeypatch):
        query_mock = MagicMock()
        query_mock.filter().all.return_value = [image]
        monkeypatch.setattr(session, 'query', query_mock)

        async_form_answer = AsyncMock(return_value=[mock_form_answer])
        monkeypatch.setattr('src.repositories.images.form_answer', async_form_answer)

        result = await ImageServices.get_all_images(user.id, session)
        expected_result = [mock_form_answer]
        assert result == expected_result

    @pytest.mark.asyncio
    async def test_update_description(self, image, mock_form_answer, session, monkeypatch):
        image_id = image.id
        new_description = "Updated description"

        async_get_image_by_id = AsyncMock(return_value=image)
        async_form_answer = AsyncMock(return_value=mock_form_answer)
        monkeypatch.setattr('src.repositories.images.get_image_by_id', async_get_image_by_id)
        monkeypatch.setattr('src.repositories.images.form_answer', async_form_answer)

        result = await ImageServices.update_description(image_id, new_description, session)

        expected_response = image
        expected_response.description = new_description
        assert result.model_dump() == expected_response.dict()

        async_get_image_by_id.assert_awaited_once_with(image.id, session)
        async_form_answer.assert_awaited_once_with(image)

    @pytest.mark.asyncio
    async def test_update_description_image_not_found(self, image, user, session, monkeypatch):
        image_id = 12345  
        new_description = "Updated description"

        async_get_image_by_id = AsyncMock(return_value=None)
        monkeypatch.setattr('src.repositories.images.get_image_by_id', async_get_image_by_id)

        result = await ImageServices.update_description(image_id, new_description, session)
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_image(self, image, user, session, monkeypatch):
        monkeypatch.setattr(CloudImage, 'remove_image', MagicMock())
        monkeypatch.setattr(session, 'commit', MagicMock())
        image_id = image.id
        username = user.username

        result = await ImageServices.delete_image(image_id, username, session)

        session.query(Image).filter_by(id=image_id).first.assert_called_once_with()
        CloudImage.remove_image.assert_called_once_with(username, image.public_id)
        session.delete.assert_called_once_with(image)
        session.commit.assert_called_once()
        assert result == image

    @pytest.mark.asyncio
    async def test_delete_image_image_not_found(self, user, session, monkeypatch):
        monkeypatch.setattr(CloudImage, 'remove_image', MagicMock())
        image_id = 123
        username = user.username

        result = await ImageServices.delete_image(image_id, username, session)

        assert result is None

    @pytest.mark.asyncio
    async def test_get_image_by_id(self, image, session):
        session.add(image)
        session.commit()

        result = await get_image_by_id(image.id, session)

        assert result is not None
        assert result.id == image.id

    @pytest.mark.asyncio
    async def test_form_answer(self, image, mock_image_response):
        result = await form_answer(image)

        assert result is not None
        assert result == mock_image_response