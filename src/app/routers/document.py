import os
import uuid
from datetime import datetime

from fastapi import APIRouter, File, HTTPException, Query, UploadFile

from app.config import DATA_DIR, MAX_UPLOAD_SIZE, OUTPUTS_DIR, SUPPORTED_DOC_EXT
from app.core.logger import get_logger
from app.document.generator import DocumentGenerator
from app.models.schemas import AskRequest, GenerateDocRequest
from app.rag.loader import (
    get_all_text,
    get_current_document_id,
    get_current_file,
    get_document_metadata,
    get_full_text,
    list_documents,
    load_document,
    set_current_document,
)
from app.rag.retriever import (
    ask_question,
    get_document_images,
    get_image_descriptions,
    get_summary,
)
from app.tts import is_ready as tts_ready
from app.tts import text_to_speech

router = APIRouter(tags=["document"])
logger = get_logger(__name__)
doc_generator = DocumentGenerator(output_dir=OUTPUTS_DIR)


@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in SUPPORTED_DOC_EXT:
        raise HTTPException(400, f"Dinh dang tai lieu khong hop le: {ext}. Ho tro: {', '.join(sorted(SUPPORTED_DOC_EXT))}")

    contents = await file.read()
    if len(contents) > MAX_UPLOAD_SIZE:
        raise HTTPException(413, f"Tep qua lon. Kich thuoc toi da la {MAX_UPLOAD_SIZE // (1024 * 1024)}MB")

    safe_name = os.path.basename(file.filename) or f"document_{datetime.now().strftime('%Y%m%d_%H%M%S')}{ext}"
    os.makedirs(DATA_DIR, exist_ok=True)
    file_path = os.path.join(DATA_DIR, safe_name)
    with open(file_path, "wb") as buf:
        buf.write(contents)

    try:
        document_id = f"doc-{uuid.uuid4().hex[:12]}"
        metadata = load_document(file_path, document_id=document_id)

        try:
            from app.rag.retriever import _analyze_all_images_in_document
            _analyze_all_images_in_document(file_path, document_id)
        except Exception as image_error:
            logger.warning("Image analysis skipped for %s: %s", file.filename, image_error)

        descriptions = get_image_descriptions(document_id)
        logger.info("Uploaded document '%s' size=%s bytes as %s", file.filename, len(contents), document_id)
        return {
            "message": f"Uploaded '{file.filename}' successfully",
            "document_id": document_id,
            "total_chars": len(metadata["full_text"]),
            "filename": file.filename,
            "chunk_count": metadata["chunk_count"],
            "images_count": len(descriptions),
        }
    except Exception as e:
        logger.exception("Loi xu ly tai lieu %s", file.filename)
        raise HTTPException(500, f"Loi xu ly tai lieu: {e}")


@router.get("/documents")
def documents():
    return {
        "current_document_id": get_current_document_id(),
        "documents": list_documents(),
    }


@router.post("/documents/{document_id}/select")
def select_document(document_id: str):
    try:
        set_current_document(document_id)
        return {
            "message": "Selected document successfully",
            "document_id": document_id,
            "metadata": get_document_metadata(document_id),
        }
    except KeyError:
        raise HTTPException(404, f"Document '{document_id}' not found")


@router.get("/document")
def document(
    include_images: bool = Query(True),
    text_limit: int = Query(5000),
    document_id: str | None = Query(None),
):
    resolved_document_id = document_id or get_current_document_id()
    text = get_full_text(document_id=resolved_document_id) if text_limit > 0 else get_all_text(document_id=resolved_document_id)
    if text_limit > 0:
        text = text[:text_limit]
    result: dict = {
        "document_id": resolved_document_id,
        "content": text,
    }
    if include_images:
        result["images"] = get_document_images(document_id=resolved_document_id)["images"]
    return result


@router.get("/document/summary")
def document_summary(document_id: str | None = Query(None)):
    resolved_document_id = document_id or get_current_document_id()
    return {
        "document_id": resolved_document_id,
        "summary": get_summary(document_id=resolved_document_id),
    }


@router.post("/re-analyze-images")
async def re_analyze_images(document_id: str | None = Query(None)):
    from app.rag.retriever import _analyze_all_images_in_document

    resolved_document_id = document_id or get_current_document_id()
    file_path = get_current_file(document_id=resolved_document_id)
    if not file_path:
        raise HTTPException(400, "No document loaded")

    try:
        descriptions = _analyze_all_images_in_document(file_path, resolved_document_id)
        return {
            "message": "Images re-analyzed successfully",
            "document_id": resolved_document_id,
            "images_found": len(descriptions),
            "descriptions": descriptions,
        }
    except Exception as e:
        raise HTTPException(500, f"Error re-analyzing images: {e}")


@router.post("/ask")
def ask(req: AskRequest):
    resolved_document_id = req.document_id or get_current_document_id()
    answer = ask_question(req.question, document_id=resolved_document_id)
    result: dict = {
        "document_id": resolved_document_id,
        "question": req.question,
        "answer": answer,
    }
    if req.speak and tts_ready():
        try:
            fname = f"answer_{datetime.now().strftime('%H%M%S')}.wav"
            outpath = os.path.join(OUTPUTS_DIR, fname)
            text_to_speech(answer, output_path=outpath, voice=req.voice)
            result["audio_url"] = f"/download/{fname}"
        except Exception as e:
            result["tts_error"] = str(e)
    return result


@router.post("/generate-docx")
def generate_docx(req: GenerateDocRequest):
    if not req.content.strip():
        raise HTTPException(400, "Content cannot be empty")

    try:
        output_path = doc_generator.create_docx(
            content=req.content,
            images=req.images,
            title=req.title,
            filename=f"{req.title.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx",
        )
        filename = os.path.basename(output_path)
        return {
            "message": "DOCX generated successfully",
            "filename": filename,
            "download_url": f"/download/{filename}",
        }
    except Exception as e:
        raise HTTPException(500, f"Error generating DOCX: {e}")


@router.post("/generate-pdf")
def generate_pdf(req: GenerateDocRequest):
    if not req.content.strip():
        raise HTTPException(400, "Content cannot be empty")

    try:
        output_path = doc_generator.create_pdf(
            content=req.content,
            images=req.images,
            title=req.title,
            filename=f"{req.title.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
        )
        filename = os.path.basename(output_path)
        return {
            "message": "PDF generated successfully",
            "filename": filename,
            "download_url": f"/download/{filename}",
        }
    except Exception as e:
        raise HTTPException(500, f"Error generating PDF: {e}")
