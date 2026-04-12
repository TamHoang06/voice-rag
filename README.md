# AI Podcast Agent

AI-powered podcast generation platform with RAG, Gemini 2.5 Flash LLM, F5-TTS voice cloning, STT, document processing (PDF/DOCX), and voice library.

## Features
- **Document Upload**: PDF, DOCX, TXT → RAG vectorstore
- **Podcast Generation**: Auto-segment + Gemini script → professional Vietnamese podcasts
- **Voice Cloning**: F5-TTS (zero-shot) + Gemini TTS fallback
- **Interactive Q&A**: Ask questions during podcast playback
- **Voice Library**: Upload/customize voices for cloning
- **Production Ready**: Rate limiting, Docker, pytest (8 test files incl. E2E)

## Quick Start

### Prerequisites
- Python 3.10+
- Git (for f5-tts dependency)
- Gemini API key (LLM + TTS + STT)

Optional (recommended):
- FFmpeg (audio processing)
- Visual C++ Build Tools (Windows native extensions)

### 1. Environment Setup
```
cd src
python -m venv .venv
```

**Windows:**
```
.venv\Scripts\Activate.ps1
```

**macOS/Linux:**
```
source .venv/bin/activate
```

### 2. Install Dependencies
```
pip install --upgrade pip
pip install -r requirements.txt
```

**CPU-only Torch (if GPU issues):**
```
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu
```

### 3. Configuration
```
copy .env.example .env
```

Edit `src/.env`:
```
GEMINI_API_KEY=your_key_here
GEMINI_TTS_VOICE=Kore  # Aoede, Charon, Fenrir...
LOG_LEVEL=DEBUG  # Verbose F5-TTS progress
```

### 4. Run Server
```
uvicorn main:app --reload
```

**Access:**
- API Docs: http://localhost:8000/docs
- Podcast Player: http://localhost:8000/podcast-player
- Voice Library: http://localhost:8000/voice-library

### 5. Test
```
pytest  # 8 test files (E2E, unit)
pytest tests/test_voices.py
```

## Docker Deploy
```
docker-compose up --build
```

## Troubleshooting

**Git not found (f5-tts):**
```
# Install Git, retry pip install -r requirements.txt
```

**Torch/FFmpeg errors:**
```
winget install ffmpeg  # Windows
pip install torch --index-url https://download.pytorch.org/whl/cpu
```

**No TTS/STT:**
```
# Check GEMINI_API_KEY in .env
curl http://localhost:8000/debug/tts
```

**.gitignore Note:**
Blocks runtime dirs (`data/`, `outputs/`, `voices/`). Untrack if needed:
```
git rm -r --cached src/static
git commit -m "Untrack static"
```

## Architecture
```
src/
├── main.py (FastAPI app)
├── app/
│   ├── routers/ (API endpoints)
│   ├── rag/ (Document loader + vectorstore)
│   ├── podcast/ (Gemini script gen)
│   ├── tts/ (Gemini + F5-TTS clone)
│   ├── stt/ (Gemini transcription)
│   └── voices/ (Custom voice upload)
├── tests/ (8 files, E2E workflow)
└── requirements.txt (pinned deps)
```

**Production ready for investors! 🚀**

