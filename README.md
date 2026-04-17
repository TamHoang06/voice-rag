
https://github.com/user-attachments/assets/5a852cf2-142f-4e2f-a080-3711ab62c258

# AI Voice Agent

AI-powered podcast generation platform with RAG, Gemini 2.5 Flash LLM, F5-TTS voice cloning, STT, document processing (PDF/DOCX), and voice library.

## Features
- **Document Upload**: PDF, DOCX, TXT → RAG vectorstore with image analysis

- **Podcast Generation**: Auto-segment + Gemini script → professional Vietnamese podcasts with segment timing

- **Voice Cloning**: F5-TTS (zero-shot voice cloning from 10s sample) + Gemini TTS fallback (9 voices)

- **Interactive Q&A**: Real-time RAG questions during podcast playback

- **Voice Library**: Upload/customize/reference voices for cloning (active voice auto-use)

- **Production Ready**: Rate limiting, Docker, pytest (8 test files incl. full E2E workflow), health checks

## Project Mechanisms

This project is a Voice Agent built with Python, using FastAPI as the main web framework, integrating Google Gemini 2.5 Flash technologies for text, audio, and automatic podcast content generation. It supports multiple languages (especially Vietnamese), with key mechanisms including Retrieval-Augmented Generation (RAG), Speech-to-Text (STT), Text-to-Speech (TTS), and podcast generation.

### 1. Main Application Startup and Configuration
   - **Explanation**: The application uses FastAPI to create RESTful APIs. On startup, it loads the vectorstore (for RAG), checks TTS readiness (requires GEMINI_API_KEY), and mounts routers for podcast, document, audio, voices. Includes rate limiting middleware to prevent overload, and serves static HTML pages for web interfaces (e.g., podcast player).
   - **Special Notes**: The core stack is "Gemini 2.5 Flash - LLM + TTS + STT", meaning all AI tasks rely on Gemini. If API key is missing, TTS/STT will be unavailable. Rate limiting is configurable via env vars, with stricter limits for heavy routes like upload (5 requests/60s).
   - **Code Snippet** (from `src/main.py`):
     ```python
     def _run_startup_tasks() -> None:
         load_vectorstore()  # Load vectorstore for RAG
         ready = tts_ready()  # Check TTS readiness
         logger.info("TTS ready = %s", ready)
         if not ready:
             logger.warning("GEMINI_API_KEY not configured in .env: TTS/STT will be unavailable")
         logger.info("Stack: Gemini 2.5 Flash - LLM + TTS + STT")
     ```
     ```python
     app.add_middleware(
         RateLimitMiddleware,
         max_requests=rate_limit_requests(),  # From config, default 60 requests/60s
         window_seconds=rate_limit_window_seconds(),
     )
     ```

### 2. RAG (Retrieval-Augmented Generation) Mechanism
   - **Explanation**: RAG allows the application to "remember" and retrieve information from documents. Documents (PDF, DOCX, TXT) are loaded, split into chunks (1200 characters, 200 overlap), embedded using HuggingFace multilingual model (`sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`), and stored in FAISS vectorstore. On query, it retrieves relevant chunks and uses Gemini for QA or summarization.
   - **Special Notes**: Embeddings support multiple languages (including Vietnamese), with lazy loading to save memory. JSON registry stores document metadata, with in-memory cache. Raises error if document is empty after extraction. Image analysis (if images in PDF) uses Gemini for descriptions.
   - **Code Snippet** (from `src/app/rag/loader.py`):
     ```python
     chunks = RecursiveCharacterTextSplitter(
         chunk_size=1200,
         chunk_overlap=200,
     ).split_documents(documents)
     vector_db = FAISS.from_documents(chunks, get_embeddings())  # Create vectorstore
     ```
     (from `src/app/rag/retriever.py`):
     ```python
     _QA_PROMPT = (
         "You are an AI assistant, answer in Vietnamese.\n"
         "Answer concisely and accurately based on the document content.\n"
         "If no information: 'No information in the document.'\n\n"
         "=== Document ===\n{context}\n\n"
         "=== Question ===\n{question}\n\n"
         "=== Answer ===\n"
     )
     ```

