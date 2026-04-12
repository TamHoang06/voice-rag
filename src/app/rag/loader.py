import json
import os
import re
import threading
import uuid
import warnings
from pathlib import Path
from typing import Any

warnings.filterwarnings("ignore")

from langchain_community.document_loaders import TextLoader
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.config import VECTOR_PATH
from app.rag._document._utils import get_reader

_EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
_REGISTRY_FILE = Path(VECTOR_PATH) / "registry.json"

_state_lock = threading.Lock()
_embeddings: HuggingFaceEmbeddings | None = None
_document_registry: dict[str, dict[str, Any]] = {}
_vector_db_cache: dict[str, FAISS] = {}
_current_document_id: str = ""


def _safe_document_label(filename: str) -> str:
    stem = Path(filename).stem or "document"
    safe = re.sub(r"[^a-zA-Z0-9_-]+", "-", stem).strip("-").lower()
    return safe[:40] or "document"


def _ensure_vector_root() -> Path:
    root = Path(VECTOR_PATH)
    root.mkdir(parents=True, exist_ok=True)
    return root


def _document_dir(document_id: str) -> Path:
    return _ensure_vector_root() / document_id


def _persist_registry() -> None:
    _ensure_vector_root()
    payload = {
        "current_document_id": _current_document_id,
        "documents": _document_registry,
    }
    _REGISTRY_FILE.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _load_registry_from_disk() -> None:
    global _current_document_id
    if not _REGISTRY_FILE.exists():
        return

    try:
        payload = json.loads(_REGISTRY_FILE.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"[RAG] Warning: could not read registry: {exc}")
        return

    docs = payload.get("documents", {})
    if isinstance(docs, dict):
        _document_registry.update(docs)

    current_id = payload.get("current_document_id", "")
    if current_id in _document_registry:
        _current_document_id = current_id


def _load_text(file_path: str) -> str:
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".txt":
        loader = TextLoader(file_path, encoding="utf-8")
        documents = loader.load()
        return "\n".join(doc.page_content for doc in documents)

    try:
        reader = get_reader(file_path)
        return reader.extract_text()
    except ValueError as exc:
        raise ValueError(f"Unsupported: {ext}. Use: .pdf, .docx, .txt") from exc


def get_embeddings() -> HuggingFaceEmbeddings:
    global _embeddings
    with _state_lock:
        if _embeddings is None:
            print(f"[RAG] Loading embeddings lazily: {_EMBEDDING_MODEL}")
            _embeddings = HuggingFaceEmbeddings(model_name=_EMBEDDING_MODEL)
        return _embeddings


def _resolve_document_id(document_id: str | None = None, required: bool = False) -> str:
    doc_id = document_id or _current_document_id
    if doc_id and doc_id in _document_registry:
        return doc_id
    if required:
        raise KeyError("No active document found")
    return ""


def load_document(file_path: str, document_id: str | None = None) -> dict[str, Any]:
    """Load tai lieu, tao FAISS vectorstore va luu theo document_id."""
    global _current_document_id

    full_text = _load_text(file_path)
    if not full_text.strip():
        raise ValueError("Document is empty after extraction.")

    doc_id = document_id or f"{_safe_document_label(file_path)}-{uuid.uuid4().hex[:8]}"

    from langchain_core.documents import Document

    documents = [Document(page_content=full_text, metadata={"document_id": doc_id})]
    chunks = RecursiveCharacterTextSplitter(
        chunk_size=1200,
        chunk_overlap=200,
    ).split_documents(documents)

    vector_db = FAISS.from_documents(chunks, get_embeddings())
    doc_dir = _document_dir(doc_id)
    doc_dir.mkdir(parents=True, exist_ok=True)
    vector_db.save_local(str(doc_dir))

    metadata = {
        "document_id": doc_id,
        "file_path": os.path.abspath(file_path),
        "filename": os.path.basename(file_path),
        "full_text": full_text,
        "chunk_count": len(chunks),
    }
    (doc_dir / "metadata.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    with _state_lock:
        _vector_db_cache[doc_id] = vector_db
        _document_registry[doc_id] = metadata
        _current_document_id = doc_id
        _persist_registry()

    print(f"[RAG] Loaded '{file_path}' as '{doc_id}' -> {len(chunks)} chunks")
    return metadata


def load_vectorstore(document_id: str | None = None) -> FAISS | None:
    """Load vectorstore tu disk theo document_id. Startup chi nap registry metadata."""
    if document_id is None:
        _ensure_vector_root()
        _load_registry_from_disk()
        if _document_registry:
            print(f"[RAG] Registry loaded ({len(_document_registry)} document(s)).")
        return None

    doc_id = _resolve_document_id(document_id=document_id, required=True)
    with _state_lock:
        cached = _vector_db_cache.get(doc_id)
    if cached is not None:
        return cached

    doc_dir = _document_dir(doc_id)
    if not doc_dir.exists():
        raise FileNotFoundError(f"Vectorstore for document_id '{doc_id}' does not exist.")

    vector_db = FAISS.load_local(
        str(doc_dir),
        get_embeddings(),
        allow_dangerous_deserialization=True,
    )

    with _state_lock:
        _vector_db_cache[doc_id] = vector_db
    print(f"[RAG] Vectorstore loaded from disk for '{doc_id}'.")
    return vector_db


def set_current_document(document_id: str) -> None:
    global _current_document_id
    doc_id = _resolve_document_id(document_id=document_id, required=True)
    with _state_lock:
        _current_document_id = doc_id
        _persist_registry()


def get_current_document_id() -> str:
    return _current_document_id


def get_document_metadata(document_id: str | None = None) -> dict[str, Any]:
    doc_id = _resolve_document_id(document_id=document_id, required=True)
    return dict(_document_registry[doc_id])


def list_documents() -> list[dict[str, Any]]:
    return [
        dict(meta)
        for _, meta in sorted(_document_registry.items(), key=lambda item: item[0])
    ]


def get_vectordb(document_id: str | None = None) -> FAISS | None:
    doc_id = _resolve_document_id(document_id=document_id)
    if not doc_id:
        return None
    return load_vectorstore(doc_id)


def get_full_text(document_id: str | None = None) -> str:
    text = get_all_text(document_id=document_id)
    return text[:5000] if text else ""


def get_all_text(document_id: str | None = None) -> str:
    doc_id = _resolve_document_id(document_id=document_id)
    if not doc_id:
        return ""
    return _document_registry.get(doc_id, {}).get("full_text", "")


def get_current_file(document_id: str | None = None) -> str:
    doc_id = _resolve_document_id(document_id=document_id)
    if not doc_id:
        return ""
    return _document_registry.get(doc_id, {}).get("file_path", "")
