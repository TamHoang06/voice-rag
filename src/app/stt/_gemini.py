import base64
import json
import urllib.error
import urllib.request

from app.config import GEMINI_SAFETY_SETTINGS, gemini_api_key, gemini_model
from app.stt._utils import _build_prompt


def _call_gemini_stt(
    audio_bytes: bytes,
    mime_type: str,
    language: str = "vi-VN",
    task: str = "transcribe",
) -> str:
    api_key = gemini_api_key()
    if not api_key:
        raise ValueError(
            "GEMINI_API_KEY chưa cấu hình.\n"
            "→ Thêm vào .env: GEMINI_API_KEY=your_key"
        )

    model = gemini_model()
    prompt = _build_prompt(language, task)
    b64 = base64.b64encode(audio_bytes).decode("utf-8")
    print(f"[STT] Gemini → {len(audio_bytes) // 1024} KB | mime={mime_type} | lang={language}")

    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"{model}:generateContent?key={api_key}"
    )
    body = json.dumps({
        "contents": [{
            "role": "user",
            "parts": [
                {"inlineData": {"mimeType": mime_type, "data": b64}},
                {"text": prompt},
            ],
        }],
        "generationConfig": {"temperature": 0.0, "maxOutputTokens": 2048},
        "safetySettings": GEMINI_SAFETY_SETTINGS,
    }).encode("utf-8")

    req = urllib.request.Request(
        url, data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raise RuntimeError(
            f"Gemini STT HTTP {e.code}: "
            f"{e.read().decode('utf-8', errors='replace')[:400]}"
        )
    except urllib.error.URLError as e:
        raise RuntimeError(f"Lỗi kết nối Gemini STT: {e.reason}")

    candidates = data.get("candidates", [])
    if not candidates:
        reason = data.get("promptFeedback", {}).get("blockReason", "UNKNOWN")
        raise RuntimeError(f"Gemini STT không trả về kết quả (blockReason={reason})")

    parts = candidates[0].get("content", {}).get("parts", [])
    return "".join(p.get("text", "") for p in parts).strip()
