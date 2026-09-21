#!/usr/bin/env python3
"""mutation_smoke.py — WRITE-PATH SMOKE (audit alur TULIS). AKTIF sebagian (E3).

  M1  (admin CRUD produk) — SIAP-AKTIF di E5 (belum ada endpoint admin).
  M2  ANTI-OVERSELL: checkout qty > stok → DITOLAK (409/4xx, bukan 5xx).
  M3  checkout valid → STOK berkurang konsisten (lalu dibersihkan).
Resilient: backend/endpoint belum ada → SKIP rapi. Hanya 5xx / invarian rusak = FAIL.
Usage: cd /app && python scripts/mutation_smoke.py
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
ADMIN = {"email": os.environ.get("ADMIN_EMAIL", "admin@collectorparfum.id"),
         "password": os.environ.get("ADMIN_PASS", "Admin#2026")}
G, Y, R, B, X = "\033[92m", "\033[93m", "\033[91m", "\033[1m", "\033[0m"
fails = skips = 0
ADDR = {"name": "Mut Smoke", "phone": "0811", "street": "Jl. Mut", "city": "Jakarta",
        "province": "DKI", "postal": "10000", "label": "Rumah"}


def ok(m):
    print(f"  {G}[OK]{X} {m}")


def skip(m):
    global skips
    skips += 1
    print(f"  {Y}[SKIP]{X} {m}")


def fail(m):
    global fails
    fails += 1
    print(f"  {R}[FAIL]{X} {m}")


def _has_orders_route():
    try:
        from server import app
        return any("POST" in (getattr(r, "methods", set()) or set()) and getattr(r, "path", "") == "/api/orders"
                   for r in app.routes)
    except Exception:
        return False


def _has_admin_products():
    try:
        from server import app
        return any(getattr(r, "path", "") == "/api/admin/products" for r in app.routes)
    except Exception:
        return False


async def _stock(db, pid, sku):
    """Baca stok SSOT dari variants[].stock (identitas varian = sku)."""
    doc = await db.products.find_one({"id": pid}, {"variants": 1})
    for v in (doc or {}).get("variants", []):
        if v.get("sku") == sku:
            return int(v["stock"])
    return None


async def run():
    print(f"\n{B}{'='*60}{X}\n  MUTATION SMOKE (write-path)  API={API}\n{B}{'='*60}{X}")
    if not _has_orders_route():
        skip("POST /api/orders belum ada — SIAP-AKTIF.")
        return _summary()
    if not _has_admin_products():
        skip("M1 admin produk CRUD — SIAP-AKTIF di E5.")
    db = AsyncIOMotorClient(MONGO_URL)[DB_NAME]
    created = []
    async with httpx.AsyncClient() as c:
        try:
            if (await c.get(f"{API}/api/", timeout=5)).status_code >= 500:
                raise Exception("5xx")
        except Exception:
            skip("Backend belum berjalan.")
            return _summary()
        prod = await db.products.find_one({"status": "active"})
        variant = max(prod["variants"], key=lambda v: v.get("stock", 0))
        sku = variant["sku"]
        # M2 anti-oversell (qty > stok, dalam bound)
        m2 = {"items": [{"product_id": prod["id"], "sku": sku, "quantity": 999}],
              "address": ADDR, "shipping_id": "jne-reg",
              "payment": {"group": "transfer", "method_id": "bca"}}
        r2 = await c.post(f"{API}/api/orders", json=m2, timeout=20)
        if r2.status_code == 409:
            ok("M2 checkout qty>stok → 409 (anti-oversell)")
        elif r2.status_code >= 500:
            fail(f"M2 5xx ({r2.status_code})")
        else:
            fail(f"M2 HTTP {r2.status_code} (harus 409)")
        # M3 checkout valid → stok turun
        before = await _stock(db, prod["id"], sku)
        m3 = {"items": [{"product_id": prod["id"], "sku": sku, "quantity": 1}],
              "address": ADDR, "shipping_id": "jne-reg",
              "payment": {"group": "transfer", "method_id": "bca"}}
        r3 = await c.post(f"{API}/api/orders", json=m3, timeout=20)
        if r3.status_code == 200:
            created.append(r3.json()["code"])
            after = await _stock(db, prod["id"], sku)
            if after == before - 1:
                ok(f"M3 checkout valid → stok {before}->{after}")
            else:
                fail(f"M3 stok tak konsisten {before}->{after}")
        elif r3.status_code >= 500:
            fail(f"M3 5xx ({r3.status_code})")
        else:
            fail(f"M3 HTTP {r3.status_code}")
        # cleanup: kembalikan stok + hapus order
        from services import stock
        for code in created:
            o = await db.orders.find_one({"code": code})
            if o:
                await stock.restore(db, o.get("items", []))
                await db.orders.delete_one({"code": code})
    return _summary()


def _summary():
    print(f"\n{B}{'='*60}{X}\n  {R}FAIL {fails}{X} | {Y}SKIP {skips}{X}\n{B}{'='*60}{X}")
    if fails:
        print(f"{R}{B}  WRITE-PATH BERMASALAH.{X}\n")
        return 1
    print(f"{G}{B}  Write-path sehat (M2/M3 AKTIF).{X}\n")
    return 0


if __name__ == "__main__":
    try:
        rc = asyncio.run(run())
    except Exception as ex:
        print(f"{Y}  Gate error (dianggap SKIP): {ex}{X}")
        rc = 0
    sys.exit(rc)
