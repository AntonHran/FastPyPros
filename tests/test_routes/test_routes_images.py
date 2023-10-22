import pytest
from fastapi.testclient import TestClient
from src.database.models import User, Image

def test_upload_file(client: TestClient, user, session, in_memory_file):
    files = [('file', ('test.jpg', in_memory_file, 'image/jpeg'))]

    response = client.post(
        "/images",
        headers={"Authorization": "Bearer"},
        data={"description": "Test image description"},
        files=files,
    )

    assert response.status_code == 201
    image = Image(**response.json())
    assert image.id is not None

def test_get_image(client, image, session, user, mock_image_response):

    response = client.get(f"/images/{image.id}")

    assert response.status_code == 200

    response_data = response.json()
    assert response_data == mock_image_response

def test_get_images(client, session, user, mock_image_response):
    response = client.get("/images")

    expected_response_data = [
        mock_image_response
    ]
    assert response.status_code == 200
    response_data = response.json()
    assert response_data == expected_response_data