import os
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, File, HTTPException, Query, UploadFile

from app.config import DATA_DIR, MAX_AUDIO_UPLOAD_SIZE, OUTPUTS_DIR, SUPPORTED_AUDIO_EXT
from app.core.logger import get_logger
from app.models.schemas import PodcastGenerateRequest, PodcastQARequest
from app.podcast.agent import answer_listener_question, generate_podcast_script
from app.podcast.script import get_current_script, get_segment, set_current_script
from app.rag.loader import get_all_text, get_current_document_id, get_current_file
from app.stt import transcribe_bytes
from app.tts import is_ready as tts_ready
from app.tts import text_to_speech

router = APIRouter(prefix="/podcast", tags=["podcast"])
logger = get_logger(__name__)


@router.post("/generate")
def podcast_generate(req: PodcastGenerateRequest):
    document_id = req.document_id or get_current_document_id()
    text = get_all_text(document_id=document_id)
    if not text:
        raise HTTPException(404, "Chua co tai lieu. Vui long upload truoc.")

    source = os.path.basename(get_current_file(document_id=document_id)) if get_current_file(document_id=document_id) else "tai lieu"
    try:
        script = generate_podcast_script(
            text=text,
            source_name=source,
            num_segments=req.num_segments,
            language=req.language,
        )
        set_current_script(script, document_id=document_id)
        return {
            "message": "Podcast script da tao thanh cong",
            "document_id": document_id,
            "title": script.title,
            "summary": script.summary,
            "total_segments": len(script.segments),
            "segments": [
                {
                    "index": s.index,
                    "title": s.title,
                    "duration_estimate": s.duration_estimate,
                    "preview": s.text[:120] + "...",
                }
                for s in script.segments
            ],
        }
    except Exception as e:
        logger.exception("Loi tao podcast script")
        raise HTTPException(500, f"Loi tao podcast script: {e}")


@router.get("/script")
def podcast_script(document_id: str | None = Query(None)):
    resolved_document_id = document_id or get_current_document_id()
    script = get_current_script(document_id=resolved_document_id)
    if not script:
        raise HTTPException(404, "Chua co podcast script.")
    payload = script.to_dict()
    payload["document_id"] = resolved_document_id
    return payload


@router.post("/tts/summary")
def podcast_tts_summary(
    voice: Optional[str] = Query(None),
    document_id: str | None = Query(None),
):
    if not tts_ready():
        raise HTTPException(503, "TTS chua san sang - kiem tra GEMINI_API_KEY")
    resolved_document_id = document_id or get_current_document_id()
    script = get_current_script(document_id=resolved_document_id)
    if not script:
        raise HTTPException(404, "Chua co podcast script")
    try:
        fname = f"podcast_intro_{datetime.now().strftime('%H%M%S')}.wav"
        outpath = os.path.join(OUTPUTS_DIR, fname)
        text_to_speech(f"{script.title}. {script.summary}", output_path=outpath, voice=voice)
        return {"document_id": resolved_document_id, "audio_url": f"/download/{fname}"}
    except Exception as e:
        logger.exception("Loi TTS intro")
        raise HTTPException(500, f"Loi TTS intro: {e}")


@router.post("/tts/{segment_index}")
def podcast_tts(
    segment_index: int,
    voice: Optional[str] = Query(None),
    document_id: str | None = Query(None),
):
    if not tts_ready():
        raise HTTPException(503, "TTS chua san sang - kiem tra GEMINI_API_KEY trong .env")

    resolved_document_id = document_id or get_current_document_id()
    segment = get_segment(segment_index, document_id=resolved_document_id)
    if not segment:
        raise HTTPException(404, f"Khong tim thay segment {segment_index}")
    if not segment.text.strip():
        raise HTTPException(422, f"Segment {segment_index} khong co noi dung")

    try:
        fname = f"podcast_seg_{segment_index}_{datetime.now().strftime('%H%M%S')}.wav"
        outpath = os.path.join(OUTPUTS_DIR, fname)
        text_to_speech(segment.text, output_path=outpath, voice=voice)
        return {
            "document_id": resolved_document_id,
            "segment_index": segment_index,
            "title": segment.title,
            "duration_est": segment.duration_estimate,
            "audio_url": f"/download/{fname}",
            "chars": len(segment.text),
        }
    except Exception as e:
        logger.exception("Loi TTS segment %s", segment_index)
        raise HTTPException(500, f"Loi TTS segment {segment_index}: {e}")


@router.post("/qa")
def podcast_qa(req: PodcastQARequest):
    document_id = req.document_id or get_current_document_id()
    script = get_current_script(document_id=document_id)
    segment = get_segment(req.segment_index, document_id=document_id)
    if not script or not segment:
        raise HTTPException(404, "Chua co podcast script hoac segment khong hop le")
    try:
        answer = answer_listener_question(req.question, segment, get_all_text(document_id=document_id))
        result: dict = {
            "document_id": document_id,
            "question": req.question,
            "answer": answer,
            "segment_index": req.segment_index,
            "segment_title": segment.title,
        }
        if tts_ready():
            try:
                fname = f"podcast_qa_{datetime.now().strftime('%H%M%S')}.wav"
                outpath = os.path.join(OUTPUTS_DIR, fname)
                text_to_speech(answer, output_path=outpath, voice=req.voice)
                result["audio_url"] = f"/download/{fname}"
            except Exception as e:
                result["tts_error"] = str(e)
        return result
    except Exception as e:
        logger.exception("Loi Q&A")
        raise HTTPException(500, f"Loi Q&A: {e}")


@router.post("/qa/voice")
async def podcast_qa_voice(
    file: UploadFile = File(...),
    segment_index: int = Query(0),
    voice: Optional[str] = Query(None),
    document_id: str | None = Query(None),
):
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in SUPPORTED_AUDIO_EXT:
        raise HTTPException(400, f"Dinh dang khong ho tro: {ext}")
    try:
        audio_bytes = await file.read()
        if len(audio_bytes) > MAX_AUDIO_UPLOAD_SIZE:
            raise HTTPException(413, f"Tep audio qua lon. Kich thuoc toi da la {MAX_AUDIO_UPLOAD_SIZE // (1024 * 1024)}MB")
        stt_result = transcribe_bytes(
            audio_bytes=audio_bytes,
            filename=file.filename,
            language="vi-VN",
            temp_dir=DATA_DIR,
        )
        question = stt_result["text"]
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Loi STT trong podcast QA voice")
        raise HTTPException(500, f"Loi STT: {e}")

    resolved_document_id = document_id or get_current_document_id()
    script = get_current_script(document_id=resolved_document_id)
    segment = get_segment(segment_index, document_id=resolved_document_id)
    if not script or not segment:
        raise HTTPException(404, "Chua co podcast script")

    answer = answer_listener_question(question, segment, get_all_text(document_id=resolved_document_id))
    result: dict = {
        "document_id": resolved_document_id,
        "transcribed_question": question,
        "answer": answer,
        "segment_index": segment_index,
    }
    if tts_ready():
        try:
            fname = f"podcast_voice_qa_{datetime.now().strftime('%H%M%S')}.wav"
            outpath = os.path.join(OUTPUTS_DIR, fname)
            text_to_speech(answer, output_path=outpath, voice=voice)
            result["audio_url"] = f"/download/{fname}"
        except Exception as e:
            result["tts_error"] = str(e)
    return result
