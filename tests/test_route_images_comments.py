from unittest.mock import MagicMock

import pytest
from fastapi import status

from src.database.models import User, Image
from src.conf import messages


@pytest.fixture
def token(client, session, user, monkeypatch):
    mock_send_email = MagicMock()
    monkeypatch.setattr("src.routes.auth.send_email", mock_send_email)
    client.post("/api/auth/signup", json=user)

    current_user: User = session.query(User).filter(User.email == user.get("email")).first()
    current_user.confirmed = True
    session.commit()
    response = client.post(
        "/api/auth/login",
        data={"username": user['email'], "password": user['password']},
    )
    data = response.json()
    return data


@pytest.fixture
def token_admin(client, session, admin, monkeypatch):
    mock_send_email = MagicMock()
    monkeypatch.setattr("src.routes.auth.send_email", mock_send_email)
    client.post("/api/auth/signup", json=admin)

    current_user: User = session.query(User).filter(User.email == admin.get("email")).first()
    current_user.confirmed = True
    current_user.roles = "admin"
    session.commit()
    response = client.post(
        "/api/auth/login",
        data={"username": admin['email'], "password": admin['password']},
    )
    data = response.json()
    return data


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


def test_post_comment(image, client, token, session, image_example):
    image_ = session.query(Image).filter(Image.origin_path == image_example["origin_path"]).first()
    assert image_.id == image_example['id']
    response = client.post(f"/api/images/{image_.id}/comments/",
                           json={"image_id": image_.id,
                                 "content": "Test text for new comment"},
                           headers={"Authorization": f"Bearer {token['access_token']}"})
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["comment"] == "Test text for new comment"


def test_post_comment_(image_example, client, token_admin, session):
    image_ = session.query(Image).filter(Image.origin_path == image_example["origin_path"]).first()
    response = client.post(f"/api/images/{image_.id}/comments/",
                           json={"image_id": image_example['id'],
                                 "content": "Test text for new comment"},
                           headers={"Authorization": f"Bearer {token_admin['access_token']}"})
    assert response.status_code == 404, response.text
    data = response.json()
    assert data["detail"] == messages.SOMETHING_WRONG


def test_show_comments(image_example, client, token, session):
    image_ = (
        session.query(Image)
        .filter(Image.origin_path == image_example["origin_path"])
        .first()
    )
    response = client.get(f"api/images/{image_.id}/comments",
                          headers={"Authorization": f"Bearer {token['access_token']}"})
    assert response.status_code == 200, response.text
    data = response.json()
    assert data[0]["comment"] == "Test text for new comment"


def test_show_comments_(image_example, client, token, session):
    response = client.get(f"api/images/{image_example['id']}/comments",
                          headers={"Authorization": f"Bearer {token['access_token']}"})
    assert response.status_code == 404, response.text
    data = response.json()
    assert data["detail"] == messages.NOT_FOUND


def test_update_comment(image_example, client, token, session):
    image_ = (
        session.query(Image)
        .filter(Image.origin_path == image_example["origin_path"])
        .first()
    )
    response = client.put(
        f"api/images/{image_.id}/comments/1?new_comment=NEW+Test+text+for+comment",
        headers={"Authorization": f"Bearer {token['access_token']}"}
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["comment"] == "NEW Test text for comment"


def test_update_comment_(image_example, client, token):
    response = client.put(
        f"api/images/{image_example['id']}/comments/10?new_comment=NEW+Test+text+for+comment",
        headers={"Authorization": f"Bearer {token['access_token']}"}
    )
    assert response.status_code == 404, response.text
    data = response.json()
    assert data["detail"] == messages.NOT_FOUND


def test_remove_comment(image_example, client, token_admin, token):
    response = client.delete(f"api/images/comments/{image_example['id']}",
                             headers={"Authorization": f"Bearer {token_admin['access_token']}"})
    assert response.status_code == status.HTTP_404_NOT_FOUND
    response = client.delete(f"api/images/comments/{image_example['id']}",
                             headers={"Authorization": f"Bearer {token['access_token']}"})
    assert response.status_code == status.HTTP_403_FORBIDDEN
