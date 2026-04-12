import io
from pathlib import Path

from app.config import default_audio_format


def get_output_format(fmt: str = None) -> str:
    if not fmt:
        return default_audio_format()
    fmt = fmt.strip().lower()
    if not fmt.startswith("."):
        fmt = "." + fmt
    return fmt if fmt in {".wav", ".mp3", ".m4a", ".ogg", ".flac", ".webm", ".mp4"} else default_audio_format()


def _build_prompt(language: str, task: str) -> str:
    lang_names = {
        "vi-VN": "tiếng Việt", "vi": "tiếng Việt",
        "en-US": "English",    "en": "English",
        "zh-CN": "中文",       "ja-JP": "日本語",
        "ko-KR": "한국어",     "fr-FR": "Français",
    }
    if task == "translate":
        return (
            "Transcribe the audio and translate everything to English. "
            "Return ONLY the translated text, no explanation, no timestamps."
        )
    lang = lang_names.get(language, language)
    return (
        f"Transcribe this audio accurately in {lang}. "
        "Return ONLY the transcript. "
        "No timestamps, no speaker labels, no explanation. "
        "If silent or unclear, return empty string."
    )


def _estimate_duration(audio_bytes: bytes) -> float:
    try:
        import soundfile as sf
        data, sr = sf.read(io.BytesIO(audio_bytes), dtype="float32", always_2d=False)
        return round(len(data) / sr, 2)
    except Exception:
        return round(len(audio_bytes) / 2000, 1)
