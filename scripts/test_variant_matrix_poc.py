#!/usr/bin/env python3
"""test_variant_matrix_poc.py — POC gabungan (Phase 1) untuk:
  A. Model varian matriks (Type × Size): create typed + typeless via admin API, auto-SKU,
     harga display = varian termurah.
  B. Order snapshot membawa variant_type + sku.
  C. Anti-oversell keyed by (type, ml): parallel checkout tak menyeberang ke tipe lain.
  D. Smart import pure funcs: suggest_mapping + validate_and_group (mapping cerdas + validasi).

Jalankan backend lebih dulu. Usage: cd /app && python scripts/test_variant_matrix_poc.py
Exit 0 = semua PASS.
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
import httpx
from motor.motor_asyncio import AsyncIOMotorClient

from services.product_io import clean_variants, gen_variant_sku
from services.product_import import suggest_mapping, validate_and_group

API = os.environ.get("API_BASE", "http://localhost:8001").rstrip("/")
MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "test_database")
ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "admin@collectorparfum.id")
ADMIN_PASS = os.environ.get("ADMIN_PASS", "Admin#2026")
G, Y, R, B, X = "\033[92m", "\033[93m", "\033[91m", "\033[1m", "\033[0m"
passed = failed = 0
ADDR = {"name": "POC", "phone": "0811", "street": "Jl. Test", "city": "Jakarta",
        "province": "DKI", "postal": "10000", "label": "Rumah"}


def ok(m):
    global passed
    passed += 1
    print(f"  {G}[OK]{X} {m}")


def bad(m):
    global failed
    failed += 1
    print(f"  {R}[FAIL]{X} {m}")


async def login(c):
    r = await c.post(f"{API}/api/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASS})
    r.raise_for_status()
    return r.json()["token"]


async def cleanup(db, slugs, extra_ids=None):
    for s in slugs:
        await db.products.delete_many({"slug": {"$regex": f"^{s}"}})
    for pid in (extra_ids or []):
        await db.products.delete_one({"id": pid})


async def test_pure_funcs():
    print(f"\n{B}D. Smart import pure functions{X}")
    # 1) mapping cerdas: header campur Indonesia/Inggris & tak baku
    headers = ["Nama Produk", "Kategori", "Tipe Varian", "Ukuran (ml)", "Harga Jual",
               "Harga Coret", "Stok", "SKU", "Gender", "Best Seller", "Deskripsi"]
    m = suggest_mapping(headers)
    checks = {
        "name": "Nama Produk", "category": "Kategori", "variant_type": "Tipe Varian",
        "variant_ml": "Ukuran (ml)", "variant_price": "Harga Jual",
        "variant_compare_at_price": "Harga Coret", "variant_stock": "Stok",
        "variant_sku": "SKU", "gender": "Gender", "best_seller": "Best Seller",
        "description": "Deskripsi",
    }
    good = all(m.get(k) == v for k, v in checks.items())
    if good:
        ok(f"suggest_mapping mencocokkan {len(checks)} kolom non-baku dengan benar")
    else:
        bad(f"suggest_mapping salah: {[(k, m.get(k)) for k in checks if m.get(k) != checks[k]]}")

    # 2) mapping header ENGLISH murni
    m2 = suggest_mapping(["slug", "name", "category", "type", "ml", "price", "stock", "sku"])
    if m2.get("variant_ml") == "ml" and m2.get("variant_price") == "price" and m2.get("variant_type") == "type":
        ok("suggest_mapping menangani header English (ml/price/type/stock/sku)")
    else:
        bad(f"suggest_mapping English gagal: {m2}")

    # 3) validate_and_group: baris valid + invalid + duplikat varian
    rows = [
        {"Nama Produk": "Aroma Uji", "Kategori": "amber", "Tipe Varian": "Standard",
         "Ukuran (ml)": "50 ml", "Harga Jual": "Rp 350.000", "Stok": "10", "Gender": "Pria"},
        {"Nama Produk": "Aroma Uji", "Kategori": "amber", "Tipe Varian": "Premium",
         "Ukuran (ml)": "50", "Harga Jual": "450000", "Stok": "5", "Gender": ""},
        {"Nama Produk": "", "Kategori": "amber", "Tipe Varian": "", "Ukuran (ml)": "30",
         "Harga Jual": "200000", "Stok": "3"},                       # error: nama kosong
        {"Nama Produk": "Salah Kategori", "Kategori": "tidakada", "Ukuran (ml)": "50",
         "Harga Jual": "100000", "Stok": "1"},                        # error: kategori tak dikenal
        {"Nama Produk": "Aroma Uji", "Kategori": "amber", "Tipe Varian": "Standard",
         "Ukuran (ml)": "50", "Harga Jual": "355000", "Stok": "2"},   # error: duplikat (Standard,50)
    ]
    cats = {"amber", "floral", "woody"}
    products, reports = validate_and_group(rows, m, cats)
    n_ok = sum(1 for r in reports if r["status"] == "ok")
    n_err = sum(1 for r in reports if r["status"] == "error")
    if n_ok == 2 and n_err == 3:
        ok(f"validate_and_group: 2 baris valid, 3 error (row-level) sesuai harapan")
    else:
        bad(f"validate_and_group hitungan salah: ok={n_ok} err={n_err} reports={[(r['row'], r['status'], r['errors']) for r in reports]}")
    # 1 produk 'Aroma Uji' dengan 2 varian (Standard 50 + Premium 50)
    prod = next((p for p in products if p["name"] == "Aroma Uji"), None)
    if prod and len(prod["volumes"]) == 2 and prod["gender"] == "Pria":
        ok("validate_and_group mengelompokkan 2 varian ke 1 produk + gender default")
    else:
        bad(f"grouping salah: {products}")

    # 4) clean_variants + auto-SKU unik & (type,ml) unik
    try:
        cv = clean_variants([
            {"type": "Standard", "ml": 50, "price": 100000, "stock": 5},
            {"type": "Premium", "ml": 50, "price": 150000, "stock": 3},
        ], product_name="Noir Oud")
        skus = {v["sku"] for v in cv}
        if len(cv) == 2 and len(skus) == 2:
            ok(f"clean_variants auto-SKU unik: {sorted(skus)}")
        else:
            bad(f"clean_variants SKU tidak unik: {cv}")
    except Exception as e:
        bad(f"clean_variants error tak terduga: {e}")

    try:
        clean_variants([
            {"type": "Standard", "ml": 50, "price": 100000, "stock": 5},
            {"type": "Standard", "ml": 50, "price": 150000, "stock": 3},
        ])
        bad("clean_variants TIDAK menolak duplikat (type,ml)")
    except ValueError:
        ok("clean_variants menolak duplikat (type,ml)")


async def test_admin_and_orders(c, db, token):
    h = {"Authorization": f"Bearer {token}"}

    # A. Create TYPED product via admin API
    print(f"\n{B}A. Create produk TYPED (Standard/Premium × ukuran) via admin API{X}")
    typed = {
        "name": "POC Typed Parfum", "category": "amber", "concentration": "EDP", "gender": "Unisex",
        "volumes": [
            {"type": "Standard", "ml": 30, "price": 200000, "stock": 10},
            {"type": "Standard", "ml": 50, "price": 300000, "stock": 8, "compare_at_price": 380000},
            {"type": "Premium", "ml": 30, "price": 260000, "stock": 6},
            {"type": "Premium", "ml": 50, "price": 360000, "stock": 5},
        ],
    }
    r = await c.post(f"{API}/api/admin/products", json=typed, headers=h)
    if r.status_code != 200:
        bad(f"create typed gagal: {r.status_code} {r.text[:200]}")
        return None, None
    prod = r.json()
    typed_slug = prod["slug"]
    vols = prod["volumes"]
    has_types = {v.get("type") for v in vols} == {"Standard", "Premium"}
    all_sku = all(v.get("sku") for v in vols)
    min_price_ok = prod["price"] == 200000
    if len(vols) == 4 and has_types and all_sku and min_price_ok:
        ok(f"typed product OK: 4 varian, tipe {sorted({v['type'] for v in vols})}, SKU auto, harga 'mulai dari'={prod['price']}")
    else:
        bad(f"typed product invalid: types={has_types} sku={all_sku} price={prod['price']} vols={vols}")

    # duplicate (type,ml) ditolak 400
    dup = dict(typed)
    dup["name"] = "POC Dup"
    dup["volumes"] = [
        {"type": "Standard", "ml": 50, "price": 300000, "stock": 8},
        {"type": "Standard", "ml": 50, "price": 320000, "stock": 2},
    ]
    rd = await c.post(f"{API}/api/admin/products", json=dup, headers=h)
    if rd.status_code == 400:
        ok("admin menolak duplikat (type,ml) -> 400")
    else:
        bad(f"admin TIDAK menolak duplikat: {rd.status_code}")

    # B. Typeless product (backward compat)
    print(f"\n{B}B. Create produk TYPELESS (satu dimensi ukuran){X}")
    typeless = {
        "name": "POC Typeless Parfum", "category": "floral", "concentration": "EDT", "gender": "Wanita",
        "volumes": [
            {"ml": 30, "price": 150000, "stock": 20},
            {"ml": 50, "price": 250000, "stock": 15},
        ],
    }
    r2 = await c.post(f"{API}/api/admin/products", json=typeless, headers=h)
    if r2.status_code == 200 and all(v.get("type") == "" for v in r2.json()["volumes"]):
        ok("typeless product OK (type='' untuk semua varian)")
    else:
        bad(f"typeless product gagal: {r2.status_code} {r2.text[:150]}")
    typeless_slug = r2.json().get("slug") if r2.status_code == 200 else None

    # Public read menampilkan type + sku
    pr = await c.get(f"{API}/api/products/{typed_slug}")
    if pr.status_code == 200 and all("sku" in v and "type" in v for v in pr.json()["volumes"]):
        ok("GET /api/products/{slug} publik menampilkan type + sku per varian")
    else:
        bad(f"public read varian kurang field: {pr.status_code}")

    # C. Order snapshot membawa variant_type + sku (Premium 50)
    print(f"\n{B}C. Order snapshot membawa variant_type + sku{X}")
    prod_id = prod["id"]
    order_payload = {
        "items": [{"product_id": prod_id, "variant_type": "Premium", "volume_ml": 50, "quantity": 1}],
        "address": ADDR, "shipping_id": "jne-reg", "payment": {"group": "transfer", "method_id": "bca"},
    }
    ro = await c.post(f"{API}/api/orders", json=order_payload)
    if ro.status_code == 200:
        item = ro.json()["items"][0]
        if item.get("variant_type") == "Premium" and item.get("sku") and item.get("unit_price") == 360000:
            ok(f"order item snapshot: type=Premium, sku={item['sku']}, unit_price=360000")
        else:
            bad(f"order snapshot varian salah: {item}")
        await db.orders.delete_one({"code": ro.json()["code"]})
        # restore stock for cleanliness
        await db.products.update_one({"id": prod_id, "volumes": {"$elemMatch": {"type": "Premium", "ml": 50}}},
                                     {"$inc": {"volumes.$.stock": 1}})
    else:
        bad(f"create order typed gagal: {ro.status_code} {ro.text[:200]}")

    # order dengan tipe SALAH -> 400 (varian tak tersedia)
    bad_payload = dict(order_payload)
    bad_payload["items"] = [{"product_id": prod_id, "variant_type": "Deluxe", "volume_ml": 50, "quantity": 1}]
    rb = await c.post(f"{API}/api/orders", json=bad_payload)
    if rb.status_code == 400:
        ok("order dengan tipe tak dikenal -> 400 (varian tak tersedia)")
    else:
        bad(f"order tipe salah TIDAK 400: {rb.status_code}")

    return typed_slug, typeless_slug


async def test_anti_oversell_by_type(c, db):
    """Standard 50 stok=1, Premium 50 stok=5. N order Standard 50 paralel:
    tepat 1 sukses, stok Standard=0, stok Premium TETAP 5 (tak menyeberang tipe)."""
    print(f"\n{B}C2. Anti-oversell keyed by (type, ml) — tak menyeberang tipe{X}")
    PID = "prd_poc_oversell"
    await db.products.delete_one({"id": PID})
    await db.products.insert_one({
        "id": PID, "slug": "poc-oversell", "name": "POC Oversell", "brand": "Collector",
        "category": "amber", "concentration": "EDP", "gender": "Unisex", "price": 100000,
        "compare_at_price": None, "best_seller": False, "is_new": False, "tags": [],
        "volumes": [
            {"type": "Standard", "ml": 50, "price": 100000, "stock": 1, "sku": "POC-STD-50ML", "compare_at_price": None},
            {"type": "Premium", "ml": 50, "price": 150000, "stock": 5, "sku": "POC-PRM-50ML", "compare_at_price": None},
        ],
        "notes": {"top": [], "heart": [], "base": []}, "description": "synthetic",
        "images": [], "video_url": None, "seo": {}, "rating_avg": 0.0, "rating_count": 0,
        "status": "active",
    })
    N = 12
    payload = {"items": [{"product_id": PID, "variant_type": "Standard", "volume_ml": 50, "quantity": 1}],
               "address": ADDR, "shipping_id": "jne-reg", "payment": {"group": "transfer", "method_id": "bca"}}

    async def shot():
        async with httpx.AsyncClient() as cc:
            try:
                r = await cc.post(f"{API}/api/orders", json=payload, timeout=25)
                return r.status_code, (r.json() if r.status_code == 200 else None)
            except Exception:
                return -1, None

    res = await asyncio.gather(*[shot() for _ in range(N)])
    succ = [j for sc, j in res if sc == 200 and j]
    err5 = sum(1 for sc, _ in res if sc >= 500)
    doc = await db.products.find_one({"id": PID}, {"volumes": 1})
    std = next(v["stock"] for v in doc["volumes"] if v["type"] == "Standard")
    prm = next(v["stock"] for v in doc["volumes"] if v["type"] == "Premium")
    for j in succ:
        await db.orders.delete_one({"code": j["code"]})
    await db.products.delete_one({"id": PID})

    if len(succ) == 1:
        ok(f"tepat 1/{N} order Standard sukses (anti-oversell)")
    else:
        bad(f"OVERSELL: {len(succ)} sukses (harus 1)")
    if std == 0:
        ok("stok Standard 50 = 0 (tak negatif)")
    else:
        bad(f"stok Standard 50 = {std} (harus 0)")
    if prm == 5:
        ok("stok Premium 50 TETAP 5 (tak menyeberang tipe — disambiguasi (type,ml) benar)")
    else:
        bad(f"stok Premium 50 = {prm} (harus 5; kebocoran antar-tipe!)")
    if err5 == 0:
        ok("tak ada 5xx saat balapan")
    else:
        bad(f"{err5} × 5xx saat balapan")


async def main():
    print(f"\n{B}{'='*64}{X}\n  POC VARIANT MATRIX (Type × Size) + SMART IMPORT  API={API}\n{B}{'='*64}{X}")
    db = AsyncIOMotorClient(MONGO_URL)[DB_NAME]
    try:
        async with httpx.AsyncClient(timeout=25) as c:
            if (await c.get(f"{API}/api/", timeout=5)).status_code >= 500:
                print(f"{R}Backend 5xx{X}"); return 1
            token = await login(c)
            await test_pure_funcs()
            typed_slug, typeless_slug = await test_admin_and_orders(c, db, token)
            await test_anti_oversell_by_type(c, db)
            # cleanup produk POC
            await cleanup(db, ["poc-typed-parfum", "poc-typeless-parfum", "poc-dup"])
    finally:
        pass
    print(f"\n{B}{'='*64}{X}\n  {G}passed={passed}{X}  {R}failed={failed}{X}\n{B}{'='*64}{X}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
