import json
import urllib.request
import urllib.error
from typing import Optional, Dict, Any

from app.config import (
    gemini_api_key, gemini_model, 
    GEMINI_SAFETY_SETTINGS,
)


class GeminiAPIError(Exception):
    """Custom exception for Gemini API errors."""
    pass


def _get_api_url(endpoint: str) -> str:
    """
    Build Gemini API URL for a given endpoint.
    
    Args:
        endpoint: The API endpoint name (e.g., 'generateContent', 'generateAudio')
    
    Returns:
        Full API URL with API key
    """
    api_key = gemini_api_key()
    if not api_key:
        raise GeminiAPIError(
            "GEMINI_API_KEY not configured.\n"
            "→ Add to .env: GEMINI_API_KEY=your_key\n"
            "→ Get from: https://aistudio.google.com/"
        )
    return (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"{gemini_model()}:{endpoint}?key={api_key}"
    )


def call_gemini_llm(
    prompt: str,
    max_tokens: int = 8192,
    temperature: float = 0.75,
) -> str:
    """
    Call Gemini LLM for text generation (podcast, Q&A, etc.).

    Args:
        prompt: The prompt text to send to Gemini
        max_tokens: Maximum tokens in response
        temperature: Creativity/randomness (0.0-1.0)

    Returns:
        Generated text from Gemini

    Raises:
        GeminiAPIError: On API failure
    """
    url = _get_api_url("generateContent")

    body = json.dumps({
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": temperature,
            "maxOutputTokens": max_tokens,
            "topP": 0.95,
        },
        "safetySettings": GEMINI_SAFETY_SETTINGS,
    }).encode("utf-8")

    try:
        req = urllib.request.Request(
            url,
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=90) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        candidates = data.get("candidates", [])
        if not candidates:
            feedback = data.get("promptFeedback", {})
            raise GeminiAPIError(f"No response from Gemini: {feedback}")

        parts = candidates[0].get("content", {}).get("parts", [])
        if not parts:
            raise GeminiAPIError("Empty response from Gemini")

        return parts[0].get("text", "").strip()

    except urllib.error.HTTPError as e:
        error_msg = e.read().decode("utf-8", errors="replace")[:300]
        raise GeminiAPIError(f"Gemini HTTP {e.code}: {error_msg}")
    except urllib.error.URLError as e:
        raise GeminiAPIError(f"Network error: {e}")
    except json.JSONDecodeError as e:
        raise GeminiAPIError(f"Invalid JSON response: {e}")
    except Exception as e:
        raise GeminiAPIError(f"Unexpected error: {e}")


def call_gemini_with_image(
    prompt: str,
    image_base64: str,
    image_mime_type: str = "image/png",
    max_tokens: int = 1024,
    temperature: float = 0.3,
) -> str:
    """
    Call Gemini multimodal API with image for vision analysis.

    Args:
        prompt: Text prompt to send with image
        image_base64: Base64 encoded image data (without data URI prefix)
        image_mime_type: MIME type of image (e.g., 'image/png', 'image/jpeg')
        max_tokens: Maximum tokens in response
        temperature: Creativity/randomness (0.0-1.0)

    Returns:
        Analysis text from Gemini

    Raises:
        GeminiAPIError: On API failure
    """
    url = _get_api_url("generateContent")

    body = json.dumps({
        "contents": [
            {
                "role": "user",
                "parts": [
                    {"inlineData": {"mimeType": image_mime_type, "data": image_base64}},
                    {"text": prompt},
                ],
            }
        ],
        "generationConfig": {
            "temperature": temperature,
            "maxOutputTokens": max_tokens,
            "topP": 0.95,
        },
        "safetySettings": GEMINI_SAFETY_SETTINGS,
    }).encode("utf-8")

    try:
        req = urllib.request.Request(
            url,
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=90) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        candidates = data.get("candidates", [])
        if not candidates:
            feedback = data.get("promptFeedback", {})
            raise GeminiAPIError(f"No response from Gemini: {feedback}")

        parts = candidates[0].get("content", {}).get("parts", [])
        if not parts:
            raise GeminiAPIError("Empty response from Gemini")

        return parts[0].get("text", "").strip()

    except urllib.error.HTTPError as e:
        error_msg = e.read().decode("utf-8", errors="replace")[:300]
        raise GeminiAPIError(f"Gemini HTTP {e.code}: {error_msg}")
    except urllib.error.URLError as e:
        raise GeminiAPIError(f"Network error: {e}")
    except json.JSONDecodeError as e:
        raise GeminiAPIError(f"Invalid JSON response: {e}")
    except Exception as e:
        raise GeminiAPIError(f"Unexpected error: {e}")


def parse_json_response(raw: str) -> Dict[str, Any]:
    """
    Parse JSON from Gemini response, handling markdown code blocks.
    
    Args:
        raw: Raw response that may include ```json...``` markers
    
    Returns:
        Parsed JSON dictionary
        
    Raises:
        GeminiAPIError: If JSON cannot be parsed
    """
    raw_clean = raw.strip()
    
    # Handle markdown code blocks
    if raw_clean.startswith("```"):
        parts = raw_clean.split("```")
        for part in parts:
            if "{" in part and "}" in part:
                raw_clean = part.strip()
                break
        if raw_clean.startswith("json"):
            raw_clean = raw_clean[4:].strip()
    
    try:
        return json.loads(raw_clean)
    except json.JSONDecodeError as e:
        raise GeminiAPIError(
            f"Failed to parse JSON response: {e}\n"
            f"First 500 chars: {raw[:500]}"
        )


# Re-export for backward compatibility
def _call_gemini_legacy(
    prompt: str,
    max_tokens: int = 8192,
    temperature: float = 0.75,
) -> str:
    """
    Legacy wrapper for backward compatibility during migration.
    Use call_gemini_llm() instead.
    """
    try:
        return call_gemini_llm(prompt, max_tokens, temperature)
    except GeminiAPIError as e:
        print(f"[GEMINI ERROR] {e}")
        return f"Error: {e}"
