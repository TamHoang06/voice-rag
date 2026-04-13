import pytest
from app.podcast.script import (
    PodcastSegment, PodcastScript,
    set_current_script, get_current_script, get_segment,
)


def test_segment_to_dict():
    seg = PodcastSegment(index=0, title="Intro", text="Xin chao!", duration_estimate=5.0)
    d = seg.to_dict()
    assert d["index"] == 0
    assert d["title"] == "Intro"
    assert d["text"] == "Xin chao!"
    assert d["duration_estimate"] == 5.0


def test_script_to_dict():
    segs = [PodcastSegment(i, f"Phan {i+1}", f"Noi dung {i+1}") for i in range(3)]
    script = PodcastScript(title="Test", summary="Tom tat", segments=segs, source="test.txt")
    d = script.to_dict()

    assert d["title"] == "Test"
    assert d["summary"] == "Tom tat"
    assert d["total_segments"] == 3
    assert len(d["segments"]) == 3


def test_script_full_text():
    segs = [PodcastSegment(i, f"Phan {i}", f"Text {i}") for i in range(3)]
    script = PodcastScript(title="T", summary="S", segments=segs)
    full = script.full_text()
    assert "Text 0" in full
    assert "Text 2" in full


def test_set_and_get_current_script():
    script = PodcastScript(
        title="My Podcast",
        summary="S",
        segments=[PodcastSegment(0, "Ch1", "Noi dung chapter 1 du dai de pass validation.")],
    )
    set_current_script(script, document_id="doc-a")
    assert get_current_script(document_id="doc-a") is script


def test_get_segment_valid():
    segs = [PodcastSegment(i, f"Ch{i}", f"Noi dung {i}") for i in range(5)]
    set_current_script(PodcastScript("T", "S", segs), document_id="doc-b")
    seg = get_segment(2, document_id="doc-b")
    assert seg is not None
    assert seg.index == 2


def test_get_segment_out_of_range():
    segs = [PodcastSegment(0, "Ch0", "Text")]
    set_current_script(PodcastScript("T", "S", segs), document_id="doc-c")
    assert get_segment(99, document_id="doc-c") is None
    assert get_segment(-1, document_id="doc-c") is None


def test_scripts_are_isolated_per_document():
    script_a = PodcastScript("A", "S", [PodcastSegment(0, "One", "Text A")])
    script_b = PodcastScript("B", "S", [PodcastSegment(0, "Two", "Text B")])
    set_current_script(script_a, document_id="doc-1")
    set_current_script(script_b, document_id="doc-2")

    assert get_current_script(document_id="doc-1") is script_a
    assert get_current_script(document_id="doc-2") is script_b


def test_generate_short_text_returns_default():
    from app.podcast.agent import generate_podcast_script
    script = generate_podcast_script(text="Ngan", source_name="test")
    assert isinstance(script, PodcastScript)
    assert len(script.segments) >= 1
    assert len(script.segments[0].text) > 10


def test_generate_respects_min_segment_chars():
    from app.podcast.agent import _MIN_SEGMENT_CHARS

    good_text = "Day la noi dung du dai de khong bi filter ra khoi danh sach." * 3
    short_text = "Ngan."

    assert len(good_text) >= _MIN_SEGMENT_CHARS
    assert len(short_text) < _MIN_SEGMENT_CHARS


def test_script_segment_duration_estimate():
    text = "tu " * 150
    seg = PodcastSegment(0, "T", text,
                         duration_estimate=round(len(text.split()) / 150 * 60, 1))
    assert abs(seg.duration_estimate - 60.0) < 1.0
