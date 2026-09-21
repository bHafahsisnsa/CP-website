#!/usr/bin/env python3
"""verify_p2a_per_user_voucher.py — bukti perbaikan P2a (race-safe per-user voucher).

Skenario:
  1) Login customer demo.
  2) Bersihkan state redemption/usage untuk (WELCOME10, user) agar test idempotent.
  3) Tembak N=6 checkout PARALEL memakai voucher WELCOME10 (per_user_limit=1).
  4) Assert: TEPAT 1 sukses, sisanya 400 "Batas pemakaian voucher ini sudah tercapai".
  5) Assert: voucher_redemptions == 1 dan voucher_user_usage.count == 1 (konsisten).
  6) Sequential guard: percobaan ke-2 (setelah 1 sukses) juga ditolak 400.

Jalankan: cd /app && python scripts/verify_p2a_per_user_voucher.py
"""
import asyncio
import os
import sys
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))
try:
    from dotenv import load_dotenv
    load_dotenv(ROOT / "backend" / ".env")
except Exception:
    pass
from motor.motor_asyncio import AsyncIOMotorClient  # noqa: E402

BASE = "http://localhost:8001/api"
CUST_EMAIL = "customer@collectorparfum.id"
CUST_PASS = "Customer#2026"
VOUCHER = "WELCOME10"  # per_user_limit = 1
N = 6

G, R, X = "\033[92m", "\033[91m", "\033[0m"


def order_payload():
    return {
        "items": [{"product_id": "prd_blancnerolibloom", "variant_type": "", "volume_ml": 30, "quantity": 1}],
        "address": {
            "name": "Kolektor Demo", "phone": "081200000000",
            "street": "Jl. Melati No. 1", "district": "Menteng",
            "city": "Jakarta", "province": "DKI Jakarta", "postal": "10310", "label": "Rumah",
        },
        "shipping_id": "jne-reg",
        "payment": {"group": "transfer", "method_id": "bca"},
        "voucher_code": VOUCHER,
        "note": "verify p2a",
    }


async def main():
    db = AsyncIOMotorClient(os.environ["MONGO_URL"])[os.environ.get("DB_NAME", "test_database")]
    failures = []

    # Login
    async with httpx.AsyncClient(timeout=30) as c:
        r = await c.post(f"{BASE}/auth/login", json={"email": CUST_EMAIL, "password": CUST_PASS})
        assert r.status_code == 200, f"login gagal: {r.status_code} {r.text}"
        token = r.json()["token"]
        uid = r.json()["user"]["id"]
    headers = {"Authorization": f"Bearer {token}"}

    # --- Cleanup state agar idempotent ---
    n_red = await db.voucher_redemptions.count_documents({"voucher_code": VOUCHER, "user_id": uid})
    if n_red:
        await db.voucher_redemptions.delete_many({"voucher_code": VOUCHER, "user_id": uid})
        await db.vouchers.update_one({"code": VOUCHER}, {"$inc": {"used_count": -n_red}})
    await db.voucher_user_usage.delete_many({"voucher_code": VOUCHER, "user_id": uid})
    # pastikan stok cukup untuk N order
    await db.products.update_one(
        {"id": "prd_blancnerolibloom", "volumes.ml": 30, "volumes.type": ""},
        {"$set": {"volumes.$.stock": 500}},
    )

    # === TEST 1: N checkout PARALEL ===
    async with httpx.AsyncClient(timeout=60) as c:
        results = await asyncio.gather(
            *[c.post(f"{BASE}/orders", json=order_payload(), headers=headers) for _ in range(N)],
            return_exceptions=True,
        )
    codes = [r.status_code if not isinstance(r, Exception) else "EXC" for r in results]
    ok = [r for r in results if not isinstance(r, Exception) and r.status_code == 200]
    limit_rejected = [
        r for r in results
        if not isinstance(r, Exception) and r.status_code == 400
        and "Batas pemakaian" in r.text
    ]
    print(f"Status codes ({N} paralel): {codes}")
    if len(ok) == 1:
        print(f"  {G}PASS{X} tepat 1 order sukses memakai voucher")
    else:
        failures.append(f"Order sukses = {len(ok)} (harusnya 1)")
        print(f"  {R}FAIL{X} order sukses = {len(ok)} (harusnya 1)")
    if len(limit_rejected) == N - 1:
        print(f"  {G}PASS{X} {N-1} sisanya ditolak 400 (batas per-user)")
    else:
        failures.append(f"Ditolak batas = {len(limit_rejected)} (harusnya {N-1})")
        print(f"  {R}FAIL{X} ditolak batas per-user = {len(limit_rejected)} (harusnya {N-1})")

    # === TEST 2: konsistensi DB ===
    red = await db.voucher_redemptions.count_documents({"voucher_code": VOUCHER, "user_id": uid})
    usage = await db.voucher_user_usage.find_one({"voucher_code": VOUCHER, "user_id": uid})
    usage_count = int((usage or {}).get("count", 0))
    print(f"DB: redemptions={red}, usage.count={usage_count}")
    if red == 1 and usage_count == 1:
        print(f"  {G}PASS{X} DB konsisten (redemptions==usage==1)")
    else:
        failures.append(f"DB tak konsisten redemptions={red} usage={usage_count}")
        print(f"  {R}FAIL{X} DB tak konsisten")

    # === TEST 3: sequential guard ===
    async with httpx.AsyncClient(timeout=30) as c:
        r = await c.post(f"{BASE}/orders", json=order_payload(), headers=headers)
    if r.status_code == 400 and "Batas pemakaian" in r.text:
        print(f"  {G}PASS{X} percobaan sequential ke-2 ditolak 400")
    else:
        failures.append(f"Sequential ke-2 status={r.status_code} body={r.text[:120]}")
        print(f"  {R}FAIL{X} sequential ke-2 status={r.status_code}")

    print()
    if failures:
        print(f"{R}VERDICT: {len(failures)} FAIL{X}")
        for f in failures:
            print("  -", f)
        return 1
    print(f"{G}VERDICT: SEMUA PASS — P2a race-safe terbukti.{X}")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
