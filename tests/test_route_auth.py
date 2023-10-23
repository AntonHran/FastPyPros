from unittest.mock import MagicMock

from src.database.models import User, BanList
from src.conf import messages


def test_signup(client, user, monkeypatch):
    mock_send_email = MagicMock()
    monkeypatch.setattr("src.routes.auth.send_email", mock_send_email)
    response = client.post("api/auth/signup", json=user)
    assert response.status_code == 201, response.text
    payload = response.json()
    assert payload["email"] == user.get("email")


def test_signup_with_duplicated_email(client, user, monkeypatch):
    mock_send_email = MagicMock()
    monkeypatch.setattr("src.routes.auth.send_email", mock_send_email)
    response = client.post("/api/auth/signup", json=user)
    assert response.status_code == 409, response.text
    payload = response.json()
    assert payload["detail"] == messages.ACCOUNT_EXISTS


def test_login(client, user, session):
    current_user: User = (
        session.query(User).filter(User.email == user.get("email")).first()
    )
    current_user.confirmed = True
    session.commit()
    response = client.post(
        "/api/auth/login",
        data={"username": user.get("email"), "password": user.get("password")},
    )
    assert response.status_code == 201, response.text
    payload = response.json()
    assert payload["token_type"] == messages.TOKEN_TYPE


def test_login_user_not_confirmed(client, user, session):
    current_user: User = (
        session.query(User).filter(User.email == user.get("email")).first()
    )
    current_user.confirmed = False
    session.commit()
    response = client.post(
        "/api/auth/login",
        data={"username": user.get("email"), "password": user.get("password")},
    )
    assert response.status_code == 401, response.text
    payload = response.json()
    assert payload["detail"] == messages.EMAIL_NOT_CONFIRMED


def test_login_user_with_wrong_email(client, user, session):
    current_user: User = (
        session.query(User).filter(User.email == user.get("email")).first()
    )
    print(current_user)
    response = client.post(
        "/api/auth/login",
        data={"username": "user2@example.com", "password": user.get("password")},
    )
    assert response.status_code == 401, response.text
    payload = response.json()  # token
    assert payload["detail"] == messages.INVALID_EMAIL


def test_login_user_with_wrong_password(client, user, session):
    current_user: User = (
        session.query(User).filter(User.email == user.get("email")).first()
    )
    current_user.confirmed = True
    session.commit()
    response = client.post(
        "/api/auth/login", data={"username": current_user.email, "password": "password"}
    )
    assert response.status_code == 401, response.text
    payload = response.json()
    assert payload["detail"] == messages.INVALID_PASSWORD


def test_login_banned_user(client, user, session):
    current_user: User = (
        session.query(User).filter(User.email == user.get("email")).first()
    )
    new_record = BanList(access_token=current_user.access_token, reason="ban")
    session.add(new_record)
    session.commit()
    response = client.post(
        "api/auth/login",
        data={"username": user.get("email"), "password": user.get("password")},
    )
    assert response.status_code == 403, response.text
    payload = response.json()
    assert payload["detail"] == messages.BAN


def test_refresh_token(client, user, session, monkeypatch):
    mock_send_email = MagicMock()
    monkeypatch.setattr("src.routes.auth.send_email", mock_send_email)
    current_user: User = (
        session.query(User).filter(User.email == user.get("email")).first()
    )
    current_user.confirmed = True
    session.commit()
    response_ = client.get(
        "/api/auth/refresh_token",
        headers={"Authorization": f"Bearer {current_user.refresh_token}"},
    )
    assert response_.status_code == 200, response_.text
    data = response_.json()
    assert data["token_type"] == messages.TOKEN_TYPE


def test_refresh_token_(client, user, session, monkeypatch):
    mock_send_email = MagicMock()
    monkeypatch.setattr("src.routes.auth.send_email", mock_send_email)
    response_ = client.get(
        "/api/auth/refresh_token",
    )
    assert response_.status_code == 403, response_.text
    data = response_.json()
    assert data["detail"] == messages.NOT_AUTHENTICATED


def test_refresh_token__(client, user, session, monkeypatch):
    mock_send_email = MagicMock()
    monkeypatch.setattr("src.routes.auth.send_email", mock_send_email)
    response_ = client.get(
        "/api/auth/refresh_token",
        headers={"Authorization": f"Bearer access_token"},
    )
    assert response_.status_code == 401, response_.text
    data = response_.json()
    assert data["detail"] == messages.COULD_NOT_VALIDATE_CREDENTIALS


