#!/usr/bin/env python
"""scripts/qa_cleanup.py — hapus permanen produk uji QA dari Mongo.

Produk uji dibuat oleh testing agent / skrip QA memakai slug berawalan
`qa-` atau `uji-`. Endpoint DELETE admin hanya melakukan SOFT-delete
(status -> archived), jadi pembersihan keras dilakukan langsung di DB.

Jalankan: python scripts/qa_cleanup.py
"""
import asyncio
import os
import sys

from motor.motor_asyncio import AsyncIOMotorClient

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "backend"))

G, R, C, X, B = "\033[92m", "\033[91m", "\033[96m", "\033[0m", "\033[1m"
PREFIXES = ("qa-", "uji-")


async def main():
    mongo_url = os.environ.get("MONGO_URL")
    db_name = os.environ.get("DB_NAME")
    if not mongo_url or not db_name:
        from dotenv import load_dotenv

        load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "backend", ".env"))
        mongo_url = os.environ.get("MONGO_URL")
        db_name = os.environ.get("DB_NAME")
    if not mongo_url or not db_name:
        print(f"{R}MONGO_URL/DB_NAME tidak tersedia.{X}")
        return 1

    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    total = 0
    for prefix in PREFIXES:
        query = {"slug": {"$regex": f"^{prefix}"}}
        found = await db.products.count_documents(query)
        if found:
            res = await db.products.delete_many(query)
            total += res.deleted_count
            print(f"  {G}✓{X} slug ^{prefix} -> {res.deleted_count} produk dihapus")
        else:
            print(f"  {C}·{X} slug ^{prefix} -> tidak ada")
    remaining = await db.products.count_documents({})
    print(f"\n{B}Total dihapus: {total}. Produk tersisa di DB: {remaining}.{X}")
    client.close()
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
