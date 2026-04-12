from typing import Optional, List
from pydantic import BaseModel


class TTSRequest(BaseModel):
    text:     str
    voice:    Optional[str] = None
    filename: Optional[str] = "tts_output.wav"


class AskRequest(BaseModel):
    question: str
    document_id: Optional[str] = None
    speak:    bool = False
    voice:    Optional[str] = None


class PodcastGenerateRequest(BaseModel):
    document_id: Optional[str] = None
    num_segments: int = 5
    language:     str = "vi"
    voice:        Optional[str] = None


class PodcastQARequest(BaseModel):
    question:      str
    document_id:   Optional[str] = None
    segment_index: int = 0
    voice:         Optional[str] = None


class GenerateDocRequest(BaseModel):
    content: str
    title:   str = "Tài liệu"
    images:  Optional[List[str]] = None
    format:  str = "docx"


class TranscribeResponse(BaseModel):
    filename: str
    text:     str
    language: str
    duration: float
