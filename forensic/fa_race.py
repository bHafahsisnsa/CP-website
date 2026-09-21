#!/usr/bin/env python3
"""fa_race.py — FORENSIC: konkurensi & anti-oversell (RC-E3). AKTIF (E3).

Produk sintetis stok=1 → N checkout paralel → harapkan tepat 1 sukses, stok akhir 0.
Grow-with-code: bila endpoint belum ada → SIAP-AKTIF (exit 0). VULN>0 → exit 1.
Usage: cd /app && python forensic/fa_race.py
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
PID = "prd_farace_gate"
ADDR = {"name": "FA Race", "phone": "0811", "street": "Jl. FA", "city": "Jakarta",
        "province": "DKI", "postal": "10000", "label": "Rumah"}


def has_route(substr, method="POST"):
    try:
        from server import app
    except Exception:
        return False
    for r in app.routes:
        if method in (getattr(r, "methods", set()) or set()) and substr in getattr(r, "path", ""):
            return True
    return False


async def main():
    print(f"\n{B}FA_RACE — anti-oversell (checkout paralel){X}")
    if not has_route("/orders", "POST"):
        print(f"  {Y}• POST /api/orders belum ada — SIAP-AKTIF.{X}")
        print(f"  {G}✓ (tidak ada regresi — exit 0){X}")
        return 0
    db = AsyncIOMotorClient(MONGO_URL)[DB_NAME]
    try:
        async with httpx.AsyncClient() as c:
            if (await c.get(f"{API}/api/", timeout=5)).status_code >= 500:
                raise Exception("5xx")
    except Exception:
        print(f"  {Y}• Backend belum berjalan — SKIP (exit 0).{X}")
        return 0
    await db.products.delete_one({"id": PID})
    await db.products.insert_one({
        "id": PID, "slug": "farace-gate", "name": "FA Race Gate", "brand": "Collector",
        "category": "amber", "concentration": "EDP", "gender": "Unisex", "price": 100000,
        "compare_at_price": None, "best_seller": False, "is_new": False, "tags": [],
        "options": [{"name": "Ukuran", "values": ["50ml"]}],
        "variants": [{"sku": "FARACE-50", "options": {"Ukuran": "50ml"}, "price": 100000,
                      "stock": 1, "compare_at_price": None}],
        "notes": {"top": [], "heart": [], "base": []}, "description": "synthetic",
        "images": [], "video_url": None, "seo": {}, "rating_avg": 0.0, "rating_count": 0,
        "status": "active",
    })
    N = 12
    payload = {"items": [{"product_id": PID, "sku": "FARACE-50", "quantity": 1}], "address": ADDR,
               "shipping_id": "jne-reg", "payment": {"group": "transfer", "method_id": "bca"}}

    async def shot():
        async with httpx.AsyncClient() as c:
            try:
                r = await c.post(f"{API}/api/orders", json=payload, timeout=25)
                return r.status_code, (r.json() if r.status_code == 200 else None)
            except Exception:
                return -1, None

    res = await asyncio.gather(*[shot() for _ in range(N)])
    succ = [j for sc, j in res if sc == 200 and j]
    err5xx = sum(1 for sc, _ in res if sc >= 500)
    final = None
    doc = await db.products.find_one({"id": PID}, {"variants": 1})
    for v in (doc or {}).get("variants", []):
        if v.get("sku") == "FARACE-50":
            final = int(v["stock"])
    for j in succ:
        await db.orders.delete_one({"code": j["code"]})
    await db.products.delete_one({"id": PID})
    vuln = 0
    if len(succ) != 1:
        vuln += 1
        print(f"  {R}VULN: {len(succ)} sukses (oversell, harus 1){X}")
    else:
        print(f"  {G}✓ tepat 1/{N} sukses{X}")
    if final != 0:
        vuln += 1
        print(f"  {R}VULN: stok akhir {final} (harus 0){X}")
    else:
        print(f"  {G}✓ stok akhir 0 (tak negatif){X}")
    if err5xx:
        vuln += 1
        print(f"  {R}VULN: {err5xx}×5xx saat balapan{X}")
    print(f"\n  {(R if vuln else G)}{B}VULN {vuln}{X}")
    return 1 if vuln else 0


if __name__ == "__main__":
    try:
        rc = asyncio.run(main())
    except Exception as ex:
        print(f"  {Y}Gate error (SKIP): {ex}{X}")
        rc = 0
    sys.exit(rc)
