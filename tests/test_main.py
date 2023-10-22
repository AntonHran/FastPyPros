import os
import sys

from fastapi.testclient import TestClient

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))

from main import app


client = TestClient(app)


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Here your images!"}


def test_healthchecker():
    response = client.get("/api/healthchecker")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to FastAPI"}

