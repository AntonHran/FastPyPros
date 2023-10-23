import pytest
import asyncio

from fastapi.exceptions import ValidationException
from datetime import datetime

from src.repositories.tags import make_record, get_image_tags, get_tag_by_name, create_tag, check_image_tags, get_tag_by_id
from src.database.models import Tag, TagToImage


class TestTags:
    @pytest.fixture
    def tags_model(self):
        return Tag(
            id=1,
            tag='tag',
            created_at=datetime.now()
        )

    @pytest.mark.asyncio
    async def test_make_record_success(self, tags_model, image, session, monkeypatch):
        async def mock_check_image_tags(tag, image_id, db):
            return tags_model
        image_id = image.id
        tag = tags_model.tag
        monkeypatch.setattr("src.repositories.tags.check_image_tags", mock_check_image_tags)
        result = await make_record(tag, image_id, session)
        assert result.tag_id == 1
        assert result.image_id == image_id

    @pytest.mark.asyncio
    async def test_make_record_failure(self, tags_model, image, session, monkeypatch):
        async def mock_check_image_tags(tag, image_id, db):
            return tags_model
        image_id = image.id
        monkeypatch.setattr("src.repositories.tags.check_image_tags", mock_check_image_tags)
        record = TagToImage(tag_id=456, image_id=image_id)
        session.add(record)

        session.commit()
        # Очікується виняток `ValidationException` при спробі викликати make_record
        with pytest.raises(ValidationException):
            await make_record(tags_model, image_id, session)

    @pytest.mark.asyncio
    async def test_get_image_tags(self, tags_model, image, session):
        # Створюємо тестовий запис в базі даних
        image_id = image.id
        tag_to_image = TagToImage(tag_id=tags_model.id, image_id=image_id)
        session.add(tags_model)
        session.add(tag_to_image)
        session.commit()

        # Викликаємо функцію get_image_tags для тестового запису
        tags = await get_image_tags(image_id, session)

        # Перевіряємо, що результат не є пустим і містить очікуваний tag_id
        assert tags is not None
        assert tags[0][0] == tags_model.id

    @pytest.mark.asyncio
    async def test_get_image_tags_with_no_records(self, session):
        # Викликаємо функцію get_image_tags для image_id без записів
        tags = await get_image_tags(2, session)

        # Перевіряємо, що результат є пустим (None)
        assert tags == []

    @pytest.mark.asyncio
    async def test_get_tag_by_name(self, tags_model, session):

        # Викликаємо функцію get_tag_by_name для тестового тегу
        result_tag = await get_tag_by_name(tags_model.tag, session)

        # Перевіряємо, що результат не є пустим і містить очікуваний тег
        assert result_tag is not None
        assert result_tag.tag == tags_model.tag

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

    # @pytest.mark.asyncio
    # async def test_create_tag_not_found(self, session):
    #     # Викликаємо функцію create_tag для створення нового тегу
    #     new_tag_name = 'new_test_tag'
    #     created_tag = await create_tag(new_tag_name, session)

    #     # Перевіряємо, що результат не є пустим і містить очікуваний тег
    #     assert created_tag is not None
    #     assert created_tag.tag == new_tag_name

    #     # Спроба створити тег з тим самим ім'ям повинна повернути None
    #     duplicate_created_tag = await create_tag(new_tag_name, session)
        
    #     # Перевіряємо, що результат цього виклику є None, оскільки тег з таким ім'ям вже існує
    #     assert duplicate_created_tag is None 

    @pytest.mark.asyncio
    async def test_check_image_tags(self, tags_model, image, session):
        # Отримуємо тестовий тег за ім'ям
        tag_name = tags_model.tag
        tag_ = await get_tag_by_name(tag_name, session)

        # Отримуємо теги для тестового зображення (в даному випадку пустий список)
        image_tags = await get_image_tags(image.id, session)

        # Перевіряємо, що функція повертає тег, коли умови виконані
        result = await check_image_tags(tag_, image_tags, session)
        assert result == tag_

        # Перевіряємо, що функція не повертає тег, коли тег вже присутній серед тегів зображення
        image_tags.append(tag_.id)
        result = await check_image_tags(tag_, image_tags, session)
        assert result is None

        # Перевіряємо, що функція не повертає тег, коли кількість тегів досягла ліміту (5)
        image_tags = [1, 2, 3, 4, 5]  # Припустимо, що у зображення вже є 5 тегів
        result = await check_image_tags(tag_, image_tags, session)
        assert result is None

        # Перевіряємо, що функція повертає тег, коли тег відсутній серед тегів зображення і кількість тегів < 5
        image_tags = [1, 2, 3, 4]  # Припустимо, що у зображення є 4 теги
        result = await check_image_tags(tag_, image_tags, session)
        assert result == tag_

    @pytest.mark.asyncio
    async def test_get_tag_by_id(self, tags_model, session):
        # Отримуємо тестовий тег за ідентифікатором, який має бути 1
        tag = await get_tag_by_id(1, session)

        # Перевіряємо, що тег не є пустим і має правильний ідентифікатор
        assert tag is not None
        assert tag.id == tags_model.id




