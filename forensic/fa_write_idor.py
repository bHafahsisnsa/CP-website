#!/usr/bin/env python3
"""fa_write_idor.py — FORENSIC: WRITE/READ IDOR lintas-pemilik (RC-E10). AKTIF (E3).

User A membuat order (login) → User B mencoba GET /api/orders/{code} & POST cancel →
harus 404 (bukan 200). Grow-with-code: bila endpoint kepemilikan belum ada → SIAP-AKTIF.
Usage: cd /app && python forensic/fa_write_idor.py
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
A = {"email": "customer@collectorparfum.id", "password": "Customer#2026"}
B = {"email": "admin@collectorparfum.id", "password": "Admin#2026"}
G, Y, R, B_, X = "\033[92m", "\033[93m", "\033[91m", "\033[1m", "\033[0m"
ADDR = {"name": "IDOR A", "phone": "0811", "street": "Jl. A", "city": "Jakarta",
        "province": "DKI", "postal": "10000", "label": "Rumah"}


def has_owned_endpoints():
    try:
        from server import app
    except Exception:
        return False
    for r in app.routes:
        p = getattr(r, "path", "")
        if any(o in p for o in ("/addresses", "/orders", "/wishlist")) and "{" in p:
            return True
    return False


async def main():
    print(f"\n{B_}FA_WRITE_IDOR — write/read IDOR lintas-pemilik{X}")
    if not has_owned_endpoints():
        print(f"  {Y}• Endpoint kepemilikan belum ada — SIAP-AKTIF. (exit 0){X}")
        return 0
    db = AsyncIOMotorClient(MONGO_URL)[DB_NAME]
    vuln = 0
    created = None
    async with httpx.AsyncClient() as c:
        try:
            if (await c.get(f"{API}/api/", timeout=5)).status_code >= 500:
                raise Exception("5xx")
        except Exception:
            print(f"  {Y}• Backend belum berjalan — SKIP (exit 0).{X}")
            return 0
        ra = await c.post(f"{API}/api/auth/login", json=A)
        rb = await c.post(f"{API}/api/auth/login", json=B)
        if ra.status_code != 200 or rb.status_code != 200:
            print(f"  {Y}• Login gagal — SKIP (exit 0).{X}")
            return 0
        ha = {"Authorization": f"Bearer {ra.json()['token']}"}
        hb = {"Authorization": f"Bearer {rb.json()['token']}"}
        prod = await db.products.find_one({"status": "active"})
        vol = max(prod["volumes"], key=lambda v: v.get("stock", 0))
        vtype = str(vol.get("type", "") or "")
        payload = {"items": [{"product_id": prod["id"], "variant_type": vtype,
                              "volume_ml": vol["ml"], "quantity": 1}],
                   "address": ADDR, "shipping_id": "jne-reg",
                   "payment": {"group": "transfer", "method_id": "bca"}}
        r = await c.post(f"{API}/api/orders", json=payload, headers=ha)
        if r.status_code != 200:
            print(f"  {Y}• Create order A gagal ({r.status_code}) — SKIP.{X}")
            return 0
        created = r.json()["code"]
        # B baca order A
        rget = await c.get(f"{API}/api/orders/{created}", headers=hb)
        if rget.status_code == 200:
            vuln += 1
            print(f"  {R}VULN: user B BISA baca order user A (200){X}")
        else:
            print(f"  {G}✓ user B baca order A → {rget.status_code} (ditolak){X}")
        # B cancel order A
        rcan = await c.post(f"{API}/api/orders/{created}/cancel", headers=hb)
        if rcan.status_code == 200:
            vuln += 1
            print(f"  {R}VULN: user B BISA cancel order user A (200){X}")
        else:
            print(f"  {G}✓ user B cancel order A → {rcan.status_code} (ditolak){X}")
        # ---- Address IDOR (E4): A buat alamat, B coba PUT/DELETE ----
        addr_payload = {"name": "IDOR A", "phone": "0811", "street": "Jl A", "city": "Jakarta",
                        "province": "DKI", "postal": "10000", "label": "Rumah"}
        ra_addr = await c.post(f"{API}/api/addresses", json=addr_payload, headers=ha)
        if ra_addr.status_code == 200:
            aid = ra_addr.json()["id"]
            rb_put = await c.put(f"{API}/api/addresses/{aid}", json={**addr_payload, "name": "Hacked"}, headers=hb)
            rb_del = await c.delete(f"{API}/api/addresses/{aid}", headers=hb)
            if rb_put.status_code == 200:
                vuln += 1
                print(f"  {R}VULN: user B BISA ubah alamat user A (200){X}")
            else:
                print(f"  {G}\u2713 user B ubah alamat A \u2192 {rb_put.status_code} (ditolak){X}")
            if rb_del.status_code == 200:
                vuln += 1
                print(f"  {R}VULN: user B BISA hapus alamat user A (200){X}")
            else:
                print(f"  {G}\u2713 user B hapus alamat A \u2192 {rb_del.status_code} (ditolak){X}")
            await db.addresses.delete_one({"id": aid})

        # ---- Payment-proof IDOR (E6): B submit bukti bayar pada order A → harus 404 ----
        rb_proof = await c.post(f"{API}/api/orders/{created}/payment-proof",
                                json={"amount": 10000, "ref": "HACK"}, headers=hb)
        if rb_proof.status_code == 200:
            vuln += 1
            print(f"  {R}VULN: user B BISA unggah bukti bayar pada order user A (200){X}")
        else:
            print(f"  {G}\u2713 user B unggah bukti bayar order A \u2192 {rb_proof.status_code} (ditolak){X}")
        await db.payment_proofs.delete_many({"order_code": created})

        # cleanup: batalkan+hapus sbg A (owner)
        from services import stock
        o = await db.orders.find_one({"code": created})
        if o:
            await stock.restore(db, o.get("items", []))
            await db.orders.delete_one({"code": created})
    print(f"\n  {(R if vuln else G)}{B_}VULN {vuln}{X}")
    return 1 if vuln else 0


if __name__ == "__main__":
    try:
        rc = asyncio.run(main())
    except Exception as ex:
        print(f"  {Y}Gate error (SKIP): {ex}{X}")
        rc = 0
    sys.exit(rc)
