import re
import os
from datetime import datetime


#Text

def fmt_time(seconds: float) -> str:
    """60.5 → '1:00'"""
    m = int(seconds // 60)
    s = int(seconds % 60)
    return f"{m}:{s:02d}"


def fmt_size(bytes_: int) -> str:
    """1536 → '1.5 KB'"""
    if bytes_ < 1024:
        return f"{bytes_} B"
    if bytes_ < 1_048_576:
        return f"{bytes_ / 1024:.0f} KB"
    return f"{bytes_ / 1_048_576:.1f} MB"


def postprocess_transcript(text: str) -> str:
    """Chuẩn hoá transcript STT: strip, collapse spaces, remove brackets, capitalize."""
    text = text.strip()
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"\[.*?\]", "", text).strip()
    return (text[0].upper() + text[1:]) if text else ""


def split_text(text: str, max_chars: int = 4500) -> list[str]:
    """
    Chia văn bản dài thành các chunk ≤ max_chars, ưu tiên cắt theo câu.
    Dùng chung cho cả TTS chunking và RAG processing.
    """
    if len(text) <= max_chars:
        return [text]

    chunks, cur = [], ""
    for sent in re.split(r"(?<=[.!?;,])\s+|(?<=\n)", text):
        if len(cur) + len(sent) + 1 <= max_chars:
            cur = (cur + " " + sent).strip()
        else:
            if cur:
                chunks.append(cur)
            if len(sent) > max_chars:
                chunks.extend(sent[i:i + max_chars] for i in range(0, len(sent), max_chars))
                cur = ""
            else:
                cur = sent
    if cur:
        chunks.append(cur)
    return [c for c in chunks if c.strip()]


#File

def safe_filename(name: str, ext: str = ".wav") -> str:
    """Tạo tên file an toàn từ name + timestamp."""
    base = re.sub(r"[^\w\-]", "_", name)[:40]
    ts   = datetime.now().strftime("%H%M%S")
    return f"{base}_{ts}{ext}"


def ensure_dirs(*dirs: str) -> None:
    """Tạo thư mục nếu chưa có."""
    for d in dirs:
        os.makedirs(d, exist_ok=True)


def file_info(path: str) -> dict:
    """Trả về metadata của một file."""
    stat = os.stat(path)
    return {
        "filename":     os.path.basename(path),
        "size_kb":      round(stat.st_size / 1024, 1),
        "created":      datetime.fromtimestamp(stat.st_ctime).isoformat(),
        "download_url": f"/download/{os.path.basename(path)}",
    }