import pytest
from app.utils import postprocess_transcript
from app.stt.stt import get_output_format, _build_prompt


def test_postprocess_strips():
    assert postprocess_transcript("  hello world  ") == "Hello world"

def test_postprocess_removes_brackets():
    assert "[Music]" not in postprocess_transcript("[Music] Xin chào")

def test_postprocess_capitalizes():
    assert postprocess_transcript("xin chào")[0].isupper()

def test_postprocess_empty():
    assert postprocess_transcript("") == ""
    assert postprocess_transcript("   ") == ""

def test_postprocess_collapses_spaces():
    result = postprocess_transcript("hello    world")
    assert "  " not in result

def test_output_format_default():
    fmt = get_output_format(None)
    assert fmt.startswith(".")

def test_output_format_normalizes():
    assert get_output_format("mp3") == ".mp3"
    assert get_output_format(".wav") == ".wav"

def test_output_format_invalid_fallback():
    result = get_output_format(".xyz")
    assert result in {".wav", ".mp3", ".m4a", ".ogg", ".flac", ".webm", ".mp4"}

def test_build_prompt_vi():
    prompt = _build_prompt("vi-VN", "transcribe")
    assert "tiếng Việt" in prompt
    assert "ONLY" in prompt

def test_build_prompt_translate():
    prompt = _build_prompt("vi-VN", "translate")
    assert "English" in prompt
    assert "translate" in prompt.lower()

def test_build_prompt_unknown_lang():
    prompt = _build_prompt("th-TH", "transcribe")
    assert "th-TH" in prompt

def test_build_prompt_en():
    prompt = _build_prompt("en-US", "transcribe")
    assert "English" in prompt