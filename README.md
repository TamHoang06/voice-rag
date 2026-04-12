# AI Podcast Agent

Project này tập trung vào workflow AI: upload tài liệu, tạo podcast, hỏi đáp với RAG, TTS/STT và voice library. Repo có nhiều file phát sinh khi chạy nên `.gitignore` đã được cấu hình để chặn các thư mục runtime như `src/data`, `src/outputs`, `src/voices`, `src/vectorstore`, `model_cache` và cả `src/static`.

## Cần cài gì trước

### Bắt buộc

- Python `3.10+`
- `git`
- API key Gemini để chạy LLM, TTS, STT

### Nên có thêm

- `ffmpeg`
  Dùng tốt hơn cho xử lý audio và tránh lỗi khi một số thư viện backend cần codec.
- Visual C++ Build Tools
  Có thể cần trên Windows nếu một số package AI phải build native extension.

## Cài đặt nhanh

### 1. Tạo môi trường

```bash
cd src
python -m venv .venv
```

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

macOS/Linux:

```bash
source .venv/bin/activate
```

### 2. Cài thư viện Python

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

Lưu ý:

- `requirements.txt` có package `f5-tts` cài trực tiếp từ GitHub, nên máy cần có `git`.
- Nếu phần `torch` hoặc `torchaudio` lỗi, cài lại theo CPU/GPU phù hợp máy của bạn.

Ví dụ CPU:

```bash
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu
```

Ví dụ CUDA 12.1:

```bash
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu121
```

### 3. Tạo file cấu hình

```bash
copy .env.example .env
```

Nếu dùng macOS/Linux:

```bash
cp .env.example .env
```

Mở `src/.env` và điền tối thiểu:

```env
GEMINI_API_KEY=your_key_here
GEMINI_TTS_VOICE=Kore
GEMINI_TTS_MODEL=gemini-2.5-flash-preview-tts
```

Tuỳ chọn nếu muốn dùng fallback TTS:

```env
OPENAI_API_KEY=your_openai_key
OPENAI_TTS_MODEL=tts-1-hd
OPENAI_TTS_VOICE=shimmer
```

## Chạy ứng dụng

Từ thư mục `src`:

```bash
uvicorn src.main:app --reload
```

Mở:

- `http://localhost:8000/docs`
- `http://localhost:8000/podcast-player`
- `http://localhost:8000/voice-library`

## Test nhanh

Từ thư mục `src`:

```bash
pytest
```

Hoặc:

```bash
pytest tests/test_voices.py
```

## Những lỗi thiếu thường gặp

### Thiếu `git`

Lỗi thường gặp khi cài `f5-tts`:

```text
git is not recognized ...
```

Cách xử lý: cài Git rồi chạy lại `pip install -r requirements.txt`.

### Thiếu API key

Nếu `GEMINI_API_KEY` chưa có, app vẫn có thể lên server nhưng các tính năng Gemini như TTS/STT/Q&A sẽ không dùng được.

### Thiếu `ffmpeg`

Nếu xử lý audio lỗi codec hoặc convert định dạng lỗi, hãy cài `ffmpeg` rồi mở terminal mới để nhận biến `PATH`.

## Ghi chú về `.gitignore`

`.gitignore` chỉ chặn file chưa được Git theo dõi. Nếu bạn muốn Git ngừng theo dõi một thư mục đã add trước đó như `src/static`, cần untrack nó một lần, ví dụ:

```bash
git rm -r --cached src/static
```

Sau đó commit lại để rule ignore có hiệu lực đúng như mong muốn.
