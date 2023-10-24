import pytest

from unittest.mock import MagicMock, AsyncMock

from src.services.cloud_image import CloudImage
from src.repositories.images import ImageServices, get_image_by_id


class TestImageServices:

    @pytest.mark.asyncio
    async def test_get_image(self, image, mock_form_answer, session, monkeypatch):
        async_get_image_by_id = AsyncMock(return_value=image)
        async_form_answer = AsyncMock(return_value=mock_form_answer)
        monkeypatch.setattr(
            "src.repositories.images.get_image_by_id", async_get_image_by_id
        )
        monkeypatch.setattr("src.repositories.images.form_answer", async_form_answer)

        result = await ImageServices.get_image(image.id, session)
        expected_result = mock_form_answer
        assert result == expected_result

        async_get_image_by_id.assert_awaited_once_with(image.id, session)
        async_form_answer.assert_awaited_once_with(image)

    @pytest.mark.asyncio
    async def test_get_all_images(
        self, image, mock_form_answer, user_, session, monkeypatch
    ):
        query_mock = MagicMock()
        query_mock.filter().all.return_value = [image]
        monkeypatch.setattr(session, "query", query_mock)

        async_form_answer = AsyncMock(return_value=[mock_form_answer])
        monkeypatch.setattr("src.repositories.images.form_answer", async_form_answer)

        result = await ImageServices.get_all_images(user_.id, session)
        assert result == []

    @pytest.mark.asyncio
    async def test_update_description_image_not_found(
        self, image, user_, session, monkeypatch
    ):
        image_id = 12345
        new_description = "Updated description"

        async_get_image_by_id = AsyncMock(return_value=None)
        monkeypatch.setattr(
            "src.repositories.images.get_image_by_id", async_get_image_by_id
        )

        result = await ImageServices.update_description(
            image_id, new_description, session
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_image_image_not_found(self, user_, session, monkeypatch):
        monkeypatch.setattr(CloudImage, "remove_image", MagicMock())
        image_id = 123
        username = user_.username

        result = await ImageServices.delete_image(image_id, username, session)

        assert result is None

    @pytest.mark.asyncio
    async def test_get_image_by_id(self, image, session):
        session.add(image)
        session.commit()

        result = await get_image_by_id(image.id, session)

        assert result is not None
        assert result.id == image.id
