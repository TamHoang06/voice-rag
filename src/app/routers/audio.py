import json
import os
import re
import uuid
from datetime import datetime
from typing import Optional

import asyncio

from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse

from app.config import OUTPUTS_DIR, FILE_MIME_MAP, DATA_DIR, SUPPORTED_AUDIO_EXT, VOICES_DIR, MAX_AUDIO_UPLOAD_SIZE
from app.core.logger import get_logger
from app.models.schemas import TTSRequest
from app.tts import text_to_speech, is_ready as tts_ready, GEMINI_VOICES
from app.config import gemini_tts_voice
from app.stt import transcribe_bytes, list_supported_formats
from app.utils import file_info
from app.db import db

router = APIRouter(tags=["audio"])
logger = get_logger(__name__)


def _safe_filename(name: str) -> str:
    name = os.path.splitext(os.path.basename(name))[0]
    safe = re.sub(r"[^\w\-]", "_", name)
    return safe[:40] if safe else "voice"


async def _save_upload_file(file: UploadFile, dest_dir: str) -> str:
    ext = os.path.splitext(file.filename)[1].lower() or ".wav"
    if ext not in SUPPORTED_AUDIO_EXT:
        raise HTTPException(400, f"Định dạng '{ext}' không hỗ trợ.")
    contents = await file.read()
    if len(contents) > MAX_AUDIO_UPLOAD_SIZE:
        raise HTTPException(413, f"Tệp audio quá lớn. Kích thước tối đa là {MAX_AUDIO_UPLOAD_SIZE // (1024 * 1024)}MB")
    basename = f"{_safe_filename(file.filename)}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}{ext}"
    os.makedirs(dest_dir, exist_ok=True)
    path = os.path.join(dest_dir, basename)
    with open(path, "wb") as f:
        f.write(contents)
    logger.info("Saved uploaded audio %s size=%s bytes", file.filename, len(contents))
    return path


@router.post("/voices/upload")
async def voice_upload(file: UploadFile = File(...), transcript: str = Form("")):
    """Lưu audio sample và transcript vào thư mục voices."""
    path = await _save_upload_file(file, VOICES_DIR)
    meta = {
        "filename": file.filename,
        "stored_filename": os.path.basename(path),
        "transcript": transcript,
        "saved_at": datetime.now().isoformat(),
        "is_active": False
    }
    # Lưu metadata vào MongoDB thay vì file JSON
    await db.voices.insert_one(meta)
    if "_id" in meta:
        meta["_id"] = str(meta["_id"])  # Convert ObjectId sang string để trả về JSON
    return {"message": "Đã lưu giọng lên server", "stored_filename": os.path.basename(path)}


@router.post("/voices/set-active")
async def voice_set_active(file: UploadFile = File(...), transcript: str = Form("")):
    """Đặt audio sample hiện tại là giọng active của thư viện."""
    ext = os.path.splitext(file.filename)[1].lower() or ".wav"
    if ext not in SUPPORTED_AUDIO_EXT:
        raise HTTPException(400, f"Định dạng '{ext}' không hỗ trợ.")
    contents = await file.read()
    if len(contents) > MAX_AUDIO_UPLOAD_SIZE:
        raise HTTPException(413, f"Tệp audio quá lớn. Kích thước tối đa là {MAX_AUDIO_UPLOAD_SIZE // (1024 * 1024)}MB")
    active_filename = f"active{ext}"
    active_path = os.path.join(VOICES_DIR, active_filename)
    os.makedirs(VOICES_DIR, exist_ok=True)
    with open(active_path, "wb") as f:
        f.write(contents)

    # Cập nhật trạng thái active trong MongoDB
    await db.voices.update_many({}, {"$set": {"is_active": False}})
    meta = {
        "active_filename": active_filename,
        "original_filename": file.filename,
        "transcript": transcript,
        "updated_at": datetime.now().isoformat(),
        "is_active": True
    }
    await db.voices.update_one({"active_filename": active_filename}, {"$set": meta}, upsert=True)

    logger.info("Set active voice sample %s size=%s bytes", file.filename, len(contents))
    return {"message": "Đã chọn giọng active", "active_filename": active_filename, "meta": meta}



