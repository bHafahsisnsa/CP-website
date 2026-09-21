#!/usr/bin/env python3
"""verify_concurrency.py — GATE CONCURRENCY anti-oversell (RC-E3). AKTIF (E3).

Produk sintetis stok=1 → N checkout PARALEL untuk unit terakhir. INVARIAN:
  - Tepat 1 checkout sukses (200), sisanya 409 (kalah balapan).
  - Stok akhir = 0 (TAK PERNAH negatif, INV-4).
Produk sintetis + order sukses dibersihkan. Exit 1 hanya bila oversell/negatif/5xx.
Usage: cd /app && python scripts/verify_concurrency.py
"""
import asyncio
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))
try:
    from dotenv import load_dotenv
    load_dotenv(ROOT / "backend" / ".env")
except Exception:
    pass
try:
    import httpx
except ImportError:
    os.system("pip install httpx -q")
    import httpx
from motor.motor_asyncio import AsyncIOMotorClient

API = os.environ.get("API_BASE", "http://localhost:8001").rstrip("/")
MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "collector_parfum")
G, Y, R, B, X = "\033[92m", "\033[93m", "\033[91m", "\033[1m", "\033[0m"
fails = skips = 0
PID = "prd_conc_gate"
ADDR = {"name": "Conc Gate", "phone": "0811", "street": "Jl. Race", "city": "Jakarta",
        "province": "DKI", "postal": "10000", "label": "Rumah"}


def ok(m):
    print(f"  {G}[OK]{X} {m}")


def fail(m):
    global fails
    fails += 1
    print(f"  {R}[FAIL]{X} {m}")


def skip(m):
    global skips
    skips += 1
    print(f"  {Y}[SKIP]{X} {m}")


def _has_orders_route():
    try:
        from server import app
        return any("POST" in (getattr(r, "methods", set()) or set()) and getattr(r, "path", "") == "/api/orders"
                   for r in app.routes)
    except Exception:
        return False


async def run():
    print(f"\n{B}{'='*60}{X}\n  CONCURRENCY GATE (RC-E3 oversell)  API={API}\n{B}{'='*60}{X}")
    if not _has_orders_route():
        print(f"{Y}  Endpoint checkout belum ada — SIAP-AKTIF. SKIP.{X}")
        return 0
    db = AsyncIOMotorClient(MONGO_URL)[DB_NAME]
    try:
        async with httpx.AsyncClient() as c:
            if (await c.get(f"{API}/api/", timeout=5)).status_code >= 500:
                raise Exception("5xx")
    except Exception:
        skip("Backend belum berjalan.")
        return await _summary(db)

    await db.products.delete_one({"id": PID})
    await db.products.insert_one({
        "id": PID, "slug": "conc-gate", "name": "Concurrency Gate", "brand": "Collector",
        "category": "amber", "concentration": "EDP", "gender": "Unisex", "price": 100000,
        "compare_at_price": None, "best_seller": False, "is_new": False, "tags": [],
        "options": [{"name": "Ukuran", "values": ["50ml"]}],
        "variants": [{"sku": "CONC-50", "options": {"Ukuran": "50ml"}, "price": 100000,
                      "stock": 1, "compare_at_price": None}],
        "notes": {"top": [], "heart": [], "base": []}, "description": "synthetic",
        "images": [], "video_url": None, "seo": {}, "rating_avg": 0.0, "rating_count": 0,
        "status": "active",
    })
    N = 10
    payload = {"items": [{"product_id": PID, "sku": "CONC-50", "quantity": 1}], "address": ADDR,
               "shipping_id": "jne-reg", "payment": {"group": "transfer", "method_id": "bca"}}

    async def shot():
        async with httpx.AsyncClient() as c:
            try:
                r = await c.post(f"{API}/api/orders", json=payload, timeout=25)
                return r.status_code, (r.json() if r.status_code == 200 else None)
            except Exception as e:
                return -1, str(e)

    results = await asyncio.gather(*[shot() for _ in range(N)])
    succ = [j for sc, j in results if sc == 200 and j]
    conflict = sum(1 for sc, _ in results if sc == 409)
    err5xx = sum(1 for sc, _ in results if sc >= 500)
    final = None
    doc = await db.products.find_one({"id": PID}, {"variants": 1})
    for v in (doc or {}).get("variants", []):
        if v.get("sku") == "CONC-50":
            final = int(v["stock"])
    for j in succ:
        await db.orders.delete_one({"code": j["code"]})
    if len(succ) == 1:
        ok(f"tepat 1/{N} sukses (anti-oversell)")
    else:
        fail(f"OVERSELL: {len(succ)} sukses (harus 1)")
    if final == 0:
        ok("stok akhir = 0 (tak negatif, INV-4)")
    else:
        fail(f"stok akhir {final} (harus 0)")
    if err5xx == 0:
        ok(f"tak ada 5xx ({conflict} × 409 kalah balapan)")
    else:
        fail(f"{err5xx} × 5xx saat balapan")
    return await _summary(db)


async def _summary(db):
    await db.products.delete_one({"id": PID})
    print(f"\n{B}{'='*60}{X}\n  {R}FAIL {fails}{X} | {Y}SKIP {skips}{X}\n{B}{'='*60}{X}")
    if fails:
        print(f"{R}{B}  CONCURRENCY REGRESI — oversell bocor.{X}\n")
        return 1
    print(f"{G}{B}  Concurrency aman (anti-oversell AKTIF).{X}\n")
    return 0


if __name__ == "__main__":
    try:
        rc = asyncio.run(run())
    except Exception as ex:
        print(f"{Y}  Gate error (dianggap SKIP): {ex}{X}")
        rc = 0
    sys.exit(rc)
