FROM python:3.10-slim

RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Tạo thư mục trước khi copy code để đảm bảo cấu trúc
RUN mkdir -p outputs data voices static

COPY . .

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]