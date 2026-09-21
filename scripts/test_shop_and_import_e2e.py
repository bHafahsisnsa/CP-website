#!/usr/bin/env python3
"""test_shop_and_import_e2e.py — uji SATU jalan: (A) alur belanja end-to-end,
(B) wizard impor produk N-dimensi (option1..4_name/value) + round-trip export.

Jalankan: cd /app && python scripts/test_shop_and_import_e2e.py
Backend harus RUNNING (supervisorctl status backend).
"""
import io
import json
import os
import sys
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
BASE = os.environ.get("API_BASE", "http://localhost:8001") + "/api"
ADMIN = (os.environ.get("ADMIN_EMAIL", "admin@collectorparfum.id"),
         os.environ.get("ADMIN_PASS", "Admin#2026"))
CUST = (os.environ.get("CUST_EMAIL", "customer@collectorparfum.id"),
        os.environ.get("CUST_PASS", "Customer#2026"))

G, R, Y, C, B, X = "\033[92m", "\033[91m", "\033[93m", "\033[96m", "\033[1m", "\033[0m"
PASS, FAIL = [], []


def ok(name, extra=""):
    PASS.append(name)
    print(f"  {G}[PASS]{X} {name}" + (f"  {extra}" if extra else ""))


def bad(name, detail=""):
    FAIL.append((name, detail))
    print(f"  {R}[FAIL]{X} {name}\n         -> {detail}")


def check(cond, name, detail=""):
    ok(name) if cond else bad(name, detail)
    return bool(cond)


def hdr(t):
    print(f"\n{C}{B}{'=' * 74}\n  {t}\n{'=' * 74}{X}")


def req(method, path, token=None, **kw):
    h = kw.pop("headers", {}) or {}
    if token:
        h["Authorization"] = f"Bearer {token}"
    return requests.request(method, BASE + path, headers=h, timeout=40, **kw)


def login(email, password):
    r = req("POST", "/auth/login", json={"email": email, "password": password})
    if r.status_code != 200:
        return None, f"HTTP {r.status_code}: {r.text[:220]}"
    return (r.json() or {}).get("token"), None


# ════════════════════════════════════════════════════════════════════════
# A. ALUR BELANJA END-TO-END
# ════════════════════════════════════════════════════════════════════════
def pick_variant(prod):
    """Ambil varian pertama yang stoknya cukup."""
    for v in prod.get("variants") or []:
        if int(v.get("stock") or 0) >= 3:
            return v
    return (prod.get("variants") or [None])[0]


ADDR = {"name": "QA Tester", "phone": "0811222333", "street": "Jl. Uji Coba No. 1",
        "district": "Menteng", "city": "Jakarta Pusat", "province": "DKI Jakarta",
        "postal": "10310", "label": "Rumah"}


