import pytest
from unittest.mock import MagicMock, patch

from src.database.models import User
from src.services.auth import auth_user
from src.conf import messages
from src.schemes.account import AccountResponse


INFO = {"first_name": "User_1",
        "last_name": "Test_1",
        "email": "user@example.com",
        "phone_number": "+380501234567",
        "location": "city_1",
        "company": "company_1",
        "position": "position_1", }


@pytest.fixture
def token(client, session, user, monkeypatch):
    mock_send_email = MagicMock()
    monkeypatch.setattr("src.routes.auth.send_email", mock_send_email)
    client.post("/api/auth/signup/", json=user)

    current_user: User = session.query(User).filter(User.email == user.get("email")).first()
    current_user.confirmed = True
    session.commit()
    response = client.post(
        "/api/auth/login/",
        data={"username": user['email'], "password": user['password']},
    )
    data = response.json()
    return data


@pytest.fixture
def token_admin(client, session, admin, monkeypatch):
    mock_send_email = MagicMock()
    monkeypatch.setattr("src.routes.auth.send_email", mock_send_email)
    client.post("/api/auth/signup/", json=admin)

    current_user: User = session.query(User).filter(User.email == admin.get("email")).first()
    current_user.confirmed = True
    current_user.roles = "admin"
    session.commit()
    response = client.post(
        "/api/auth/login/",
        data={"username": admin['email'], "password": admin['password']},
    )
    data = response.json()
    return data


def test_read_without_account(token, user, client, session):
    with patch.object(auth_user, "red") as redis_mock:
        redis_mock.get.return_value = None
    response = client.get(f"api/users/accounts/{user.get('username')}/",
                          headers={"Authorization": f"Bearer {token['access_token']}"}, )
    assert response.status_code == 404, response.text
    data = response.json()
    assert data["detail"] == messages.ACCOUNT_NOT_FOUND


def test_create_account(token, account, client, session):
    with patch.object(auth_user, "red") as redis_mock:
        redis_mock.get.return_value = None
    response = client.post(f"api/users/accounts/",
                           json=INFO,
                           headers={"Authorization": f"Bearer {token['access_token']}"}, )
    assert response.status_code == 201

    account_response = AccountResponse(**response.json())
    assert account_response.first_name == account.get("first_name")
    assert account_response.last_name == account.get("last_name")
    assert account_response.email == account.get("email")


def test_create_wrong_account(token, account, client, session):
    with patch.object(auth_user, "red") as redis_mock:
        redis_mock.get.return_value = None
    response = client.post(f"api/users/accounts/",
                           json={},
                           headers={"Authorization": f"Bearer {token['access_token']}"}, )
    assert response.status_code == 422


def test_read_account(token, user, account, client, session):
    with patch.object(auth_user, "red") as redis_mock:
        redis_mock.get.return_value = None
    response = client.get(f"api/users/accounts/{user.get('username')}/",
                          headers={"Authorization": f"Bearer {token['access_token']}"}, )
    assert response.status_code == 200

    account_response = AccountResponse(**response.json())
    assert account_response.username == user.get("username")
    assert account_response.first_name == account.get("first_name")
    assert account_response.last_name == account.get("last_name")
    assert account_response.email == account.get("email")


def test_update_account(user, token, client, session):
    with patch.object(auth_user, "red") as redis_mock:
        redis_mock.get.return_value = None
    account_data = {
        "first_name": "John",
        "last_name": "Doer",
        "email": "johndoe@example.com",
    }
    with patch.object(auth_user, "red") as redis_mock:
        redis_mock.get.return_value = None
    response = client.put(f"api/users/accounts/{user.get('username')}/",
                          json=account_data,
                          headers={"Authorization": f"Bearer {token['access_token']}"}, )
    assert response.status_code == 200

    account_response = AccountResponse(**response.json())
    assert account_response.username == user["username"]
    assert account_response.first_name == "John"
    assert account_response.last_name == "Doer"
    assert account_response.email == "johndoe@example.com"


def test_update_account_(user, token, client, session):
    with patch.object(auth_user, "red") as redis_mock:
        redis_mock.get.return_value = None
    account_data = {
        "first_name": "John",
        "last_name": "Doer",
        "email": "johndoe@example.com",
    }
    with patch.object(auth_user, "red") as redis_mock:
        redis_mock.get.return_value = None
    response = client.put(f"api/users/accounts/{user['email']}/",
                          json=account_data,
                          headers={"Authorization": f"Bearer {token['access_token']}"}, )
    assert response.status_code == 404


def test_update_account_avatar(token, client, monkeypatch):
    mock_generate_name = MagicMock()
    mock_upload = MagicMock()
    mock_get_url = MagicMock()
    mock_get_url.return_value = "new_url"
    monkeypatch.setattr("src.services.cloud_image.CloudImage.generate_file_name", mock_generate_name)
    monkeypatch.setattr("src.services.cloud_image.CloudImage.upload", mock_upload)
    monkeypatch.setattr("src.services.cloud_image.CloudImage.get_url_for_avatar", mock_get_url)

    file = "file".encode()
    response = client.patch("api/users/accounts/",
                            headers={"Authorization": f"Bearer {token['access_token']}"},
                            files={"file": ("test_image.jpg", file)})
    assert response.status_code == 200, response.text
    assert response.json()["avatar"] == mock_get_url()


