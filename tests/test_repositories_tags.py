import pytest

from datetime import datetime

from src.repositories.tags import get_image_tags, get_tag_by_name, create_tag, get_tag_by_id
from src.database.models import Tag


class TestTags:
    @pytest.fixture
    def tags_model(self):
        return Tag(
            id=1,
            tag='tag',
            created_at=datetime.now()
        )

    @pytest.mark.asyncio
    async def test_get_image_tags_with_no_records(self, session):
        # Викликаємо функцію get_image_tags для image_id без записів
        tags = await get_image_tags(2, session)

        # Перевіряємо, що результат є пустим (None)
        assert tags == []

    @pytest.mark.asyncio
    async def test_get_tag_by_name_not_found(self, session):

        # Викликаємо функцію get_tag_by_name для тегу, який не існує
        result_tag = await get_tag_by_name('non_existent_tag', session)

        # Перевіряємо, що результат є None, оскільки тег не був знайдений
        assert result_tag is None

    @pytest.mark.asyncio
    async def test_create_tag(self, session):
        # Викликаємо функцію create_tag для створення нового тегу
        new_tag_name = 'new_tag'
        created_tag = await create_tag(new_tag_name, session)

        # Перевіряємо, що результат не є пустим і містить очікуваний тег
        assert created_tag is not None
        assert created_tag.tag == new_tag_name

        # Перевіряємо, що тег був збережений в базу даних
        retrieved_tag = session.query(Tag).filter_by(tag=new_tag_name).first()
        assert retrieved_tag is not None
        assert retrieved_tag.tag == new_tag_name

    @pytest.mark.asyncio
    async def test_get_tag_by_id(self, tags_model, session):
        # Отримуємо тестовий тег за ідентифікатором, який має бути 1
        tag = await get_tag_by_id(1, session)

        # Перевіряємо, що тег не є пустим і має правильний ідентифікатор
        assert tag is not None
        assert tag.id == tags_model.id
