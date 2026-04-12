import importlib
from pathlib import Path

from fastapi.testclient import TestClient

from app.podcast.script import PodcastScript, PodcastSegment


def _build_e2e_test_client(monkeypatch, tmp_path, *, tts_ready=True, stt_raises=False):
    import main

    importlib.reload(main)

    from app.routers import audio as audio_router
    from app.routers import document as document_router
    from app.routers import podcast as podcast_router

    data_dir = tmp_path / "data"
    outputs_dir = tmp_path / "outputs"
    voices_dir = tmp_path / "voices"
    data_dir.mkdir()
    outputs_dir.mkdir()
    voices_dir.mkdir()

    state: dict = {
        "documents": {},
        "tts_calls": [],
        "stt_calls": [],
    }

    def fake_load_document(file_path: str, document_id: str | None = None):
        text = Path(file_path).read_text(encoding="utf-8")
        resolved_document_id = document_id or "doc-test"
        state["documents"][resolved_document_id] = {
            "text": text,
            "file_path": file_path,
        }
        return {
            "document_id": resolved_document_id,
            "file_path": file_path,
            "filename": Path(file_path).name,
            "full_text": text,
            "chunk_count": 2,
        }

    def fake_get_image_descriptions(document_id: str | None = None):
        return {}

    def fake_ask_question(question: str, document_id: str | None = None):
        return f"[{document_id}] Tra loi cho: {question}"

    def fake_get_all_text(document_id: str | None = None):
        doc = state["documents"].get(document_id or "")
        return doc["text"] if doc else ""

    def fake_get_current_file(document_id: str | None = None):
        doc = state["documents"].get(document_id or "")
        return doc["file_path"] if doc else ""

    def fake_generate_podcast_script(
        text: str,
        source_name: str = "tai lieu",
        num_segments: int = 5,
        language: str = "vi",
    ):
        segments = [
            PodcastSegment(
                index=i,
                title=f"Phan {i + 1}",
                text=f"Segment {i + 1} cho {source_name}. {text[:40]}",
                duration_estimate=15.0 + i,
            )
            for i in range(num_segments)
        ]
        return PodcastScript(
            title="Podcast Demo",
            summary="Tom tat demo",
            segments=segments,
            source=source_name,
        )

    def fake_answer_listener_question(question: str, current_segment: PodcastSegment, full_text: str):
        return f"Tra loi voice QA: {question} | {current_segment.title}"

    def fake_tts_ready():
        return tts_ready

    def fake_text_to_speech(text: str, output_path: str = None, voice: str = None):
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(b"RIFFdemoWAVE")
        state["tts_calls"].append(
            {
                "text": text,
                "output_path": str(output),
                "voice": voice,
            }
        )
        return str(output)

    def fake_transcribe_bytes(
        audio_bytes: bytes,
        filename: str = "upload.wav",
        language: str = "vi-VN",
        task: str = "transcribe",
        temp_dir: str = None,
        output_format: str = None,
    ):
        state["stt_calls"].append(
            {
                "filename": filename,
                "language": language,
                "task": task,
                "size": len(audio_bytes),
            }
        )
        if stt_raises:
            raise RuntimeError("mock stt unavailable")
        return {
            "text": "Hay tom tat tai lieu giup toi",
            "language": language or "vi-VN",
            "duration": 1.25,
        }

    monkeypatch.setattr(document_router, "DATA_DIR", str(data_dir))
    monkeypatch.setattr(document_router, "OUTPUTS_DIR", str(outputs_dir))
    monkeypatch.setattr(document_router, "load_document", fake_load_document)
    monkeypatch.setattr(document_router, "get_image_descriptions", fake_get_image_descriptions)
    monkeypatch.setattr(document_router, "ask_question", fake_ask_question)

    monkeypatch.setattr(podcast_router, "OUTPUTS_DIR", str(outputs_dir))
    monkeypatch.setattr(podcast_router, "DATA_DIR", str(data_dir))
    monkeypatch.setattr(podcast_router, "get_all_text", fake_get_all_text)
    monkeypatch.setattr(podcast_router, "get_current_file", fake_get_current_file)
    monkeypatch.setattr(podcast_router, "generate_podcast_script", fake_generate_podcast_script)
    monkeypatch.setattr(podcast_router, "answer_listener_question", fake_answer_listener_question)
    monkeypatch.setattr(podcast_router, "tts_ready", fake_tts_ready)
    monkeypatch.setattr(podcast_router, "text_to_speech", fake_text_to_speech)
    monkeypatch.setattr(podcast_router, "transcribe_bytes", fake_transcribe_bytes)

    monkeypatch.setattr(audio_router, "DATA_DIR", str(data_dir))
    monkeypatch.setattr(audio_router, "OUTPUTS_DIR", str(outputs_dir))
    monkeypatch.setattr(audio_router, "VOICES_DIR", str(voices_dir))
    monkeypatch.setattr(audio_router, "tts_ready", fake_tts_ready)
    monkeypatch.setattr(audio_router, "text_to_speech", fake_text_to_speech)
    monkeypatch.setattr(audio_router, "transcribe_bytes", fake_transcribe_bytes)

    client = TestClient(main.app)
    return client, state, outputs_dir


