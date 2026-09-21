#!/usr/bin/env python3
"""test_e3_core.py — POC CORE E3 (Cart/Checkout/Orders). PROVE-BEFORE-BUILD.

Membuktikan inti write-path E3 bekerja & aman SEBELUM wiring UI penuh:
  T1  Happy order (guest): total == compute_pricing SSOT, stok turun, code CP########.
  T2  Anti-oversell: produk stok=1, N checkout PARALEL → tepat 1 sukses, stok akhir 0 (>=0).
  T3  Cancel (owner): stok DIKEMBALIKAN + status=cancelled (SM1, RC-E6).
  T4  State-machine (import SSOT): pending->shipped 400, pay cancelled 400, complete unpaid honest.
  T5  IDOR: user B TIDAK bisa baca order milik user A (404).
  T6  Voucher redemption atomik: order pakai WELCOME10 → used_count++ + redemption (CE1).
  T7  Adversarial: qty>stock → 409; produk/varian tak ada → 400; NEVER 5xx.

Self-cleaning: semua data sintetis dihapus di akhir → DB kembali pristine.
Usage: cd /app && python scripts/test_e3_core.py
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

from services.pricing import compute_pricing  # SSOT referensi
from services import variants as V  # SSOT model varian N-dimensi (derive volumes)

API = os.environ.get("API_BASE", "http://localhost:8001").rstrip("/")
MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "collector_parfum")
CUST = {"email": "customer@collectorparfum.id", "password": "Customer#2026"}
G, Y, R, B, X = "\033[92m", "\033[93m", "\033[91m", "\033[1m", "\033[0m"

passed = failed = 0
CREATED_ORDERS = []
SYNTH_PRODUCTS = []


def ok(m):
    global passed
    passed += 1
    print(f"  {G}[PASS]{X} {m}")


def bad(m):
    global failed
    failed += 1
    print(f"  {R}[FAIL]{X} {m}")


ADDR = {"name": "Uji Coba", "phone": "0811", "street": "Jl. Tes 1",
        "city": "Jakarta", "province": "DKI", "postal": "10000", "label": "Rumah"}


async def _login(client, creds):
    r = await client.post(f"{API}/api/auth/login", json=creds, timeout=15)
    if r.status_code == 200:
        return r.json().get("token")
    return None


async def _pick_product(db):
    """Ambil satu produk seeded + varian TYPELESS berstok memadai.

    SSOT stok kini `variants[]` (model N-dimensi); `volumes[]` di dokumen DB bisa stale.
    Karena itu derive volumes via V.serialize_product (SATU jalur dengan API)."""
    best = None
    async for d in db.products.find({"status": "active"}):
        p = V.serialize_product({k: v for k, v in d.items() if k != "_id"})
        vols = p.get("volumes") or []
        typeless = [v for v in vols if str(v.get("type", "") or "") == ""]
        if len(vols) >= 3 and typeless:
            return p, max(typeless, key=lambda v: v.get("stock", 0))
        if best is None and vols:
            best = (p, max(vols, key=lambda v: v.get("stock", 0)))
    return best


async def _stock(db, pid, ml):
    """Stok varian by ml — dibaca dari SSOT variants[] (derive), BUKAN volumes persisted."""
    doc = await db.products.find_one({"id": pid})
    if not doc:
        return None
    p = V.serialize_product({k: v for k, v in doc.items() if k != "_id"})
    vols = p.get("volumes") or []
    for v in vols:
        if int(v.get("ml") or 0) == int(ml) and str(v.get("type", "") or "") == "":
            return int(v.get("stock", 0))
    for v in vols:
        if int(v.get("ml") or 0) == int(ml):
            return int(v.get("stock", 0))
    return None


async def t1_happy(client, db):
    print(f"\n{B}T1 — Happy order (guest){X}")
    p, vol = await _pick_product(db)
    before = await _stock(db, p["id"], vol["ml"])
    payload = {
        "items": [{"product_id": p["id"], "volume_ml": vol["ml"], "quantity": 2}],
        "address": ADDR, "shipping_id": "jne-reg",
        "payment": {"group": "transfer", "method_id": "bca"},
    }
    r = await client.post(f"{API}/api/orders", json=payload, timeout=20)
    if r.status_code != 200:
        return bad(f"POST /orders HTTP {r.status_code}: {r.text[:150]}")
    o = r.json()
    CREATED_ORDERS.append(o["code"])
    exp = compute_pricing(
        [{"unit_price": vol["price"], "quantity": 2}],
        voucher=None, shipping={"price": 22000}, payment_group="transfer", cod_fee=0,
    )
    if o.get("total") == exp["total"] and o.get("subtotal") == exp["subtotal"]:
        ok(f"total server == compute_pricing ({o['total']})")
    else:
        bad(f"total drift: order={o.get('total')} exp={exp['total']}")
    if o.get("code", "").startswith("CP") and len(o.get("code", "")) == 10:
        ok(f"kode unik terformat: {o['code']}")
    else:
        bad(f"format kode salah: {o.get('code')}")
    after = await _stock(db, p["id"], vol["ml"])
    if after == before - 2:
        ok(f"stok turun {before} -> {after}")
    else:
        bad(f"stok tak konsisten: {before} -> {after}")
    if o.get("status") == "pending" and o.get("payment_status") == "belum_bayar":
        ok("status awal pending / belum_bayar")
    else:
        bad(f"status awal salah: {o.get('status')}/{o.get('payment_status')}")


async def t2_oversell(db):
    print(f"\n{B}T2 — Anti-oversell (N checkout paralel, stok=1){X}")
    pid = "prd_e3test_oversell"
    SYNTH_PRODUCTS.append(pid)
    await db.products.delete_one({"id": pid})
    await db.products.insert_one({
        "id": pid, "slug": "e3test-oversell", "name": "E3 Test Oversell",
        "brand": "Collector", "category": "amber", "concentration": "EDP", "gender": "Unisex",
        "price": 100000, "compare_at_price": None, "best_seller": False, "is_new": False,
        "tags": [], "volumes": [{"ml": 50, "price": 100000, "stock": 1}],
        "notes": {"top": [], "heart": [], "base": []}, "description": "synthetic",
        "images": [], "video_url": None, "seo": {}, "rating_avg": 0.0, "rating_count": 0,
        "status": "active",
    })
    N = 8
    payload = {
        "items": [{"product_id": pid, "volume_ml": 50, "quantity": 1}],
        "address": ADDR, "shipping_id": "jne-reg",
        "payment": {"group": "transfer", "method_id": "bca"},
    }

    async def _shot():
        async with httpx.AsyncClient() as c:
            try:
                r = await c.post(f"{API}/api/orders", json=payload, timeout=20)
                return r.status_code, (r.json() if r.status_code == 200 else None)
            except Exception as e:
                return -1, str(e)

    results = await asyncio.gather(*[_shot() for _ in range(N)])
    succ = [j for sc, j in results if sc == 200 and j]
    conflict = [sc for sc, _ in results if sc == 409]
    for j in succ:
        CREATED_ORDERS.append(j["code"])
    final = await _stock(db, pid, 50)
    if len(succ) == 1:
        ok(f"tepat 1 dari {N} checkout sukses (sisanya ditolak)")
    else:
        bad(f"OVERSELL: {len(succ)} sukses (harus 1). 409={len(conflict)}")
    if final == 0:
        ok("stok akhir = 0 (tak pernah negatif, INV-4)")
    else:
        bad(f"stok akhir {final} (harus 0)")
    if len(conflict) == N - 1:
        ok(f"{len(conflict)} checkout kalah balapan → 409 (bukan 5xx)")
    else:
        bad(f"jumlah 409 tak sesuai: {conflict}")


async def t3_cancel(client, db):
    print(f"\n{B}T3 — Cancel oleh pemilik → stok kembali (SM1){X}")
    token = await _login(client, CUST)
    if not token:
        return bad("login customer gagal")
    h = {"Authorization": f"Bearer {token}"}
    p, vol = await _pick_product(db)
    before = await _stock(db, p["id"], vol["ml"])
    payload = {
        "items": [{"product_id": p["id"], "volume_ml": vol["ml"], "quantity": 1}],
        "address": ADDR, "shipping_id": "jne-reg",
        "payment": {"group": "transfer", "method_id": "bca"},
    }
    r = await client.post(f"{API}/api/orders", json=payload, headers=h, timeout=20)
    if r.status_code != 200:
        return bad(f"create (auth) HTTP {r.status_code}")
    code = r.json()["code"]
    CREATED_ORDERS.append(code)
    mid = await _stock(db, p["id"], vol["ml"])
    rc = await client.post(f"{API}/api/orders/{code}/cancel", headers=h, timeout=20)
    if rc.status_code != 200 or rc.json().get("status") != "cancelled":
        return bad(f"cancel HTTP {rc.status_code}: {rc.text[:120]}")
    after = await _stock(db, p["id"], vol["ml"])
    if mid == before - 1 and after == before:
        ok(f"stok {before}->{mid}->(cancel)->{after} (dikembalikan)")
    else:
        bad(f"stok cancel tak konsisten: {before}->{mid}->{after}")


async def t4_state_machine(db):
    print(f"\n{B}T4 — State-machine SSOT (transition_order){X}")
    from services import orders as svc
    # SM2: pending -> shipped ilegal
    try:
        await svc.transition_order(db, {"code": "X", "status": "pending", "items": [],
                                        "paid_amount": 0, "total": 1000}, "shipped")
        bad("SM2 pending->shipped TIDAK ditolak")
    except svc.InvalidTransition:
        ok("SM2 pending->shipped ditolak (RC-E7)")
    # SM3: bayar/confirm order cancelled ilegal
    try:
        await svc.transition_order(db, {"code": "X", "status": "cancelled", "items": [],
                                        "paid_amount": 0, "total": 1000}, "paid")
        bad("SM3 cancelled->paid TIDAK ditolak")
    except svc.InvalidTransition:
        ok("SM3 aksi pada order terminal ditolak (RC-E8)")
    # SM4: complete order belum lunas → payment_status tetap jujur
    code = "CPTEST_SM4"
    await db.orders.delete_one({"code": code})
    await db.orders.insert_one({
        "id": "ord_test_sm4", "code": code, "user_id": None, "items": [],
        "subtotal": 100000, "discount": 0, "voucher_code": None, "shipping": {"price": 0},
        "payment": {"group": "transfer"}, "cod_fee": 0, "total": 100000, "paid_amount": 0,
        "status": "shipped", "payment_status": "belum_bayar",
    })
    order = await db.orders.find_one({"code": code})
    res = await svc.transition_order(db, order, "completed")
    if res.get("status") == "completed" and res.get("payment_status") in ("belum_bayar", "dp"):
        ok(f"SM4 complete unpaid → payment_status jujur ({res['payment_status']}, bukan lunas)")
    else:
        bad(f"SM4 payment drift: {res.get('payment_status')}")
    await db.orders.delete_one({"code": code})


async def t5_idor(client, db):
    print(f"\n{B}T5 — IDOR: user B tak bisa baca order user A{X}")
    token = await _login(client, CUST)
    h = {"Authorization": f"Bearer {token}"}
    p, vol = await _pick_product(db)
    payload = {
        "items": [{"product_id": p["id"], "volume_ml": vol["ml"], "quantity": 1}],
        "address": ADDR, "shipping_id": "jne-reg",
        "payment": {"group": "transfer", "method_id": "bca"},
    }
    r = await client.post(f"{API}/api/orders", json=payload, headers=h, timeout=20)
    code = r.json()["code"]
    CREATED_ORDERS.append(code)
    # user B (admin, beda user) coba baca
    bmail = {"email": "admin@collectorparfum.id", "password": "Admin#2026"}
    btok = await _login(client, bmail)
    rb = await client.get(f"{API}/api/orders/{code}", headers={"Authorization": f"Bearer {btok}"}, timeout=15)
    if rb.status_code == 404:
        ok("user B baca order user A → 404 (IDOR-safe)")
    else:
        bad(f"IDOR bocor: user B HTTP {rb.status_code}")
    # owner bisa baca
    ra = await client.get(f"{API}/api/orders/{code}", headers=h, timeout=15)
    if ra.status_code == 200 and ra.json().get("code") == code:
        ok("owner bisa baca order sendiri")
    else:
        bad(f"owner gagal baca: HTTP {ra.status_code}")


async def t6_voucher_redemption(client, db):
    print(f"\n{B}T6 — Redemption voucher atomik (CE1){X}")
    token = await _login(client, CUST)
    h = {"Authorization": f"Bearer {token}"}
    v_before = await db.vouchers.find_one({"code": "WELCOME10"})
    uc_before = int(v_before.get("used_count", 0))
    red_before = await db.voucher_redemptions.count_documents({"voucher_code": "WELCOME10"})
    p, vol = await _pick_product(db)
    payload = {
        "items": [{"product_id": p["id"], "volume_ml": vol["ml"], "quantity": 1}],
        "address": ADDR, "shipping_id": "jne-reg",
        "payment": {"group": "transfer", "method_id": "bca"},
        "voucher_code": "WELCOME10",
    }
    r = await client.post(f"{API}/api/orders", json=payload, headers=h, timeout=20)
    if r.status_code != 200:
        return bad(f"order+voucher HTTP {r.status_code}: {r.text[:150]}")
    o = r.json()
    CREATED_ORDERS.append(o["code"])
    exp_disc = round(vol["price"] * 10 / 100)
    if o.get("discount") == exp_disc and o.get("voucher_code") == "WELCOME10":
        ok(f"diskon 10% diterapkan server ({o['discount']})")
    else:
        bad(f"diskon salah: {o.get('discount')} exp {exp_disc}")
    v_after = await db.vouchers.find_one({"code": "WELCOME10"})
    red_after = await db.voucher_redemptions.count_documents({"voucher_code": "WELCOME10"})
    if int(v_after.get("used_count", 0)) == uc_before + 1 and red_after == red_before + 1:
        ok("used_count++ & voucher_redemptions++ (atomik, CE1)")
    else:
        bad(f"CE1 drift: used {uc_before}->{v_after.get('used_count')} red {red_before}->{red_after}")


async def t7_adversarial(client, db):
    print(f"\n{B}T7 — Adversarial (no 5xx){X}")
    p, vol = await _pick_product(db)
    # qty > stock (dalam batas bound le=999, tapi > stok tersedia → 409)
    huge = {"items": [{"product_id": p["id"], "volume_ml": vol["ml"], "quantity": 999}],
            "address": ADDR, "shipping_id": "jne-reg",
            "payment": {"group": "transfer", "method_id": "bca"}}
    r = await client.post(f"{API}/api/orders", json=huge, timeout=20)
    if r.status_code == 409:
        ok("qty>stok → 409 (bukan 5xx)")
    else:
        bad(f"qty>stok HTTP {r.status_code} (harus 409)")
    # qty di luar bound (>=1e6) → 422 validasi (bukan 5xx)
    absurd = {"items": [{"product_id": p["id"], "volume_ml": vol["ml"], "quantity": 9999999}],
              "address": ADDR, "shipping_id": "jne-reg",
              "payment": {"group": "transfer", "method_id": "bca"}}
    ra = await client.post(f"{API}/api/orders", json=absurd, timeout=20)
    if ra.status_code == 422:
        ok("qty absurd (>bound) → 422 validasi (numeric bound)")
    else:
        bad(f"qty absurd HTTP {ra.status_code} (harus 422)")
    # produk tak ada
    ghost = {"items": [{"product_id": "prd_ghost", "volume_ml": 50, "quantity": 1}],
             "address": ADDR, "shipping_id": "jne-reg",
             "payment": {"group": "transfer", "method_id": "bca"}}
    r2 = await client.post(f"{API}/api/orders", json=ghost, timeout=20)
    if r2.status_code == 400:
        ok("produk tak ada → 400")
    else:
        bad(f"produk ghost HTTP {r2.status_code} (harus 400)")
    # shipping invalid
    badship = {"items": [{"product_id": p["id"], "volume_ml": vol["ml"], "quantity": 1}],
               "address": ADDR, "shipping_id": "NGAWUR",
               "payment": {"group": "transfer", "method_id": "bca"}}
    r3 = await client.post(f"{API}/api/orders", json=badship, timeout=20)
    if r3.status_code == 400:
        ok("shipping invalid → 400")
    else:
        bad(f"shipping invalid HTTP {r3.status_code}")


async def cleanup(db):
    for code in set(CREATED_ORDERS):
        o = await db.orders.find_one({"code": code})
        if o:
            # kembalikan stok bila order belum cancelled (agar seed tetap pristine)
            if o.get("status") != "cancelled":
                from services import stock
                await stock.restore(db, o.get("items", []))
            # kompensasi voucher agar CE1 konsisten pasca-test
            vc = o.get("voucher_code")
            if vc:
                await db.vouchers.update_one({"code": vc, "used_count": {"$gt": 0}},
                                            {"$inc": {"used_count": -1}})
                await db.voucher_redemptions.delete_one({"order_code": code})
                # rilis juga slot per-user (jika ada) agar voucher_user_usage tak bocor
                if o.get("user_id"):
                    await db.voucher_user_usage.update_one(
                        {"voucher_code": vc, "user_id": o["user_id"], "count": {"$gt": 0}},
                        {"$inc": {"count": -1}},
                    )
            await db.orders.delete_one({"code": code})
    for pid in set(SYNTH_PRODUCTS):
        await db.products.delete_one({"id": pid})
    await db.orders.delete_many({"code": {"$regex": "^CPTEST"}})


async def main():
    print(f"\n{B}{'='*60}{X}\n  TEST E3 CORE (Cart/Checkout/Orders)  API={API}\n{B}{'='*60}{X}")
    client_db = AsyncIOMotorClient(MONGO_URL)
    db = client_db[DB_NAME]
    async with httpx.AsyncClient() as client:
        try:
            if (await client.get(f"{API}/api/", timeout=5)).status_code >= 500:
                raise Exception("5xx")
        except Exception:
            print(f"{R}Backend tidak berjalan.{X}")
            return 1
        try:
            await t1_happy(client, db)
            await t2_oversell(db)
            await t3_cancel(client, db)
            await t4_state_machine(db)
            await t5_idor(client, db)
            await t6_voucher_redemption(client, db)
            await t7_adversarial(client, db)
        finally:
            await cleanup(db)
    client_db.close()
    print(f"\n{B}{'='*60}{X}\n  {G}PASS {passed}{X} | {R}FAIL {failed}{X}\n{B}{'='*60}{X}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
