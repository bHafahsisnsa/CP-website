#!/usr/bin/env python3
"""verify_schema.py — field-level + id-prefix + enum + FK sanity (DB clean-seed).

Menangkap drift skema yang lolos runtime: id-prefix salah, enum di luar himpunan,
FK menggantung (mis. product.category tak ada di categories). WAJIB jalan sesudah seed.
Usage: cd /app && python scripts/verify_schema.py
Exit 0 = valid. 1 = ada pelanggaran.
"""
import asyncio
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
try:
    from dotenv import load_dotenv
    load_dotenv(ROOT / "backend" / ".env")
except Exception:
    pass
from motor.motor_asyncio import AsyncIOMotorClient  # noqa: E402

G, Y, R, C, B, X = "\033[92m", "\033[93m", "\033[91m", "\033[96m", "\033[1m", "\033[0m"
MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "collector_parfum")

# koleksi -> prefix id yang diharapkan (bila pakai id berprefiks)
ID_PREFIX = {
    "users": "usr_", "products": "prd_", "categories": "cat_", "vouchers": "vcr_",
    "orders": "ord_", "addresses": "adr_", "reviews": "rev_", "audit_logs": "aud_",
    "voucher_redemptions": "vrd_", "wishlists": "wsh_", "carts": "crt_",
    "media_assets": "med_", "payment_proofs": "pay_", "analytics_events": "evt_",
    "import_sessions": "imp_",
}
ENUMS = {
    "users.role": {"admin", "customer"},
    "users.status": {"active", "inactive"},
    "products.concentration": {"EDP", "EDT"},
    "products.gender": {"Pria", "Wanita", "Unisex"},
    "products.status": {"active", "archived"},
    "vouchers.type": {"percent", "flat", "free_shipping"},
    "payment_methods.group": {"transfer", "ewallet", "cod"},
    "orders.status": {"pending", "paid", "packed", "shipped", "completed", "cancelled"},
    "orders.payment_status": {"belum_bayar", "dp", "lunas"},
}
fails = []


def fail(msg):
    fails.append(msg)
    print(f"  {R}[FAIL]{X} {msg}")


def ok(msg):
    print(f"  {G}[OK]{X} {msg}")


async def check_prefix(db):
    print(f"\n{C}{B}ID-PREFIX{X}")
    for coll, prefix in ID_PREFIX.items():
        docs = await db[coll].find({}, {"id": 1, "_id": 0}).to_list(2000)
        bad = [d.get("id") for d in docs if d.get("id") and not str(d["id"]).startswith(prefix)]
        if bad:
            fail(f"{coll}: {len(bad)} id tanpa prefix '{prefix}' (contoh: {bad[:3]})")
        elif docs:
            ok(f"{coll}: {len(docs)} id berprefix '{prefix}'")


async def check_enums(db):
    print(f"\n{C}{B}ENUM{X}")
    for key, allowed in ENUMS.items():
        coll, field = key.split(".")
        docs = await db[coll].find({}, {field: 1, "_id": 0}).to_list(5000)
        bad = sorted({str(d.get(field)) for d in docs if d.get(field) is not None and d.get(field) not in allowed})
        if bad:
            fail(f"{key}: nilai di luar himpunan sah {sorted(allowed)} -> {bad}")
        elif docs:
            ok(f"{key}: semua sah")


async def check_fk(db):
    print(f"\n{C}{B}FOREIGN KEY{X}")
    cat_slugs = {c["slug"] for c in await db.categories.find({}, {"slug": 1, "_id": 0}).to_list(500)}
    prods = await db.products.find({}, {"category": 1, "slug": 1, "_id": 0}).to_list(5000)
    dangling = [p.get("slug") for p in prods if p.get("category") not in cat_slugs]
    if dangling:
        fail(f"products.category menggantung (tak ada di categories): {dangling[:5]}")
    elif prods:
        ok(f"products.category → categories OK ({len(prods)} produk)")
    else:
        print(f"  {Y}(belum ada produk — FK produk dilewati di fase fondasi){X}")

    # order.items[].product_id → products.id
    prod_ids = {p["id"] for p in await db.products.find({}, {"id": 1, "_id": 0}).to_list(5000)}
    orders = await db.orders.find({}, {"items": 1, "code": 1, "_id": 0}).to_list(5000)
    bad_orders = []
    for o in orders:
        for it in o.get("items", []):
            if it.get("product_id") not in prod_ids:
                bad_orders.append(o.get("code"))
                break
    if bad_orders:
        fail(f"orders.items.product_id menggantung: {bad_orders[:5]}")
    elif orders:
        ok(f"orders.items.product_id → products OK ({len(orders)} order)")

    # wishlist.product_ids → products.id (E4)
    wishlists = await db.wishlists.find({}, {"product_ids": 1, "user_id": 1, "_id": 0}).to_list(20000)
    bad_wish = [w.get("user_id") for w in wishlists
                if any(pid not in prod_ids for pid in w.get("product_ids", []))]
    if bad_wish:
        fail(f"wishlist.product_ids menggantung (tak ada di products): {bad_wish[:5]}")
    elif wishlists:
        ok(f"wishlist.product_ids → products OK ({len(wishlists)} wishlist)")


async def main():
    print(f"\n{B}{'='*60}{X}\n  VERIFY SCHEMA (DB: {DB_NAME})\n{B}{'='*60}{X}")
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    await check_prefix(db)
    await check_enums(db)
    await check_fk(db)
    client.close()
    print(f"\n{B}{'='*60}{X}")
    if fails:
        print(f"  {R}{B}SCHEMA VIOLATION: {len(fails)}{X}\n")
        return 1
    print(f"  {G}{B}SCHEMA OK.{X}\n")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
