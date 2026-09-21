#!/usr/bin/env python3
"""test_e4_core.py — POC CORE E4 (Customer Account). PROVE-BEFORE-BUILD.

  T1 Profil: update name/phone; response TANPA password_hash (BR-1).
  T2 Alamat single-default (INV-A1): alamat pertama auto-default; default kedua memindah default;
     set_default eksplisit; delete default -> promosikan; SELALU <=1 default.
  T3 IDOR alamat (RC-E10): user B PUT/DELETE alamat user A -> 404.
  T4 Wishlist: toggle add/remove, DEDUPE, FK reject produk hantu (400), merge union idempotent.
  T5 Auth wajib: endpoint akun tanpa Bearer -> 401.

Self-cleaning. Usage: cd /app && python scripts/test_e4_core.py
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
CUST = {"email": "customer@collectorparfum.id", "password": "Customer#2026"}
ADMIN = {"email": "admin@collectorparfum.id", "password": "Admin#2026"}
G, R, B, X = "\033[92m", "\033[91m", "\033[1m", "\033[0m"
passed = failed = 0
ADDR = {"name": "A", "phone": "0811", "street": "Jl 1", "city": "Jakarta", "province": "DKI", "postal": "10000", "label": "Rumah"}


def ok(m):
    global passed
    passed += 1
    print(f"  {G}[PASS]{X} {m}")


def bad(m):
    global failed
    failed += 1
    print(f"  {R}[FAIL]{X} {m}")


async def login(c, creds):
    r = await c.post(f"{API}/api/auth/login", json=creds, timeout=15)
    return r.json()["token"] if r.status_code == 200 else None


async def default_count(db, uid):
    return await db.addresses.count_documents({"user_id": uid, "is_default": True})


async def main():
    print(f"\n{B}{'='*60}{X}\n  TEST E4 CORE (Customer Account)  API={API}\n{B}{'='*60}{X}")
    db = AsyncIOMotorClient(MONGO_URL)[DB_NAME]
    async with httpx.AsyncClient() as c:
        try:
            if (await c.get(f"{API}/api/", timeout=5)).status_code >= 500:
                raise Exception()
        except Exception:
            print(f"{R}Backend mati.{X}")
            return 1
        ta = await login(c, CUST)
        tb = await login(c, ADMIN)
        ha = {"Authorization": f"Bearer {ta}"}
        hb = {"Authorization": f"Bearer {tb}"}
        me = (await c.get(f"{API}/api/auth/me", headers=ha)).json()
        uid = me["id"]
        # bersihkan state awal
        await db.addresses.delete_many({"user_id": uid})
        await db.wishlists.delete_many({"user_id": uid})

        # T1 profil
        print(f"\n{B}T1 profil{X}")
        r = await c.put(f"{API}/api/account/profile", headers=ha, json={"name": "Kolektor Demo", "phone": "08123"})
        if r.status_code == 200 and r.json().get("phone") == "08123" and "password_hash" not in r.json():
            ok("update profil + tanpa password_hash")
        else:
            bad(f"profil: {r.status_code} {r.text[:100]}")

        # T2 single default
        print(f"\n{B}T2 alamat single-default (INV-A1){X}")
        a1 = (await c.post(f"{API}/api/addresses", headers=ha, json={**ADDR, "name": "Addr1"})).json()
        if a1.get("is_default") is True:
            ok("alamat pertama auto-default")
        else:
            bad("alamat pertama tidak default")
        a2 = (await c.post(f"{API}/api/addresses", headers=ha, json={**ADDR, "name": "Addr2", "is_default": True})).json()
        dc = await default_count(db, uid)
        a1r = await db.addresses.find_one({"id": a1["id"]})
        if a2.get("is_default") and not a1r.get("is_default") and dc == 1:
            ok("default kedua memindah default (tepat 1 default)")
        else:
            bad(f"default drift: count={dc}")
        # set default balik ke a1
        await c.post(f"{API}/api/addresses/{a1['id']}/default", headers=ha)
        if await default_count(db, uid) == 1 and (await db.addresses.find_one({"id": a1["id"]}))["is_default"]:
            ok("set_default eksplisit → tepat 1 default")
        else:
            bad("set_default gagal")
        # update a2 tanpa default → tetap <=1
        await c.put(f"{API}/api/addresses/{a2['id']}", headers=ha, json={**ADDR, "name": "Addr2b", "is_default": False})
        if await default_count(db, uid) == 1:
            ok("update non-default → tetap ≤1 default")
        else:
            bad(f"INV-A1 rusak setelah update: {await default_count(db, uid)}")
        # delete default a1 → promote
        await c.delete(f"{API}/api/addresses/{a1['id']}", headers=ha)
        if await db.addresses.count_documents({"user_id": uid}) == 1 and await default_count(db, uid) == 1:
            ok("hapus default → promosikan alamat tersisa")
        else:
            bad(f"promote gagal: total={await db.addresses.count_documents({'user_id': uid})} def={await default_count(db, uid)}")

        # T3 IDOR
        print(f"\n{B}T3 IDOR alamat (RC-E10){X}")
        victim = (await c.post(f"{API}/api/addresses", headers=ha, json={**ADDR, "name": "Victim"})).json()
        rb_put = await c.put(f"{API}/api/addresses/{victim['id']}", headers=hb, json={**ADDR, "name": "Hacked"})
        rb_del = await c.delete(f"{API}/api/addresses/{victim['id']}", headers=hb)
        if rb_put.status_code == 404 and rb_del.status_code == 404:
            ok("user B PUT/DELETE alamat user A → 404")
        else:
            bad(f"IDOR bocor: PUT={rb_put.status_code} DEL={rb_del.status_code}")
        still = await db.addresses.find_one({"id": victim["id"]})
        if still and still["name"] == "Victim":
            ok("alamat korban tak berubah")
        else:
            bad("alamat korban termodifikasi/hilang")

        # T4 wishlist
        print(f"\n{B}T4 wishlist (dedupe + FK + merge){X}")
        prods = await db.products.find({"status": "active"}, {"id": 1}).to_list(5)
        p1, p2, p3 = prods[0]["id"], prods[1]["id"], prods[2]["id"]
        r1 = (await c.post(f"{API}/api/wishlist/toggle", headers=ha, json={"product_id": p1})).json()
        r2 = (await c.post(f"{API}/api/wishlist/toggle", headers=ha, json={"product_id": p1})).json()  # remove
        if p1 in r1["product_ids"] and p1 not in r2["product_ids"]:
            ok("toggle add/remove")
        else:
            bad(f"toggle salah: {r1} {r2}")
        # add p1, p2
        await c.post(f"{API}/api/wishlist/toggle", headers=ha, json={"product_id": p1})
        await c.post(f"{API}/api/wishlist/toggle", headers=ha, json={"product_id": p2})
        ghost = await c.post(f"{API}/api/wishlist/toggle", headers=ha, json={"product_id": "prd_ghost_x"})
        if ghost.status_code == 400:
            ok("FK: produk hantu ditolak (400)")
        else:
            bad(f"FK: produk hantu HTTP {ghost.status_code}")
        # merge dgn duplikat + p3
        merged = (await c.post(f"{API}/api/wishlist/merge", headers=ha, json={"product_ids": [p1, p3, p3, "prd_ghost_x"]})).json()
        ids = merged["product_ids"]
        if sorted(ids) == sorted({p1, p2, p3}) and len(ids) == len(set(ids)):
            ok(f"merge union idempotent + dedupe + drop-FK ({len(ids)} item)")
        else:
            bad(f"merge salah: {ids}")

        # T5 auth wajib
        print(f"\n{B}T5 auth wajib{X}")
        codes = []
        for ep, m in [("/api/addresses", "get"), ("/api/wishlist", "get"), ("/api/account/profile", "put")]:
            fn = getattr(c, m)
            rr = await (fn(f"{API}{ep}", json={}) if m == "put" else fn(f"{API}{ep}"))
            codes.append(rr.status_code)
        if all(x == 401 for x in codes):
            ok("semua endpoint akun tanpa Bearer → 401")
        else:
            bad(f"auth guard bocor: {codes}")

        # cleanup
        await db.addresses.delete_many({"user_id": uid})
        await db.wishlists.delete_many({"user_id": uid})
    print(f"\n{B}{'='*60}{X}\n  {G}PASS {passed}{X} | {R}FAIL {failed}{X}\n{B}{'='*60}{X}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
