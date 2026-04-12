from app.rag.loader import (
    get_all_text,
    get_current_document_id,
    get_current_file,
    get_full_text,
    list_documents,
)
from app.utils import fmt_size, fmt_time, postprocess_transcript, safe_filename


def test_initial_full_text_empty_or_string():
    text = get_full_text()
    assert isinstance(text, str)
    assert len(text) <= 5000


def test_initial_all_text_is_string():
    assert isinstance(get_all_text(), str)


def test_initial_current_file_is_string():
    assert isinstance(get_current_file(), str)


def test_initial_current_document_id_is_string():
    assert isinstance(get_current_document_id(), str)


def test_list_documents_returns_list():
    assert isinstance(list_documents(), list)


def test_get_full_text_truncates_at_5000():
    text = get_full_text()
    assert len(text) <= 5000


def test_fmt_time_zero():
    assert fmt_time(0) == "0:00"


def test_fmt_time_minutes():
    assert fmt_time(90) == "1:30"
    assert fmt_time(60) == "1:00"
    assert fmt_time(3661) == "61:01"


def test_fmt_time_seconds():
    assert fmt_time(5) == "0:05"
    assert fmt_time(59) == "0:59"


def test_fmt_size_bytes():
    assert "B" in fmt_size(512)


def test_fmt_size_kb():
    result = fmt_size(2048)
    assert "KB" in result


def test_fmt_size_mb():
    result = fmt_size(2 * 1024 * 1024)
    assert "MB" in result


def test_safe_filename_no_spaces():
    name = safe_filename("my podcast", ".wav")
    assert " " not in name
    assert name.endswith(".wav")


def test_safe_filename_has_ext():
    assert safe_filename("test", ".mp3").endswith(".mp3")
    assert safe_filename("test", ".wav").endswith(".wav")


def test_safe_filename_sanitizes():
    name = safe_filename("hello/world:test", ".wav")
    assert "/" not in name
    assert ":" not in name


def test_postprocess_transcript_smoke():
    assert postprocess_transcript("  xin chao  ").startswith("Xin")
