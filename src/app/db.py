import os
from motor.motor_asyncio import AsyncIOMotorClient

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "voice_agent")

client = AsyncIOMotorClient(MONGO_URI)
db = client[DB_NAME]

def get_db():
    """Trả về instance của database để sử dụng trong các module khác."""
    return db