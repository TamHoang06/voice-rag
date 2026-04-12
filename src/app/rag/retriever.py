import os
from typing import Any

from app.core.gemini_client import GeminiAPIError, call_gemini_llm
from app.rag._document._image_analyzer import ImageAnalyzer
from app.rag._document._utils import get_reader
from app.rag.loader import get_all_text, get_current_document_id, get_current_file, get_vectordb

_image_state: dict[str, dict[str, Any]] = {}


def _doc_state(document_id: str) -> dict[str, Any]:
    state = _image_state.setdefault(
        document_id,
        {"descriptions": {}, "images_analyzed": False},
    )
    return state


def _call_gemini(prompt: str, max_tokens: int = 1024, temperature: float = 0.2) -> str:
    try:
        return call_gemini_llm(prompt, max_tokens, temperature)
    except GeminiAPIError as e:
        print(f"[RAG GEMINI ERROR] {e}")
        return f"Loi Gemini: {e}"


_QA_PROMPT = (
    "Ban la tro ly AI, tra loi bang tieng Viet.\n"
    "Dua vao noi dung tai lieu de tra loi ngan gon, dung trong tam.\n"
    "Neu khong co thong tin: 'Khong co thong tin nay trong tai lieu.'\n\n"
    "=== Tai lieu ===\n{context}\n\n"
    "=== Cau hoi ===\n{question}\n\n"
    "=== Tra loi ===\n"
)

_SUMMARY_PROMPT = (
    "Tom tat tai lieu sau bang tieng Viet, 3-5 cau, neu y chinh:\n\n"
    "{text}\n\nTom tat:"
)


def _analyze_all_images_in_document(file_path: str, document_id: str) -> dict[int, str]:
    state = _doc_state(document_id)
    state["descriptions"] = {}

    if not os.path.exists(file_path):
        print(f"[RAG IMAGE] File not found: {file_path}")
        state["images_analyzed"] = True
        return {}

    ext = os.path.splitext(file_path)[1].lower()
    print(f"[RAG IMAGE] Processing {os.path.basename(file_path)} (ext: {ext})")

    try:
        reader = get_reader(file_path)
        images = reader.extract_images()
    except ValueError:
        print(f"[RAG IMAGE] Unsupported format: {ext}")
        state["images_analyzed"] = True
        return {}
    except Exception as e:
        print(f"[RAG IMAGE] Error extracting images: {e}")
        state["images_analyzed"] = True
        return {}

    print(f"[RAG IMAGE] Found {len(images)} images in {os.path.basename(file_path)}")
    if not images:
        state["images_analyzed"] = True
        return {}

    state["descriptions"] = ImageAnalyzer.analyze_batch(images)
    state["images_analyzed"] = True
    return state["descriptions"]


def get_image_descriptions(document_id: str | None = None) -> dict[int, str]:
    resolved_document_id = document_id or get_current_document_id()
    if not resolved_document_id:
        return {}
    return dict(_doc_state(resolved_document_id)["descriptions"])


def ask_question(question: str, document_id: str | None = None) -> str:
    db = get_vectordb(document_id=document_id)
    if db is None:
        return "Vui long upload tai lieu truoc."

    doc_id = document_id or get_current_document_id()
    docs = db.as_retriever(search_kwargs={"k": 4}).invoke(question)
    context = "\n\n".join(d.page_content for d in docs)

    state = _doc_state(doc_id) if doc_id else {"images_analyzed": False, "descriptions": {}}
    if state.get("images_analyzed") and state.get("descriptions"):
        image_context = "\n\n=== Hinh anh trong tai lieu ===\n"
        for idx, desc in sorted(state["descriptions"].items()):
            image_context += f"\n[Hinh {idx}] {desc}\n"
        context += image_context

    prompt = _QA_PROMPT.format(context=context, question=question)
    answer = _call_gemini(prompt, max_tokens=4096)
    print(f"[RAG] Q: {question[:80]}")
    print(f"[RAG] A: {answer[:120]}{'...' if len(answer) > 120 else ''}")
    return answer


def get_summary(document_id: str | None = None) -> str:
    text = get_all_text(document_id=document_id)
    if not text:
        return "Chua co tai lieu."
    return _call_gemini(
        _SUMMARY_PROMPT.format(text=text[:5000]),
        max_tokens=300,
        temperature=0.3,
    )


def get_document_images(document_id: str | None = None) -> dict[str, Any]:
    file_path = get_current_file(document_id=document_id)
    if not file_path or not os.path.exists(file_path):
        return {
            "images": [],
            "total": 0,
            "source": None,
            "message": "Chua co tai lieu.",
        }

    try:
        ext = os.path.splitext(file_path)[1].lower()
        reader = get_reader(file_path)
        images = reader.extract_images()
        return {
            "source": os.path.basename(file_path),
            "format": ext.lstrip(".").upper(),
            "total": len(images),
            "images": images,
            "message": f"Tim thay {len(images)} hinh anh." if images else "Khong tim thay hinh anh.",
        }
    except Exception as e:
        print(f"[RAG] Error getting images: {e}")
        return {
            "images": [],
            "total": 0,
            "source": None,
            "message": f"Loi: {e}",
        }
