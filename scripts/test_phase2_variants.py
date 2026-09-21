"""test_phase2_variants.py — POC/validasi end-to-end sistem VARIAN N-dimensi.

Menguji: serialize katalog (options/variants/range), create produk N-dimensi via admin,
order by SKU + snapshot, anti-oversell (409), resolusi legacy (variant_type+volume_ml),
dan update stok. Jalankan: `python scripts/test_phase2_variants.py` (backend harus hidup).
"""
import sys
import httpx

BASE = "http://localhost:8001/api"
ADMIN = {"email": "admin@collectorparfum.id", "password": "Admin#2026"}
PASS, FAIL = [], []


def ok(name, cond, extra=""):
    (PASS if cond else FAIL).append(name)
    print(f"  {'✓' if cond else '✗'} {name}" + (f" — {extra}" if extra and not cond else ""))


def main():
    c = httpx.Client(base_url=BASE, timeout=30)

    # 0) Admin token
    r = c.post("/auth/login", json=ADMIN)
    token = r.json().get("token")
    AH = {"Authorization": f"Bearer {token}"}
    ok("admin login", bool(token))

    # 1) Katalog serialize: options/variants/range hadir untuk semua produk
    prods = c.get("/products").json()
    all_have = all(p.get("variants") and p.get("options") and p.get("price_min") for p in prods)
    ok("list products punya options/variants/price_min", all_have, f"{len(prods)} produk")

    pdp = c.get("/products/noir-oud-intense").json()
    ok("PDP noir-oud: 3 dimensi (Konsentrasi/Tipe/Ukuran)", len(pdp.get("options", [])) == 3)
    ok("PDP noir-oud: 6 variants", len(pdp.get("variants", [])) == 6)
    ok("PDP price range 385000..1350000",
       pdp.get("price_min") == 385000 and pdp.get("price_max") == 1350000)

    # 2) Create produk N-dimensi via admin (Konsentrasi[EDP,EDT] x Ukuran[50ml,100ml] = 4 varian)
    payload = {
        "name": "POC Nebula Test", "category": prods[0]["category"],
        "concentration": "EDP", "gender": "Unisex",
        "options": [
            {"name": "Konsentrasi", "values": ["EDP", "EDT"]},
            {"name": "Ukuran", "values": ["50ml", "100ml"]},
        ],
        "variants": [
            {"options": {"Konsentrasi": "EDP", "Ukuran": "50ml"}, "price": 500000, "stock": 5},
            {"options": {"Konsentrasi": "EDP", "Ukuran": "100ml"}, "price": 800000, "stock": 3, "compare_at_price": 900000},
            {"options": {"Konsentrasi": "EDT", "Ukuran": "50ml"}, "price": 400000, "stock": 10},
            {"options": {"Konsentrasi": "EDT", "Ukuran": "100ml"}, "price": 650000, "stock": 2},
        ],
        "description": "Produk uji N-dimensi.", "status": "active",
    }
    r = c.post("/admin/products", json=payload, headers=AH)
    ok("create produk N-dimensi (201/200)", r.status_code in (200, 201), f"{r.status_code} {r.text[:200]}")
    created = r.json()
    pid = created.get("id")
    ok("created price_min=400000 price_max=800000",
       created.get("price_min") == 400000 and created.get("price_max") == 800000,
       f"{created.get('price_min')}..{created.get('price_max')}")
    ok("created 4 variants ber-SKU", len(created.get("variants", [])) == 4 and all(v.get("sku") for v in created.get("variants", [])))
    edt50 = next((v for v in created["variants"] if v["options"] == {"Konsentrasi": "EDT", "Ukuran": "50ml"}), None)
    ok("varian EDT/50ml ada (stock=10)", edt50 and edt50["stock"] == 10)
    sku_edt50 = edt50["sku"] if edt50 else None

    # 3) Order by SKU (guest) → snapshot benar + stok turun di variants
    order_body = {
        "items": [{"product_id": pid, "sku": sku_edt50, "quantity": 2}],
        "address": {"name": "Uji", "phone": "0812", "street": "Jl Test", "city": "Jakarta", "province": "DKI"},
        "shipping_id": "jne-reg", "payment": {"group": "transfer", "method_id": "bca"},
    }
    r = c.post("/orders", json=order_body)
    ok("order by SKU sukses", r.status_code in (200, 201), f"{r.status_code} {r.text[:250]}")
    if r.status_code in (200, 201):
        od = r.json()
        it = (od.get("items") or [{}])[0]
        ok("order item snapshot sku benar", it.get("sku") == sku_edt50)
        ok("order item options snapshot (N-dim)", it.get("options") == {"Konsentrasi": "EDT", "Ukuran": "50ml"}, str(it.get("options")))
        ok("order item variant_type composite = 'EDT'", it.get("variant_type") == "EDT", str(it.get("variant_type")))
        ok("order item unit_price=400000 vol=50", it.get("unit_price") == 400000 and it.get("volume_ml") == 50)

    # verifikasi stok turun 10 -> 8 pada variants (via admin get)
    after = c.get(f"/admin/products/{pid}", headers=AH).json()
    v_after = next((v for v in after["variants"] if v["sku"] == sku_edt50), {})
    ok("stok EDT/50ml turun 10 -> 8", v_after.get("stock") == 8, str(v_after.get("stock")))

    # 4) Anti-oversell: pesan 999 dari EDT/100ml (stock=2) → 409
    r = c.post("/orders", json={
        "items": [{"product_id": pid, "sku": next(v["sku"] for v in created["variants"] if v["options"] == {"Konsentrasi": "EDT", "Ukuran": "100ml"}), "quantity": 999}],
        "address": {"name": "Uji", "phone": "0812", "street": "Jl Test", "city": "Jakarta", "province": "DKI"},
        "shipping_id": "jne-reg", "payment": {"group": "transfer", "method_id": "bca"},
    })
    ok("anti-oversell → 409", r.status_code == 409, f"{r.status_code}")

    # 5) Legacy payload (variant_type composite + volume_ml) → resolve
    r = c.post("/orders", json={
        "items": [{"product_id": pid, "variant_type": "EDP", "volume_ml": 50, "quantity": 1}],
        "address": {"name": "Uji", "phone": "0812", "street": "Jl Test", "city": "Jakarta", "province": "DKI"},
        "shipping_id": "jne-reg", "payment": {"group": "transfer", "method_id": "bca"},
    })
    ok("legacy payload (type+ml) resolve → sukses", r.status_code in (200, 201), f"{r.status_code} {r.text[:200]}")
    if r.status_code in (200, 201):
        it = r.json()["items"][0]
        ok("legacy resolve → sku EDP/50ml + price 500000", it.get("unit_price") == 500000 and it.get("options", {}).get("Ukuran") == "50ml")

    # 6) Update produk: ubah stok EDT/50ml → 20, harga → 420000
    upd = dict(payload)
    upd["variants"] = [dict(v) for v in payload["variants"]]
    for v in upd["variants"]:
        if v["options"] == {"Konsentrasi": "EDT", "Ukuran": "50ml"}:
            v["stock"], v["price"] = 20, 420000
    r = c.put(f"/admin/products/{pid}", json=upd, headers=AH)
    ok("update produk sukses", r.status_code == 200, f"{r.status_code} {r.text[:200]}")
    if r.status_code == 200:
        v = next((x for x in r.json()["variants"] if x["options"] == {"Konsentrasi": "EDT", "Ukuran": "50ml"}), {})
        ok("update stok=20 harga=420000 (reset via editor)", v.get("stock") == 20 and v.get("price") == 420000)

    # 7) Validasi: variants tanpa dimensi ukuran → tolak 400
    r = c.post("/admin/products", json={
        "name": "POC Invalid", "category": prods[0]["category"],
        "options": [{"name": "Konsentrasi", "values": ["EDP"]}],
        "variants": [{"options": {"Konsentrasi": "EDP"}, "price": 100000, "stock": 1}],
    }, headers=AH)
    ok("tolak produk tanpa dimensi ukuran → 400", r.status_code == 400, f"{r.status_code}")

    # cleanup: archive produk uji
    if pid:
        c.delete(f"/admin/products/{pid}", headers=AH)

    print(f"\nRESULT: {len(PASS)} passed, {len(FAIL)} failed")
    if FAIL:
        print("FAILED:", FAIL)
        sys.exit(1)


if __name__ == "__main__":
    main()
