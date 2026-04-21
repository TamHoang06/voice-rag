# Style Guide - Voice Agent Project

## 1. Naming Conventions

### Variables (tiếng Việt & English)
```python
# ✅ CORRECT - Clear, descriptive
document_id = "doc-abc123"
gemini_api_key = os.getenv("GEMINI_API_KEY")
audio_chunk_duration = 2.5
is_voice_cloning_enabled = True

# ❌ WRONG - Ambiguous, unclear
doc_id = "doc-abc123"  # Use full words
api_key = "..."  # Can confuse with other APIs
duration = 2.5  # Too generic
enable_voice = True  # Ambiguous
```

### Vietnamese Variable Names (Optional)
```python
# If using Vietnamese for domain concepts, be consistent
tài_liệu_id = "doc-abc123"          # Document ID
âm_thanh_đầu_vào = "input.wav"     # Input audio
ngôn_ngữ_đích = "vi-VN"            # Target language

# Mix only when necessary, prefer English for code
document_id = "doc-abc123"  # Preferred
podcast_title = "Tiêu đề Podcast"  # Mixed: English variable, Vietnamese value
```

### Functions & Methods
```python
# ✅ CORRECT - verb_noun format, descriptive
def generate_podcast_script(doc_id: str) -> dict:
    """Generate podcast script from document."""
    pass

def transcribe_audio_file(audio_path: str) -> str:
    """Transcribe audio file to text."""
    pass

def retrieve_rag_context(query: str, doc_id: str, k: int = 4) -> List[Document]:
    """Retrieve relevant document chunks."""
    pass

# ❌ WRONG - vague or too short
def gen_script():  # Too short
    pass

def process():  # Too vague
    pass

def get():  # Ambiguous
    pass
```

### Private Functions
```python
# Use leading underscore for internal functions
def _estimate_audio_duration(audio_bytes: bytes) -> float:
    """Internal helper - not part of public API."""
    pass

def _merge_wav_chunks(chunks: List[bytes]) -> bytes:
    """Internal audio processing."""
    pass

# Multiple underscores for very internal
def __validate_chunk_size(size: int) -> bool:
    """Name-mangled internal method."""
    pass
```

### Constants
```python
# UPPERCASE_WITH_UNDERSCORES
CHUNK_SIZE = 1200
CHUNK_OVERLAP = 200
MAX_AUDIO_FILE_SIZE = 30 * 1024 * 1024  # 30MB
DEFAULT_LANGUAGE = "vi-VN"
SUPPORTED_OUTPUT_FORMATS = ["wav", "mp3", "m4a", "ogg", "flac", "webm", "mp4"]

# Grouped related constants
GEMINI_VOICES = {
    "Aoede": "Female, natural",
    "Charon": "Male, deep",
    "Kore": "Female, warm",
}

TTS_CHUNK_SIZE = 4500  # Max chars per TTS API call
STT_MAX_FILE_SIZE = 30 * 1024 * 1024  # 30MB
RATE_LIMIT_WINDOW = 60  # seconds
```

### Classes
```python
# PascalCase for all classes
class DocumentLoader:
    """Load documents and create vectorstore."""
    pass

class RateLimitMiddleware:
    """Rate limiting middleware for FastAPI."""
    pass

class PodcastGenerator:
    """Generate podcast from documents."""
    pass

class VoiceCloneManager:
    """Manage voice cloning operations."""
    pass

# Exceptions follow class naming
class DocumentProcessingError(Exception):
    """Raised when document processing fails."""
    pass

class VectostoreException(Exception):
    """Raised for vectorstore operations."""
    pass
```

### Files & Directories
```
# Lowercase with underscores
src/
  app/
    core/
      gemini_client.py
      rate_limit.py
      logger.py
    
    rag/
      loader.py
      retriever.py
      _document/
        _pdf_reader.py
        _word_reader.py
        _reader_base.py
    
    routers/
      document.py
      podcast.py
      audio.py
      voices.py
    
    models/
      schemas.py
```

