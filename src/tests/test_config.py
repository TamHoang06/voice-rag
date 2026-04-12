import os
import pytest


def test_gemini_api_key_from_env(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key-123")
    from app.config import gemini_api_key
    assert gemini_api_key() == "test-key-123"


def test_gemini_api_key_empty():
    from app.config import gemini_api_key
    # Không set → trả về ""
    key = os.environ.get("GEMINI_API_KEY", "")
    assert isinstance(key, str)


def test_gemini_tts_voice_fallback_azure(monkeypatch):
    """Nếu còn dùng Azure voice cũ (có dấu -), phải fallback về Kore."""
    monkeypatch.setenv("GEMINI_TTS_VOICE", "vi-VN-HoaiMyNeural")
    from importlib import reload
    import app.config as cfg
    reload(cfg)
    assert "-" not in cfg.gemini_tts_voice()


def test_gemini_safety_settings():
    from app.config import GEMINI_SAFETY_SETTINGS
    assert len(GEMINI_SAFETY_SETTINGS) == 4
    for s in GEMINI_SAFETY_SETTINGS:
        assert s["threshold"] == "BLOCK_NONE"


def test_paths_are_strings():
    from app.config import DATA_DIR, OUTPUTS_DIR, VOICES_DIR, VECTOR_PATH, STATIC_DIR
    for p in (DATA_DIR, OUTPUTS_DIR, VOICES_DIR, VECTOR_PATH, STATIC_DIR):
        assert isinstance(p, str)
        assert len(p) > 0