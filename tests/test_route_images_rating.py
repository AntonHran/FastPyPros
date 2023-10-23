import pytest
from unittest.mock import MagicMock

from src.database.models import User, Rating, Image
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
def take_image(token_admin, session, client, monkeypatch):
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
        f"api/images/?description={image.get('description')}",
        headers={"Authorization": f"Bearer {token['access_token']}"},
        files={"file": ("test_image.jpg", file)},
    )
    assert response.status_code == 201, response.text
    assert response.json()["origin_path"] == mock_get_url()


def test_make_rate(image, token, client, session):
    img = Image(description=image["description"],
                public_id="public_id",
                origin_path="origin_path",
                transformed_path="",
                slug="",
                rating=0)
    session.add(img)
    session.commit()
    session.refresh(img)
    image_ = session.query(Image).filter(Image.description == image["description"]).first()
    response = client.post(f"api/images/{image_.id}/rate/",
                           json={"image_id": image_.id, "rate": 4},
                           headers={"Authorization": f"Bearer {token['access_token']}"})
    assert response.status_code == 201, response.text
    image = response.json()
    assert image["rate"] == 4


def test_delete_rate(token_admin, take_image, user, client, session):
    cur_user = session.query(User).filter(User.username == user["username"]).first()
    image_ = (
        session.query(Image).filter(Image.description == take_image["description"]).first()
    )
    res = session.query(Rating).filter(Rating.image_id == image_.id, Rating.user_id == cur_user.id).first()
    assert res.image_id == image_.id
    response = client.delete(
        f"api/images/{3}/rating/user_id={1}",
        headers={"Authorization": f"Bearer {token_admin['access_token']}"},
    )
    assert response.status_code == 204, response.text


def test_make_rate_own(image, token, client, session):
    image_ = session.query(Image).filter(Image.description == image["description"]).first()
    response = client.post(f"api/images/{image_.id}/rate/",
                           json={"image_id": image_.id, "rate": 5},
                           headers={"Authorization": f"Bearer {token['access_token']}"})
    assert response.status_code == 409, response.text
    image = response.json()
    assert image["detail"] == messages.RATE_OWN_IMAGE


def test_make_rate_repeat(take_image, token, client, session):
    image_ = session.query(Image).filter(Image.description == take_image["description"]).first()
    response = client.post(f"api/images/{image_.id}/rate/",
                           json={"image_id": image_.id, "rate": 4},
                           headers={"Authorization": f"Bearer {token['access_token']}"})
    assert response.status_code == 409, response.text
    image = response.json()
    assert image["detail"] == messages.REPEAT_RATE


def test_get_rates(token_admin, take_image, client, session):
    image_ = (
        session.query(Image).filter(Image.description == take_image["description"]).first()
    )
    rec = session.query(Rating).filter(Rating.image_id == image_.id).all()
    assert rec[0].rate == 4
    response = client.get(f"api/images/{image_.id}/rating/",
                          headers={"Authorization": f"Bearer {token_admin['access_token']}"})
    assert response.status_code == 200, response.text


def test_get_rates_(token_admin, image, client, session):
    response = client.get(f"api/images/rating/{5}",
                          headers={"Authorization": f"Bearer {token_admin['access_token']}"})
    assert response.status_code == 404, response.text


def test_delete_rate_(token_admin, image, user, client, session):
    cur_user = session.query(User).filter(User.username == user["username"]).first()
    image_ = (
        session.query(Image).filter(Image.description == image["description"]).first()
    )
    response = client.delete(
        f"api/images/{image_.id}/rating//{cur_user.id}",
        headers={"Authorization": f"Bearer {token_admin['access_token']}"},
    )
    assert response.status_code == 404, response.text
    data = response.json()
    assert data["detail"] == messages.NOT_FOUND
