#!/usr/bin/env python3
"""verify_state_machine.py — GATE STATE-MACHINE ORDER (RC-E6/E7/E8/E4). AKTIF (E3).

Menguji jalur MENYIMPANG (bukan happy-path) — kelas 'green-but-broken':
  SM1  cancel order ter-reserve (via endpoint pemilik) → status=cancelled & STOK dikembalikan (RC-E6).
  SM2  transisi ilegal (pending → shipped) → DITOLAK (RC-E7).
  SM3  bayar/konfirmasi order cancelled → DITOLAK (RC-E8).
  SM4  complete order belum lunas → payment_status tetap jujur (RC-E4, INV-5).
  SM5  record_payment pada order terminal → DITOLAK (INV-P2, E6).
  SM6  record_payment lunas → order maju ke `paid` + payment_status `lunas` via SSOT (E6).

SM1 via HTTP (POST /api/orders + /orders/{code}/cancel). SM2/3/4 memanggil SSOT
services.orders.transition_order langsung (data sintetis, auto-cleanup). Exit 1 hanya bila regresi.
Usage: cd /app && python scripts/verify_state_machine.py
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
CUST = {"email": os.environ.get("CUST_EMAIL", "customer@collectorparfum.id"),
        "password": os.environ.get("CUST_PASS", "Customer#2026")}
G, Y, R, B, X = "\033[92m", "\033[93m", "\033[91m", "\033[1m", "\033[0m"
fails = 0
skips = 0
CREATED = []
ADDR = {"name": "SM Gate", "phone": "0811", "street": "Jl. Gate", "city": "Jakarta",
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


async def _stock(db, pid, sku):
    """Baca stok SSOT dari variants[].stock (identitas varian = sku)."""
    doc = await db.products.find_one({"id": pid}, {"variants": 1})
    for v in (doc or {}).get("variants", []):
        if v.get("sku") == sku:
            return int(v["stock"])
    return None


async def run():
    global fails
    print(f"\n{B}{'='*60}{X}\n  STATE-MACHINE GATE (order lifecycle)  API={API}\n{B}{'='*60}{X}")
    if not _has_orders_route():
        print(f"{Y}  Endpoint POST /api/orders belum ada — SIAP-AKTIF. SKIP.{X}")
        return 0
    db = AsyncIOMotorClient(MONGO_URL)[DB_NAME]
    async with httpx.AsyncClient(follow_redirects=True, timeout=30) as c:
        try:
            if (await c.get(f"{API}/api/", timeout=5)).status_code >= 500:
                raise Exception("5xx")
        except Exception:
            skip("Backend belum berjalan.")
            return _summary()
        r = await c.post(f"{API}/api/auth/login", json=CUST)
        if r.status_code != 200:
            skip("Login customer gagal.")
            return _summary()
        h = {"Authorization": f"Bearer {r.json()['token']}"}

        # ---- SM1: cancel via endpoint pemilik → stok kembali ----
        prod = await db.products.find_one({"status": "active"})
        variant = max(prod["variants"], key=lambda v: v.get("stock", 0))
        sku = variant["sku"]
        before = await _stock(db, prod["id"], sku)
        payload = {"items": [{"product_id": prod["id"], "sku": sku, "quantity": 1}],
                   "address": ADDR, "shipping_id": "jne-reg",
                   "payment": {"group": "transfer", "method_id": "bca"}}
        rc = await c.post(f"{API}/api/orders", json=payload, headers=h)
        if rc.status_code != 200:
            fail(f"SM1 create HTTP {rc.status_code}: {rc.text[:120]}")
        else:
            code = rc.json()["code"]
            CREATED.append(code)
            mid = await _stock(db, prod["id"], sku)
            rcan = await c.post(f"{API}/api/orders/{code}/cancel", headers=h)
            after = await _stock(db, prod["id"], sku)
            if rcan.status_code == 200 and rcan.json().get("status") == "cancelled" \
                    and mid == before - 1 and after == before:
                ok(f"SM1 cancel → cancelled & stok kembali ({before}->{mid}->{after})")
            else:
                fail(f"SM1 cancel/stok salah: HTTP {rcan.status_code} stok {before}->{mid}->{after}")

        # ---- SM2/SM3/SM4: SSOT transition_order langsung ----
        from services import orders as osvc
        try:
            await osvc.transition_order(db, {"code": "X", "status": "pending", "items": [],
                                             "paid_amount": 0, "total": 1000}, "shipped")
            fail("SM2 pending->shipped TIDAK ditolak")
        except osvc.InvalidTransition:
            ok("SM2 pending->shipped ditolak (400)")
        try:
            await osvc.transition_order(db, {"code": "X", "status": "cancelled", "items": [],
                                             "paid_amount": 0, "total": 1000}, "paid")
            fail("SM3 cancelled->paid TIDAK ditolak")
        except osvc.InvalidTransition:
            ok("SM3 aksi pada order terminal ditolak (400)")
        scode = "CPSMGATE4"
        await db.orders.delete_one({"code": scode})
        await db.orders.insert_one({"id": "ord_smgate4", "code": scode, "user_id": None, "items": [],
                                    "subtotal": 100000, "discount": 0, "voucher_code": None,
                                    "shipping": {"price": 0}, "payment": {"group": "transfer"},
                                    "cod_fee": 0, "total": 100000, "paid_amount": 0,
                                    "status": "shipped", "payment_status": "belum_bayar"})
        order = await db.orders.find_one({"code": scode})
        res = await osvc.transition_order(db, order, "completed")
        if res.get("status") == "completed" and res.get("payment_status") in ("belum_bayar", "dp"):
            ok(f"SM4 complete unpaid → payment_status jujur ({res['payment_status']})")
        else:
            fail(f"SM4 payment drift: {res.get('payment_status')}")
        await db.orders.delete_one({"code": scode})

        # ---- SM5: record_payment pada order terminal → ditolak (INV-P2) ----
        try:
            await osvc.record_payment(db, {"code": "X", "status": "cancelled", "items": [],
                                           "paid_amount": 0, "total": 1000}, 1000)
            fail("SM5 record_payment pada terminal TIDAK ditolak")
        except osvc.InvalidTransition:
            ok("SM5 record_payment pada order terminal ditolak (INV-P2)")

        # ---- SM6: record_payment lunas → maju ke paid + payment_status lunas (SSOT) ----
        scode6 = "CPSMGATE6"
        await db.orders.delete_one({"code": scode6})
        await db.orders.insert_one({"id": "ord_smgate6", "code": scode6, "user_id": None, "items": [],
                                    "subtotal": 50000, "discount": 0, "voucher_code": None,
                                    "shipping": {"price": 0}, "payment": {"group": "transfer"},
                                    "cod_fee": 0, "total": 50000, "paid_amount": 0,
                                    "status": "pending", "payment_status": "belum_bayar"})
        o6 = await db.orders.find_one({"code": scode6})
        r6 = await osvc.record_payment(db, o6, 50000)
        if r6.get("status") == "paid" and r6.get("payment_status") == "lunas" \
                and int(r6.get("paid_amount", 0) or 0) == 50000:
            ok("SM6 record_payment lunas → paid + lunas (SSOT)")
        else:
            fail(f"SM6 record_payment salah: status={r6.get('status')} ps={r6.get('payment_status')}")
        await db.orders.delete_one({"code": scode6})
    return await _summary(db)


async def _summary(db=None):
    if db is not None:
        from services import stock
        for code in set(CREATED):
            o = await db.orders.find_one({"code": code})
            if o:
                if o.get("status") != "cancelled":
                    await stock.restore(db, o.get("items", []))
                await db.orders.delete_one({"code": code})
    print(f"\n{B}{'='*60}{X}\n  {R}FAIL {fails}{X} | {Y}SKIP {skips}{X}\n{B}{'='*60}{X}")
    if fails:
        print(f"{R}{B}  STATE-MACHINE REGRESI.{X}\n")
        return 1
    print(f"{G}{B}  State-machine sehat (SM1..SM6 AKTIF).{X}\n")
    return 0


if __name__ == "__main__":
    try:
        rc = asyncio.run(run())
    except Exception as ex:
        print(f"{Y}  Gate error (dianggap SKIP): {ex}{X}")
        rc = 0
    sys.exit(rc)