def test_request_email(client, user, session, monkeypatch):
    mock_send_email = MagicMock()
    monkeypatch.setattr("src.routes.auth.send_email", mock_send_email)
    response = client.post(
        "/api/auth/request_email",
        json={"email": user.get("email")},
    )
    print(response.json())
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["message"] == messages.EMAIL_ALREADY_CONFIRMED


def test_reset_password(client, user):
    response = client.post(
        "/api/auth/reset_password",
        json={
            "email": user.get("email"),
            "new_password": "123456",
            "confirm_password": "123456",
        },
    )
    assert response.status_code == 200, response.text
    payload = response.json()
    print(payload)
    assert payload["message"] == messages.RESET_COMPLETE


def test_reset_password_(client, user):
    response = client.post(
        "/api/auth/reset_password",
        json={
            "email": "lkbm@example.com",
            "new_password": "123456",
            "confirm_password": "123456",
        },
    )
    assert response.status_code == 404, response.text
    payload = response.json()
    print(payload)
    assert payload["detail"] == messages.INVALID_EMAIL


def test_reset_password__(client, user):
    response = client.post(
        "/api/auth/reset_password",
        json={
            "email": user.get("email"),
            "new_password": "123456",
            "confirm_password": "123450",
        },
    )
    assert response.status_code == 409, response.text
    payload = response.json()
    assert payload["detail"] == messages.PASSWORDS_NOT_EQUAL


def test_logout(client, user, session):
    cur_user: User = session.query(User).filter(User.email == user.get("email")).first()
    headers = {"Authorization": f"Bearer {cur_user.access_token}"}
    response = client.post("api/auth/logout", headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert "message" in data
    assert data["message"] == messages.LOGOUT


def test_confirmed_email(client, user, session, monkeypatch):
    mock_send_email = MagicMock()
    monkeypatch.setattr("src.routes.auth.send_email", mock_send_email)
    mock_send_get_email_from_token = MagicMock()
    monkeypatch.setattr("src.services.auth.Token.get_email_from_token", mock_send_get_email_from_token)
    mock_send_get_email_from_token.return_value = user["email"]
    confirmation_token = mock_send_email()
    cur_user: User = session.query(User).filter(User.email == user.get("email")).first()

    response = client.get(f"api/auth/confirmed_email/{confirmation_token}",
                          headers={"Authorization": f"Bearer {cur_user.access_token}"})
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == messages.EMAIL_ALREADY_CONFIRMED
    confirmed_user = session.query(User).filter(User.email == user["email"]).first()
    assert confirmed_user.confirmed == True


def test_confirmed_email_(client, user, session, monkeypatch):
    mock_send_email = MagicMock()
    monkeypatch.setattr("src.routes.auth.send_email", mock_send_email)
    mock_send_get_email_from_token = MagicMock()
    monkeypatch.setattr("src.services.auth.Token.get_email_from_token", mock_send_get_email_from_token)
    mock_send_get_email_from_token.return_value = user["password"]
    confirmation_token = mock_send_email()
    cur_user: User = session.query(User).filter(User.email == user.get("email")).first()

    response = client.get(f"api/auth/confirmed_email/{confirmation_token}",
                          headers={"Authorization": f"Bearer {cur_user.access_token}"})
    assert response.status_code == 400
    data = response.json()
    assert data["detail"] == messages.VERIFICATION_ERROR


def test_confirmed_email__(client, user, session, monkeypatch):
    mock_send_email = MagicMock()
    monkeypatch.setattr("src.routes.auth.send_email", mock_send_email)
    mock_send_get_email_from_token = MagicMock()
    monkeypatch.setattr("src.services.auth.Token.get_email_from_token", mock_send_get_email_from_token)
    mock_send_get_email_from_token.return_value = user["email"]
    confirmation_token = mock_send_email()
    cur_user: User = session.query(User).filter(User.email == user.get("email")).first()
    cur_user.confirmed = False
    session.commit()
    session.refresh(cur_user)
    response = client.get(f"api/auth/confirmed_email/{confirmation_token}",
                          headers={"Authorization": f"Bearer {cur_user.access_token}"})
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == messages.EMAIL_CONFIRMED