### 3. STT (Speech-to-Text) Mechanism
   - **Explanation**: Converts audio files (WAV, MP3, etc.) to text using Gemini 2.5 Flash. Supports multiple languages (default vi-VN), estimates duration, and post-processes transcripts (removes extra characters).
   - **Special Notes**: Only supports formats in `AUDIO_MIME_MAP` (wav, mp3, m4a, etc.). Raises FileNotFoundError if file doesn't exist. Task can be "transcribe" or "translate". Max size 30MB.
   - **Code Snippet** (from `src/app/stt/stt.py`):
     ```python
     def transcribe_audio(
         audio_path: str,
         language: str = "vi-VN",  # Default Vietnamese
         task: str = "transcribe",
     ) -> dict:
         raw = _call_gemini_stt(audio_bytes, mime_type, locale, task)
         text = postprocess_transcript(raw)  # Post-processing
         duration = _estimate_duration(audio_bytes)
         return {"text": text, "language": locale, "duration": duration, "segments": []}
     ```

### 4. TTS (Text-to-Speech) Mechanism
   - **Explanation**: Converts text to WAV audio using Gemini 2.5 Flash. Supports multiple voices (Kore, Charon, etc.), splits text if too long (4500 chars/chunk), and merges into a single file.
   - **Special Notes**: Requires GEMINI_API_KEY to function. Voices defined in `GEMINI_VOICES` dict. Skips if text is empty. Default output WAV, can convert formats. Fallback to OpenAI if needed.
   - **Code Snippet** (from `src/app/tts/tts.py`):
     ```python
     GEMINI_VOICES = {
         "Aoede":   "Aoede — Female, natural",
         "Charon":  "Charon — Male, deep",
         # ...
     }
     def text_to_speech(text: str, output_path: str = None, voice: str = None) -> str:
         if not text or not text.strip():
             raise ValueError("Text is empty")
         # Split and call Gemini TTS
     ```

### 5. Podcast Generation Mechanism
   - **Explanation**: From loaded documents via RAG, uses Gemini to generate Vietnamese podcast scripts, divided into segments (each 150-280 words, 1-2 min read). Then TTS each segment into audio. Scripts cached by document_id.
   - **Special Notes**: Prompt requires exact number of segments, written naturally as speech. Segments have short titles. QA for listener questions based on script. Audio saved in outputs/.
   - **Code Snippet** (from `src/app/podcast/agent.py`):
     ```python
     _GENERATE_PROMPT = """\
     You are a professional Vietnamese podcast producer.
     Task: Convert the document into a fully Vietnamese podcast script, engaging and easy to listen to...
     Create exactly {num_segments} segments...
     """
     ```
     (from `src/app/podcast/script.py`):
     ```python
     @dataclass
     class PodcastSegment:
         index: int
         title: str
         text: str
         duration_estimate: float = 0.0
     ```

### 6. Security and Logging Mechanism
   - **Explanation**: Uses logger for logging, and rate limiting for API protection. Gemini has safety settings "BLOCK_NONE" for all categories (harassment, hate speech, etc.), allowing freer content.
   - **Special Notes**: This setting may risk allowing harmful content if used for sensitive material. Route-specific rate limiting (upload/transcribe stricter). Logging aids debugging, but no data encryption.
   - **Code Snippet** (from `src/app/config.py`):
     ```python
     GEMINI_SAFETY_SETTINGS = [
         {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
         # ...
     ]
     def rate_limit_route_policies() -> dict[str, tuple[int, int]]:
         return {
             "/upload": (5, 60),  # 5 requests/60s for upload
         }
     ```

