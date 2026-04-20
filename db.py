import os
from motor.motor_asyncio import AsyncIOMotorClient

# Lấy cấu hình từ môi trường hoặc mặc định
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "voice_agent")

# Khởi tạo client MongoDB (Async)
client = AsyncIOMotorClient(MONGO_URI)
db = client[DB_NAME]

def get_db():
    """Trả về instance của database để sử dụng trong các module khác."""
    return db