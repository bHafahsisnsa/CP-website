"""Cek referensi URL media di seluruh koleksi, agar aman menghapus aset uji."""
import asyncio, os, json
from pathlib import Path
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

ROOT = Path(__file__).resolve().parents[1] / "backend"
load_dotenv(ROOT / ".env")
client = AsyncIOMotorClient(os.environ["MONGO_URL"])
db = client[os.environ.get("DB_NAME", "collector_parfum")]

URLS = [
    "/api/media/originals/2026/08/503122740ffb4ef6.jpg",
    "/api/media/originals/2026/08/3ca6c235ec6b4ec6.jpg",
    "/api/media/originals/2026/08/b400d580fa814584.jpg",
    "/api/media/originals/2026/08/31b73ae947874c5a.jpg",
    "/api/media/originals/2026/08/cc34dd3d9cd34f54.jpg",
    "/api/media/originals/2026/08/707292357f75468b.jpg",
    "/api/media/originals/2026/08/569ed310bfe34af8.jpg",
]

COLLECTIONS = ["products", "categories", "occasions", "characters", "content",
               "store_locations", "payment_methods", "settings", "store_reviews"]

async def main():
    for url in URLS:
        # derived thumb base too
        base = url.split("/")[-1].split(".")[0]
        hits = []
        for col in COLLECTIONS:
            # search raw json for the url substring or the uuid base
            cursor = db[col].find({})
            async for doc in cursor:
                s = json.dumps(doc, default=str)
                if url in s or base in s:
                    hits.append(f"{col}:{doc.get('id') or doc.get('slug') or doc.get('key')}")
        print(f"{url}\n   refs: {hits if hits else 'NONE'}")
    client.close()

asyncio.run(main())
