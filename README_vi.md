# Tác Nhân Giọng Nói AI

Nền tảng tạo podcast do AI hỗ trợ với RAG, Gemini 2.5 Flash LLM, sao chép giọng nói F5-TTS, STT, xử lý tài liệu (PDF/DOCX) và thư viện giọng nói.

## Tính Năng
- **Tải Lên Tài Liệu**: PDF, DOCX, TXT → kho vectorstore RAG với phân tích hình ảnh

- **Tạo Podcast**: Phân đoạn tự động + script Gemini → podcast tiếng Việt chuyên nghiệp với thời gian đoạn

- **Sao Chép Giọng Nói**: F5-TTS (sao chép giọng nói không mẫu mã từ mẫu 10 giây) + thoại lệnh dự phòng Gemini (9 giọng)

- **Hỏi Đáp Tương Tác**: Câu hỏi RAG thời gian thực trong quá trình phát podcast

- **Thư Viện Giọng Nói**: Tải lên/tùy chỉnh/tham chiếu giọng nói để sao chép (tự động sử dụng giọng nói hoạt động)

- **Sẵn Sàng Sản Xuất**: Giới hạn tốc độ, Docker, pytest (8 tệp kiểm tra bao gồm quy trình E2E đầy đủ), kiểm tra sức khỏe

## Cơ Chế Dự Án

Dự án này là một Voice Agent được xây dựng bằng Python, sử dụng FastAPI làm framework web chính, tích hợp các công nghệ Google Gemini 2.5 Flash để xử lý văn bản, âm thanh và tạo nội dung podcast tự động. Nó hỗ trợ nhiều ngôn ngữ (đặc biệt là tiếng Việt), với các cơ chế chính bao gồm Retrieval-Augmented Generation (RAG), Speech-to-Text (STT), Text-to-Speech (TTS) và tạo podcast.

### 1. Khởi Động Ứng Dụng Chính và Cấu Hình
   - **Giải Thích**: Ứng dụng sử dụng FastAPI để tạo API RESTful. Khi khởi động, nó tải vectorstore (cho RAG), kiểm tra sự sẵn sàng của TTS (cần GEMINI_API_KEY) và gắn kết các bộ định tuyến cho podcast, tài liệu, âm thanh, giọng nói. Bao gồm middleware giới hạn tốc độ để tránh quá tải, và phục vụ các trang HTML tĩnh cho giao diện web (ví dụ: trình phát podcast).
   - **Lưu Ý Đặc Biệt**: Stack chính là "Gemini 2.5 Flash - LLM + TTS + STT", có nghĩa là tất cả các tác vụ AI đều dựa vào Gemini. Nếu thiếu khóa API, TTS/STT sẽ không khả dụng. Giới hạn tốc độ có thể cấu hình qua các biến env, với giới hạn chặt hơn cho các tuyến nặng như tải lên (5 yêu cầu/60 giây).
   - **Đoạn Code Minh Họa** (từ `src/main.py`):
     ```python
     def _run_startup_tasks() -> None:
         load_vectorstore()  # Tải vectorstore cho RAG
         ready = tts_ready()  # Kiểm tra sự sẵn sàng TTS
         logger.info("TTS ready = %s", ready)
         if not ready:
             logger.warning("GEMINI_API_KEY chưa được cấu hình trong .env: TTS/STT sẽ không khả dụng")
         logger.info("Stack: Gemini 2.5 Flash - LLM + TTS + STT")
     ```
     ```python
     app.add_middleware(
         RateLimitMiddleware,
         max_requests=rate_limit_requests(),  # Từ config, mặc định 60 yêu cầu/60 giây
         window_seconds=rate_limit_window_seconds(),
     )
     ```

