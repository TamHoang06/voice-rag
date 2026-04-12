from contextlib import asynccontextmanager
from dotenv import load_dotenv
import os
import pathlib
import sys

_CUR_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(_CUR_DIR, ".env"))

sys.path.insert(0, _CUR_DIR)

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from app.config import (
    DATA_DIR,
    OUTPUTS_DIR,
    STATIC_DIR,
    VOICES_DIR,
    rate_limit_requests,
    rate_limit_window_seconds,
)
from app.core.logger import get_logger
from app.core.rate_limit import RateLimitMiddleware
from app.rag.loader import load_vectorstore
from app.routers import audio, document, podcast, voices
from app.tts import is_ready as tts_ready

logger = get_logger(__name__)


def _run_startup_tasks() -> None:
    load_vectorstore()
    ready = tts_ready()
    logger.info("TTS ready = %s", ready)
    if not ready:
        logger.warning("GEMINI_API_KEY chua duoc cau hinh trong .env: TTS/STT se khong kha dung")
    logger.info("Stack: Gemini 2.5 Flash - LLM + TTS + STT")
    logger.info("Docs  -> http://localhost:8000/docs")
    logger.info("App   -> http://localhost:8000/podcast-player")


@asynccontextmanager
async def lifespan(app: FastAPI):
    _run_startup_tasks()
    yield


app = FastAPI(
    title="AI Podcast Agent",
    description="Gemini 2.5 Flash - LLM + TTS + STT",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    RateLimitMiddleware,
    max_requests=rate_limit_requests(),
    window_seconds=rate_limit_window_seconds(),
)

for _d in (OUTPUTS_DIR, DATA_DIR, STATIC_DIR, VOICES_DIR):
    os.makedirs(_d, exist_ok=True)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

app.include_router(document.router)
app.include_router(podcast.router)
app.include_router(audio.router)
app.include_router(voices.router)


def _serve(filename: str) -> HTMLResponse:
    path = pathlib.Path(STATIC_DIR) / filename
    if not path.exists():
        return HTMLResponse(f"<h1>Khong tim thay {filename}</h1>", status_code=404)
    return HTMLResponse(path.read_text(encoding="utf-8"))


@app.get("/", response_class=HTMLResponse)
def serve_index():
    return _serve("index.html")


@app.get("/ui", response_class=HTMLResponse)
def serve_ui():
    return _serve("index.html")


@app.get("/podcast-player", response_class=HTMLResponse)
def serve_podcast():
    return _serve("podcast_player.html")


@app.get("/voice-library", response_class=HTMLResponse)
def serve_voice_library():
    return _serve("voice_library.html")


@app.get("/api")
def api_info():
    return {
        "name": "AI Podcast Agent",
        "version": "2.0.0",
        "stack": "Gemini 2.5 Flash (LLM + TTS + STT)",
        "tts_ready": tts_ready(),
        "gemini_key": "set" if os.environ.get("GEMINI_API_KEY") else "not set",
        "pages": {
            "podcast_player": "/podcast-player",
            "voice_library": "/voice-library",
            "api_docs": "/docs",
        },
        "endpoints": {
            "upload": "POST /upload",
            "podcast_generate": "POST /podcast/generate",
            "podcast_tts": "POST /podcast/tts/{index}",
            "podcast_qa": "POST /podcast/qa",
            "voices_upload": "POST /voices/upload",
            "voices_set_active": "POST /voices/set-active",
            "tts": "POST /text-to-speech",
            "stt": "POST /transcribe",
            "download": "GET  /download/{filename}",
            "debug_tts": "GET  /debug/tts",
        },
    }


@app.get("/health")
def health_check():
    return {"status": "ok", "tts_ready": tts_ready()}
