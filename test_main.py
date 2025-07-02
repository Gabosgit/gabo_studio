from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_user_get():
    response = client.get("/user/1")
    assert response.status_code == 200