### 2. Cơ Chế RAG (Retrieval-Augmented Generation)
   - **Giải Thích**: RAG cho phép ứng dụng "ghi nhớ" và truy xuất thông tin từ các tài liệu. Các tài liệu (PDF, DOCX, TXT) được tải, chia thành các đoạn (1200 ký tự, 200 chồng chéo), nhúng bằng mô hình đa ngôn ngữ HuggingFace (`sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`) và lưu trữ trong vectorstore FAISS. Khi truy vấn, nó truy xuất các đoạn liên quan và sử dụng Gemini để hỏi đáp hoặc tóm tắt.
   - **Lưu Ý Đặc Biệt**: Embeddings hỗ trợ nhiều ngôn ngữ (bao gồm tiếng Việt), tải lại lười biếng để tiết kiệm bộ nhớ. Bộ đăng ký JSON lưu siêu dữ liệu tài liệu, với bộ đệm trong bộ nhớ. Nếu tài liệu trống sau khi trích xuất, sẽ gây ra lỗi. Phân tích hình ảnh (nếu có hình ảnh trong PDF) sử dụng Gemini để mô tả.
   - **Đoạn Code Minh Họa** (từ `src/app/rag/loader.py`):
     ```python
     chunks = RecursiveCharacterTextSplitter(
         chunk_size=1200,
         chunk_overlap=200,
     ).split_documents(documents)
     vector_db = FAISS.from_documents(chunks, get_embeddings())  # Tạo vectorstore
     ```
     (từ `src/app/rag/retriever.py`):
     ```python
     _QA_PROMPT = (
         "Bạn là một trợ lý AI, hãy trả lời bằng tiếng Việt.\n"
         "Trả lời ngắn gọn và chính xác dựa trên nội dung tài liệu.\n"
         "Nếu không có thông tin: 'Không có thông tin trong tài liệu.'\n\n"
         "=== Tài Liệu ===\n{context}\n\n"
         "=== Câu Hỏi ===\n{question}\n\n"
         "=== Trả Lời ===\n"
     )
     ```

### 3. Cơ Chế STT (Speech-to-Text)
   - **Giải Thích**: Chuyển đổi các tệp âm thanh (WAV, MP3, v.v.) thành văn bản bằng Gemini 2.5 Flash. Hỗ trợ nhiều ngôn ngữ (mặc định vi-VN), ước tính thời lượng và xử lý hậu kỳ bản ghi âm (loại bỏ ký tự thừa).
   - **Lưu Ý Đặc Biệt**: Chỉ hỗ trợ các định dạng trong `AUDIO_MIME_MAP` (wav, mp3, m4a, v.v.). Gây ra FileNotFoundError nếu tệp không tồn tại. Tác vụ có thể là "transcribe" (chuyển đổi) hoặc "translate" (dịch). Kích thước tối đa 30MB.
   - **Đoạn Code Minh Họa** (từ `src/app/stt/stt.py`):
     ```python
     def transcribe_audio(
         audio_path: str,
         language: str = "vi-VN",  # Mặc định tiếng Việt
         task: str = "transcribe",
     ) -> dict:
         raw = _call_gemini_stt(audio_bytes, mime_type, locale, task)
         text = postprocess_transcript(raw)  # Xử lý hậu kỳ
         duration = _estimate_duration(audio_bytes)
         return {"text": text, "language": locale, "duration": duration, "segments": []}
     ```

### 4. Cơ Chế TTS (Text-to-Speech)
   - **Giải Thích**: Chuyển đổi văn bản thành âm thanh WAV bằng Gemini 2.5 Flash. Hỗ trợ nhiều giọng nói (Kore, Charon, v.v.), chia nhỏ văn bản nếu quá dài (4500 ký tự/đoạn) và hợp nhất thành một tệp duy nhất.
   - **Lưu Ý Đặc Biệt**: Cần GEMINI_API_KEY để hoạt động. Giọng nói được xác định trong từ điển `GEMINI_VOICES`. Bỏ qua nếu văn bản trống. Đầu ra mặc định WAV, có thể chuyển đổi định dạng. Dự phòng sang OpenAI nếu cần.
   - **Đoạn Code Minh Họa** (từ `src/app/tts/tts.py`):
     ```python
     GEMINI_VOICES = {
         "Aoede":   "Aoede — Nữ, tự nhiên",
         "Charon":  "Charon — Nam, trầm",
         # ...
     }
     def text_to_speech(text: str, output_path: str = None, voice: str = None) -> str:
         if not text or not text.strip():
             raise ValueError("Văn bản trống")
         # Chia nhỏ và gọi Gemini TTS
     ```