@router.post("/text-to-speech")
async def text_to_speech_api(request: TTSRequest):
    if not request.text.strip():
        raise HTTPException(400, "Text không được để trống")
    
    # Kiểm tra có active voice từ voice library không
    active_meta = await db.voices.find_one({"is_active": True})
    
    try:
        safe = os.path.basename(request.filename or "tts_output.wav")
        if not safe.endswith(".wav"):
            safe += ".wav"
        outpath = os.path.join(OUTPUTS_DIR, safe)
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # Case 1: Nếu client yêu cầu giọng Gemini cụ thể thì dùng Gemini TTS
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        if request.voice:
            if not tts_ready():
                raise HTTPException(503, "TTS chưa sẵn sàng — kiểm tra GEMINI_API_KEY")
            text_to_speech(text=request.text, output_path=outpath, voice=request.voice)
            return {
                "message":      "Đã tạo audio bằng Gemini TTS",
                "chars":        len(request.text),
                "audio_url":    f"/download/{safe}",
                "download_url": f"/download/{safe}",
                "engine":       "Gemini TTS",
                "voice":        request.voice,
            }

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # Case 2: Có active voice → dùng F5-TTS để clone giọng
        # speaker_audio chỉ dùng để học giọng, KHÔNG copy ra output
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        if active_meta:
            active_audio_path = os.path.join(VOICES_DIR, active_meta["active_filename"])
            if not os.path.exists(active_audio_path):
                raise HTTPException(
                    404, 
                    f"File giọng active không tồn tại: {active_meta['active_filename']}"
                )

            logger.info(
                "Voice cloning: speaker=%s | text_len=%s | transcript_len=%s",
                active_meta["original_filename"], 
                len(request.text),
                len(active_meta.get("transcript", ""))
            )

            try:
                from app.tts.f5tts_inference import infer_f5tts

                logger.info("Gọi F5-TTS cloning với text: '%s'", request.text[:120])

                # Gọi đúng theo API của hàm infer_f5tts bạn đang có
                await asyncio.to_thread(
                    infer_f5tts,
                    text=request.text.strip(),                    # Text cần đọc
                    speaker_audio_path=active_audio_path,         # File giọng mẫu
                    speaker_transcript=active_meta.get("transcript", request.text[:300]),
                    output_path=outpath,
                    fallback_to_speaker=False,                    # Không cho fallback về file gốc
                    timeout_seconds=300,
                )

                # Kiểm tra output có thực sự được tạo không
                if not os.path.exists(outpath):
                    raise Exception("F5-TTS không tạo ra file output")

                output_size = os.path.getsize(outpath)
                speaker_size = os.path.getsize(active_audio_path)

                logger.info("F5-TTS cloning hoàn tất. Output size: %s bytes", output_size)
                

                # Cảnh báo nếu output gần giống file gốc (nghi ngờ fallback)
                if abs(output_size - speaker_size) < 10000:
                    logger.warning(
                        "CẢNH BÁO: Output size gần giống file gốc (%s vs %s). "
                        "Có thể F5-TTS đang fallback.", output_size, speaker_size
                    )
                    
                # Kiểm tra text trước khi clone
                if len(request.text.strip()) < 15:
                    raise HTTPException(
                        400, 
                        "Text quá ngắn để voice cloning. Vui lòng nhập ít nhất 15-20 ký tự."
                )
                    
                return {
                    "message":      "✓ Voice cloning thành công",
                    "chars":        len(request.text),
                    "audio_url":    f"/download/{safe}",
                    "download_url": f"/download/{safe}",
                    "engine":       "F5-TTS (Voice Cloning)",
                    "voice_source": active_meta.get("original_filename", "Unknown"),
                    "output_size":  output_size,
                }

            except ImportError:
                raise HTTPException(503, "F5-TTS chưa được cài đặt.\nChạy: pip install f5-tts")
            except Exception as f5_error:
                logger.exception("F5-TTS inference failed")
                raise HTTPException(
                    500,
                    f"Voice cloning thất bại: {str(f5_error)[:250]}\n"
                    "Gợi ý:\n"
                    "• Kiểm tra transcript của giọng mẫu có khớp với giọng không\n"
                    "• Thử với văn bản dài hơn (ít nhất 15-20 từ)\n"
                    "• Đảm bảo GPU/VRAM đủ nếu dùng CUDA"
                )
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # Case 3: Không có active voice và không chọn giọng cụ thể → Dùng Gemini mặc định
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        if not tts_ready():
            raise HTTPException(503, "TTS chưa sẵn sàng — kiểm tra GEMINI_API_KEY")
        text_to_speech(text=request.text, output_path=outpath, voice=request.voice)
        return {
            "message":      "Đã tạo audio bằng Gemini TTS",
            "chars":        len(request.text),
            "audio_url":    f"/download/{safe}",
            "download_url": f"/download/{safe}",
            "engine":       "Gemini TTS",
            "voice":        request.voice,
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Lỗi TTS: {str(e)[:200]}")



@router.post("/transcribe")
async def transcribe(
    file:     UploadFile = File(...),
    language: str = Query("vi"),
    task:     str = Query("transcribe"),
):
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in SUPPORTED_AUDIO_EXT:
        raise HTTPException(400, f"Định dạng '{ext}' không hỗ trợ.")
    try:
        audio_bytes = await file.read()
        if len(audio_bytes) > MAX_AUDIO_UPLOAD_SIZE:
            raise HTTPException(413, f"Tệp audio quá lớn. Kích thước tối đa là {MAX_AUDIO_UPLOAD_SIZE // (1024 * 1024)}MB")
        lang_param  = None if language.lower() in ("none", "auto", "") else language
        result      = transcribe_bytes(
            audio_bytes=audio_bytes,
            filename=file.filename,
            language=lang_param,
            task=task,
            temp_dir=DATA_DIR,
        )
        logger.info("Transcribe audio %s size=%s bytes", file.filename, len(audio_bytes))
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Lỗi transcribe audio %s", file.filename)
        raise HTTPException(500, f"Lỗi transcribe: {e}")
    return {
        "filename": file.filename,
        "text":     result["text"],
        "language": result["language"],
        "duration": result["duration"],
    }


@router.get("/tts-voices")
def tts_voices():
    return {
        "engine":        "Gemini 2.5 Flash TTS",
        "voices":        GEMINI_VOICES,
        "current_voice": gemini_tts_voice(),
        "tip":           "Set GEMINI_TTS_VOICE=Charon trong .env để đổi giọng mặc định",
    }


@router.get("/stt-status")
def stt_status():
    fmt = list_supported_formats()
    return {
        "engine":         fmt["stt_engine"],
        "gemini_key_set": bool(os.environ.get("GEMINI_API_KEY")),
        "input_formats":  fmt["input_formats"],
    }


@router.get("/download/{filename}")
def download_file(filename: str):
    safe = os.path.basename(filename)
    path = os.path.abspath(os.path.join(OUTPUTS_DIR, safe))
    if not os.path.exists(path):
        raise HTTPException(404, f"File '{safe}' không tồn tại")
    ext = os.path.splitext(safe)[1].lower()
    return FileResponse(
        path,
        media_type=FILE_MIME_MAP.get(ext, "application/octet-stream"),
        filename=safe,
    )


@router.get("/outputs")
def list_outputs():
    if not os.path.exists(OUTPUTS_DIR):
        return {"files": [], "total": 0}
    files = [
        file_info(os.path.join(OUTPUTS_DIR, f))
        for f in sorted(os.listdir(OUTPUTS_DIR))
        if os.path.isfile(os.path.join(OUTPUTS_DIR, f))
    ]
    return {"files": files, "total": len(files)}


@router.delete("/outputs/{filename}")
def delete_output(filename: str):
    safe = os.path.basename(filename)
    path = os.path.join(OUTPUTS_DIR, safe)
    if not os.path.exists(path):
        raise HTTPException(404, f"File '{safe}' không tồn tại")
    os.remove(path)
    return {"message": f"Đã xoá '{safe}'"}


@router.get("/debug/tts")
def debug_tts():
    """Chẩn đoán Gemini TTS — mở /debug/tts trên browser."""
    import json, urllib.request, urllib.error

    api_key = os.environ.get("GEMINI_API_KEY", "")
    model   = os.environ.get("GEMINI_TTS_MODEL", "gemini-2.5-flash-preview-tts")
    voice   = gemini_tts_voice()

    info: dict = {
        "GEMINI_API_KEY":   f"SET ({api_key[:8]}…)" if api_key else "⚠ KHÔNG SET",
        "GEMINI_TTS_MODEL": model,
        "GEMINI_TTS_VOICE": voice,
        "tts_ready":        bool(api_key),
    }

    if not api_key:
        info["hint"] = "Thêm GEMINI_API_KEY=... vào .env rồi restart server"
        return info

    url  = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    body = json.dumps({
        "contents": [{"role": "user", "parts": [{"text": "Xin chào."}]}],
        "generationConfig": {
            "responseModalities": ["AUDIO"],
            "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": voice}}},
        },
    }).encode("utf-8")
    req = urllib.request.Request(
        url, data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            data  = json.loads(resp.read().decode("utf-8"))
        parts = data.get("candidates", [{}])[0].get("content", {}).get("parts", [])
        info["test"] = f"✓ THÀNH CÔNG — {'audio nhận được' if any('inlineData' in p for p in parts) else 'không có audio?'}"
    except urllib.error.HTTPError as e:
        err   = e.read().decode("utf-8", errors="replace")
        hints = {
            400: "Voice name sai hoặc model không hỗ trợ TTS",
            401: "API key sai hoặc chưa active",
            403: "Hết quota hoặc không có quyền",
            404: "Model không tồn tại",
            429: "Rate limit — thử lại sau",
        }
        info["test"] = f"✗ HTTP {e.code}: {err[:300]}"
        info["hint"] = hints.get(e.code, f"HTTP {e.code}")
    except urllib.error.URLError as e:
        info["test"] = f"✗ Không kết nối: {e.reason}"
    return info