from unittest.mock import MagicMock

import pytest

from src.database.models import Image
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


def test_get_images_(client, image, token):
    response = client.get("api/images/",
                          headers={"Authorization": f"Bearer {token['access_token']}"})

    assert response.status_code == 404
    response_data = response.json()
    assert response_data["detail"] == messages.NOT_FOUND


def test_upload_file(image, token, client, monkeypatch):
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
        f"api/images/?description={image.description}",
        headers={"Authorization": f"Bearer {token['access_token']}"},
        files={"file": ("test_image.jpg", file)},
    )
    assert response.status_code == 201, response.text
    assert response.json()["origin_path"] == mock_get_url()


def test_get_image(client, image, token):

    response = client.get(f"api/images/{1}",
                          headers={"Authorization": f"Bearer {token['access_token']}"})
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["description"] == image.description


def test_get_image_(client, image, token):

    response = client.get(f"api/images/{10}",
                          headers={"Authorization": f"Bearer {token['access_token']}"})
    assert response.status_code == 404
    response_data = response.json()
    assert response_data["detail"] == messages.NOT_FOUND


def test_get_images(client, image, token):
    response = client.get("api/images/",
                          headers={"Authorization": f"Bearer {token['access_token']}"})

    assert response.status_code == 200
    response_data = response.json()
    assert response_data[0]["description"] == image.description


def test_update_description(image, token, client, session):
    # image_ = session.query(Image).filter(Image.description == image["description"]).first()
    response = client.patch(f"api/images/{image.id}?description=new_description",
                            data={"description": "new description"},
                            headers={"Authorization": f"Bearer {token['access_token']}"})
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["description"] == "new_description"


def test_update_description__(image, token, client, session):

    response = client.patch(f"api/images/{10}?description=new_description",
                            data={"description": "new description"},
                            headers={"Authorization": f"Bearer {token['access_token']}"})
    assert response.status_code == 409, response.text
    data = response.json()
    assert data["detail"] == messages.NOT_YOUR_IMAGE


def test_delete_image_(image, token, client, session):
    response = client.delete(f"api/images/{10}",
                             headers={"Authorization": f"Bearer {token['access_token']}"}
                             )
    assert response.status_code == 409, response.text
    data = response.json()
    assert data["detail"] == messages.NOT_YOUR_IMAGE


def test_delete_image__(image_example, token_admin, client, session):
    image_ = session.query(Image).filter(Image.description == image_example["description"]).first()
    response = client.delete(
        f"api/images/{image_.id}",
        headers={"Authorization": f"Bearer {token_admin['access_token']}"},
    )
    assert response.status_code == 204, response.text


def test_delete_image(image, token, client, session):
    image_ = session.query(Image).filter(Image.description == "new_description_1").first()
    response = client.delete(f"api/images/{image.id}",
                             headers={"Authorization": f"Bearer {token['access_token']}"}
                             )
    assert response.status_code == 204, response.text