def test_remove_account(token, user, account, client, session):
    with patch.object(auth_user, "red") as redis_mock:
        redis_mock.get.return_value = None
    response = client.delete(f"api/users/accounts/",
                             headers={"Authorization": f"Bearer {token['access_token']}"}, )
    assert response.status_code == 204, response.text


def test_remove_account_(token, user, account, client, session):
    with patch.object(auth_user, "red") as redis_mock:
        redis_mock.get.return_value = None
    response = client.delete(f"api/users/accounts/",
                             headers={"Authorization": f"Bearer {token['access_token']}"}, )
    assert response.status_code == 404, response.text
    data = response.json()
    assert data["detail"] == messages.ACCOUNT_NOT_FOUND


def test_update_account_avatar_(token, client, monkeypatch):
    with patch.object(auth_user, "red") as redis_mock:
        redis_mock.get.return_value = None
    mock_generate_name = MagicMock()
    mock_upload = MagicMock()
    mock_get_url = MagicMock()
    mock_get_url.return_value = "new_url"
    monkeypatch.setattr("src.services.cloud_image.CloudImage.generate_file_name", mock_generate_name)
    monkeypatch.setattr("src.services.cloud_image.CloudImage.upload", mock_upload)
    monkeypatch.setattr("src.services.cloud_image.CloudImage.get_url_for_avatar", mock_get_url)

    file = "file".encode()
    response = client.patch("api/users/accounts/",
                            headers={"Authorization": f"Bearer {token['access_token']}"},
                            files={"file": ("test_image.jpg", file)})
    assert response.status_code == 404, response.text
    assert response.json()["detail"] == messages.ACCOUNT_NOT_FOUND


def test_get_users(user, token_admin, client):

    with patch.object(auth_user, "red") as redis_mock:
        redis_mock.get.return_value = None
    response = client.get("api/users/",
                          headers={"Authorization": f"Bearer {token_admin['access_token']}"}, )
    assert response.status_code == 200, response.text
    assert response.json()[0]["email"] == user["email"]


def test_get_user(user, token_admin, client, session):
    with patch.object(auth_user, "red") as redis_mock:
        redis_mock.get.return_value = None
    cur_user = session.query(User).filter(User.username == user["username"]).first()
    response = client.get(f"api/users/{cur_user.id}/",
                          headers={"Authorization": f"Bearer {token_admin['access_token']}"}, )
    assert response.status_code == 200, response.text
    assert response.json()["email"] == cur_user.email


def test_ban(user, token_admin, client, session):
    with patch.object(auth_user, "red") as redis_mock:
        redis_mock.get.return_value = None
    cur_user = session.query(User).filter(User.username == user["username"]).first()
    assert cur_user.email == user["email"]
    response = client.post(f"api/users/{cur_user.id}?reason=logout",
                           headers={"Authorization": f"Bearer {token_admin['access_token']}"}, )
    assert response.status_code == 201, response.text


def test_ban_(user, token_admin, client, session, monkeypatch):
    with patch.object(auth_user, "red") as redis_mock:
        redis_mock.get.return_value = None
    mock_remove_folder = MagicMock()
    monkeypatch.setattr(
        "src.services.cloud_image.CloudImage.remove_folder", mock_remove_folder
    )
    cur_user = session.query(User).filter(User.username == user["username"]).first()
    response = client.post(f"api/users/{cur_user.id}?reason=ban",
                           headers={"Authorization": f"Bearer {token_admin['access_token']}"}, )
    assert response.status_code == 201, response.text


def test_remove_user(user, token_admin, client, session, monkeypatch):
    with patch.object(auth_user, "red") as redis_mock:
        redis_mock.get.return_value = None
    mock_remove_folder = MagicMock()
    monkeypatch.setattr(
        "src.services.cloud_image.CloudImage.remove_folder", mock_remove_folder
    )
    cur_user = session.query(User).filter(User.username == user["username"]).first()
    response = client.delete(f"api/users/{cur_user.id}/",
                             headers={"Authorization": f"Bearer {token_admin['access_token']}"}, )
    assert response.status_code == 204, response.text


def test_remove_user_repeat(user, token_admin, client, session, monkeypatch):
    with patch.object(auth_user, "red") as redis_mock:
        redis_mock.get.return_value = None
    mock_remove_folder = MagicMock()
    monkeypatch.setattr(
        "src.services.cloud_image.CloudImage.remove_folder", mock_remove_folder
    )
    cur_user = session.query(User).filter(User.username == user["username"]).first()
    response = client.delete(f"api/users/{3}/",
                             headers={"Authorization": f"Bearer {token_admin['access_token']}"}, )
    assert response.status_code == 404, response.text
    assert response.json()["detail"] == messages.NOT_FOUND

