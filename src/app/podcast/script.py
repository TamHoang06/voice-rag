from dataclasses import asdict, dataclass, field
import threading
from typing import List, Optional


@dataclass
class PodcastSegment:
    index: int
    title: str
    text: str
    duration_estimate: float = 0.0

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class PodcastScript:
    title: str
    summary: str
    segments: List[PodcastSegment] = field(default_factory=list)
    source: str = ""

    def full_text(self) -> str:
        return "\n\n".join(s.text for s in self.segments)

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "summary": self.summary,
            "source": self.source,
            "total_segments": len(self.segments),
            "segments": [s.to_dict() for s in self.segments],
        }


_lock = threading.Lock()
_scripts_by_document: dict[str, PodcastScript] = {}
_current_document_id: str = ""


def set_current_script(script: PodcastScript, document_id: str) -> None:
    global _current_document_id
    with _lock:
        _scripts_by_document[document_id] = script
        _current_document_id = document_id


def get_current_script(document_id: str | None = None) -> Optional[PodcastScript]:
    with _lock:
        doc_id = document_id or _current_document_id
        return _scripts_by_document.get(doc_id)


def get_segment(index: int, document_id: str | None = None) -> Optional[PodcastSegment]:
    script = get_current_script(document_id=document_id)
    if script and 0 <= index < len(script.segments):
        return script.segments[index]
    return None