## 2. Code Style Rules

### Imports
```python
# ✅ CORRECT - Organized, clear
import os
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime

import fastapi
from pydantic import BaseModel, Field, validator
from langchain.document_loaders import PyPDFLoader
from sentence_transformers import SentenceTransformer

from src.app.core.logger import get_logger
from src.app.config import GEMINI_API_KEY
from src.app.rag.loader import load_vectorstore

# ❌ WRONG - Disorganized
from src.app.config import GEMINI_API_KEY
import os
from langchain.document_loaders import PyPDFLoader
from src.app.core.logger import get_logger
from pydantic import BaseModel
import json
```

### Line Length
```python
# Max 100 characters per line (soft limit), 120 hard limit
# Break long lines logically

# ✅ CORRECT - Readable
response = generate_qa_answer(
    question=user_question,
    doc_id=document_id,
    include_images=True,
    max_context_chunks=4
)

# ❌ WRONG - Too long
response = generate_qa_answer(question=user_question, doc_id=document_id, include_images=True, max_context_chunks=4)
```

### String Formatting
```python
# ✅ CORRECT - f-strings (Python 3.6+)
logger.info(f"Processing document {doc_id} with {len(segments)} segments")
error_msg = f"Failed to load {file_path}: {error}"

# ✅ ALSO CORRECT - For logging
logger.info("Processing document %s with %d segments", doc_id, len(segments))

# ❌ AVOID - Old style
message = "Processing document {} with {} segments".format(doc_id, len(segments))
message = "Processing document " + doc_id + " ..."  # String concatenation
```

### Type Hints
```python
# ✅ CORRECT - All public functions have type hints
def generate_podcast_script(
    doc_id: str,
    num_segments: Optional[int] = None
) -> Dict[str, any]:
    """Generate podcast script."""
    pass

# ✅ COMPLEX TYPES
from typing import Dict, List, Tuple, Union, Optional

def process_segments(
    segments: List[Dict[str, str]],
    voice: Optional[str] = None
) -> Tuple[List[str], int]:
    """Process segments and return (file paths, total duration)."""
    pass

# ❌ AVOID - No type hints
def process(data):
    pass
```

### Docstrings
```python
# ✅ CORRECT - Google style docstring
def generate_qa_answer(
    question: str,
    doc_id: str,
    include_images: bool = True
) -> str:
    """
    Generate answer to question using RAG and document context.
    
    Args:
        question: User's question string
        doc_id: Document ID to search context from
        include_images: Whether to include image descriptions in context
    
    Returns:
        Answer string in Vietnamese language
    
    Raises:
        FileNotFoundError: If document not found in registry
        ValueError: If question is empty or whitespace only
    
    Examples:
        >>> answer = generate_qa_answer(
        ...     "What is the main topic?",
        ...     "doc-abc123"
        ... )
        >>> print(answer)
        "The main topic is..."
    """
    pass

# ✅ CLASS DOCSTRING
class DocumentLoader:
    """
    Load documents and create FAISS vectorstore.
    
    Supports PDF, DOCX, and TXT formats. Handles text extraction,
    chunking, embedding, and image analysis.
    
    Attributes:
        vectorstore_path: Path to FAISS index directory
        embedding_model: HuggingFace embedding model instance
        chunk_size: Size of text chunks (default 1200)
    
    Example:
        >>> loader = DocumentLoader()
        >>> vectorstore = loader.load_document("document.pdf")
    """
    pass
```

### Comments
```python
# ✅ CORRECT - Clear, concise comments
# Retrieve 4 most relevant chunks from document
context_chunks = vectorstore.similarity_search(query, k=4)

# Rate limiting: max 3 requests per second
time.sleep(0.3)

# Skip empty segments to avoid TTS errors
if segment.get("text", "").strip():
    segments.append(segment)

# ❌ AVOID - Obvious or unnecessary comments
x = x + 1  # Increment x by 1

# Unnecessary comment that just repeats code
chunks = split_text(doc)  # Split the document into chunks
```

