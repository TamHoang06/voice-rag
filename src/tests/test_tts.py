import struct
import pytest


def test_pcm_to_wav_magic_bytes():
    from app.tts.tts import _pcm_to_wav
    wav = _pcm_to_wav(b"\x00" * 200)
    assert wav[:4] == b"RIFF"
    assert wav[8:12] == b"WAVE"
    assert wav[12:16] == b"fmt "
    assert wav[36:40] == b"data"

def test_pcm_to_wav_sample_rate():
    from app.tts.tts import _pcm_to_wav
    wav = _pcm_to_wav(b"\x00" * 100, sr=24000)
    sr = struct.unpack_from("<I", wav, 24)[0]
    assert sr == 24000

def test_pcm_to_wav_data_size():
    from app.tts.tts import _pcm_to_wav
    pcm = b"\xff" * 480
    wav = _pcm_to_wav(pcm)
    assert struct.unpack_from("<I", wav, 40)[0] == 480

def test_pcm_to_wav_total_length():
    from app.tts.tts import _pcm_to_wav
    pcm = b"\x00" * 100
    assert len(_pcm_to_wav(pcm)) == 44 + len(pcm)

def test_pad_empty_returns_fallback():
    from app.tts.tts import _pad
    assert _pad("") == "Nội dung trống."

def test_pad_short_adds_period():
    from app.tts.tts import _pad, MIN_CHARS
    result = _pad("Hi")
    assert result.endswith(".")

def test_pad_long_unchanged():
    from app.tts.tts import _pad
    text = "Đây là một đoạn văn đủ dài để không cần pad thêm gì cả."
    assert _pad(text) == text

def test_split_short_no_split():
    from app.utils import split_text
    text = "Ngắn."
    assert split_text(text, max_chars=500) == [text]

def test_split_long_multiple_chunks():
    from app.utils import split_text
    text   = ("Đây là một câu văn dài. " * 300).strip()
    chunks = split_text(text, max_chars=500)
    assert len(chunks) > 1
    assert all(c.strip() for c in chunks)

def test_split_no_empty_chunks():
    from app.utils import split_text
    chunks = split_text("Câu một. Câu hai. Câu ba.", max_chars=15)
    assert all(c.strip() for c in chunks)

def test_is_ready_false(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "")
    from app.tts.tts import is_ready
    assert is_ready() is False

def test_is_ready_true(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "fake-key")
    from app.tts.tts import is_ready
    assert is_ready() is True

def test_gemini_voices_content():
    from app.tts.tts import GEMINI_VOICES
    assert "Kore" in GEMINI_VOICES
    assert "Charon" in GEMINI_VOICES
    assert len(GEMINI_VOICES) >= 6