def test_shopping_flow():
    hdr("A. ALUR BELANJA: katalog -> PDP -> varian -> cart -> checkout -> pesanan")
    state = {}

    # A1 — katalog
    r = req("GET", "/products?limit=100")
    if not check(r.status_code == 200, "A1 GET /products 200", f"HTTP {r.status_code} {r.text[:180]}"):
        return state
    products = r.json()
    if not check(isinstance(products, list) and len(products) > 0,
                 "A2 katalog berisi produk", f"dapat {len(products) if isinstance(products, list) else products}"):
        return state
    print(f"       {len(products)} produk di katalog")

    # A3 — PDP detail via slug
    slug = products[0]["slug"]
    r = req("GET", f"/products/{slug}")
    if not check(r.status_code == 200, f"A3 GET /products/{slug} 200", f"HTTP {r.status_code} {r.text[:180]}"):
        return state
    prod = r.json()
    check(bool(prod.get("options")), "A4 PDP punya options[] (N-dimensi)", f"options={prod.get('options')}")
    check(bool(prod.get("variants")), "A5 PDP punya variants[]", f"variants={prod.get('variants')}")
    v = pick_variant(prod)
    if not check(v and v.get("sku"), "A6 varian punya SKU", f"variant={v}"):
        return state
    print(f"       produk='{prod['name']}' sku={v['sku']} harga={v.get('price')} stok={v.get('stock')}")
    state["prod"], state["variant"] = prod, v

    # A7 — PDP slug tidak ada -> 404
    r = req("GET", "/products/slug-yang-tidak-ada-xyz")
    check(r.status_code == 404, "A7 PDP slug tak dikenal -> 404", f"HTTP {r.status_code}")

    # A8 — login customer
    tok, err = login(*CUST)
    if not check(tok, "A8 login customer", err or "token kosong"):
        return state
    state["cust_token"] = tok

    # A9/A10 — server cart
    r = req("PUT", "/cart", token=tok, json={
        "items": [{"product_id": prod["id"], "sku": v["sku"], "quantity": 2}], "note": "uji QA"})
    check(r.status_code == 200, "A9 PUT /cart simpan item", f"HTTP {r.status_code} {r.text[:200]}")
    r = req("GET", "/cart", token=tok)
    cart = r.json() if r.status_code == 200 else {}
    check(r.status_code == 200 and len(cart.get("items") or []) == 1,
          "A10 GET /cart berisi 1 item", f"HTTP {r.status_code} {str(cart)[:200]}")

    # A11 — cart butuh login
    r = req("GET", "/cart")
    check(r.status_code in (401, 403), "A11 GET /cart tanpa token -> 401/403", f"HTTP {r.status_code}")

    # A12 — metode kirim & bayar
    r = req("GET", "/shipping-methods")
    ships = r.json() if r.status_code == 200 else []
    if not check(r.status_code == 200 and len(ships) > 0, "A12 GET /shipping-methods ada isi",
                 f"HTTP {r.status_code} {str(ships)[:180]}"):
        return state
    r = req("GET", "/payment-methods")
    pays = r.json() if r.status_code == 200 else []
    if not check(r.status_code == 200 and len(pays) > 0, "A13 GET /payment-methods ada isi",
                 f"HTTP {r.status_code} {str(pays)[:180]}"):
        return state
    ship = ships[0]
    pay = pays[0]
    ship_id = ship.get("id") or ship.get("code")
    print(f"       kirim='{ship.get('name')}' ({ship_id})  bayar='{pay.get('name')}' grup={pay.get('group')}")
    state["ship_id"], state["pay"] = ship_id, pay

    # A14 — stok sebelum order
    stock_before = int(v.get("stock") or 0)

    order_payload = {
        "items": [{"product_id": prod["id"], "sku": v["sku"], "quantity": 2}],
        "address": ADDR, "shipping_id": ship_id,
        "payment": {"group": pay.get("group"), "method_id": pay.get("id") or pay.get("code")},
        "note": "pesanan uji QA",
    }

    # A14 — buat pesanan (user login)
    r = req("POST", "/orders", token=tok, json=order_payload)
    if not check(r.status_code == 200, "A14 POST /orders buat pesanan (login)",
                 f"HTTP {r.status_code} {r.text[:400]}"):
        return state
    order = r.json()
    code = order.get("code")
    check(bool(code), "A15 pesanan punya kode", str(order)[:200])
    print(f"       kode={code} subtotal={order.get('subtotal')} "
          f"kirim={(order.get('shipping') or {}).get('price')} cod_fee={order.get('cod_fee')} "
          f"total={order.get('total')} status={order.get('status')}")
    state["order_code"] = code

    # A16 — matematika total dihitung server (subtotal - diskon + ongkir + cod_fee)
    ship_price = int(((order.get("shipping") or {}).get("price")) or 0)
    exp = (int(order.get("subtotal", 0)) - int(order.get("discount", 0) or 0)
           + ship_price + int(order.get("cod_fee", 0) or 0))
    check(int(order.get("total", -1)) == exp, "A16 total = subtotal - diskon + ongkir + cod_fee",
          f"total={order.get('total')} vs hitung={exp} "
          f"(sub={order.get('subtotal')} disc={order.get('discount')} "
          f"ship={ship_price} cod={order.get('cod_fee')})")
    check(int(order.get("subtotal", 0)) == int(v.get("price")) * 2,
          "A17 subtotal sesuai harga varian x qty",
          f"subtotal={order.get('subtotal')} harga={v.get('price')}")

    # A18 — stok berkurang
    r = req("GET", f"/products/{slug}")
    after = next((x for x in (r.json().get("variants") or []) if x.get("sku") == v["sku"]), None)
    check(after and int(after["stock"]) == stock_before - 2,
          "A18 stok varian berkurang 2 setelah order",
          f"sebelum={stock_before} sesudah={after and after.get('stock')}")

    # A19/A20 — riwayat & detail pesanan
    r = req("GET", "/orders", token=tok)
    lst = r.json() if r.status_code == 200 else []
    check(r.status_code == 200 and any(o.get("code") == code for o in lst),
          "A19 GET /orders memuat pesanan baru", f"HTTP {r.status_code} n={len(lst)}")
    r = req("GET", f"/orders/{code}", token=tok)
    check(r.status_code == 200 and r.json().get("code") == code,
          "A20 GET /orders/{code} detail pemilik", f"HTTP {r.status_code} {r.text[:180]}")

    # A21 — item pesanan menyimpan SKU sebagai SSOT
    items = (r.json() or {}).get("items") or []
    check(items and items[0].get("sku") == v["sku"], "A21 item pesanan menyimpan sku",
          f"item={str(items[:1])[:200]}")

    # A22 — IDOR: admin bukan pemilik -> 404
    atok, aerr = login(*ADMIN)
    if atok:
        r = req("GET", f"/orders/{code}", token=atok)
        check(r.status_code == 404, "A22 pesanan user lain -> 404 (IDOR-safe)", f"HTTP {r.status_code}")
        state["admin_token"] = atok
    else:
        bad("A22 login admin untuk uji IDOR", aerr)

    # A23 — guest checkout
    gp = json.loads(json.dumps(order_payload))
    gp["items"][0]["quantity"] = 1
    r = req("POST", "/orders", json=gp)
    check(r.status_code == 200, "A23 guest checkout (tanpa token) berhasil",
          f"HTTP {r.status_code} {r.text[:300]}")
    if r.status_code == 200:
        state["guest_code"] = r.json().get("code")

    # A24 — anti-oversell
    op = json.loads(json.dumps(order_payload))
    op["items"][0]["quantity"] = 999
    r = req("POST", "/orders", token=tok, json=op)
    check(r.status_code == 409, "A24 qty melebihi stok -> 409 Stok tidak mencukupi",
          f"HTTP {r.status_code} {r.text[:220]}")

    # A25 — SKU tidak dikenal -> 400
    op = json.loads(json.dumps(order_payload))
    op["items"][0]["sku"] = "SKU-TIDAK-ADA-999"
    r = req("POST", "/orders", token=tok, json=op)
    check(r.status_code in (400, 404, 409), "A25 SKU tak dikenal ditolak (4xx)",
          f"HTTP {r.status_code} {r.text[:220]}")

    # A26 — qty 0 ditolak validasi
    op = json.loads(json.dumps(order_payload))
    op["items"][0]["quantity"] = 0
    r = req("POST", "/orders", token=tok, json=op)
    check(r.status_code == 422, "A26 qty=0 -> 422 validasi", f"HTTP {r.status_code}")

    # A27 — shipping_id palsu ditolak
    op = json.loads(json.dumps(order_payload))
    op["shipping_id"] = "kurir-hantu"
    r = req("POST", "/orders", token=tok, json=op)
    check(r.status_code == 400, "A27 shipping_id tak dikenal -> 400", f"HTTP {r.status_code} {r.text[:200]}")

    # A28..A30 — voucher
    r = req("GET", "/vouchers")
    vouchers = r.json() if r.status_code == 200 else []
    check(r.status_code == 200, "A28 GET /vouchers 200", f"HTTP {r.status_code}")
    if vouchers:
        vc = vouchers[0].get("code")
        sub = int(v.get("price")) * 2
        r = req("POST", "/vouchers/validate", token=tok,
                json={"code": vc, "subtotal": sub, "items": [
                    {"product_id": prod["id"], "sku": v["sku"], "quantity": 2}]})
        check(r.status_code in (200, 400), f"A29 POST /vouchers/validate ({vc})",
              f"HTTP {r.status_code} {r.text[:220]}")
        if r.status_code == 200 and (r.json() or {}).get("valid"):
            vp = json.loads(json.dumps(order_payload))
            vp["voucher_code"] = vc
            vp["items"][0]["quantity"] = 1
            r2 = req("POST", "/orders", token=tok, json=vp)
            if r2.status_code == 200:
                o2 = r2.json()
                check(int(o2.get("discount") or 0) > 0, "A30 order pakai voucher -> diskon > 0",
                      f"discount={o2.get('discount')}")
            else:
                check(r2.status_code == 400, "A30 order pakai voucher (ditolak dgn alasan jelas)",
                      f"HTTP {r2.status_code} {r2.text[:220]}")
        else:
            ok("A30 voucher tidak berlaku untuk keranjang ini (respons jelas)")
        r = req("POST", "/vouchers/validate", token=tok,
                json={"code": "KODE-PALSU-XYZ", "subtotal": 100000, "items": []})
        check(r.status_code in (200, 400) and (r.status_code == 400 or not (r.json() or {}).get("valid")),
              "A31 voucher palsu ditolak", f"HTTP {r.status_code} {r.text[:200]}")

    # A32 — batal pesanan + stok kembali
    r = req("GET", f"/products/{slug}")
    st_before_cancel = next((x["stock"] for x in r.json()["variants"] if x["sku"] == v["sku"]), None)
    r = req("POST", f"/orders/{code}/cancel", token=tok)
    if check(r.status_code == 200, "A32 POST /orders/{code}/cancel 200", f"HTTP {r.status_code} {r.text[:220]}"):
        check((r.json() or {}).get("status") == "cancelled", "A33 status jadi cancelled",
              f"status={(r.json() or {}).get('status')}")
        r = req("GET", f"/products/{slug}")
        st_after = next((x["stock"] for x in r.json()["variants"] if x["sku"] == v["sku"]), None)
        check(int(st_after) == int(st_before_cancel) + 2, "A34 stok dikembalikan setelah batal",
              f"sebelum={st_before_cancel} sesudah={st_after}")
        r = req("POST", f"/orders/{code}/cancel", token=tok)
        check(r.status_code == 400, "A35 batal 2x -> 400 transisi invalid", f"HTTP {r.status_code}")

    # A36 — wishlist
    r = req("POST", "/wishlist/toggle", token=tok, json={"product_id": prod["id"]})
    check(r.status_code == 200, "A36 POST /wishlist/toggle 200", f"HTTP {r.status_code} {r.text[:180]}")
    r = req("GET", "/wishlist", token=tok)
    check(r.status_code == 200, "A37 GET /wishlist 200", f"HTTP {r.status_code}")

    # A38 — alamat tersimpan
    r = req("POST", "/addresses", token=tok, json={**ADDR, "is_default": True})
    check(r.status_code in (200, 201), "A38 POST /addresses 200/201", f"HTTP {r.status_code} {r.text[:180]}")

    # A39 — daftar user baru lalu checkout
    email = f"qa_{int(time.time())}@example.com"
    r = req("POST", "/auth/register", json={"name": "QA Baru", "email": email, "password": "Qa#123456"})
    if check(r.status_code in (200, 201), "A39 POST /auth/register user baru",
             f"HTTP {r.status_code} {r.text[:220]}"):
        ntok = (r.json() or {}).get("token") or login(email, "Qa#123456")[0]
        if ntok:
            np_ = json.loads(json.dumps(order_payload))
            np_["items"][0]["quantity"] = 1
            r = req("POST", "/orders", token=ntok, json=np_)
            check(r.status_code == 200, "A40 user baru bisa checkout", f"HTTP {r.status_code} {r.text[:250]}")
            if r.status_code == 200:
                r2 = req("GET", f"/orders/{code}", token=ntok)
                check(r2.status_code == 404, "A41 user baru tak bisa lihat order user lain -> 404",
                      f"HTTP {r2.status_code}")
    return state