### 5. Cơ Chế Tạo Podcast
   - **Giải Thích**: Từ các tài liệu đã tải qua RAG, sử dụng Gemini để tạo các script podcast tiếng Việt, chia thành các đoạn (mỗi đoạn 150-280 từ, đọc 1-2 phút). Sau đó, TTS từng đoạn thành âm thanh. Script được lưu vào bộ đệm theo document_id.
   - **Lưu Ý Đặc Biệt**: Prompt yêu cầu số đoạn chính xác, được viết tự nhiên như lời nói. Các đoạn có các tiêu đề ngắn. Hỏi đáp cho các câu hỏi của người nghe dựa trên script. Âm thanh được lưu trong outputs/.
   - **Đoạn Code Minh Họa** (từ `src/app/podcast/agent.py`):
     ```python
     _GENERATE_PROMPT = """\
     Bạn là một nhà sản xuất podcast người Việt chuyên nghiệp.
     Nhiệm vụ: Chuyển tài liệu sau thành một script podcast hoàn toàn bằng tiếng Việt, hấp dẫn và dễ nghe...
     Tạo đúng {num_segments} đoạn...
     """
     ```
     (từ `src/app/podcast/script.py`):
     ```python
     @dataclass
     class PodcastSegment:
         index: int
         title: str
         text: str
         duration_estimate: float = 0.0
     ```

### 6. Cơ Chế Bảo Mật và Ghi Nhật Ký
   - **Giải Thích**: Sử dụng logger để ghi nhật ký và giới hạn tốc độ để bảo vệ API. Gemini có các cài đặt bảo mật "BLOCK_NONE" cho tất cả các danh mục (qu騷rảo, căm thù, v.v.), cho phép nội dung tự do hơn.
   - **Lưu Ý Đặc Biệt**: Cài đặt này có thể có rủi ro cho phép nội dung có hại nếu được sử dụng cho tài liệu nhạy cảm. Giới hạn tốc độ theo tuyến (tải lên/chuyển mã ngặt hơn). Ghi nhật ký giúp gỡ lỗi, nhưng không mã hóa dữ liệu.
   - **Đoạn Code Minh Họa** (từ `src/app/config.py`):
     ```python
     GEMINI_SAFETY_SETTINGS = [
         {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
         # ...
     ]
     def rate_limit_route_policies() -> dict[str, tuple[int, int]]:
         return {
             "/upload": (5, 60),  # 5 yêu cầu/60 giây để tải lên
         }
     ```

### Ghi Chú Chung cho Dự Án
- **Phụ Thuộc AI**: Tất cả đều dựa vào Gemini 2.5 Flash, yêu cầu khóa API ổn định. Nếu Gemini không hoạt động, dự phòng sang OpenAI để TTS.
- **Ngôn Ngữ**: Tập trung vào tiếng Việt, với các prompt và đầu ra bằng tiếng Việt.
- **Hiệu Suất**: Tải lại lười biếng embeddings, lưu vào bộ đệm vectorstore/script để tránh tải lại. Kích thước tải lên bị giới hạn (50MB cho tệp, 30MB cho âm thanh).
- **Rủi Ro**: Các cài đặt bảo mật "BLOCK_NONE" có thể cho phép nội dung có hại; giới hạn tốc độ có thể bị vượt qua nếu cấu hình không đúng. Không có xác thực mặc định.
- **Môi Trường**: Chạy trong Docker, với requirements.txt liệt kê các phụ thuộc như langchain, fastapi, v.v.

## Demo
### 1. Xem Xét RAG
- Video minh họa: xem xét quy trình RAG, bao gồm nhập tài liệu, tạo kho vector và hỏi đáp do mô hình điều khiển.

- Chọn chương & Giọng nói:

<img width="695" height="347" alt="Rag_Select" src="https://github.com/user-attachments/assets/bc018843-3fca-4da7-9259-760318dca412" />

- Video giữ chỗ:

https://github.com/user-attachments/assets/9281d997-a963-4a61-8baa-2cc8507cdaa3

- Chia tài liệu thành các phần ngắn gọn:

### 2. Hỏi Đáp Dựa Trên Văn Bản
- Video minh họa: tương tác với giao diện hỏi đáp AI bằng cách nhập các truy vấn văn bản và xem xét phản hồi của hệ thống.

- Video giữ chỗ:

https://github.com/user-attachments/assets/ce8eca08-f5fb-4aa5-b4ed-7393bed0fa5f

### 3. Hỏi Đáp Dựa Trên Giọng Nói
- Video minh họa: nói một câu hỏi vào nền tảng và nhận câu trả lời AI bằng cách sử dụng hỏi đáp hỗ trợ giọng nói.

- Video giữ chỗ:

https://github.com/user-attachments/assets/f35a7a21-bd06-4204-aa44-b3f0a6f7f981

### 4. Giọng nói Gemini TTS
- Video minh họa: tạo lời nói bằng cách sử dụng các tùy chọn giọng nói AI tích hợp của Gemini và so sánh các đầu ra giọng nói khác nhau.

- Video giữ chỗ:

