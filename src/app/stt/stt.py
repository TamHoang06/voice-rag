import os
from pathlib import Path

from app.config import AUDIO_MIME_MAP, DATA_DIR
from app.stt._gemini import _call_gemini_stt
from app.stt._utils import get_output_format, _build_prompt, _estimate_duration
from app.utils import postprocess_transcript


def transcribe_audio(
    audio_path: str,
    language: str = "vi-VN",
    task: str = "transcribe",
) -> dict:
    """
    Transcribe file audio bằng Gemini 2.5 Flash.

    Returns:
        dict: text, language, duration, segments
    """
    path = Path(audio_path).resolve()
    if not path.exists():
        raise FileNotFoundError(f"[STT] File không tồn tại: '{path}'")

    ext = path.suffix.lower()
    mime_type = AUDIO_MIME_MAP.get(ext, "audio/wav")
    audio_bytes = path.read_bytes()
    print(f"[STT] Reading: {path.name} ({len(audio_bytes) // 1024} KB)")

    locale = {
        "vi": "vi-VN", "en": "en-US", "zh": "zh-CN",
        "ja": "ja-JP", "ko": "ko-KR", "fr": "fr-FR",
    }.get(language, language) if len(language) <= 3 else language

    raw = _call_gemini_stt(audio_bytes, mime_type, locale, task)
    text = postprocess_transcript(raw)
    duration = _estimate_duration(audio_bytes)

    print(f"[STT] Done — {duration}s | {text[:100]}{'…' if len(text) > 100 else ''}")
    return {"text": text, "language": locale, "duration": duration, "segments": []}


def transcribe_bytes(
    audio_bytes: bytes,
    filename: str = "upload.wav",
    language: str = "vi-VN",
    task: str = "transcribe",
    temp_dir: str = None,
    output_format: str = None,
) -> dict:
    """Transcribe từ bytes — lưu temp → transcribe → xoá temp."""
    temp_dir = os.path.abspath(temp_dir or DATA_DIR)
    os.makedirs(temp_dir, exist_ok=True)

    ext = Path(filename).suffix.lower() or ".wav"
    temp_path = os.path.join(temp_dir, f"_stt_{os.urandom(8).hex()}{ext}")

    print(f"[STT] Writing {len(audio_bytes) // 1024} KB → '{temp_path}'")
    with open(temp_path, "wb") as f:
        f.write(audio_bytes)

    try:
        result = transcribe_audio(temp_path, language=language, task=task)
        result["output_format"] = get_output_format(output_format)
        return result
    finally:
        try:
            os.remove(temp_path)
        except Exception:
            pass


def list_supported_formats() -> dict:
    return {
        "input_formats": sorted({".wav", ".mp3", ".m4a", ".ogg", ".flac", ".webm", ".mp4"}),
        "output_formats": sorted({".wav", ".mp3", ".m4a", ".ogg", ".flac", ".webm", ".mp4"}),
        "default_output_format": get_output_format(None),
        "stt_engine": f"Gemini {os.environ.get('GEMINI_MODEL', 'gemini-2.5-flash')}",
        "tts_engine": "Gemini 2.5 Flash TTS",
    }