### General Notes for the Project
- **AI Dependency**: All rely on Gemini 2.5 Flash, requiring stable API key. If Gemini fails, fallback to OpenAI for TTS.
- **Language**: Focused on Vietnamese, with prompts and outputs in Vietnamese.
- **Performance**: Lazy loading embeddings, caching vectorstore/script to avoid reload. Upload size limited (50MB for files, 30MB for audio).
- **Risks**: "BLOCK_NONE" safety settings may allow harmful content; rate limiting can be bypassed if misconfigured. No default authentication.
- **Environment**: Runs in Docker, with requirements.txt listing deps like langchain, fastapi, etc.

## Demo
### 1. RAG review
- Demonstration video: review the RAG workflow, including document ingestion, vector store creation, and model-driven question answering.

- Select chapter & Voice:


<img width="695" height="347" alt="Rag_Select" src="https://github.com/user-attachments/assets/bc018843-3fca-4da7-9259-760318dca412" />

- Placeholder video:



https://github.com/user-attachments/assets/3f47fb5e-6d67-49c1-9dc1-b84560875d58



- Divide the document into concise sections:



https://github.com/user-attachments/assets/2b00977e-c976-46b2-822d-e062b601b719





### 2. Text-based Q&A
- Demonstration video: interact with the AI Q&A interface by entering text queries and reviewing the system’s responses.

- Placeholder video:

https://github.com/user-attachments/assets/44f4e895-2abb-40cd-9abd-2218081c86b1



### 3. Voice-based Q&A
- Demonstration video: speak a question into the platform and receive an AI answer using voice-enabled Q&A.

- Placeholder video:




https://github.com/user-attachments/assets/b73e1474-6a14-4590-b975-ba0a9a479458





### 4. Gemini TTS voices
- Demonstration video: generate speech using Gemini’s built-in AI voice options and compare different voice outputs.

- Placeholder video:




https://github.com/user-attachments/assets/34a2f642-d8a3-45b2-a2eb-d261ad80e0bf





### 5. Upload audio assets
- Demonstration video: add audio files to the project repository and use them as input for processing or playback.

- Placeholder video:


https://github.com/user-attachments/assets/ee3bef46-c62a-4965-96f0-11f11c1f26d9




### 6. Record audio assets
- Demonstration video: record audio directly into the repository and save it for later retrieval or processing.

- Placeholder video:





https://github.com/user-attachments/assets/b8fb5e8a-4b39-495b-9a65-95cbecbbe7a1




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

### Document Management
```
POST /upload                          → Upload PDF/DOCX/TXT & create RAG vectorstore
GET  /documents                       → List all uploaded documents
POST /documents/{document_id}/select  → Select active document
GET  /document                        → Get current document metadata
GET  /document/summary                → Get AI-generated summary of document
POST /ask                             → Q&A on current document (text)
POST /generate-docx                   → Export Q&A results to DOCX
POST /generate-pdf                    → Export Q&A results to PDF
POST /re-analyze-images               → Reanalyze document images with Gemini Vision
```

### Podcast Generation & Playback
```
POST /podcast/generate                → Generate podcast script from document
GET  /podcast/script                  → Get generated podcast script
POST /podcast/tts/summary             → Convert summary to speech (F5-TTS/Gemini)
POST /podcast/tts/{segment_index}     → Convert specific segment to speech
POST /podcast/qa                      → Q&A on podcast (text-based)
POST /podcast/qa/voice                → Q&A on podcast (voice-based with STT)
```

### Voice Library & TTS
```
GET  /voices/available                → List all available voices (all providers)
GET  /voices/available/{provider}     → List voices by provider (gemini, f5)
GET  /voices/providers                → List supported voice providers
POST /voices/upload                   → Upload voice sample for F5-TTS cloning
POST /voices/set-active               → Set active voice for text-to-speech
POST /text-to-speech                  → Text-to-speech with selected voice
```

### File Management
```
GET  /download/{filename}             → Download generated audio/documents
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
VOICE-AGENT/
├── .dockerignore               # Docker exclusion rules
├── .gitignore                  # Git exclusion rules
├── Dockerfile                  # Container build instructions
├── docker-compose.yml          # Multi-container orchestration
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
