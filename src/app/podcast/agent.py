import json
from app.core.gemini_client import call_gemini_llm, parse_json_response, GeminiAPIError
from app.podcast.script import PodcastScript, PodcastSegment

# ── Constants ─────────────────────────────────────────────────────────────────
_MIN_TEXT_CHARS    = 80
_MIN_SEGMENT_CHARS = 50


# ── Gemini LLM wrapper ────────────────────────────────────────────────────────

from app.core.logger import get_logger

logger = get_logger(__name__)

def _call_gemini(prompt: str, max_tokens: int = 8192, temperature: float = 0.75) -> str:
    """Wrapper for backward compatibility and error handling."""
    try:
        return call_gemini_llm(prompt, max_tokens, temperature)
    except GeminiAPIError as e:
        logger.error("[PODCAST GEMINI ERROR] %s", e)
        return f"Lỗi Gemini: {e}"


# ── Prompts ───────────────────────────────────────────────────────────────────

_GENERATE_PROMPT = """\
Bạn là một podcast producer người Việt chuyên nghiệp.

Nhiệm vụ: Chuyển tài liệu sau thành script podcast hoàn toàn bằng tiếng Việt, hấp dẫn, dễ nghe.

Yêu cầu nghiêm ngặt:
- Tạo đúng {num_segments} segments (không ít hơn, không nhiều hơn).
- Mỗi segment có 1 ý chính rõ ràng, khoảng 150-280 từ (đọc khoảng 1-2 phút).
- Viết như lời nói tự nhiên: câu ngắn, có từ chuyển tiếp.
- Không dùng markdown, bullet points, hay định dạng đặc biệt.
- Mỗi segment phải có tiêu đề ngắn gọn (5-8 từ).

Trả về CHỈ JSON theo đúng format sau, không thêm bất kỳ chữ nào khác:

{{
  "title": "Tiêu đề podcast ngắn gọn bằng tiếng Việt",
  "summary": "Tóm tắt ngắn 1-2 câu bằng tiếng Việt",
  "segments": [
    {{
      "index": 0,
      "title": "Tiêu đề segment",
      "text": "Nội dung script đọc to..."
    }}
  ]
}}

Tài liệu nguồn: {source_name}

=== NỘI DUNG TÀI LIỆU ===
{text}
=========================

Tạo đúng {num_segments} segments ngay bây giờ:\
"""

_QA_PROMPT = """\
Bạn là AI dẫn podcast tiếng Việt đang tương tác với người nghe.

Chapter đang phát: [{segment_title}]
{segment_text}

Toàn bộ tài liệu:
{full_text}

Câu hỏi: "{question}"

Yêu cầu:
- Trả lời chi tiết và đầy đủ: 3-7 câu, tối đa 1500 từ.
- Hoàn toàn bằng tiếng Việt tự nhiên.
- Kết thúc bằng gợi ý tiếp tục nghe nếu phù hợp.

Trả lời:\
"""


# ── Public API ────────────────────────────────────────────────────────────────

def generate_podcast_script(
    text:         str,
    source_name:  str = "tài liệu",
    num_segments: int = 5,
    language:     str = "vi",
) -> PodcastScript:
    """Dùng Gemini tạo podcast script từ raw text."""
    text = text.strip()

    # Guard: nội dung quá ngắn
    logger = get_logger(__name__)
    if len(text) < _MIN_TEXT_CHARS:
        logger.warning("[PODCAST] Text quá ngắn (%d chars) — dùng script mặc định", len(text))
        filler = (
            f"Tài liệu '{source_name}' có nội dung: {text}. "
            f"Đây là nội dung rất ngắn. "
            f"Hãy thêm nội dung chi tiết hơn để tạo podcast đầy đủ."
        )
        return PodcastScript(
            title=source_name,
            summary=f"Nội dung ngắn: {text[:100]}",
            segments=[PodcastSegment(
                index=0, title="Nội dung",
                text=filler,
                duration_estimate=round(len(filler.split()) / 150 * 60, 1),
            )],
            source=source_name,
        )

    text_input      = text[:15000]
    actual_segments = min(num_segments, max(1, len(text_input) // 300), 15)

    logger = get_logger(__name__)
    prompt = _GENERATE_PROMPT.format(
        num_segments=actual_segments,
        source_name=source_name,
        text=text_input,
    )

    logger.info("[PODCAST] Generating %d segments from %d chars…", actual_segments, len(text_input))
    raw = _call_gemini(prompt, max_tokens=8192, temperature=0.8)

    # Sử dụng parse_json_response để xử lý JSON an toàn hơn
    data = parse_json_response(raw)
    
    if not data:
        logger.warning("[PODCAST] JSON parse thất bại hoặc rỗng — dùng fallback")
        chunk = max(800, len(text) // actual_segments)
        data  = {
            "title":   f"Podcast về {source_name}",
            "summary": text[:200],
            "segments": [
                {"index": i, "title": f"Phần {i+1}", "text": text[i*chunk:(i+1)*chunk]}
                for i in range(actual_segments)
            ],
        }

    # Build & validate segments
    segments = []
    for seg in data.get("segments", []):
        txt = str(seg.get("text", "")).strip()
        if len(txt) < _MIN_SEGMENT_CHARS:
            logger.debug("[PODCAST] Bỏ segment '%s' — quá ngắn (%d chars)", seg.get('title',''), len(txt))
            continue
        segments.append(PodcastSegment(
            index=len(segments),
            title=str(seg.get("title", f"Phần {len(segments)+1}")),
            text=txt,
            duration_estimate=round(len(txt.split()) / 150 * 60, 1),
        ))

    # Fallback: chia thủ công nếu Gemini không tạo đủ
    if len(segments) < max(1, actual_segments // 2):
        logger.info("[PODCAST] Quá ít segments — chia thủ công")
        chunk    = max(800, len(text) // actual_segments)
        segments = [
            PodcastSegment(
                index=i, title=f"Phần {i+1}",
                text=text[i*chunk:(i+1)*chunk].strip(),
                duration_estimate=round(
                    len(text[i*chunk:(i+1)*chunk].split()) / 150 * 60, 1
                ),
            )
            for i in range(actual_segments)
            if text[i*chunk:(i+1)*chunk].strip()
        ]

    script = PodcastScript(
        title=data.get("title", source_name),
        summary=data.get("summary", ""),
        segments=segments[:actual_segments],
        source=source_name,
    )
    logger.info("[PODCAST] Done → '%s' | %d/%d segments", script.title, len(script.segments), actual_segments)
    return script


def answer_listener_question(
    question:        str,
    current_segment: PodcastSegment,
    full_text:       str,
) -> str:
    """Trả lời câu hỏi của người nghe khi pause podcast."""
    prompt = _QA_PROMPT.format(
        segment_title=current_segment.title,
        segment_text=current_segment.text[:600],
        full_text=full_text[:4000],
        question=question,
    )
    answer = _call_gemini(prompt, max_tokens=4096, temperature=0.7)

    if len(answer) > 5000:
        answer = answer[:5000].rsplit(".", 1)[0] + "."

    logger.debug("[Q&A] Q: %s", question[:80])
    logger.debug("[Q&A] A (%d chars): %s…", len(answer), answer[:120])
    return answer
