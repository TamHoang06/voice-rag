import multiprocessing as mp
import os
import shutil
from pathlib import Path
from queue import Empty

_DEFAULT_TIMEOUT_SECONDS = int(os.environ.get("F5TTS_TIMEOUT_SECONDS", "180"))
_MAX_REF_TEXT_CHARS = int(os.environ.get("F5TTS_MAX_REF_TEXT_CHARS", "300"))
_MAX_GEN_TEXT_CHARS = int(os.environ.get("F5TTS_MAX_GEN_TEXT_CHARS", "300"))


def _normalize_text(text: str) -> str:
    return " ".join((text or "").split()).strip()


def _trim_text(text: str, max_chars: int) -> str:
    text = _normalize_text(text)
    if len(text) <= max_chars:
        return text
    trimmed = text[:max_chars].rsplit(" ", 1)[0].strip()
    return trimmed if trimmed else text[:max_chars].strip()


def _safe_fallback_copy(speaker_path: Path, output_path: str) -> str:
    """Fallback: copy nguyên file giọng mẫu nếu F5-TTS thất bại"""
    print("[F5TTS] FALLBACK → using original speaker audio")
    shutil.copy(speaker_path, output_path)
    print(f"[F5TTS] Fallback saved → {output_path}")
    return output_path


def _infer_worker(
    speaker_audio_path: str,
    speaker_transcript: str,
    gen_text: str,
    output_path: str,
    status_queue,
) -> None:
    try:
        import torch
        from f5_tts.api import F5TTS

        device = "cuda" if torch.cuda.is_available() else "cpu"
        status_queue.put(("status", f"Loading F5-TTS model on {device.upper()}..."))

        model = F5TTS(device=device)

        status_queue.put(("status", "Synthesizing audio..."))
        
        model.infer(
            ref_file=speaker_audio_path,
            ref_text=speaker_transcript,
            gen_text=gen_text,
            show_info=lambda *args, **kwargs: None,
            progress=None,
            file_wave=output_path,
        )

        if not os.path.exists(output_path):
            raise RuntimeError("F5-TTS finished but no output file was created")

        status_queue.put(("done", output_path))

    except Exception as exc:
        status_queue.put(("error", f"{type(exc).__name__}: {exc}"))


def infer_f5tts(
    text: str,
    speaker_audio_path: str,
    speaker_transcript: str,
    output_path: str = None,
    fallback_to_speaker: bool = True,
    timeout_seconds: int | None = None,
) -> str:
    """
    Voice cloning using F5-TTS with improved timeout and fallback.
    """
    speaker_path = Path(speaker_audio_path).resolve()
    if not speaker_path.exists():
        raise FileNotFoundError(f"[F5TTS] Speaker audio not found: {speaker_path}")

    if not output_path:
        from app.config import OUTPUTS_DIR
        output_path = os.path.join(OUTPUTS_DIR, f"f5tts_{os.urandom(8).hex()}.wav")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Tăng timeout mặc định lên 3 phút (180 giây)
    timeout_seconds = int(timeout_seconds or _DEFAULT_TIMEOUT_SECONDS)

    ref_text = _trim_text(speaker_transcript, _MAX_REF_TEXT_CHARS)
    gen_text = _trim_text(text, _MAX_GEN_TEXT_CHARS)

    print(f"[F5TTS] Starting → timeout={timeout_seconds}s | device=CPU/GPU")
    print(f"[F5TTS] Text: '{gen_text[:100]}...' | Ref text: {len(ref_text)} chars")

    ctx = mp.get_context("spawn")
    status_queue = ctx.Queue()
    process = ctx.Process(
        target=_infer_worker,
        args=(str(speaker_path), ref_text, gen_text, output_path, status_queue),
        daemon=True,
    )

    process.start()

    result_path = None
    error_message = None

    try:
        while True:
            try:
                kind, payload = status_queue.get(timeout=timeout_seconds)
            except Empty:
                error_message = f"timeout after {timeout_seconds}s"
                print(f"[F5TTS] TIMEOUT → {error_message}")
                break

            if kind == "status":
                print(f"[F5TTS] {payload}")
                continue
            if kind == "done":
                result_path = payload
                break
            if kind == "error":
                error_message = payload
                print(f"[F5TTS] ERROR → {payload}")
                break

        if process.is_alive():
            process.terminate()
        process.join(timeout=10)

    finally:
        try:
            status_queue.close()
        except Exception:
            pass

    if result_path and os.path.exists(result_path):
        print(f"[F5TTS] SUCCESS → {result_path} ({os.path.getsize(result_path)//1024} KB)")
        return result_path

    # Fallback nếu timeout hoặc lỗi
    if fallback_to_speaker:
        print(f"[F5TTS] FALLBACK triggered: {error_message or 'unknown error'}")
        return _safe_fallback_copy(speaker_path, output_path)

    raise RuntimeError(
        f"F5-TTS inference failed: {error_message or 'unknown failure'}.\n"
        f"Suggestions:\n"
        f"• Chạy lần đầu sẽ chậm (tải model) → thử lại lần 2\n"
        f"• Dùng GPU nếu có (CUDA)\n"
        f"• Giảm độ dài text hoặc transcript\n"
        f"• Tăng timeout trong .env: F5TTS_TIMEOUT_SECONDS=300"
    )