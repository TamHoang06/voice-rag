import importlib

import pytest
from fastapi.testclient import TestClient


def test_rate_limiting_exceeded(monkeypatch):
    monkeypatch.setenv("RATE_LIMIT_REQUESTS", "3")
    monkeypatch.setenv("RATE_LIMIT_WINDOW_SECONDS", "60")

    import main
    importlib.reload(main)

    client = TestClient(main.app)

    for i in range(3):
        response = client.get("/api")
        assert response.status_code == 200
        assert response.json()["name"] == "AI Podcast Agent"

    response = client.get("/api")
    assert response.status_code == 429
    assert "Too many requests" in response.text


def test_rate_limit_exempt_paths(monkeypatch):
    monkeypatch.setenv("RATE_LIMIT_REQUESTS", "1")
    monkeypatch.setenv("RATE_LIMIT_WINDOW_SECONDS", "60")

    import main
    importlib.reload(main)

    client = TestClient(main.app)

    response = client.get("/docs")
    assert response.status_code == 200


def test_rate_limit_separate_api_keys(monkeypatch):
    monkeypatch.setenv("RATE_LIMIT_REQUESTS", "2")
    monkeypatch.setenv("RATE_LIMIT_WINDOW_SECONDS", "60")

    import main
    importlib.reload(main)

    client = TestClient(main.app)

    first = client.get("/api", headers={"x-api-key": "key-a"})
    second = client.get("/api", headers={"x-api-key": "key-a"})
    assert first.status_code == 200
    assert second.status_code == 200

    third = client.get("/api", headers={"x-api-key": "key-a"})
    assert third.status_code == 429

    other = client.get("/api", headers={"x-api-key": "key-b"})
    assert other.status_code == 200


def test_upload_route_throttle(monkeypatch):
    monkeypatch.setenv("RATE_LIMIT_UPLOAD_REQUESTS", "1")
    monkeypatch.setenv("RATE_LIMIT_UPLOAD_WINDOW_SECONDS", "60")
    monkeypatch.setenv("RATE_LIMIT_REQUESTS", "60")
    monkeypatch.setenv("RATE_LIMIT_WINDOW_SECONDS", "60")

    import main
    importlib.reload(main)

    client = TestClient(main.app)

    file_payload = {
        "file": ("test.txt", b"Hello world", "text/plain"),
    }

    response1 = client.post("/upload", files=file_payload)
    assert response1.status_code in (200, 201)

    response2 = client.post("/upload", files=file_payload)
    assert response2.status_code == 429