def _upload_and_generate_podcast(client: TestClient):
    upload_response = client.post(
        "/upload",
        files={"file": ("sample.txt", b"Noi dung tai lieu AI de demo nha dau tu.", "text/plain")},
    )
    assert upload_response.status_code == 200
    document_id = upload_response.json()["document_id"]

    podcast_response = client.post(
        "/podcast/generate",
        json={
            "document_id": document_id,
            "num_segments": 2,
            "language": "vi",
        },
    )
    assert podcast_response.status_code == 200
    return document_id


def test_e2e_upload_ask_podcast_tts_stt(monkeypatch, tmp_path):
    client, state, outputs_dir = _build_e2e_test_client(monkeypatch, tmp_path)

    with client:
        upload_response = client.post(
            "/upload",
            files={"file": ("sample.txt", b"Noi dung tai lieu AI de demo nha dau tu.", "text/plain")},
        )
        assert upload_response.status_code == 200
        upload_data = upload_response.json()
        document_id = upload_data["document_id"]
        assert document_id.startswith("doc-")
        assert upload_data["chunk_count"] == 2

        ask_response = client.post(
            "/ask",
            json={
                "document_id": document_id,
                "question": "Tai lieu noi ve dieu gi?",
                "speak": False,
            },
        )
        assert ask_response.status_code == 200
        ask_data = ask_response.json()
        assert ask_data["document_id"] == document_id
        assert "Tai lieu noi ve dieu gi?" in ask_data["answer"]

        podcast_response = client.post(
            "/podcast/generate",
            json={
                "document_id": document_id,
                "num_segments": 2,
                "language": "vi",
            },
        )
        assert podcast_response.status_code == 200
        podcast_data = podcast_response.json()
        assert podcast_data["document_id"] == document_id
        assert podcast_data["total_segments"] == 2

        script_response = client.get("/podcast/script", params={"document_id": document_id})
        assert script_response.status_code == 200
        script_data = script_response.json()
        assert script_data["document_id"] == document_id
        assert script_data["total_segments"] == 2

        tts_response = client.post("/podcast/tts/0", params={"document_id": document_id, "voice": "Kore"})
        assert tts_response.status_code == 200
        tts_data = tts_response.json()
        assert tts_data["document_id"] == document_id
        assert tts_data["audio_url"].startswith("/download/")
        assert len(state["tts_calls"]) == 1
        assert list(outputs_dir.glob("*.wav"))

        stt_response = client.post(
            "/transcribe?language=vi&task=transcribe",
            files={"file": ("question.wav", b"fake-audio", "audio/wav")},
        )
        assert stt_response.status_code == 200
        stt_data = stt_response.json()
        assert stt_data["filename"] == "question.wav"
        assert stt_data["text"] == "Hay tom tat tai lieu giup toi"
        assert state["stt_calls"][0]["task"] == "transcribe"


