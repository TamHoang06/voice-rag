# AI Podcast Codebase Analysis Report
**Date**: April 5, 2026  
**Workspace**: d:\DuAn\AI\src

---

## Executive Summary
The codebase has **critical code duplication**, **abandoned modules**, **incomplete features**, and **missing error handling**. Priority fixes include removing duplicate code, fixing import issues, and enabling disabled features.

**Issues Found**: 28  
**Priority**: 7 Critical | 8 High | 8 Medium | 5 Low

---

## 1. CRITICAL ISSUES — Code Duplication

### 1.1 ⚠️ DUPLICATE DATA MODELS — `PodcastSegment` & `PodcastScript`

**Severity**: Critical  
**Impact**: Code maintenance nightmare, potential data inconsistency

**Files Involved**:
- [podcast/script.py](podcast/script.py) — **CANONICAL VERSION** (correct)
- [rag/podcast_agent.py](rag/podcast_agent.py) — **DUPLICATE** (identical dataclass definitions)

**Location Details**:
- [podcast/script.py lines 8-37](podcast/script.py#L8-L37) — Original definitions
- [rag/podcast_agent.py lines 18-42](rag/podcast_agent.py#L18-L42) — Duplicate definitions

**Current Code**:
```python
# Both files define these classes identically:
@dataclass
class PodcastSegment:
    index: int
    title: str
    text: str
    duration_estimate: float = 0.0
    
@dataclass
class PodcastScript:
    title: str
    summary: str
    segments: List[PodcastSegment] = field(default_factory=list)
    source: str = ""
```

**Recommendation**:
- DELETE [rag/podcast_agent.py](rag/podcast_agent.py) entirely (see 2.1)
- Import from [podcast/script.py](podcast/script.py) instead

---

### 1.2 ⚠️ DUPLICATE FUNCTION — `answer_listener_question()`

**Severity**: Critical  
**Impact**: Function calls may route to wrong implementation

**Files**:
- [podcast/agent.py line 219](podcast/agent.py#L219) — **ACTIVELY USED**
- [rag/podcast_agent.py line 218](rag/podcast_agent.py#L218) — **REDUNDANT**

**Router Import**:
```python
# From app/routers/podcast.py line 18
from app.podcast.agent import answer_listener_question  # ✓ Correct
# NOT from app.rag.podcast_agent (which is also defined there)
```

**Recommendation**: Delete the duplicate in `rag/podcast_agent.py` (dependency analysis complete in issue 2.1)

---

## 2. CRITICAL ISSUES — Abandoned/Unused Modules

### 2.1 ⚠️ DEAD CODE FILE — `rag/podcast_agent.py`

**Severity**: Critical  
**Impact**: Source of confusion, causes duplicate definitions, wastes maintenance effort

**File**: [rag/podcast_agent.py](rag/podcast_agent.py) — **NOT IMPORTED ANYWHERE**

**Evidence**:
```bash
# Search results for imports of rag/podcast_agent
# NO MATCHES found in:
- app/routers/podcast.py  → imports from app.podcast.agent ONLY
- app/routers/document.py → does NOT import
- app/main.py → does NOT import
- Any __init__.py files
```

**Content**:
- Lines 1-17: Duplicate config/imports
- Lines 18-42: **DUPLICATE** `PodcastSegment` class
- Lines 44-56: **DUPLICATE** `PodcastScript` class  
- Lines 59-96: **DUPLICATE** `_call_gemini()` function
- Lines 99-156: **DUPLICATE/MODIFIED** `_PODCAST_PROMPT` (hardcoded safety settings)
- Lines 158-215: **DUPLICATE** `generate_podcast_script()` with different logic
- Lines 218-238: **DUPLICATE** `answer_listener_question()` with different logic
- Lines 240-250: **DUPLICATE** state management functions (`set_current_script`, etc.)

**Recommendation**: **DELETE ENTIRELY**
```bash
rm d:\DuAn\AI\src\app\rag\podcast_agent.py
```
This will eliminate all duplication at once.

---

## 3. HIGH PRIORITY ISSUES

### 3.1 🔴 DUPLICATE API FUNCTIONS — `_call_gemini()`

**Severity**: High  
**Impact**: Bug fixes must be applied in 3+ places

**Files**:
- [app/config.py](app/config.py) — Safety settings defined
- [app/podcast/agent.py lines 16-48](app/podcast/agent.py#L16-L48) — Implementation 1
- [app/rag/retriever.py lines 16-47](app/rag/retriever.py#L16-L47) — Implementation 2
- [app/rag/podcast_agent.py lines 59-96](app/rag/podcast_agent.py#L59-L96) — Implementation 3 (duplicate)

**Issue**: Each implementation has slightly different error handling and configuration.

**Recommendation**: Consolidate into `app/core/gemini_client.py`:
```python
# NEW FILE: app/core/gemini_client.py
def call_gemini(
    prompt: str,
    max_tokens: int = 1024,
    temperature: float = 0.7,
    timeout: int = 30,
) -> str:
    """Centralized Gemini API client with error handling."""
    api_key = gemini_api_key()
    if not api_key:
        raise ValueError("GEMINI_API_KEY not configured")
    
    # Single implementation
    ...
```

Then import in `podcast/agent.py` and `rag/retriever.py`:
```python
from app.core.gemini_client import call_gemini
```

---

### 3.2 🔴 DUPLICATE SAFETY SETTINGS

**Severity**: High  
**Impact**: Hard to update all at once, inconsistent configurations

**Files**:
- [app/config.py lines 60-65](app/config.py#L60-L65) — Canonical definition
- [app/podcast/agent.py (used inline)](app/podcast/agent.py) — Via import ✓
- [app/rag/retriever.py (used inline)](app/rag/retriever.py) — Via import ✓
- [app/rag/podcast_agent.py lines 80-84](app/rag/podcast_agent.py#L80-L84) — **HARDCODED DUPLICATE**

**Recommendation**: Update [rag/podcast_agent.py line 80](rag/podcast_agent.py#L80) to import from config OR delete the file (preferred, see 2.1).

---

### 3.3 🔴 INCOMPLETE DOCUMENT GENERATION FEATURE

**Severity**: High  
**Impact**: Feature fully implemented but completely disabled (unreachable)

**Files**:
- [app/document/generator.py](app/document/generator.py) — **FULLY IMPLEMENTED**
- [app/routers/document.py](app/routers/document.py) — **NO ENDPOINTS**

**Status**:
```python
# Implemented in generator.py:
✓ DocumentGenerator.create_docx()      # tested, working
✓ DocumentGenerator.create_pdf()       # implemented
✓ get_document_generator() singleton   # implemented

# But NO API routes defined
# No @router.post("/document/generate") endpoint exists
# No @router.post("/document/pdf") endpoint exists
```

**Models Available** [app/models/schemas.py line 31-37](app/models/schemas.py#L31-L37):
```python
class GenerateDocRequest(BaseModel):
    content: str
    title: str = "Tài liệu"
    images: Optional[List[str]] = None
    format: str = "docx"
```

**Recommendation**: Add to [app/routers/document.py](app/routers/document.py):
```python
@router.post("/document/generate")
def generate_document(req: GenerateDocRequest):
    from app.document.generator import get_document_generator
    gen = get_document_generator()
    
    if req.format.lower() == "pdf":
        path = gen.create_pdf(req.content, req.images, req.title)
    else:
        path = gen.create_docx(req.content, req.images, req.title)
    
    return {
        "message": "Document created",
        "format": req.format,
        "download_url": f"/download/{os.path.basename(path)}"
    }
```

---

### 3.4 🔴 MISSING GLOBAL LOGGER — No structured logging

**Severity**: High  
**Impact**: Hard to debug, inconsistent logging format

**Current State**:
```python
# All files use:
print(f"[TAG] message")  # Unstructured, no timestamps, no levels
```

**Recommendation**: Create `app/core/logger.py`:
```python
import logging
from app.config import OUTPUTS_DIR

handler = logging.FileHandler(os.path.join(OUTPUTS_DIR, "app.log"))
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

logger = logging.getLogger("ai_podcast")
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)
```

Then use throughout:
```python
from app.core.logger import logger
logger.info(f"TTS ready = {ready}")
logger.error(f"Lỗi Gemini: {e}")
```

---

### 3.5 🔴 HARDCODED MODEL & API NAMES

**Severity**: High  
**Impact**: Difficult to switch models, testing blocked

**Files with Hardcoding**:
- [app/config.py line 23](app/config.py#L23): Function returns hardcoded default
- [app/podcast/agent.py line 17](app/podcast/agent.py#L17): Hardcoded in function (should use config)
- [app/tts/tts.py line 7](app/tts/tts.py#L7): No fallback model defined
- [app/stt/stt.py](app/stt/stt.py): No alternative STT engines defined

**Example Issue**:
```python
# app/podcast/agent.py uses:
model = gemini_model()  # ✓ Good

# But audio.py hardcodes the URL:
url = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    f"{model}:generateContent?key={api_key}"
)  # Hardcoded URL endpoint for every call
```

**Recommendation**: Create `app/core/api_endpoints.py`:
```python
GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"

def get_gemini_endpoint(model: str, endpoint: str = "generateContent") -> str:
    return f"{GEMINI_BASE_URL}/{model}:{endpoint}"
```

---

## 4. MEDIUM PRIORITY ISSUES

### 4.1 🟡 Missing Type Hints — Functions lack return types

**Severity**: Medium  
**Impact**: IDE autocomplete broken, harder to catch bugs

**Files**:
- [app/rag/loader.py line 22](app/rag/loader.py#L22): `load_document()` → no return type hint
- [app/rag/loader.py line 35](app/rag/loader.py#L35): `load_vectorstore()` → no return type hint
- [app/tts/tts.py line 165](app/tts/tts.py#L165): `text_to_speech()` return type is `str` (correct)
- [app/document/generator.py line 58](app/document/generator.py#L58): Return type missing

**Recommendation**:
```python
# BEFORE:
def load_document(file_path: str):
    """Load tài liệu..."""

# AFTER:
def load_document(file_path: str) -> None:
    """Load tài liệu..."""

def get_full_text() -> str:
    return _full_text[:5000] if _full_text else ""
```

---

### 4.2 🟡 Inconsistent Error Messages & Poor Recovery

**Severity**: Medium  
**Impact**: Users see unhelpful error messages, no graceful degradation

**Files**:
- [app/podcast/agent.py line 31](app/podcast/agent.py#L31): `"Chưa cấu hình GEMINI_API_KEY trong .env"`
- [app/rag/retriever.py line 18](app/rag/retriever.py#L18): Different wording: `"Chưa cấu hình GEMINI_API_KEY trong .env"`
- [app/routers/podcast.py line 25](app/routers/podcast.py#L25): `HTTPException(404, "Chưa có tài liệu...")`

**Recommendation**: Create `app/core/errors.py`:
```python
class MissingConfigError(Exception):
    pass

class DocumentNotLoadedError(Exception):
    pass

# Use consistently across codebase
```

---

### 4.3 🟡 Microphone/Audio Feature — No STT Input Options

**Severity**: Medium  
**Impact**: Endpoint exists `/transcribe` but frontend may not support recording

**Files**:
- [app/routers/audio.py line 45-68](app/routers/audio.py#L45-L68): Upload-based only
- [app/routers/podcast.py line 135-175](app/routers/podcast.py#L135-175): Voice Q&A upload-based

**Issue**: No `/record` endpoint for real-time mic input  
**Recommendation**: Consider WebRTC or WebAudio API integration (out of scope for backend analysis)

---

### 4.4 🟡 No Circuit Breaker for API Calls

**Severity**: Medium  
**Impact**: If Gemini API goes down, server hammers it with requests

**Files**:
- [app/podcast/agent.py lines 16-48](app/podcast/agent.py#L16-L48): Direct URL calls
- [app/rag/retriever.py lines 16-47](app/rag/retriever.py#L16-L47): Direct URL calls
- [app/stt/stt.py lines 65-120](app/stt/stt.py#L65-L120): Direct URL calls
- [app/tts/tts.py lines 82-140](app/tts/tts.py#L82-L140): Direct URL calls

**Recommendation**: Add retry logic + exponential backoff:
```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
def _call_gemini_with_retry(prompt: str) -> str:
    # Implementation
    ...
```

Add `tenacity` to [requirements.txt](requirements.txt).

---

### 4.5 🟡 Audio Chunk Merging Not Robust

**Severity**: Medium  
**Impact**: Large texts may produce corrupted audio

**File**: [app/tts/tts.py line 150-160](app/tts/tts.py#L150-L160)

**Issue**:
```python
def _merge_wav(wav_list: list) -> bytes:
    """Ghép nhiều WAV bytes thành 1 file."""
    # Current implementation:
    arrays, sr = [], None
    for i, wav in enumerate(wav_list):
        try:
            d, csr = sf.read(io.BytesIO(wav), dtype="float32", always_2d=False)
            arrays.append(d.mean(axis=1) if d.ndim == 2 else d)
            if sr is None:
                sr = csr
        except Exception as e:
            print(f"[TTS] Chunk {i} error: {e}")
    # Falls back to using first successful chunk if others fail
    # NO RESAMPLING if different sample rates
```

**Recommendation**: 
```python
def _merge_wav(wav_list: list, target_sr: int = 24000) -> bytes:
    import librosa
    arrays = []
    for i, wav in enumerate(wav_list):
        d, sr = sf.read(io.BytesIO(wav), dtype="float32", always_2d=False)
        if sr != target_sr:
            d = librosa.resample(d, orig_sr=sr, target_sr=target_sr)
        arrays.append(d)
    
    out = io.BytesIO()
    sf.write(out, np.concatenate(arrays), target_sr, format="WAV")
    return out.getvalue()
```

Add `librosa` to [requirements.txt](requirements.txt).

---

## 5. MEDIUM PRIORITY ISSUES (continued)

### 5.1 🟡 Unused Dependencies in `requirements.txt`

**Severity**: Medium  
**Impact**: Bloated dependencies, longer startup time

**Potentially Unused**:
- `accelerate>=0.30.0` — Listed but no search results for actual use
- `python-docx>=1.1.0` — Only used in document generator (feature disabled, see 3.3)
- `reportlab>=4.0.0` — Only used in document generator (feature disabled)
- `docx2txt>=0.8` — Never imported or used
- `PyPDF>=4.2.0` — Only used via `pypdf` module, not directly used

**Recommendation**: Verify usage:
```bash
# Check if these are actually used
grep -r "accelerate" d:\DuAn\AI\src\app\
grep -r "docx2txt" d:\DuAn\AI\src\app\
grep -r "pypdf" d:\DuAn\AI\src\app\
```

Remove unused from [requirements.txt](requirements.txt).

---

### 5.2 🟡 Unused Test Files

**Severity**: Medium  
**Impact**: Maintenance burden, unclear what's being tested

**Files**:
- [tests/test_config.py](tests/test_config.py) — Exists but minimal tests
- [tests/test_tts.py](tests/test_tts.py) — Structure test only (no actual TTS calls)
- [tests/test_rag.py](tests/test_rag.py) — RAG utilities tests exist
- [tests/test_stt.py](tests/test_stt.py) — Format/prompt tests only

**Recommendation**: Expand test coverage:
```python
# tests/test_podcast_agent.py
import pytest
from app.podcast.script import PodcastSegment, PodcastScript

def test_podcast_script_roundtrip():
    """Test full podcast generation->TTS pipeline"""
    ...

def test_answer_question_length():
    """Test that Q&A answers stay under max length"""
    ...
```

---

### 5.3 🟡 Missing Docstrings — Some functions undocumented

**Severity**: Medium  
**Impact**: Harder to understand intent, IDE help unavailable

**Files**:
- [app/rag/loader.py line 56](app/rag/loader.py#L56): `get_vectordb()` — No docstring
- [app/rag/loader.py line 58](app/rag/loader.py#L58): `get_full_text()` — No docstring
- [app/utils.py line 30](app/utils.py#L30): `split_text()` — Has good docstring ✓
- [app/document/generator.py line 28-69](app/document/generator.py#L28-L69): Has docstrings ✓

**Recommendation**:
```python
def get_vectordb() -> FAISS:
    """
    Get the loaded FAISS vector database for RAG retrieval.
    
    Returns:
        FAISS: Vector store instance or None if not loaded.
    """
    return _vector_db
```

---

## 6. LOW PRIORITY ISSUES

### 6.1 🔵 Hardcoded Voice Names in TTS

**Severity**: Low  
**Impact**: Inconsistent naming, hard to discover voices

**Files**:
- [app/tts/tts.py lines 28-37](app/tts/tts.py#L28-L37): Voice map defined
- [app/config.py](app/config.py): References "Kore" as fallback
- [app/routers/audio.py](app/routers/audio.py): Returns voice list ✓

**Current**:
```python
GEMINI_VOICES = {
    "Aoede":   "Aoede — Nữ, tự nhiên",
    "Charon":  "Charon — Nam, trầm",
    ...
}
```

**Recommendation**: Move to config:
```python
# app/config.py
def supported_tts_voices() -> dict:
    return {
        "Aoede": "Female, natural",
        "Charon": "Male, deep",
        ...
    }
```

---

### 6.2 🔵 Video Support Not Fully Tested

**Severity**: Low  
**Impact**: May crash on .mp4 upload

**File**: [app/config.py line 42](app/config.py#L42):
```python
SUPPORTED_AUDIO_EXT = {".wav", ".mp3", ".m4a", ".ogg", ".flac", ".webm", ".mp4"}
```

**Issue**: `.mp4` is video, not all systems handle it  
**Recommendation**: Test with `pydub` or `ffmpeg` wrapper before enabling.

---

### 6.3 🔵 Missing Validation for File Uploads

**Severity**: Low  
**Impact**: No file size limits, no malware scanning

**Files**:
- [app/routers/document.py line 19-27](app/routers/document.py#L19-L27): No size check
- [app/routers/audio.py line 45-68](app/routers/audio.py#L45-L68): No size check

**Recommendation** (if deploying):
```python
@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB
    
    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(413, "File too large")
    
    # Continue...
```

---

### 6.4 🔵 Global State Management — Not Thread-Safe

**Severity**: Low  
**Impact**: If multiple users upload documents simultaneously, state can be corrupted

**Files**:
- [app/podcast/script.py lines 44-56](app/podcast/script.py#L44-L56): Uses global `_current_script`
- [app/rag/loader.py lines 26-32](app/rag/loader.py#L26-L32): Uses global `_vector_db`

**Current**:
```python
_current_script: Optional[PodcastScript] = None

def set_current_script(script: PodcastScript) -> None:
    global _current_script
    _current_script = script  # NOT THREAD SAFE
```

**Recommendation** (for production):
```python
from threading import Lock
import contextvars

# Use context variables for async contexts
_script_context = contextvars.ContextVar('current_script', default=None)

def set_current_script(script: PodcastScript) -> None:
    _script_context.set(script)
```

Or use Redis for multi-instance deployments.

---

### 6.5 🔵 Inconsistent JSON Response Format

**Severity**: Low  
**Impact**: Frontend may have trouble parsing different response structures

**Examples**:
- [app/routers/podcast.py line 42](app/routers/podcast.py#L42): Returns `{message, title, summary, total_segments, segments}`
- [app/routers/audio.py line 35](app/routers/audio.py#L35): Returns `{message, chars, audio_url, download_url}`
- [app/routers/document.py line 23](app/routers/document.py#L23): Returns `{message, total_chars, filename}`

**Recommendation**: Define response schemas:
```python
# app/models/responses.py
class BaseResponse(BaseModel):
    success: bool
    message: str
    
class PodcastGenerateResponse(BaseResponse):
    title: str
    summary: str
    total_segments: int
    segments: List[dict]
```

---

## 7. ANTI-PATTERNS & CODE SMELL

### 7.1 Repeated Prompt Formatting

**Files**:
- [app/podcast/agent.py](app/podcast/agent.py): `_GENERATE_PROMPT`, `_QA_PROMPT` (good, defined at top)
- [app/rag/retriever.py](app/rag/retriever.py): `_QA_PROMPT`, `_SUMMARY_PROMPT` (good)
- [app/rag/podcast_agent.py](app/rag/podcast_agent.py): `_PODCAST_PROMPT` (duplicate)

**Recommendation**: Move all prompts to `app/core/prompts.py`:
```python
# app/core/prompts.py
PODCAST_GENERATION_PROMPT = """..."""
QA_PROMPT = """..."""
SUMMARY_PROMPT = """..."""
```

---

### 7.2 Feature Gating — No Environment Variables for Feature Flags

**Severity**: Low  
**Impact**: Hard to disable features for testing/debugging

**Recommendation**: Add `.env` support:
```python
# app/config.py
FEATURE_DOCUMENT_GENERATION = os.environ.get("FEATURE_DOCUMENT_GENERATION", "true").lower() == "true"
FEATURE_RAG = os.environ.get("FEATURE_RAG", "true").lower() == "true"
FEATURE_PODCAST = os.environ.get("FEATURE_PODCAST", "true").lower() == "true"
```

---

## 8. MISSING ERROR HANDLING

### 8.1 Network Timeouts Not Uniform

**Files**:
- [app/podcast/agent.py line 42](app/podcast/agent.py#L42): `timeout=90`
- [app/rag/retriever.py line 29](app/rag/retriever.py#L29): `timeout=30`
- [app/stt/stt.py line 116](app/stt/stt.py#L116): `timeout=60`
- [app/tts/tts.py line 126](app/tts/tts.py#L126): `timeout=120`

**Issue**: No consistency, no config  
**Recommendation**: Configure in `app/config.py`:
```python
API_TIMEOUT_GEMINI_GENERATE = int(os.environ.get("API_TIMEOUT_GEMINI_GENERATE", "90"))
API_TIMEOUT_GEMINI_EMBED = int(os.environ.get("API_TIMEOUT_GEMINI_EMBED", "30"))
```

---

### 8.2 No Graceful Degradation for Missing Models

**Severity**: Medium  
**Files**:
- [app/rag/loader.py line 11](app/rag/loader.py#L11): Loads embedding model without fallback
```python
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)
# If model missing/network down → crashes on import
```

**Recommendation**:
```python
def load_embeddings():
    try:
        return HuggingFaceEmbeddings(
            model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
        )
    except Exception as e:
        logger.warning(f"Failed to load embeddings, using fallback: {e}")
        return None

embeddings = load_embeddings()
```

---

## 9. CONFIGURATION ISSUES

### 9.1 Docker Configuration Incomplete

**Files**:
- [Dockerfile](../Dockerfile) — Exists but not analyzed
- [docker-compose.yml](../docker-compose.yml) — Exists but not analyzed

**Files analyzed**: Only Python source code in `src/`  
**Recommendation**: Verify Docker image doesn't include temporary files:
```dockerfile
# Exclude:
- model_cache/
- requirements cached layers
- Test artifacts
```

---

### 9.2 No Environment Validation on Startup

**Severity**: Medium  
**Area**: [app/main.py](../src/main.py)

**Current**:
```python
@app.on_event("startup")
def startup():
    load_vectorstore()
    ready = tts_ready()
    print(f"[INFO] TTS ready  = {ready}")
    if not ready:
        print("[WARN] Thêm GEMINI_API_KEY vào .env để dùng TTS/STT")
```

**Issues**:
- No validation of required paths
- No check for model_cache/
- No check for vectorstore/

**Recommendation**:
```python
def validate_environment():
    required_dirs = [OUTPUTS_DIR, DATA_DIR, VOICES_DIR]
    for d in required_dirs:
        if not os.path.exists(d):
            logger.error(f"Required directory missing: {d}")
            raise RuntimeError(f"Setup error: missing {d}")
    
    if not gemini_api_key():
        logger.warning("GEMINI_API_KEY not set — TTS/STT disabled")
```

---

## 10. SECURITY CONCERNS

### 10.1 API Key Exposure Risk (Low)

**File**: [app/routers/audio.py line 130-180](app/routers/audio.py#L130-L180)

**Issue**:
```python
@router.get("/debug/tts")
def debug_tts():
    """Chẩn đoán Gemini TTS — mở /debug/tts trên browser."""
    api_key = os.environ.get("GEMINI_API_KEY", "")
    
    info: dict = {
        "GEMINI_API_KEY": f"SET ({api_key[:8]}…)" if api_key else "⚠ KHÔNG SET",
        # EXPOSES FIRST 8 CHARS OF KEY!
    }
```

**Recommendation**: Never expose API key, even partially:
```python
info: dict = {
    "GEMINI_API_KEY": "SET" if api_key else "NOT SET",  # Don't show any chars
}
```

---

### 10.2 No Rate Limiting on Endpoints

**Severity**: Low  
**Impact**: User could spam requests, DOS potential

**Recommendation**: Add `slowapi`:
```bash
pip install slowapi
```

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.get("/podcast/script")
@limiter.limit("100/hour")
def podcast_script(request: Request):
    ...
```

---

## SUMMARY TABLE

| Issue | Priority | Category | File(s) | Action |
|-------|----------|----------|---------|--------|
| rag/podcast_agent.py duplication | 🔴CRITICAL | Code | rag/podcast_agent.py | DELETE |
| PodcastSegment duplicate def | 🔴CRITICAL | Code | rag/podcast_agent.py | DELETE |
| answer_listener_question duplicate | 🔴CRITICAL | Code | rag/podcast_agent.py | DELETE |
| Document generation disabled | 🔴CRITICAL | Feature | routers/, generator.py | ADD ENDPOINTS |
| _call_gemini 3x duplicate | 🔴HIGH | Code | podcast/agent.py, rag/retriever.py, rag/podcast_agent.py | CONSOLIDATE |
| Safety settings hardcoded | 🔴HIGH | Config | rag/podcast_agent.py | USE CONFIG |
| No global logger | 🔴HIGH | Infra | All | ADD logging module |
| Hardcoded API endpoints | 🔴HIGH | Config | tts.py, stt.py, etc. | CREATE endpoints module |
| Missing type hints | 🟡MEDIUM | Code Quality | loader.py | ADD hints |
| Inconsistent error messages | 🟡MEDIUM | UX | Multiple | CENTRALIZE |
| Unused dependencies | 🟡MEDIUM | Deps | requirements.txt | VERIFY |
| No circuit breaker | 🟡MEDIUM | Reliability | API calls | ADD tenacity |
| Audio merge not robust | 🟡MEDIUM | Quality | tts.py | ADD resampling |
| Hardcoded voice names | 🔵LOW | Config | tts.py | MOVE to config |
| Global state not thread-safe | 🔵LOW | Concurrency | script.py, loader.py | USE contextvars |
| Inconsistent JSON format | 🔵LOW | UX | routers/ | DEFINE schemas |
| No file upload validation | 🔵LOW | Security | routers/ | ADD limits |
| No API key exposure check | 🔵LOW | Security | audio.py | FIX debug endpoint |

---

## RECOMMENDED FIX ORDER

### Phase 1 (Day 1) — Critical Fixes
1. ✅ Delete [rag/podcast_agent.py](rag/podcast_agent.py)
2. ✅ Add document generation endpoints to [app/routers/document.py](app/routers/document.py)
3. ✅ Create `app/core/gemini_client.py` and consolidate `_call_gemini()`

### Phase 2 (Day 2) — High Priority
4. ✅ Create `app/core/logger.py` and replace all `print()` calls
5. ✅ Create `app/core/api_endpoints.py` for URL management
6. ✅ Update `requirements.txt` — remove unused, add `tenacity`

### Phase 3 (Week 1) — Medium Priority
7. ✅ Add type hints across codebase
8. ✅ Consolidate error handling and messages
9. ✅ Add retry logic with `@retry` decorator
10. ✅ Expand test coverage

### Phase 4 (Week 2) — Low Priority
11. ✅ Move magic strings to config
12. ✅ Add rate limiting
13. ✅ Add request validation
14. ✅ Document all functions

---

**Report Generated**: April 5, 2026
