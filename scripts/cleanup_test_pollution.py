"""One-off cleanup: hapus gambar uji (test-data) yang ditinggalkan testing agent
pada produk 'prd_greenbasillime' sehingga produk kembali memakai placeholder bersih
seperti 11 produk lainnya. Aman & idempotent.
"""
import asyncio
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

ROOT = Path(__file__).resolve().parents[1] / "backend"
load_dotenv(ROOT / ".env")

MONGO_URL = os.environ["MONGO_URL"]
DB_NAME = os.environ.get("DB_NAME", "collector_parfum")


async def main():
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    prod = await db.products.find_one({"id": "prd_greenbasillime"})
    if not prod:
        print("green-basil-lime tidak ditemukan; skip")
        return
    before = prod.get("images") or []
    res = await db.products.update_one(
        {"id": "prd_greenbasillime"}, {"$set": {"images": []}}
    )
    print(f"green-basil-lime images: {before} -> [] (modified={res.modified_count})")
    client.close()


if __name__ == "__main__":
    asyncio.run(main())
