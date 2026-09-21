"""db.py — Motor (async MongoDB) client + accessor.

Single source of truth untuk koneksi database.
Env: MONGO_URL, DB_NAME (JANGAN di-hardcode / diubah).
"""
import os
from pathlib import Path

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv(Path(__file__).parent / ".env")

_MONGO_URL = os.environ["MONGO_URL"]
_DB_NAME = os.environ.get("DB_NAME", "collector_parfum")

_client = AsyncIOMotorClient(_MONGO_URL)
db = _client[_DB_NAME]


def get_db():
    """Kembalikan handle database kanonik."""
    return db


def close():
    _client.close()