## 3. Formatting & Spacing

### Whitespace
```python
# ✅ CORRECT - Proper spacing
def calculate_duration(word_count: int) -> float:
    """Calculate reading duration in seconds."""
    words_per_minute = 150
    return (word_count / words_per_minute) * 60


def another_function():
    """Another function separated by 2 blank lines."""
    pass


# ❌ WRONG - No spacing or too much
def function1(): pass
def function2(): pass


def function3():
    pass
```

### Dictionary & List Formatting
```python
# ✅ CORRECT - Multi-line for clarity
segment = {
    "index": 0,
    "title": "Introduction",
    "text": "Welcome to the podcast...",
    "duration_estimate": 120
}

voices = [
    "Aoede",
    "Charon",
    "Fenrir",
    "Puck",
    "Schedar",
]

# ✅ ALSO CORRECT - Single line for short items
config = {"mode": "production", "debug": False}
languages = ["vi-VN", "en-US"]
```

## 4. Error Handling

### Exception Types
```python
# ✅ CORRECT - Specific exceptions
if not os.path.exists(audio_path):
    raise FileNotFoundError(f"Audio file not found: {audio_path}")

if file_size > MAX_SIZE:
    raise ValueError(f"File exceeds limit: {MAX_SIZE} bytes")

if not voice_id in available_voices:
    raise KeyError(f"Voice not found: {voice_id}")

# Custom exceptions for domain logic
class DocumentProcessingError(Exception):
    """Raised when document processing fails."""
    pass

raise DocumentProcessingError("PDF extraction failed") from e

# ❌ AVOID - Generic exceptions
raise Exception("Something went wrong")
```

### Try-Except Blocks
```python
# ✅ CORRECT - Specific exception handling
try:
    result = gemini_client.transcribe_audio(audio_path)
except FileNotFoundError:
    logger.error(f"Audio file not found: {audio_path}")
    raise
except Exception as e:
    logger.error(f"Transcription failed: {e}", exc_info=True)
    raise DocumentProcessingError("STT failed") from e

# ❌ AVOID - Too broad
try:
    result = some_operation()
except:
    pass
```

## 5. Logging

### Logging Levels
```python
from src.app.core.logger import get_logger

logger = get_logger(__name__)

# DEBUG - Detailed info for debugging
logger.debug("Vectorstore loaded with %d documents", doc_count)

# INFO - General informational messages
logger.info(f"Podcast generated for {doc_id} with {num_segments} segments")

# WARNING - Warning messages about potential issues
logger.warning("GEMINI_API_KEY not configured: TTS/STT unavailable")

# ERROR - Error messages with exception info
logger.error(f"Failed to process {file_path}", exc_info=True)

# CRITICAL - Critical errors
logger.critical("Vectorstore corrupted, cannot continue")
```

### Structured Logging
```python
# ✅ CORRECT - Include context
logger.info(
    "TTS generation completed",
    extra={
        "doc_id": doc_id,
        "segment_count": len(segments),
        "duration_ms": elapsed_time,
        "voice": voice_id,
    }
)

# ❌ AVOID - Too much or too little context
logger.info("Done")  # Too vague
logger.debug("x = 1, y = 2, z = 3, ...")  # Too much detail
```

## 6. FastAPI Conventions

### Route Organization
```python
# ✅ CORRECT - Grouped by feature
from fastapi import APIRouter

router = APIRouter(
    prefix="/podcast",
    tags=["podcast"],
    responses={404: {"description": "Not found"}}
)

@router.get("/{doc_id}", response_model=PodcastScript)
async def get_podcast(doc_id: str):
    """Get podcast script for document."""
    pass

@router.post("/{doc_id}/generate")
async def generate_podcast_audio(doc_id: str, request: GenerateRequest):
    """Generate podcast audio."""
    pass
```

