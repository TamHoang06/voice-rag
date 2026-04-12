import os
import time

from app.config import OUTPUTS_DIR, gemini_tts_voice
from app.tts._gemini import _call_gemini_tts
from app.core.logger import get_logger
from app.tts._utils import _merge_wav, _pcm_to_wav, _pad
from app.utils import split_text

# ── Constants ─────────────────────────────────────────────────────────────────
AUDIO_FILE = os.path.join(OUTPUTS_DIR, "answer.wav")
MAX_CHARS_CHUNK = 4500
MIN_CHARS = 10

GEMINI_VOICES = {
    "Aoede":   "Aoede — Nữ, tự nhiên",
    "Charon":  "Charon — Nam, trầm",
    "Fenrir":  "Fenrir — Nam, mạnh",
    "Kore":    "Kore — Nữ, nhẹ nhàng",
    "Puck":    "Puck — Nam, linh hoạt",
    "Schedar": "Schedar — Nữ, rõ ràng",
    "Leda":    "Leda — Nữ, ấm áp",
    "Orus":    "Orus — Nam, sang trọng",
    "Zephyr":  "Zephyr — Nữ, sáng",
}


def is_ready() -> bool:
    from app.config import gemini_api_key

    logger = get_logger(__name__)
    ok = bool(gemini_api_key())
    if not ok:
        logger.warning("[TTS] is_ready=False — chưa set GEMINI_API_KEY")
    return ok


def text_to_speech(text: str, output_path: str = None, voice: str = None) -> str:
    """
    Chuyển text → WAV bằng Gemini 2.5 Flash TTS.

    Args:
        text:        Văn bản cần đọc
        output_path: Đường dẫn output WAV (default: outputs/answer.wav)
        voice:       Tên giọng Gemini: Kore, Charon, Aoede, ...

    Returns:
        Đường dẫn file WAV đã lưu
    """
    if not text or not text.strip():
        raise ValueError("Input text is empty.")

    os.makedirs(OUTPUTS_DIR, exist_ok=True)
    out = os.path.abspath(output_path or AUDIO_FILE)
    logger = get_logger(__name__)
    chunks = split_text(text.strip(), max_chars=MAX_CHARS_CHUNK)
    logger.info("[TTS] %d chunk(s) | voice=%s", len(chunks), voice or gemini_tts_voice())

    if len(chunks) == 1:
        wav = _call_gemini_tts(chunks[0], voice=voice)
    else:
        parts = []
        logger = get_logger(__name__)
        for i, chunk in enumerate(chunks, 1):
            logger.debug("[TTS] [%d/%d] %s…", i, len(chunks), chunk[:60])
            parts.append(_call_gemini_tts(chunk, voice=voice))
            if i < len(chunks):
                time.sleep(0.3)
        wav = _merge_wav(parts)

    logger = get_logger(__name__)
    with open(out, "wb") as f:
        f.write(wav)

    logger.info("[TTS] Saved → %s (%d KB)", out, os.path.getsize(out) // 1024)
    return out
