import os
from pathlib import Path

_BASE_DIR = Path(__file__).parent.parent
DATA_DIR      = str(_BASE_DIR / "data")
OUTPUTS_DIR   = str(_BASE_DIR / "outputs")
VOICES_DIR    = str(_BASE_DIR / "voices")
VECTOR_PATH   = str(_BASE_DIR / "vectorstore")
STATIC_DIR    = str(_BASE_DIR / "static")

SUPPORTED_DOC_EXT      = {".pdf", ".docx", ".txt"}
MAX_UPLOAD_SIZE        = 50 * 1024 * 1024   # 50 MB
MAX_AUDIO_UPLOAD_SIZE  = 30 * 1024 * 1024   # 30 MB
#Gemini LLM
def gemini_api_key() -> str:
    return os.environ.get("GEMINI_API_KEY", "")

def gemini_model() -> str:
    return os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")

#Gemini TTS
def gemini_tts_model() -> str:
    return os.environ.get("GEMINI_TTS_MODEL", "gemini-2.5-flash-preview-tts")

def gemini_tts_voice() -> str:
    v = os.environ.get("GEMINI_TTS_VOICE") or os.environ.get("AZURE_VOICE_NAME", "Kore")
    return v if "-" not in v else "Kore"   # fallback nếu còn Azure voice cũ

#OpenAI (fallback TTS)
def openai_api_key() -> str:
    return os.environ.get("OPENAI_API_KEY", "")

def openai_tts_model() -> str:
    return os.environ.get("OPENAI_TTS_MODEL", "tts-1-hd")

def openai_tts_voice() -> str:
    return os.environ.get("OPENAI_TTS_VOICE", "shimmer")

#Audio
SUPPORTED_AUDIO_EXT   = {".wav", ".mp3", ".m4a", ".ogg", ".flac", ".webm", ".mp4"}
SUPPORTED_OUTPUT_FMTS = {".wav", ".mp3", ".m4a", ".ogg", ".flac", ".webm", ".mp4"}

def default_audio_format() -> str:
    return os.environ.get("AUDIO_OUTPUT_FORMAT", ".wav")

#Rate limiting
def rate_limit_requests() -> int:
    return int(os.environ.get("RATE_LIMIT_REQUESTS", "60"))


def rate_limit_window_seconds() -> int:
    return int(os.environ.get("RATE_LIMIT_WINDOW_SECONDS", "60"))


def rate_limit_route_policies() -> dict[str, tuple[int, int]]:
    """Route-specific rate limit policies.

    Returns a mapping of request path to (max_requests, window_seconds).
    Heavy routes like /upload and /transcribe use tighter limits by default.
    """
    return {
        "/upload": (
            int(os.environ.get("RATE_LIMIT_UPLOAD_REQUESTS", "5")),
            int(os.environ.get("RATE_LIMIT_UPLOAD_WINDOW_SECONDS", "60")),
        ),
        "/transcribe": (
            int(os.environ.get("RATE_LIMIT_TRANSCRIBE_REQUESTS", "10")),
            int(os.environ.get("RATE_LIMIT_TRANSCRIBE_WINDOW_SECONDS", "60")),
        ),
    }

#Gemini safety settings
GEMINI_SAFETY_SETTINGS = [
    {"category": "HARM_CATEGORY_HARASSMENT",        "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH",       "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
]

#MIME maps
AUDIO_MIME_MAP = {
    ".wav":  "audio/wav",
    ".mp3":  "audio/mp3",
    ".m4a":  "audio/mp4",
    ".ogg":  "audio/ogg",
    ".flac": "audio/flac",
    ".webm": "audio/webm",
    ".mp4":  "audio/mp4",
}

FILE_MIME_MAP = {
    ".wav":  "audio/wav",
    ".mp3":  "audio/mpeg",
    ".m4a":  "audio/mp4",
    ".ogg":  "audio/ogg",
    ".flac": "audio/flac",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".pdf":  "application/pdf",
}

#Voice Library
AVAILABLE_VOICES = {
    "gemini": [
        {"id": "Kore", "name": "Kore", "language": "en", "gender": "female", "description": "Natural female voice"},
        {"id": "Puck", "name": "Puck", "language": "en", "gender": "male", "description": "Energetic male voice"},
        {"id": "Charon", "name": "Charon", "language": "en", "gender": "male", "description": "Deep male voice"},
        {"id": "Fenrir", "name": "Fenrir", "language": "en", "gender": "male", "description": "Powerful male voice"},
        {"id": "Aoede", "name": "Aoede", "language": "en", "gender": "female", "description": "Melodic female voice"},
    ],
    "azure": [
        {"id": "vi-VN-HoaiMyNeural", "name": "Hoài My", "language": "vi", "gender": "female", "description": "Vietnamese female voice"},
        {"id": "vi-VN-NamMinhNeural", "name": "Nam Minh", "language": "vi", "gender": "male", "description": "Vietnamese male voice"},
        {"id": "en-US-AriaNeural", "name": "Aria", "language": "en", "gender": "female", "description": "English female voice"},
        {"id": "en-US-ZiraNeural", "name": "Zira", "language": "en", "gender": "female", "description": "English female voice"},
        {"id": "en-GB-SoniaNeural", "name": "Sonia", "language": "en-GB", "gender": "female", "description": "British female voice"},
    ],
    "openai": [
        {"id": "alloy", "name": "Alloy", "language": "en", "gender": "neutral", "description": "Balanced neutral voice"},
        {"id": "echo", "name": "Echo", "language": "en", "gender": "male", "description": "Deep male voice"},
        {"id": "fable", "name": "Fable", "language": "en", "gender": "female", "description": "Warm female voice"},
        {"id": "onyx", "name": "Onyx", "language": "en", "gender": "male", "description": "Powerful male voice"},
        {"id": "nova", "name": "Nova", "language": "en", "gender": "female", "description": "Youthful female voice"},
        {"id": "shimmer", "name": "Shimmer", "language": "en", "gender": "female", "description": "Bright female voice"},
    ],
}