https://github.com/user-attachments/assets/67981e56-2c45-47ae-a995-d7f1e5a6583c

### 5. Tải Lên Tài Sản Âm Thanh
- Video minh họa: thêm các tệp âm thanh vào kho lưu trữ dự án và sử dụng chúng làm đầu vào để xử lý hoặc phát lại.

- Video giữ chỗ:

https://github.com/user-attachments/assets/a217a418-9eef-443a-8483-dec78357d9c0

### 6. Ghi Âm Tài Sản Âm Thanh
- Video minh họa: ghi âm trực tiếp vào kho lưu trữ và lưu nó để truy xuất hoặc xử lý sau này.

- Video giữ chỗ:

https://github.com/user-attachments/assets/25abb3c9-17fd-48d5-8797-6b96f6723bba

## Bắt Đầu Nhanh

### Điều Kiên Tiên Quyết
- Python 3.10+
- Git (để phụ thuộc f5-tts)
- Khóa API Gemini (LLM + TTS + STT: https://makersuite.google.com/app/apikey)

Tùy chọn (được đề xuất):
- FFmpeg (xử lý âm thanh: `winget install ffmpeg`)
- Công cụ Visual C++ Build (PyTorch gốc Windows)

### 1. Thiết Lập Môi Trường
```
cd src
python -m venv .venv
```

**Windows:**
```
.venv\Scripts\Activate.ps1
```

**macOS/Linux:**
```
source .venv/bin/activate
```

### 2. Cài Đặt Phụ Thuộc
```
pip install --upgrade pip
pip install -r requirements.txt
```

**Torch Chỉ CPU (được đề xuất để chạy lần đầu):**
```
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu
```

### 3. Cấu Hình
```
copy .env.example .env
```

Chỉnh sửa `src/.env`:
```
GEMINI_API_KEY=your_gemini_key
GEMINI_TTS_VOICE=Kore  # Charon, Aoede, Fenrir, Puck...
LOG_LEVEL=DEBUG  # Nhật ký tiến trình F5-TTS + podcast generation
RATE_LIMIT_REQUESTS=100
```

### 4. Chạy Máy Chủ
```
uvicorn main:app --reload --port 8000
```

### 5. Bộ Kiểm Tra
```
pytest  # Độ phủ quy trình 100%
pytest tests/test_e2e_flow.py::test_e2e_positive_full_pipeline  # Tải lên → Podcast → TTS → STT
```

## Triển Khai Sản Xuất Docker
```
docker-compose up --build
```
- Cổng 8000 được hiển thị
- Tất cả các phụ thuộc được tích hợp
- Gắn kết khối lượng để tồn tại

## Điểm Cuối API

### Quản Lý Tài Liệu
```
POST /upload                          → Tải lên PDF/DOCX/TXT & tạo vectorstore RAG
GET  /documents                       → Liệt kê tất cả các tài liệu đã tải lên
POST /documents/{document_id}/select  → Chọn tài liệu hoạt động
GET  /document                        → Nhận siêu dữ liệu tài liệu hiện tại
GET  /document/summary                → Nhận tóm tắt tài liệu do AI tạo
POST /ask                             → Hỏi đáp về tài liệu hiện tại (văn bản)
POST /generate-docx                   → Xuất kết quả hỏi đáp sang DOCX
POST /generate-pdf                    → Xuất kết quả hỏi đáp sang PDF
POST /re-analyze-images               → Phân tích lại hình ảnh tài liệu bằng Gemini Vision
```

### Tạo & Phát Podcast
```
POST /podcast/generate                → Tạo script podcast từ tài liệu
GET  /podcast/script                  → Nhận script podcast đã tạo
POST /podcast/tts/summary             → Chuyển tóm tắt thành lời nói (F5-TTS/Gemini)
POST /podcast/tts/{segment_index}     → Chuyển đoạn cụ thể thành lời nói
POST /podcast/qa                      → Hỏi đáp trên podcast (dựa trên văn bản)
POST /podcast/qa/voice                → Hỏi đáp trên podcast (dựa trên giọng nói với STT)
```

### Thư Viện Giọng Nói & TTS
```
GET  /voices/available                → Liệt kê tất cả giọng nói khả dụng (tất cả nhà cung cấp)
GET  /voices/available/{provider}     → Liệt kê giọng nói theo nhà cung cấp (gemini, f5)
GET  /voices/providers                → Liệt kê các nhà cung cấp giọng nói được hỗ trợ
POST /voices/upload                   → Tải lên mẫu giọng nói để sao chép F5-TTS
POST /voices/set-active               → Đặt giọng nói hoạt động cho chuyển đổi văn bản thành lời nói
POST /text-to-speech                  → Chuyển đổi văn bản thành lời nói bằng giọng nói đã chọn
```

### Quản Lý Tệp
```
GET  /download/{filename}             → Tải xuống âm thanh/tài liệu được tạo
```

## Khắc Phục Sự Cố

**Git Bị Thiếu (f5-tts):**
```
winget install Git.Git
pip install -r requirements.txt
```

**Lỗi Torch/Audio:**
```
pip uninstall torch torchaudio
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu
winget install ffmpeg
```

**Không Có Phản Hồi TTS/STT:**
```
curl http://localhost:8000/debug/tts  # Kiểm tra API Gemini
# Xác minh GEMINI_API_KEY hợp lệ/hạn ngạch
```

**F5-TTS chậm/chạy lần đầu:**
```
# Bình thường: tải xuống mô hình 2GB → hết thời gian chờ 3 phút tự động dự phòng
LOG_LEVEL=DEBUG  # Xem "[F5TTS] Đang tải mô hình..."
GPU được khuyến nghị để suy luận <30 giây
```

**Bảo vệ .gitignore:**
Khóa thời gian chạy (`data/`, `outputs/`, `voices/`, `vectorstore/`). Kho sạch sẽ.

## Cây Kiến Trúc
```
VOICE-AGENT/
├── .dockerignore               # Quy tắc loại trừ Docker
├── .gitignore                  # Quy tắc loại trừ Git
├── Dockerfile                  # Hướng dẫn xây dựng container
├── docker-compose.yml          # Điều phối multi-container
├── README.md                   # Tài liệu chính
├── SECURITY_ROTATION_CHECKLIST.md # Hướng dẫn bảo mật & xoay khóa
├── TODO.md                     # Lộ trình và các nhiệm vụ chưa xong
├── requirements.txt            # Phụ thuộc được ghim
├── tests/                      # 8 bài kiểm tra E2E & Unit toàn diện
└── src/                        # Gốc Ứng Dụng FastAPI
    ├── __init__.py             # Đánh dấu gói
    ├── .env                    # Biến môi trường cục bộ
    ├── .env.example            # Mẫu cho các biến môi trường
    ├── main.py                 # Điểm vào ứng dụng
    ├── pytest.ini              # Cấu hình Pytest
    └── app/                    # LOGIC CỐT LÕI (Cấu Trúc Sâu)
        ├── __init__.py         # Đánh dấu gói
        ├── config.py           # Cài đặt ứng dụng & Cấu hình Giọng nói
        ├── utils.py            # Hàm tiện ích dùng chung
        ├── core/               # Vận hành kinh doanh trung tâm/động cơ
        ├── document/           # Phân tích & tiền xử lý tài liệu
        ├── models/             # Lược đồ dữ liệu & mô hình Pydantic
        ├── podcast/            # Kịch bản & Tạo Podcast
        ├── rag/                # RAG: FAISS, Loaders & Vision
        ├── routers/            # Điểm cuối API (Audio/Doc/Podcast/Voices)
        ├── stt/                # Speech-to-Text (Gemini)
        ├── tts/                # Text-to-Speech (Hybrid F5/Gemini)
        ├── data/               # [Cục bộ] Dữ liệu mẫu (Git bị bỏ qua)
        ├── outputs/            # [Cục bộ] Âm thanh được tạo (Git bị bỏ qua)
        ├── static/             # Tài sản giao diện người dùng (HTML/JS/CSS)
        ├── vectorstore/        # [Cục bộ] Tệp chỉ mục FAISS (Git bị bỏ qua)
        └── voices/             # [Cục bộ] Thư viện giọng nói tùy chỉnh (Git bị bỏ qua)
```

## Ngăn Xếp Công Nghệ
| Thành Phần | Công Nghệ |
|-----------|-----------|
| Backend | FastAPI 0.111 + Uvicorn |
| LLM/TTS/STT | Gemini 2.5 Flash |
| Sao Chép Giọng Nói | F5-TTS (GitHub mới nhất) |
| RAG | LangChain + FAISS + HuggingFaceEmbeddings |
| Tài Liệu | PyPDF + python-docx + Gemini Vision |
| Âm Thanh | TorchAudio + FFmpeg |
| Kiểm Tra | pytest (E2E + unit) |
| Triển Khai | Docker Compose |
