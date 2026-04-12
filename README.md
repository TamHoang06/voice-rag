# AI Podcast Agent

AI-powered podcast generation platform with RAG, Gemini 2.5 Flash LLM, F5-TTS voice cloning, STT, document processing (PDF/DOCX), and voice library.

## Features
- **Document Upload**: PDF, DOCX, TXT → RAG vectorstore with image analysis
- **Podcast Generation**: Auto-segment + Gemini script → professional Vietnamese podcasts with segment timing
- **Voice Cloning**: F5-TTS (zero-shot voice cloning from 10s sample) + Gemini TTS fallback (9 voices)
- **Interactive Q&A**: Real-time RAG questions during podcast playback
- **Voice Library**: Upload/customize/reference voices for cloning (active voice auto-use)
- **Production Ready**: Rate limiting, Docker, pytest (8 test files incl. full E2E workflow), health checks

## Quick Start

### Prerequisites
- Python 3.10+
- Git (for f5-tts dependency)
- Gemini API key (LLM + TTS + STT: https://makersuite.google.com/app/apikey)

Optional (recommended):
- FFmpeg (audio processing: `winget install ffmpeg`)
- Visual C++ Build Tools (Windows PyTorch native)

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

**CPU-only Torch (recommended for first run):**
```
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu
```

### 3. Configuration
```
copy .env.example .env
```

Edit `src/.env`:
```
GEMINI_API_KEY=your_gemini_key
GEMINI_TTS_VOICE=Kore  # Charon, Aoede, Fenrir, Puck...
LOG_LEVEL=DEBUG  # F5-TTS progress + podcast generation logs
RATE_LIMIT_REQUESTS=100
```

### 4. Run Server
```
uvicorn main:app --reload --port 8000
```

**Access UIs:**
- API Docs: http://localhost:8000/docs
- **Podcast Player**: http://localhost:8000/podcast-player ← **MAIN DEMO**
- Voice Library: http://localhost:8000/voice-library
- Health: http://localhost:8000/health
- Debug TTS: http://localhost:8000/debug/tts

### 5. Test Suite
```
pytest  # 100% workflow coverage
pytest tests/test_e2e_flow.py::test_e2e_positive_full_pipeline  # Upload→Podcast→TTS→STT
```

## Docker Production Deploy
```
docker-compose up --build
```
- Port 8000 exposed
- All deps baked in
- Volume mounts for persistence

## API Endpoints
```
POST /upload (PDF/DOCX) → RAG vectorstore
POST /podcast/generate → Gemini script
POST /text-to-speech → F5-TTS clone OR Gemini TTS
POST /podcast/qa → RAG Q&A
POST /voices/upload → Custom voice library
GET /download/{file} → Audio export
```

## Troubleshooting

**Missing Git (f5-tts):**
```
winget install Git.Git
pip install -r requirements.txt
```

**Torch/audio errors:**
```
pip uninstall torch torchaudio
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu
winget install ffmpeg
```

**No TTS/STT response:**
```
curl http://localhost:8000/debug/tts  # Gemini API test
# Verify GEMINI_API_KEY valid/quota
```

**F5-TTS slow/first-run:**
```
# Normal: downloads 2GB model → 3min timeout auto-fallback
LOG_LEVEL=DEBUG  # Watch "[F5TTS] Loading model..."
GPU recommended for <30s inference
```

**.gitignore Protection:**
Blocks runtime (`data/`, `outputs/`, `voices/`, `vectorstore/`). Clean repo.

## Architecture Tree
```
d:/DuAn/voice-rag/
├── README.md                 # This doc
├── docker-compose.yml        # 1-click deploy
├── src/                      # FastAPI app root
│   ├── main.py              # App entry + lifespan (vectorstore preload)
│   ├── requirements.txt     # Pinned deps
│   └── app/
│       ├── config.py        # Env vars + voices list
│       ├── routers/         # 4 routers: audio/document/podcast/voices
│       ├── rag/             # FAISS vectorstore + PDF/DOCX loaders + Gemini vision
│       ├── podcast/         # Script generation + Q&A agent
│       ├── tts/             # Gemini TTS + F5-TTS multiprocessing timeout
│       ├── stt/             # Gemini STT with format support
│       └── voices/          # Active voice JSON + upload handler
├── tests/                   # 8 comprehensive tests
└── .gitignore               # Clean repo
```

## Tech Stack
| Component | Tech |
|-----------|------|
| Backend | FastAPI 0.111 + Uvicorn |
| LLM/TTS/STT | Gemini 2.5 Flash |
| Voice Clone | F5-TTS (GitHub latest) |
| RAG | LangChain + FAISS + HuggingFaceEmbeddings |
| Docs | PyPDF + python-docx + Gemini Vision |
| Audio | TorchAudio + FFmpeg |
| Tests | pytest (E2E + unit) |
| Deploy | Docker Compose |

**Zero-config production → Investor demo-ready! 🚀**

