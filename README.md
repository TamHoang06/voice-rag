
https://github.com/user-attachments/assets/4afdf234-e48f-4dc1-a0e8-4554ad99e834
<img width="695" height="347" alt="Rag_Select" src="https://github.com/user-attachments/assets/bc018843-3fca-4da7-9259-760318dca412" />
# # AI Voice Agent

AI-powered podcast generation platform with RAG, Gemini 2.5 Flash LLM, F5-TTS voice cloning, STT, document processing (PDF/DOCX), and voice library.

## Features
- **Document Upload**: PDF, DOCX, TXT → RAG vectorstore with image analysis

- **Podcast Generation**: Auto-segment + Gemini script → professional Vietnamese podcasts with segment timing

- **Voice Cloning**: F5-TTS (zero-shot voice cloning from 10s sample) + Gemini TTS fallback (9 voices)

- **Interactive Q&A**: Real-time RAG questions during podcast playback

- **Voice Library**: Upload/customize/reference voices for cloning (active voice auto-use)

- **Production Ready**: Rate limiting, Docker, pytest (8 test files incl. full E2E workflow), health checks

## Demo
### 1. RAG review
- Demonstration video: review the RAG workflow, including document ingestion, vector store creation, and model-driven question answering.

- Select chapter & Voice:

<img width="695" height="347" alt="Rag_Select" src="https://github.com/user-attachments/assets/296bc299-13ff-45d8-9502-5ef43b0717cd" />

- Placeholder video:


https://github.com/user-attachments/assets/9281d997-a963-4a61-8baa-2cc8507cdaa3


### 2. Text-based Q&A
- Demonstration video: interact with the AI Q&A interface by entering text queries and reviewing the system’s responses.
- 
- Placeholder video:




https://github.com/user-attachments/assets/51946d88-f888-4302-866d-cd48c1a7c199



### 3. Voice-based Q&A
- Demonstration video: speak a question into the platform and receive an AI answer using voice-enabled Q&A.

- Placeholder video:




https://github.com/user-attachments/assets/82fc461d-c701-48af-9783-44c6392f378e


### 4. Gemini TTS voices
- Demonstration video: generate speech using Gemini’s built-in AI voice options and compare different voice outputs.

- Placeholder video:


https://github.com/user-attachments/assets/25c85eac-5ccb-4f50-b411-3fa8509cc1f5



### 5. Upload audio assets
- Demonstration video: add audio files to the project repository and use them as input for processing or playback.

- Placeholder video:





### 6. Record audio assets
- Demonstration video: record audio directly into the repository and save it for later retrieval or processing.

- Placeholder video:



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
voice-rag/
├── .dockerignore               # Docker exclusion rules
├── .gitignore                  # Git exclusion rules
├── CODEBASE_ANALYSIS.md        # Technical analysis of the codebase
├── CODEBASE_ANALYSIS_REPORT.md # Summary report of codebase health
├── Dockerfile                  # Container build instructions
├── docker-compose.yml          # Multi-container orchestration
├── QUICK_SUMMARY.md            # High-level project overview
├── README.md                   # Main documentation
├── SECURITY_ROTATION_CHECKLIST.md # Security & Key rotation guide
├── TODO.md                     # Roadmap and pending tasks
├── requirements.txt            # Pinned dependencies
├── tests/                      # 8 comprehensive E2E & Unit tests
└── src/                        # FastAPI Application Root
    ├── __init__.py             # Package marker
    ├── .env                    # Local environment variables
    ├── .env.example            # Template for environment variables
    ├── main.py                 # Application entry point
    ├── pytest.ini              # Pytest configuration
    └── app/                    # CORE LOGIC (Deep Structure)
        ├── __init__.py         # Package marker
        ├── config.py           # App settings & Voice configurations
        ├── utils.py            # Shared utility functions
        ├── core/               # Central business logic/engine
        ├── document/           # Document parsing & preprocessing
        ├── models/             # Data schemas & Pydantic models
        ├── podcast/            # Scripting & Podcast generation
        ├── rag/                # RAG: FAISS, Loaders & Vision
        ├── routers/            # API Endpoints (Audio/Doc/Podcast/Voices)
        ├── stt/                # Speech-to-Text (Gemini)
        ├── tts/                # Text-to-Speech (Hybrid F5/Gemini)
        ├── data/               # [Local] Sample data (Git ignored)
        ├── outputs/            # [Local] Generated audio (Git ignored)
        ├── static/             # Frontend assets (HTML/JS/CSS)
        ├── vectorstore/        # [Local] FAISS index files (Git ignored)
        └── voices/             # [Local] Custom voice library (Git ignored)
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

**Zero-config production → Investor demo-ready! **

