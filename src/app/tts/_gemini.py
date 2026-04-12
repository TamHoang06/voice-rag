import base64
import json
import urllib.error
import urllib.request

from app.config import GEMINI_SAFETY_SETTINGS, gemini_api_key, gemini_tts_model, gemini_tts_voice
from app.tts._utils import _pad, _pcm_to_wav


def _call_gemini_tts(text: str, voice: str = None) -> bytes:
    """Call Gemini TTS API and return WAV bytes."""
    api_key = gemini_api_key()
    if not api_key:
        raise ValueError(
            "GEMINI_API_KEY chưa cấu hình.\n"
            "→ Thêm vào .env: GEMINI_API_KEY=your_key\n"
            "→ Lấy tại: https://aistudio.google.com/"
        )

    text = _pad(text)
    voice = voice or gemini_tts_voice()
    model = gemini_tts_model()
    print(f"[TTS] Gemini → {len(text)} chars | voice={voice} | model={model}")

    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"{model}:generateContent?key={api_key}"
    )
    body = json.dumps({
        "contents": [{"role": "user", "parts": [{"text": text}]}],
        "generationConfig": {
            "responseModalities": ["AUDIO"],
            "speechConfig": {
                "voiceConfig": {"prebuiltVoiceConfig": {"voiceName": voice}}
            },
        },
        "safetySettings": GEMINI_SAFETY_SETTINGS,
    }).encode("utf-8")

    req = urllib.request.Request(
        url, data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        err = e.read().decode("utf-8", errors="replace")
        print(f"[TTS] HTTP {e.code}: {err}")
        raise RuntimeError(
            f"Gemini TTS HTTP {e.code}: {err[:400]}\n"
            f"Voice={voice} | Key={'set' if api_key else 'EMPTY'}"
        )
    except urllib.error.URLError as e:
        raise RuntimeError(f"Lỗi kết nối Gemini TTS: {e.reason}")

    candidates = data.get("candidates", [])
    if not candidates:
        block = data.get("promptFeedback", {}).get("blockReason", "UNKNOWN")
        if block == "PROHIBITED_CONTENT":
            raise RuntimeError(
                "Gemini TTS từ chối nội dung (PROHIBITED_CONTENT).\n"
                f"Text: '{text[:80]}'\n"
                "Nguyên nhân: text quá ngắn, chứa ký tự đặc biệt/URL/code."
            )
        raise RuntimeError(f"Gemini TTS không trả về candidates (blockReason={block})")

    for part in candidates[0].get("content", {}).get("parts", []):
        inline = part.get("inlineData", {})
        if inline.get("mimeType", "").startswith("audio/") and inline.get("data"):
            pcm = base64.b64decode(inline["data"])
            print(f"[TTS] OK — {len(pcm):,} bytes PCM")
            return _pcm_to_wav(pcm)

    raise RuntimeError("Gemini TTS không trả về audio inlineData.")