def test_e2e_podcast_qa_voice(monkeypatch, tmp_path):
    client, state, outputs_dir = _build_e2e_test_client(monkeypatch, tmp_path)

    with client:
        document_id = _upload_and_generate_podcast(client)
        response = client.post(
            "/podcast/qa/voice",
            params={"document_id": document_id, "segment_index": 1, "voice": "Kore"},
            files={"file": ("listener.wav", b"voice-question", "audio/wav")},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["document_id"] == document_id
        assert data["transcribed_question"] == "Hay tom tat tai lieu giup toi"
        assert data["segment_index"] == 1
        assert data["audio_url"].startswith("/download/")
        assert len(state["stt_calls"]) == 1
        assert len(state["tts_calls"]) == 1
        assert list(outputs_dir.glob("*.wav"))


def test_e2e_text_to_speech_endpoint(monkeypatch, tmp_path):
    client, state, outputs_dir = _build_e2e_test_client(monkeypatch, tmp_path)

    with client:
        response = client.post(
            "/text-to-speech",
            json={
                "text": "Xin chao nha dau tu",
                "voice": "Kore",
                "filename": "demo-audio.wav",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["engine"] == "Gemini TTS"
        assert data["audio_url"] == "/download/demo-audio.wav"
        assert state["tts_calls"][0]["voice"] == "Kore"
        assert (outputs_dir / "demo-audio.wav").exists()


def test_e2e_negative_invalid_document_id(monkeypatch, tmp_path):
    client, _, _ = _build_e2e_test_client(monkeypatch, tmp_path)

    with client:
        ask_response = client.post(
            "/ask",
            json={
                "document_id": "doc-not-found",
                "question": "Co gi trong tai lieu?",
                "speak": False,
            },
        )
        assert ask_response.status_code == 200
        assert ask_response.json()["answer"] == "[doc-not-found] Tra loi cho: Co gi trong tai lieu?"

        podcast_response = client.post(
            "/podcast/generate",
            json={
                "document_id": "doc-not-found",
                "num_segments": 2,
                "language": "vi",
            },
        )
        assert podcast_response.status_code == 404

        select_response = client.post("/documents/doc-not-found/select")
        assert select_response.status_code == 404


def test_e2e_negative_invalid_file_types(monkeypatch, tmp_path):
    client, _, _ = _build_e2e_test_client(monkeypatch, tmp_path)

    with client:
        upload_response = client.post(
            "/upload",
            files={"file": ("sample.exe", b"bad", "application/octet-stream")},
        )
        assert upload_response.status_code == 400

        transcribe_response = client.post(
            "/transcribe?language=vi&task=transcribe",
            files={"file": ("question.txt", b"not-audio", "text/plain")},
        )
        assert transcribe_response.status_code == 400

        podcast_qa_voice_response = client.post(
            "/podcast/qa/voice",
            params={"document_id": "doc-any", "segment_index": 0},
            files={"file": ("listener.txt", b"not-audio", "text/plain")},
        )
        assert podcast_qa_voice_response.status_code == 400


def test_e2e_negative_tts_unavailable(monkeypatch, tmp_path):
    client, _, _ = _build_e2e_test_client(monkeypatch, tmp_path, tts_ready=False)

    with client:
        response = client.post(
            "/text-to-speech",
            json={
                "text": "Xin chao nha dau tu",
                "voice": "Kore",
                "filename": "demo-audio.wav",
            },
        )
        assert response.status_code == 503

        document_id = _upload_and_generate_podcast(client)
        podcast_tts_response = client.post(
            "/podcast/tts/0",
            params={"document_id": document_id, "voice": "Kore"},
        )
        assert podcast_tts_response.status_code == 503


def test_e2e_negative_stt_unavailable(monkeypatch, tmp_path):
    client, _, _ = _build_e2e_test_client(monkeypatch, tmp_path, stt_raises=True)

    with client:
        transcribe_response = client.post(
            "/transcribe?language=vi&task=transcribe",
            files={"file": ("question.wav", b"fake-audio", "audio/wav")},
        )
        assert transcribe_response.status_code == 500

        document_id = _upload_and_generate_podcast(client)
        podcast_qa_voice_response = client.post(
            "/podcast/qa/voice",
            params={"document_id": document_id, "segment_index": 0},
            files={"file": ("listener.wav", b"voice-question", "audio/wav")},
        )
        assert podcast_qa_voice_response.status_code == 500