# ════════════════════════════════════════════════════════════════════════
# B. WIZARD IMPOR N-DIMENSI
# ════════════════════════════════════════════════════════════════════════
IO = "/admin/products/io"
SAMPLES = ROOT / "tests" / "import_samples"


def purge_qa_products():
    """Hapus PERMANEN produk uji berprefix 'QA ' langsung dari Mongo.

    Endpoint DELETE admin sengaja hanya soft-delete (INV-M2: status='archived') agar FK
    order tetap aman. Untuk uji otomatis itu menyisakan sampah 'archived' di katalog/daftar
    admin, jadi dokumen dibersihkan langsung di sini.
    """
    import asyncio
    import os as _os

    from motor.motor_asyncio import AsyncIOMotorClient

    sys.path.insert(0, str(ROOT / "backend"))
    try:
        from dotenv import load_dotenv
        load_dotenv(ROOT / "backend" / ".env")
    except Exception:
        pass

    async def _run():
        cli = AsyncIOMotorClient(_os.environ["MONGO_URL"])
        db = cli[_os.environ.get("DB_NAME", "collector_parfum")]
        res = await db.products.delete_many({"name": {"$regex": "^QA ", "$options": "i"}})
        cli.close()
        return res.deleted_count

    try:
        return asyncio.run(_run())
    except Exception as e:  # pragma: no cover - cleanup best-effort
        print(f"       (peringatan) cleanup gagal: {e}")
        return 0


