from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_not_found_item():
    r = client.get("/items/999")
    assert r.status_code == 404
    body = r.json()
    assert body["status"] == 404
    assert body["title"] == "not found"
    assert body["type"].endswith("#not_found")
    assert body["correlation_id"]


def test_validation_error():
    r = client.post("/items", json={"name": ""})
    assert r.status_code == 422
    body = r.json()
    assert body["status"] == 422
    assert body["type"].endswith("#validation_error")
    assert body["title"] == "Request validation error"
    assert body["correlation_id"]