### Request Validation
```python
from pydantic import BaseModel, Field, validator

class GenerateRequest(BaseModel):
    """Podcast generation request."""
    voice: str = Field(default="Kore", description="Voice to use")
    output_format: str = Field(default="wav")
    num_segments: Optional[int] = Field(default=None, ge=1, le=15)
    
    @validator('voice')
    def validate_voice(cls, v):
        if v not in AVAILABLE_VOICES:
            raise ValueError(f"Invalid voice: {v}")
        return v
```

## 7. Testing Conventions

### Test File Organization
```python
# tests/test_podcast.py
import pytest
from src.app.podcast.agent import generate_podcast_script

class TestPodcastGeneration:
    """Test suite for podcast generation."""
    
    def test_generate_script_success(self):
        """Test successful script generation from document."""
        script = generate_podcast_script("doc-test-123")
        assert script["title"]
        assert len(script["segments"]) > 0
    
    def test_generate_script_missing_document(self):
        """Test error handling for missing document."""
        with pytest.raises(FileNotFoundError):
            generate_podcast_script("doc-nonexistent")
    
    @pytest.mark.asyncio
    async def test_async_operation(self):
        """Test async function."""
        result = await async_function()
        assert result is not None
```

### Test Naming
```python
# ✅ CORRECT - Descriptive test names
def test_generate_podcast_with_valid_document():
    pass

def test_generate_podcast_raises_error_for_missing_document():
    pass

def test_tts_converts_text_to_audio_correctly():
    pass

# ❌ AVOID - Vague test names
def test_function():
    pass

def test_1():
    pass
```

## 8. Vietnamese-Specific Guidelines

### Comments in Vietnamese
```python
# ✅ ACCEPTABLE - Document domain knowledge in Vietnamese
# Xử lý âm thanh: chia thành các đoạn và ghép lại
# Audio processing: split into chunks and merge

# Lưu trữ document metadata trong JSON registry
# Store document metadata in JSON registry
voice_data = load_voice_library()  # Tải thư viện giọng

# ✅ PREFERRED - English for technical code
# Process audio chunks and merge into single file
def merge_audio_chunks(chunks: List[bytes]) -> bytes:
    pass
```

### Translation Standards
```python
# If translating error messages for Vietnamese users:
if not document:
    raise FileNotFoundError("Tài liệu không tìm thấy")  # "Document not found"

logger.warning("API key không được cấu hình")  # "API key not configured"

# For public API responses, use English
response = {"error": "Document not found", "status": 404}
```

## 9. Configuration Files

### YAML Configuration
```yaml
# config.yaml
app:
  name: "voice-agent"
  version: "1.0.0"
  debug: false

gemini:
  api_key: "${GEMINI_API_KEY}"
  timeout: 30
  max_retries: 3

rag:
  chunk_size: 1200
  chunk_overlap: 200
  embedding_model: "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

tts:
  default_voice: "Kore"
  max_chunk_size: 4500
  output_format: "wav"

stt:
  default_language: "vi-VN"
  max_file_size: 31457280  # 30MB

rate_limiting:
  enabled: true
  requests_per_window: 60
  window_seconds: 60
```

## 10. Checklist Before Commit

- [ ] All variables have clear names (no abbreviations)
- [ ] All public functions have type hints and docstrings
- [ ] No hardcoded values (use constants or config)
- [ ] Error handling with specific exception types
- [ ] Logging added for debugging and monitoring
- [ ] No unused imports or variables
- [ ] Tests written for new functions
- [ ] Comments explain "why", not "what"
- [ ] PEP 8 style followed (100-120 char lines)
- [ ] No `print()` statements (use logger instead)
- [ ] No `TODO` comments without context
- [ ] No commented-out code blocks