def test_import_wizard(admin_token):
    hdr("B. WIZARD IMPOR PRODUK N-DIMENSI (option1..4_name/value)")
    if not admin_token:
        bad("B0 token admin tidak tersedia", "login admin gagal")
        return

    # B1/B2 — template
    for fmt in ("csv", "xlsx"):
        r = req("GET", f"{IO}/template?format={fmt}", token=admin_token)
        okk = r.status_code == 200 and len(r.content) > 100
        check(okk, f"B1 GET template?format={fmt}", f"HTTP {r.status_code} bytes={len(r.content)}")
        if fmt == "csv" and okk:
            head = r.content.decode("utf-8-sig").splitlines()[0]
            need = [f"option{i}_{k}" for i in range(1, 5) for k in ("name", "value")]
            miss = [c for c in need if c not in head]
            check(not miss, "B2 header template punya option1..4_name/value", f"kurang={miss}")

    # B3 — RBAC: non-admin dilarang
    ctok, _ = login(*CUST)
    if ctok:
        r = req("GET", f"{IO}/template?format=csv", token=ctok)
        check(r.status_code in (401, 403), "B3 non-admin akses import -> 401/403", f"HTTP {r.status_code}")
        r = req("GET", f"{IO}/export?format=csv")
        check(r.status_code in (401, 403), "B4 export tanpa token -> 401/403", f"HTTP {r.status_code}")

    # Ekspektasi diturunkan dari isi file sample (1 baris = 1 varian).
    # sample_legacy: kolom 'concentration' juga jadi dimensi -> Konsentrasi x Ukuran (2 dimensi).
    expected = {
        "sample_2d.csv": {"dims": 2, "variants": 2, "names": ["Konsentrasi", "Ukuran"], "legacy": False},
        "sample_3d.csv": {"dims": 3, "variants": 4, "names": ["Konsentrasi", "Tipe", "Ukuran"], "legacy": False},
        "sample_4d.csv": {"dims": 4, "variants": 3,
                          "names": ["Konsentrasi", "Edisi", "Tipe", "Ukuran"], "legacy": False},
        "sample_legacy.csv": {"dims": 2, "variants": 2,
                              "names": ["Konsentrasi", "Ukuran"], "legacy": True},
    }
    created_slugs = []

    for fname, exp in expected.items():
        path = SAMPLES / fname
        if not path.exists():
            bad(f"B5 {fname} tidak ditemukan", str(path))
            continue
        tag = fname.replace(".csv", "")
        print(f"\n  {Y}--- {fname} (harap {exp['dims']} dimensi) ---{X}")

        # analyze
        r = req("POST", f"{IO}/analyze", token=admin_token,
                files={"file": (fname, path.read_bytes(), "text/csv")})
        if not check(r.status_code == 200, f"B6[{tag}] POST /analyze 200",
                     f"HTTP {r.status_code} {r.text[:250]}"):
            continue
        an = r.json()
        mapping, rows, headers = an["suggested_mapping"], an["rows"], an["headers"]
        check(len(rows) > 0, f"B7[{tag}] baris terbaca", f"rows={len(rows)}")
        # smart-mapping harus mengenali dimensi
        if not exp["legacy"]:
            mapped_dims = sum(1 for i in range(1, 5)
                              if mapping.get(f"option{i}_name") and mapping.get(f"option{i}_value"))
            check(mapped_dims == exp["dims"],
                  f"B8[{tag}] smart-mapping kenali {exp['dims']} pasangan dimensi",
                  f"terdeteksi={mapped_dims} mapping={ {k: v for k, v in mapping.items() if 'option' in k} }")
        else:
            check(bool(mapping.get("variant_ml")), f"B8[{tag}] smart-mapping kenali kolom legacy variant_ml",
                  f"mapping={mapping}")
        for req_key in ("name", "category", "variant_price"):
            check(bool(mapping.get(req_key)), f"B9[{tag}] mapping wajib '{req_key}' terisi",
                  f"headers={headers} mapping={mapping}")

        # validate
        r = req("POST", f"{IO}/validate", token=admin_token, json={"rows": rows, "mapping": mapping})
        if not check(r.status_code == 200, f"B10[{tag}] POST /validate 200",
                     f"HTTP {r.status_code} {r.text[:250]}"):
            continue
        val = r.json()
        summ = val["summary"]
        check(summ["error"] == 0, f"B11[{tag}] validasi tanpa error baris",
              f"summary={summ} reports={str(val['reports'])[:400]}")
        check(summ["products"] == 1, f"B12[{tag}] baris dikelompokkan jadi 1 produk", f"summary={summ}")
        if val["products"]:
            p = val["products"][0]
            opts = p.get("options") or []
            check(len(opts) == exp["dims"], f"B13[{tag}] produk punya {exp['dims']} options[]",
                  f"options={opts}")
            if exp["names"]:
                check([o["name"] for o in opts] == exp["names"],
                      f"B14[{tag}] nama dimensi & urutan benar", f"dapat={[o.get('name') for o in opts]}")
            check(len(p.get("variants") or []) == exp["variants"],
                  f"B15[{tag}] jumlah varian = {exp['variants']}", f"variants={len(p.get('variants') or [])}")
            # SSOT kombinasi varian = variant["options"] (dict dimensi -> nilai)
            combos = [tuple(sorted((x.get("options") or {}).items())) for x in p.get("variants") or []]
            check(all(combos) and len(combos) == len(set(combos)),
                  f"B16[{tag}] setiap varian punya options[] & kombinasi unik", f"combos={combos}")
            check(all(len(c) == exp["dims"] for c in combos),
                  f"B16b[{tag}] tiap varian punya {exp['dims']} nilai dimensi", f"combos={combos}")

        # commit
        r = req("POST", f"{IO}/commit", token=admin_token,
                json={"rows": rows, "mapping": mapping, "mode": "upsert"})
        if not check(r.status_code == 200, f"B17[{tag}] POST /commit 200",
                     f"HTTP {r.status_code} {r.text[:300]}"):
            continue
        res = r.json()
        check(res["failed"] == 0, f"B18[{tag}] commit tanpa gagal",
              f"result={ {k: v for k, v in res.items() if k != 'reports'} }")
        check(res["created"] + res["updated"] == 1, f"B19[{tag}] 1 produk dibuat/diupdate",
              f"created={res['created']} updated={res['updated']}")

        # produk hasil impor tampil di storefront dengan options N-dimensi
        pname = rows[0].get(mapping["name"])
        rr = req("GET", "/products?limit=200")
        found = next((x for x in rr.json() if x.get("name") == pname), None)
        if check(bool(found), f"B20[{tag}] produk hasil impor tampil di /products", f"cari='{pname}'"):
            created_slugs.append(found["slug"])
            rr = req("GET", f"/products/{found['slug']}")
            det = rr.json()
            check(len(det.get("options") or []) == exp["dims"],
                  f"B21[{tag}] PDP produk impor punya {exp['dims']} dimensi",
                  f"options={det.get('options')}")
            check(all(x.get("sku") for x in det.get("variants") or []),
                  f"B22[{tag}] semua varian punya SKU (auto-generate)",
                  f"variants={det.get('variants')}")

        # idempotensi: commit ulang mode add-only harus skip
        r = req("POST", f"{IO}/commit", token=admin_token,
                json={"rows": rows, "mapping": mapping, "mode": "add-only"})
        check(r.status_code == 200 and r.json().get("skipped") == 1,
              f"B23[{tag}] commit ulang add-only -> skipped", f"{r.status_code} {r.text[:200]}")

    # B24..B27 — round-trip export -> re-import
    print(f"\n  {Y}--- round-trip export -> re-import ---{X}")
    # Snapshot facet taksonomi SEBELUM round-trip (regresi data-loss: dulu export tidak
    # membawa occasions/characters sehingga re-import mode Upsert MENGOSONGKAN keduanya).
    facet_before = {}
    for p in req("GET", "/products?limit=500").json():
        d = req("GET", f"/products/{p['slug']}")
        if d.status_code == 200:
            dd = d.json()
            facet_before[p["slug"]] = (dd.get("occasions") or [], dd.get("characters") or [])
    n_facet_before = sum(1 for v in facet_before.values() if v[0] or v[1])
    r = req("GET", f"{IO}/export?format=csv", token=admin_token)
    if check(r.status_code == 200 and len(r.content) > 200, "B24 GET /export?format=csv",
             f"HTTP {r.status_code} bytes={len(r.content)}"):
        text = r.content.decode("utf-8-sig")
        head = text.splitlines()[0]
        need = [f"option{i}_{k}" for i in range(1, 5) for k in ("name", "value")]
        check(all(c in head for c in need), "B25 header export punya option1..4_name/value",
              f"kurang={[c for c in need if c not in head]}")
        check("variant_type" not in head and "variant_ml" not in head,
              "B26 header export TIDAK memakai kolom 2D lama", f"header={head}")
        check("occasions" in head and "characters" in head,
              "B47 header export membawa kolom occasions & characters (round-trip lossless)",
              f"header={head}")
        r2 = req("POST", f"{IO}/analyze", token=admin_token,
                 files={"file": ("re.csv", r.content, "text/csv")})
        if check(r2.status_code == 200, "B27 re-analyze hasil export 200", f"HTTP {r2.status_code}"):
            an = r2.json()
            n_before = len(req("GET", "/products?limit=500").json())
            r3 = req("POST", f"{IO}/commit", token=admin_token,
                     json={"rows": an["rows"], "mapping": an["suggested_mapping"], "mode": "upsert"})
            if check(r3.status_code == 200, "B28 re-commit hasil export 200",
                     f"HTTP {r3.status_code} {r3.text[:300]}"):
                res = r3.json()
                check(res["failed"] == 0 and res["created"] == 0,
                      "B29 round-trip idempoten (0 gagal, 0 produk baru)",
                      f"result={ {k: v for k, v in res.items() if k != 'reports'} }")
                n_after = len(req("GET", "/products?limit=500").json())
                check(n_before == n_after, "B30 jumlah produk tidak berubah setelah round-trip",
                      f"sebelum={n_before} sesudah={n_after}")
                # B48 — occasions/characters TIDAK boleh hilang setelah round-trip.
                lost = []
                for slug, (occ_b, chr_b) in facet_before.items():
                    d = req("GET", f"/products/{slug}")
                    if d.status_code != 200:
                        continue
                    dd = d.json()
                    if set(occ_b) - set(dd.get("occasions") or []) or set(chr_b) - set(dd.get("characters") or []):
                        lost.append(slug)
                check(n_facet_before > 0 and not lost,
                      "B48 occasions/characters tetap utuh setelah round-trip (anti data-loss)",
                      f"produk ber-facet={n_facet_before} hilang={lost[:5]}")

    # B31 — XLSX template bisa dibaca balik oleh analyze
    r = req("GET", f"{IO}/template?format=xlsx", token=admin_token)
    if r.status_code == 200:
        r2 = req("POST", f"{IO}/analyze", token=admin_token, files={
            "file": ("t.xlsx", r.content,
                     "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")})
        check(r2.status_code == 200 and len(r2.json().get("rows") or []) >= 4,
              "B31 analyze template XLSX terbaca (>=4 baris)",
              f"HTTP {r2.status_code} {r2.text[:220]}")

    # B32 — file rusak / format salah ditolak rapi (bukan 5xx)
    r = req("POST", f"{IO}/analyze", token=admin_token,
            files={"file": ("x.csv", b"", "text/csv")})
    check(r.status_code == 400, "B32 file kosong -> 400 (bukan 5xx)", f"HTTP {r.status_code}")
    r = req("POST", f"{IO}/analyze", token=admin_token,
            files={"file": ("x.txt", b"halo", "text/plain")})
    check(r.status_code == 400, "B33 ekstensi tak didukung -> 400", f"HTTP {r.status_code}")
    r = req("POST", f"{IO}/validate", token=admin_token, json={"rows": [{"a": "1"}], "mapping": {}})
    check(r.status_code == 200 and r.json()["summary"]["error"] >= 1,
          "B34 mapping kosong -> laporan error baris (bukan 5xx)", f"HTTP {r.status_code} {r.text[:220]}")
    r = req("POST", f"{IO}/commit", token=admin_token, json={"rows": [], "mapping": {}, "mode": "ngawur"})
    check(r.status_code == 400, "B35 mode commit invalid -> 400", f"HTTP {r.status_code}")

    # B36 — 5 dimensi: kolom option5 harus diabaikan, tidak crash
    csv5 = ("name,category,option1_name,option1_value,option2_name,option2_value,option3_name,"
            "option3_value,option4_name,option4_value,option5_name,option5_value,variant_price,variant_stock\n"
            "QA Lima Dimensi,amber,A,a1,B,b1,C,c1,Ukuran,50ml,E,e1,300000,4\n")
    r = req("POST", f"{IO}/analyze", token=admin_token,
            files={"file": ("d5.csv", csv5.encode(), "text/csv")})
    if check(r.status_code == 200, "B36 analyze file 5 dimensi 200 (option5 diabaikan)",
             f"HTTP {r.status_code} {r.text[:220]}"):
        an = r.json()
        m = an["suggested_mapping"]
        check(not any(k.startswith("option5") for k in m),
              "B37 tidak ada key option5 di mapping (cap 4 dimensi)", f"mapping={m}")
        r2 = req("POST", f"{IO}/validate", token=admin_token,
                 json={"rows": an["rows"], "mapping": m})
        check(r2.status_code == 200, "B38 validate file 5 dimensi tidak 5xx",
              f"HTTP {r2.status_code} {r2.text[:220]}")
        if r2.status_code == 200 and r2.json()["products"]:
            check(len(r2.json()["products"][0]["options"]) <= 4,
                  "B39 dimensi dibatasi maksimal 4", f"options={r2.json()['products'][0]['options']}")

    # B41 — produk archived + mode add-only: HARUS dilaporkan sebagai archived agar admin paham
    #        kenapa produknya tidak muncul di storefront (celah UX yang diperbaiki).
    path2 = SAMPLES / "sample_2d.csv"
    if path2.exists():
        r = req("POST", f"{IO}/analyze", token=admin_token,
                files={"file": ("sample_2d.csv", path2.read_bytes(), "text/csv")})
        if r.status_code == 200:
            an = r.json()
            m = an["suggested_mapping"]
            # pastikan ada (upsert) lalu arsipkan
            req("POST", f"{IO}/commit", token=admin_token,
                json={"rows": an["rows"], "mapping": m, "mode": "upsert"})
            rr = req("GET", "/products/qa-mawar-fresh")
            if rr.status_code == 200:
                pid = rr.json()["id"]
                ra = req("DELETE", f"/admin/products/{pid}", token=admin_token)
                check(ra.status_code == 200 and (ra.json() or {}).get("archived") is True,
                      "B41 DELETE admin = soft-delete (status archived, INV-M2)",
                      f"HTTP {ra.status_code} {ra.text[:180]}")
                check(req("GET", "/products/qa-mawar-fresh").status_code == 404,
                      "B42 produk archived tidak tampil di storefront (404)", "masih tampil")
                r2 = req("POST", f"{IO}/commit", token=admin_token,
                         json={"rows": an["rows"], "mapping": m, "mode": "add-only"})
                if check(r2.status_code == 200, "B43 add-only atas produk archived -> 200",
                         f"HTTP {r2.status_code} {r2.text[:200]}"):
                    res = r2.json()
                    check(res.get("skipped") == 1 and res.get("skipped_archived") == 1,
                          "B44 dilaporkan skipped_archived=1 (admin tahu produk tersembunyi)",
                          f"skipped={res.get('skipped')} skipped_archived={res.get('skipped_archived')} "
                          f"details={res.get('skipped_details')}")
                r3 = req("POST", f"{IO}/commit", token=admin_token,
                         json={"rows": an["rows"], "mapping": m, "mode": "upsert"})
                if check(r3.status_code == 200 and r3.json().get("updated") == 1,
                         "B45 upsert memulihkan produk archived", f"{r3.status_code} {r3.text[:200]}"):
                    check(req("GET", "/products/qa-mawar-fresh").status_code == 200,
                          "B46 produk aktif kembali & tampil di storefront", "masih 404")

    # B47 — bersihkan produk QA: DELETE admin hanya soft-delete (by design), jadi dokumen
    #        dihapus langsung dari Mongo supaya katalog/daftar admin tidak tercemar sisa uji.
    purged = purge_qa_products()
    print(f"       cleanup: {purged} produk QA dihapus permanen dari DB")


def main():
    hdr("PRA-SYARAT")
    try:
        r = requests.get(BASE + "/health", timeout=15)
        if not check(r.status_code == 200 and r.json().get("db"),
                     "P1 backend /api/health OK + DB terhubung", r.text[:200]):
            sys.exit(1)
    except Exception as e:
        bad("P1 backend tidak dapat dihubungi", repr(e))
        sys.exit(1)

    state = test_shopping_flow()
    atok = state.get("admin_token") or login(*ADMIN)[0]
    test_import_wizard(atok)

    hdr("RINGKASAN")
    print(f"  {G}PASS: {len(PASS)}{X}    {R}FAIL: {len(FAIL)}{X}")
    if FAIL:
        print(f"\n{R}{B}  GAGAL:{X}")
        for n, d in FAIL:
            print(f"   {R}x{X} {n}\n     {d}")
        sys.exit(1)
    print(f"\n{G}{B}  SEMUA UJI LULUS.{X}\n")


if __name__ == "__main__":
    main()
