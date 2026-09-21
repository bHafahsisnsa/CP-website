#!/usr/bin/env python3
"""test_e5_core.py — POC CORE E5 (Admin Backoffice). PROVE-BEFORE-BUILD.

  T1 RBAC (RC-E10): /api/admin/* tanpa token -> 401; token customer -> 403.
  T2 Dashboard (BR-1): agregat revenue/orders_by_status/active_products/low_stock.
  T3 Produk CRUD (BR-2): create; varian ml duplikat -> 400; compare_at_price<=price -> 400;
     update; archive (soft-delete, status=archived, TIDAK terhapus, INV-M2); restore.
  T4 Kategori CRUD (BR-3): create; delete diblok bila dipakai produk (400); delete bebas OK.
  T5 Voucher CRUD (BR-4): percent value>100 -> 400; create; used_count read-only saat update; delete.
  T6 Proses pesanan (BR-6): status HANYA via transition_order — ilegal (pending->shipped) -> 400;
     legal (pending->paid) OK. INV-M3: edit harga produk TIDAK mengubah snapshot order.
  T7 Moderasi ulasan (BR-5): hide review published -> rating produk recompute (INV-C3).
  T8 Media (BR-8): POST media -> muncul di list.
  T9 Audit (INV-M1): setiap mutasi admin menulis audit_logs.

Self-cleaning. Usage: cd /app && python scripts/test_e5_core.py
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
G, R, Y, B, X = "\033[92m", "\033[91m", "\033[93m", "\033[1m", "\033[0m"
passed = failed = 0
ADDR = {"name": "Admin Test", "phone": "0811", "street": "Jl Uji", "city": "Jakarta",
        "province": "DKI", "postal": "10000", "label": "Rumah"}


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


def _product_payload(name, price1=120000, price2=190000, cap=None):
    p = {
        "name": name, "brand": "Collector", "category": "amber",
        "concentration": "EDP", "gender": "Unisex",
        "best_seller": False, "is_new": True, "tags": ["uji", "e5"],
        "volumes": [{"ml": 30, "price": price1, "stock": 9},
                    {"ml": 50, "price": price2, "stock": 6}],
        "notes": {"top": ["Bergamot"], "heart": ["Oud"], "base": ["Musk"]},
        "description": "Produk uji E5.", "status": "active",
    }
    if cap is not None:
        p["compare_at_price"] = cap
    return p


async def main():
    global passed
    print(f"\n{B}{'='*64}{X}\n  TEST E5 CORE (Admin Backoffice)  API={API}\n{B}{'='*64}{X}")
    db = AsyncIOMotorClient(MONGO_URL)[DB_NAME]
    created = {"products": [], "categories": [], "vouchers": [], "orders": [], "media": []}
    async with httpx.AsyncClient() as c:
        try:
            if (await c.get(f"{API}/api/", timeout=5)).status_code >= 500:
                raise Exception()
        except Exception:
            print(f"{R}Backend mati.{X}")
            return 1
        tc = await login(c, CUST)
        ta = await login(c, ADMIN)
        hc = {"Authorization": f"Bearer {tc}"}
        ha = {"Authorization": f"Bearer {ta}"}

        # ---------- T1 RBAC ----------
        print(f"\n{B}T1 RBAC (/api/admin/* dijaga){X}")
        routes = ["/api/admin/dashboard", "/api/admin/products", "/api/admin/orders",
                  "/api/admin/vouchers", "/api/admin/categories", "/api/admin/media"]
        no_tok = [(await c.get(f"{API}{p}")).status_code for p in routes]
        cust_tok = [(await c.get(f"{API}{p}", headers=hc)).status_code for p in routes]
        if all(s == 401 for s in no_tok):
            ok("tanpa token → 401 di semua route admin")
        else:
            bad(f"tanpa token bocor: {dict(zip(routes, no_tok))}")
        if all(s == 403 for s in cust_tok):
            ok("token customer → 403 di semua route admin (no escalation)")
        else:
            bad(f"customer escalation: {dict(zip(routes, cust_tok))}")

        # ---------- T2 Dashboard ----------
        print(f"\n{B}T2 Dashboard (BR-1){X}")
        d = (await c.get(f"{API}/api/admin/dashboard", headers=ha)).json()
        if isinstance(d.get("active_products"), int) and d["active_products"] >= 1 \
                and "orders_by_status" in d and isinstance(d.get("low_stock"), list):
            ok(f"dashboard agregat (active={d['active_products']}, revenue={d['revenue']})")
        else:
            bad(f"dashboard tidak lengkap: {str(d)[:160]}")

        # ---------- T3 Produk CRUD ----------
        print(f"\n{B}T3 Produk CRUD (BR-2){X}")
        # varian ml duplikat -> 400
        dup = _product_payload("Uji Dup")
        dup["volumes"] = [{"ml": 30, "price": 100000, "stock": 3},
                          {"ml": 30, "price": 120000, "stock": 2}]
        r = await c.post(f"{API}/api/admin/products", headers=ha, json=dup)
        ok("varian ml duplikat → 400") if r.status_code == 400 else bad(f"dup ml HTTP {r.status_code}")
        # compare_at_price <= price -> 400
        r = await c.post(f"{API}/api/admin/products", headers=ha, json=_product_payload("Uji Cap", cap=50000))
        ok("compare_at_price<=price → 400") if r.status_code == 400 else bad(f"cap HTTP {r.status_code}")
        # create valid
        r = await c.post(f"{API}/api/admin/products", headers=ha, json=_product_payload("Uji E5 Produk", cap=250000))
        if r.status_code == 200:
            prod = r.json()
            created["products"].append(prod["id"])
            good = prod["price"] == 120000 and prod["status"] == "active" and prod["slug"]
            ok(f"create produk (slug={prod['slug']}, price={prod['price']})") if good else bad(f"create field salah: {prod}")
        else:
            bad(f"create produk HTTP {r.status_code} {r.text[:120]}")
            prod = None
        if prod:
            pid = prod["id"]
            # update
            upd = _product_payload("Uji E5 Produk EDIT", price1=130000, cap=300000)
            r = await c.put(f"{API}/api/admin/products/{pid}", headers=ha, json=upd)
            if r.status_code == 200 and r.json()["name"] == "Uji E5 Produk EDIT" and r.json()["price"] == 130000:
                ok("update produk (nama + harga varian utama)")
            else:
                bad(f"update HTTP {r.status_code} {r.text[:120]}")
            # archive (soft-delete)
            r = await c.delete(f"{API}/api/admin/products/{pid}", headers=ha)
            doc = await db.products.find_one({"id": pid})
            if r.status_code == 200 and doc and doc.get("status") == "archived":
                ok("archive → status=archived, dokumen TIDAK terhapus (INV-M2)")
            else:
                bad(f"archive gagal: HTTP {r.status_code} doc={'ada' if doc else 'HILANG'}")
            # archived tak muncul di storefront publik
            pub = await c.get(f"{API}/api/products/{prod['slug']}")
            ok("produk archived → 404 di storefront publik") if pub.status_code == 404 else bad(f"archived masih publik: {pub.status_code}")
            # restore
            r = await c.post(f"{API}/api/admin/products/{pid}/restore", headers=ha)
            doc = await db.products.find_one({"id": pid})
            ok("restore → status=active") if (r.status_code == 200 and doc.get("status") == "active") else bad("restore gagal")

        # ---------- T4 Kategori CRUD ----------
        print(f"\n{B}T4 Kategori CRUD (BR-3){X}")
        r = await c.post(f"{API}/api/admin/categories", headers=ha,
                         json={"name": "Uji Kategori E5", "desc": "kat uji", "active": True})
        if r.status_code == 200:
            cat = r.json()
            created["categories"].append(cat["id"])
            ok(f"create kategori (slug={cat['slug']})")
            # delete kategori bebas (belum dipakai) OK
            rd = await c.delete(f"{API}/api/admin/categories/{cat['id']}", headers=ha)
            if rd.status_code == 200:
                created["categories"].remove(cat["id"])
                ok("delete kategori tak-terpakai → OK")
            else:
                bad(f"delete kategori HTTP {rd.status_code}")
        else:
            bad(f"create kategori HTTP {r.status_code} {r.text[:120]}")
        # delete kategori dipakai produk → 400 (pakai 'amber' yang dipakai seed/produk uji)
        amber = await db.categories.find_one({"slug": "amber"})
        if amber:
            rd = await c.delete(f"{API}/api/admin/categories/{amber['id']}", headers=ha)
            ok("delete kategori terpakai produk → 400 (FK-safe)") if rd.status_code == 400 else bad(f"FK kategori HTTP {rd.status_code}")

        # ---------- T5 Voucher CRUD ----------
        print(f"\n{B}T5 Voucher CRUD (BR-4){X}")
        r = await c.post(f"{API}/api/admin/vouchers", headers=ha,
                         json={"code": "E5PERCENT", "type": "percent", "value": 150, "label": "x"})
        ok("percent value>100 → 400") if r.status_code in (400, 422) else bad(f"percent bound HTTP {r.status_code}")
        r = await c.post(f"{API}/api/admin/vouchers", headers=ha,
                         json={"code": "e5test10", "type": "percent", "value": 10, "label": "Uji E5", "min_spend": 50000})
        if r.status_code == 200:
            v = r.json()
            created["vouchers"].append(v["id"])
            good = v["code"] == "E5TEST10" and v["used_count"] == 0
            ok("create voucher (code UPPERCASE, used_count=0)") if good else bad(f"voucher field: {v}")
            # tamper used_count via update → harus diabaikan (system-owned)
            await db.vouchers.update_one({"id": v["id"]}, {"$set": {"used_count": 7}})
            r2 = await c.put(f"{API}/api/admin/vouchers/{v['id']}", headers=ha,
                             json={"code": "E5TEST10", "type": "percent", "value": 15, "label": "Uji E5 Edit"})
            after = await db.vouchers.find_one({"id": v["id"]})
            if r2.status_code == 200 and after.get("used_count") == 7 and after.get("value") == 15:
                ok("update voucher pertahankan used_count (read-only) + ubah value")
            else:
                bad(f"used_count/update salah: {after.get('used_count')}/{after.get('value')}")
        else:
            bad(f"create voucher HTTP {r.status_code} {r.text[:120]}")

        # ---------- T6 Proses pesanan + INV-M3 ----------
        print(f"\n{B}T6 Proses pesanan via transition_order (BR-6) + INV-M3{X}")
        if prod:
            # customer buat order atas produk uji
            ship = await db.shipping_methods.find_one({"active": True})
            pay = await db.payment_methods.find_one({"group": "transfer", "active": True})
            body = {"items": [{"product_id": prod["id"], "volume_ml": 30, "quantity": 1}],
                    "address": ADDR, "shipping_id": ship["id"],
                    "payment": {"group": "transfer", "method_id": pay["id"]}}
            ro = await c.post(f"{API}/api/orders", headers=hc, json=body)
            if ro.status_code == 200:
                order = ro.json()
                code = order["code"]
                created["orders"].append(code)
                snap_price = order["items"][0]["unit_price"]
                # ilegal: pending -> shipped
                ill = await c.put(f"{API}/api/admin/orders/{code}/status", headers=ha, json={"status": "shipped"})
                ok("transisi ilegal pending→shipped → 400") if ill.status_code == 400 else bad(f"ilegal HTTP {ill.status_code}")
                # legal: pending -> paid
                leg = await c.put(f"{API}/api/admin/orders/{code}/status", headers=ha, json={"status": "paid"})
                ok("transisi legal pending→paid → 200 (paid)") if (leg.status_code == 200 and leg.json()["status"] == "paid") else bad(f"legal HTTP {leg.status_code}")
                # INV-M3: edit harga produk → snapshot order TAK berubah
                await c.put(f"{API}/api/admin/products/{prod['id']}", headers=ha,
                            json=_product_payload("Uji E5 Produk PRICE", price1=999000, cap=None))
                od = await db.orders.find_one({"code": code})
                if od["items"][0]["unit_price"] == snap_price:
                    ok(f"INV-M3 snapshot order imutabel (tetap {snap_price} walau produk diedit)")
                else:
                    bad(f"INV-M3 rusak: snapshot {od['items'][0]['unit_price']} != {snap_price}")
                # archive produk yang direferensikan order → tetap ada (INV-M2)
                await c.delete(f"{API}/api/admin/products/{prod['id']}", headers=ha)
                still = await db.products.find_one({"id": prod["id"]})
                ok("archive produk direferensikan order → tetap ada (INV-M2)") if still else bad("produk terhapus padahal direferensikan order")
            else:
                bad(f"buat order uji HTTP {ro.status_code} {ro.text[:140]}")

        # ---------- T7 Moderasi ulasan ----------
        print(f"\n{B}T7 Moderasi ulasan (BR-5) + recompute rating (INV-C3){X}")
        rev = await db.reviews.find_one({"status": "published", "product_id": {"$ne": None}})
        if rev:
            pid = rev["product_id"]
            before = await db.products.find_one({"id": pid}, {"rating_count": 1})
            bcount = int(before.get("rating_count", 0) or 0)
            rh = await c.put(f"{API}/api/admin/reviews/{rev['id']}/status", headers=ha, json={"status": "hidden"})
            after = await db.products.find_one({"id": pid}, {"rating_count": 1})
            acount = int(after.get("rating_count", 0) or 0)
            if rh.status_code == 200 and acount == bcount - 1:
                ok(f"hide ulasan → rating_count {bcount}→{acount} (recompute)")
            else:
                bad(f"moderasi/recompute salah: {bcount}->{acount} HTTP {rh.status_code}")
            # kembalikan
            await c.put(f"{API}/api/admin/reviews/{rev['id']}/status", headers=ha, json={"status": "published"})
            restored = await db.products.find_one({"id": pid}, {"rating_count": 1})
            ok("publish ulasan lagi → rating_count pulih") if int(restored.get("rating_count", 0) or 0) == bcount else bad("recompute tak pulih")
        else:
            print(f"  {Y}(tak ada review published untuk diuji){X}")

        # ---------- T8 Media ----------
        print(f"\n{B}T8 Media library (BR-8){X}")
        rm = await c.post(f"{API}/api/admin/media", headers=ha,
                          json={"kind": "image", "url": "https://example.com/uji-e5.jpg", "alt": "uji"})
        if rm.status_code == 200:
            med = rm.json()
            created["media"].append(med["id"])
            lst = (await c.get(f"{API}/api/admin/media", headers=ha)).json()
            ok("POST media → muncul di list") if any(m["id"] == med["id"] for m in lst) else bad("media tak muncul di list")
        else:
            bad(f"POST media HTTP {rm.status_code} {rm.text[:120]}")

        # ---------- T9 Audit INV-M1 ----------
        print(f"\n{B}T9 Audit trail (INV-M1){X}")
        entities = await db.audit_logs.distinct("entity")
        need = {"products", "categories", "vouchers", "orders", "reviews", "media_assets"}
        have = need & set(entities)
        if need.issubset(set(entities)):
            ok(f"audit_logs mencatat mutasi: {sorted(have)}")
        else:
            bad(f"INV-M1: audit kurang entity {sorted(need - set(entities))} (ada: {sorted(have)})")

        # ---------- Cleanup ----------
        for code in created["orders"]:
            o = await db.orders.find_one({"code": code})
            if o:
                try:
                    from services import stock
                    await stock.restore(db, o.get("items", []))
                except Exception:
                    pass
                await db.orders.delete_one({"code": code})
                await db.voucher_redemptions.delete_many({"order_code": code})
        for pid in created["products"]:
            await db.products.delete_one({"id": pid})
        for cid in created["categories"]:
            await db.categories.delete_one({"id": cid})
        for vid in created["vouchers"]:
            await db.vouchers.delete_one({"id": vid})
        for mid in created["media"]:
            await db.media_assets.delete_one({"id": mid})

    print(f"\n{B}{'='*64}{X}\n  {G}PASS {passed}{X} | {R}FAIL {failed}{X}\n{B}{'='*64}{X}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
