import importlib

import pytest
from fastapi.testclient import TestClient


def test_get_available_voices():
    """Test getting all available voices."""
    import main
    importlib.reload(main)
    client = TestClient(main.app)

    response = client.get("/voices/available")
    assert response.status_code == 200
    data = response.json()

    # Check structure
    assert "gemini" in data

    # Check each provider has voices
    for provider, voices in data.items():
        assert isinstance(voices, list)
        assert len(voices) > 0
        for voice in voices:
            assert "id" in voice
            assert "name" in voice
            assert "language" in voice
            assert "gender" in voice
            assert "description" in voice


def test_get_provider_voices():
    """Test getting voices for a specific provider."""
    import main
    importlib.reload(main)
    client = TestClient(main.app)

    response = client.get("/voices/available/gemini")
    assert response.status_code == 200
    voices = response.json()

    assert isinstance(voices, list)
    assert len(voices) > 0
    assert voices[0]["id"] == "Kore"


def test_get_provider_voices_invalid():
    """Test getting voices for invalid provider."""
    import main
    importlib.reload(main)
    client = TestClient(main.app)

    response = client.get("/voices/available/invalid")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


def test_get_voice_providers():
    """Test getting list of voice providers."""
    import main
    importlib.reload(main)
    client = TestClient(main.app)

    response = client.get("/voices/providers")
    assert response.status_code == 200
    data = response.json()

    assert "providers" in data
    providers = data["providers"]
    assert "gemini" in providers
    assert "azure" not in providers
    assert "openai" not in providers
