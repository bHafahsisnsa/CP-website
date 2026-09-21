#!/usr/bin/env python3
"""verify_cross_entity.py — GATE konsistensi LINTAS-ENTITAS (RC-E9). (grow-with-code)

Cek konsistensi yang HANYA muncul lintas koleksi (lolos cek per-entitas):
  CE1  voucher.used_count == jumlah order memakai voucher tsb.
  CE2  Σ order.paid_amount ≤ Σ order.total (tak ada overpay agregat).
  CE3  setiap order.items[].product_id ADA di products (FK live) — juga verify_schema.
  CE4  order.total live == subtotal - discount + shipping.price + cod_fee (rekomputasi).
  CE5  paid_amount == Σ bukti bayar `verified` (non-COD) — uang tak muncul dari udara (E6).

Berjalan pada data yang ADA (order/voucher). Bila belum ada order → 0 cek → PASS.
Usage: cd /app && python scripts/verify_cross_entity.py
"""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
try:
    from dotenv import load_dotenv
    load_dotenv(ROOT / "backend" / ".env")
except Exception:
    pass
from pymongo import MongoClient

G, Y, R, B, X = "\033[92m", "\033[93m", "\033[91m", "\033[1m", "\033[0m"
DB = MongoClient(os.environ.get("MONGO_URL", "mongodb://localhost:27017"))[os.environ.get("DB_NAME", "collector_parfum")]
fails = 0


def report(name, bad, total):
    global fails
    if bad:
        fails += 1
        print(f"  {R}[FAIL]{X} {name}: {len(bad)}/{total} → {bad[:5]}")
    else:
        print(f"  {G}[OK]{X} {name} ({total} diperiksa)")


def main():
    print(f"\n{B}{'='*60}{X}\n  CROSS-ENTITY GATE (RC-E9)\n{B}{'='*60}{X}")
    orders = list(DB.orders.find({}, {"_id": 0}))
    if not orders:
        print(f"  {Y}(belum ada order — SIAP-AKTIF di fase business-logic){X}")
        print(f"\n{G}{B}  Cross-entity OK (nihil data).{X}\n")
        return 0
    prod_ids = {p["id"] for p in DB.products.find({}, {"id": 1, "_id": 0})}
    vouchers = {v["code"]: v for v in DB.vouchers.find({}, {"_id": 0})}

    # CE1 voucher.used_count == #order pakai voucher == #voucher_redemptions (anti phantom)
    ce1 = []
    used = {}
    for o in orders:
        vc = o.get("voucher_code")
        if vc:
            used[vc] = used.get(vc, 0) + 1
    redeemed = {}
    for r in DB.voucher_redemptions.find({}, {"voucher_code": 1, "_id": 0}):
        vc = r.get("voucher_code")
        if vc:
            redeemed[vc] = redeemed.get(vc, 0) + 1
    for code, v in vouchers.items():
        uc = int(v.get("used_count", 0) or 0)
        n_ord = used.get(code, 0)
        n_red = redeemed.get(code, 0)
        if not (uc == n_ord == n_red):
            ce1.append(f"{code}(used={uc},orders={n_ord},redemptions={n_red})")
    report("CE1 voucher.used_count == #orders == #redemptions", ce1, len(vouchers))

    # CE2 overpay agregat
    tot = sum(int(o.get("total", 0) or 0) for o in orders)
    paid = sum(int(o.get("paid_amount", 0) or 0) for o in orders)
    report("CE2 Σpaid ≤ Σtotal (anti-overpay agregat)", (["overpay"] if paid > tot else []), len(orders))

    # CE3 FK item->product
    ce3 = []
    for o in orders:
        for it in o.get("items", []):
            if it.get("product_id") not in prod_ids:
                ce3.append(o.get("code"))
                break
    report("CE3 order.items.product_id -> products (FK)", ce3, len(orders))

    # CE4 total rekomputasi
    ce4 = []
    for o in orders:
        exp = int(o.get("subtotal", 0) or 0) - int(o.get("discount", 0) or 0) \
            + int((o.get("shipping") or {}).get("price", 0) or 0) + int(o.get("cod_fee", 0) or 0)
        if exp != int(o.get("total", 0) or 0):
            ce4.append(o.get("code"))
    report("CE4 total == subtotal-discount+ship+cod (live)", ce4, len(orders))

    # CE5 rekonsiliasi bukti bayar (E6): paid_amount == Σ bukti verified (kecuali COD)
    verified = {}
    for p in DB.payment_proofs.find({"status": "verified"}, {"order_code": 1, "amount": 1, "_id": 0}):
        verified[p["order_code"]] = verified.get(p["order_code"], 0) + int(p.get("amount", 0) or 0)
    ce5 = []
    for o in orders:
        if (o.get("payment") or {}).get("group") == "cod":
            continue
        if int(o.get("paid_amount", 0) or 0) != verified.get(o.get("code"), 0):
            ce5.append(o.get("code"))
    report("CE5 paid_amount == Σ bukti verified (non-COD, E6)", ce5, len(orders))

    # CE6 (E7 INV-G1): event analytics `purchase` tak mengarang order (no phantom revenue).
    order_codes = {o.get("code") for o in orders}
    purch = list(DB.analytics_events.find({"type": "purchase"}, {"order_code": 1, "_id": 0}))
    ce6 = [p.get("order_code") for p in purch
           if p.get("order_code") and p.get("order_code") not in order_codes]
    report("CE6 purchase event.order_code -> orders (E7, no phantom)", ce6, len(purch))

    print(f"\n{B}{'='*60}{X}")
    if fails:
        print(f"  {R}{B}CROSS-ENTITY VIOLATION: {fails}.{X}\n")
        return 1
    print(f"  {G}{B}Cross-entity konsisten.{X}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
