from unittest.mock import MagicMock

import pytest

from src.database.models import Image, Tag
from src.conf import messages


@pytest.fixture
def image_example(token_admin, session, client, monkeypatch):
    mock_generate_name = MagicMock()
    mock_generate_name.return_value = "public_id"
    mock_upload = MagicMock()
    mock_get_url = MagicMock()
    mock_get_url.return_value = "image_url"
    monkeypatch.setattr(
        "src.services.cloud_image.CloudImage.generate_file_name", mock_generate_name
    )
    monkeypatch.setattr("src.services.cloud_image.CloudImage.upload", mock_upload)
    monkeypatch.setattr(
        "src.services.cloud_image.CloudImage.get_url_for_avatar", mock_get_url
    )
    file = "file".encode()
    response = client.post(
        f"api/images/?description=example",
        headers={"Authorization": f"Bearer {token_admin['access_token']}"},
        files={"file": ("test_image.jpg", file)},
    )
    image_exp = response.json()
    return image_exp


def test_get_tags(client, token):
    response = client.get("api/images/tags/",
                          headers={"Authorization": f"Bearer {token['access_token']}"})
    assert response.status_code == 404, response.text
    data = response.json()
    assert data["detail"] == messages.NOT_FOUND


def test_add_tag_to_image(client, image_example, session, token_admin):
    image_ = session.query(Image).filter(Image.description == image_example["description"]).first()
    response = client.post(f"api/images/{image_.id}/tags?tag=new_tag",
                           headers={"Authorization": f"Bearer {token_admin['access_token']}"})
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["tag"] == "new_tag"


def test_add_tag_to_image_2(client, image_example, session, token_admin):
    image_ = session.query(Image).filter(Image.description == image_example["description"]).first()
    response = client.post(f"api/images/{image_.id}/tags?tag=tag",
                           headers={"Authorization": f"Bearer {token_admin['access_token']}"})
    assert response.status_code == 201, response.text


def test_add_tag_to_image_3(client, image_example, session, token_admin):
    image_ = session.query(Image).filter(Image.description == image_example["description"]).first()
    response = client.post(f"api/images/{image_.id}/tags?tag=tag2",
                           headers={"Authorization": f"Bearer {token_admin['access_token']}"})
    assert response.status_code == 201, response.text


def test_add_tag_to_image_4(client, image_example, session, token_admin):
    image_ = session.query(Image).filter(Image.description == image_example["description"]).first()
    response = client.post(f"api/images/{image_.id}/tags?tag=tag3",
                           headers={"Authorization": f"Bearer {token_admin['access_token']}"})
    assert response.status_code == 201, response.text


def test_add_tag_to_image_5(client, image_example, session, token_admin):
    image_ = session.query(Image).filter(Image.description == image_example["description"]).first()
    response = client.post(f"api/images/{image_.id}/tags?tag=tag4",
                           headers={"Authorization": f"Bearer {token_admin['access_token']}"})
    assert response.status_code == 201, response.text


def test_add_tag_to_image_6(client, image_example, session, token_admin):
    image_ = session.query(Image).filter(Image.description == image_example["description"]).first()
    response = client.post(f"api/images/{image_.id}/tags?tag=tag3",
                           headers={"Authorization": f"Bearer {token_admin['access_token']}"})
    assert response.status_code == 409, response.text
    data = response.json()
    assert data["detail"] == messages.LIMIT_EXCEEDED


def test_get_tags_(client, token):
    response = client.get("api/images/tags/",
                          headers={"Authorization": f"Bearer {token['access_token']}"})
    assert response.status_code == 200, response.text
    data = response.json()
    assert data[0]["tag"] == "new_tag"


def test_update_tag(token_admin, client, session):
    tag_ = session.query(Tag).filter(Tag.tag == "new_tag").first()
    response = client.put(f"api/images/tags/{tag_.id}?new_tag=TAG",
                          json={"tag_id": tag_.id,
                                "new_tag": "TAG"},
                          headers={"Authorization": f"Bearer {token_admin['access_token']}"})
    assert response.status_code == 200, response.text


def test_delete_tag(token_admin, client, session):
    tag_ = session.query(Tag).filter(Tag.tag == "new_tag").first()
    response = client.delete(f"api/images/tags/{tag_.id}/",
                             headers={"Authorization": f"Bearer {token_admin['access_token']}"})
    assert response.status_code == 204, response.text

