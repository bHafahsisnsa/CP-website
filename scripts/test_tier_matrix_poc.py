#!/usr/bin/env python
"""scripts/test_tier_matrix_poc.py — POC INTI: matriks harga per TIER + aktivasi massal.

Membuktikan (bukan mengklaim) di SKALA PENUH memakai file asli klien
`tests/user_uploads/IMPOR_PRODUK_COLLECTOR_PARFUM_1.xlsx` (6.426 baris / 1.071 produk):

  1. POST /api/admin/products/io/analyze  -> file terbaca, smart-mapping lengkap.
  2. POST /api/admin/products/io/tiers    -> tier & dimensi efektif terdeteksi TEPAT.
  3. Terapkan matriks (tier x kombinasi dimensi) ke rows  -> POST /validate error = 0.
  4. POST /commit  -> 1.071 produk dibuat, archived, stok 0, harga PERSIS sesuai matriks.
  5. Storefront: produk archived TIDAK tampil.
  6. POST /api/admin/products/bulk-status -> aktivasi massal, produk tampil di storefront.
  7. Adversarial + RBAC: tanpa 5xx, 401/403/400/409 sesuai kontrak.
  8. Cleanup: hapus produk uji langsung dari Mongo (DELETE API hanya soft-delete).

Jalankan: python scripts/test_tier_matrix_poc.py
"""
import asyncio
import os
import sys
from collections import OrderedDict

import requests
from openpyxl import load_workbook

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "backend"))
from services.product_tiers import extract_tier  # noqa: E402  (SSOT deteksi tier)

BASE = os.environ.get("BACKEND_BASE", "http://localhost:8001/api")
ADMIN = (os.environ.get("ADMIN_EMAIL", "admin@collectorparfum.id"),
         os.environ.get("ADMIN_PASS", "Admin#2026"))
CUSTOMER = (os.environ.get("CUST_EMAIL", "customer@collectorparfum.id"),
            os.environ.get("CUST_PASS", "Customer#2026"))
XLSX = "tests/user_uploads/IMPOR_PRODUK_COLLECTOR_PARFUM_1.xlsx"

G, R, Y, C, X, B = "\033[92m", "\033[91m", "\033[93m", "\033[96m", "\033[0m", "\033[1m"
PASS = FAIL = 0

# Harga UJI (bukan harga final klien) — sengaja unik per sel agar drift terdeteksi.
TIER_BASE = {"CP01": 150000, "CP02": 200000, "CP03": 275000, "EXCLUSIVE": 450000}
SIZE_MULT = {"35ml": 100, "60ml": 160, "100ml": 240}
TYPE_MULT = {"Standard": 100, "Super": 125}


def ok(label, cond, extra=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  {G}[PASS]{X} {label}" + (f"  {extra}" if extra else ""))
    else:
        FAIL += 1
        print(f"  {R}[FAIL]{X} {label}" + (f"  {extra}" if extra else ""))
    return bool(cond)


def head(t):
    print(f"\n{C}{B}--- {t} ---{X}")


def login(creds):
    r = requests.post(f"{BASE}/auth/login",
                      json={"email": creds[0], "password": creds[1]}, timeout=30)
    r.raise_for_status()
    return {"Authorization": f"Bearer {r.json()['token']}"}


# --------------------------------------------------------------------------------------
# Algoritma ISI HARGA MASSAL — kontrak yang WAJIB dicerminkan 1:1 oleh frontend
# (components/admin/import/importBulkFill.js). Ditulis di sini agar bisa diuji otomatis.
# --------------------------------------------------------------------------------------
def row_combo_key(row, mapping, dim_order):
    """Kunci kombinasi dimensi satu baris, mengikuti urutan dimensi dari /tiers."""
    pairs = {}
    for i in range(1, 5):
        nh, vh = mapping.get(f"option{i}_name"), mapping.get(f"option{i}_value")
        if not nh or not vh:
            continue
        n = str(row.get(nh) or "").strip()
        v = str(row.get(vh) or "").strip()
        if n and v:
            pairs[n] = v
    if set(pairs) != set(dim_order):
        return None
    return "|".join(pairs[n] for n in dim_order)


def apply_bulk_fill(rows, mapping, dim_order, tier_column, matrix,
                    *, overwrite_price=False, fill_if_empty=None, force_values=None):
    """Isi harga dari matrix[tier][combo_key] + nilai kolom lain.

    DUA semantik berbeda (sengaja dipisah — inilah temuan POC):
      - `fill_if_empty`: hanya mengisi sel yang KOSONG atau "0" (mis. Konsentrasi).
      - `force_values` : SELALU menimpa (mis. Status -> 'archived', Stok -> 0). Wajib ada
        karena file klien sudah menulis `status=active` di semua baris, sehingga mode
        "isi bila kosong" TIDAK akan pernah membuat produk jadi draft.
    `overwrite_price` mengatur apakah harga yang sudah > 0 boleh ditimpa matriks.
    Kembalikan statistik; `rows` dimutasi di tempat (seperti state React).
    """
    stats = {"price_filled": 0, "rows_skipped_no_tier": 0, "rows_skipped_no_combo": 0,
             "rows_skipped_no_cell": 0, "filled_if_empty": 0, "forced": 0}
    price_h = mapping.get("variant_price")
    for row in rows:
        for canon, val in (fill_if_empty or {}).items():
            h = mapping.get(canon)
            if not h or val in (None, ""):
                continue
            cur = str(row.get(h) or "").strip()
            if cur == "" or cur == "0":
                row[h] = str(val)
                stats["filled_if_empty"] += 1
        for canon, val in (force_values or {}).items():
            h = mapping.get(canon)
            if not h or val in (None, ""):
                continue
            row[h] = str(val)
            stats["forced"] += 1
        if not price_h:
            continue
        tier = extract_tier(row.get(tier_column)) if tier_column else ""
        if not tier:
            stats["rows_skipped_no_tier"] += 1
            continue
        key = row_combo_key(row, mapping, dim_order)
        if not key:
            stats["rows_skipped_no_combo"] += 1
            continue
        cell = (matrix.get(tier) or {}).get(key)
        if cell in (None, "", 0):
            stats["rows_skipped_no_cell"] += 1
            continue
        cur = str(row.get(price_h) or "").strip()
        try:
            cur_num = int(float(cur.replace(".", "").replace(",", "") or 0))
        except ValueError:
            cur_num = 0
        if overwrite_price or cur_num <= 0:
            row[price_h] = str(int(cell))
            stats["price_filled"] += 1
    return stats


def read_sheet(path, sheet="Produk"):
    wb = load_workbook(path, data_only=True, read_only=True)
    ws = wb[sheet] if sheet in wb.sheetnames else wb[wb.sheetnames[0]]
    it = ws.iter_rows(values_only=True)
    hdr = [str(h).strip() if h is not None else "" for h in next(it)]
    rows = []
    for r in it:
        if not any(c not in (None, "") for c in r):
            continue
        rows.append({hdr[i]: ("" if v is None else str(v).strip())
                     for i, v in enumerate(r) if i < len(hdr)})
    wb.close()
    return hdr, rows


def purge(slugs):
    from dotenv import load_dotenv
    from motor.motor_asyncio import AsyncIOMotorClient
    load_dotenv("backend/.env")

    async def run():
        c = AsyncIOMotorClient(os.environ["MONGO_URL"])
        db = c[os.environ["DB_NAME"]]
        n = 0
        chunk = list(slugs)
        for i in range(0, len(chunk), 500):
            res = await db.products.delete_many({"slug": {"$in": chunk[i:i + 500]}})
            n += res.deleted_count
        left = await db.products.count_documents({})
        return n, left
    return asyncio.run(run())


def db_snapshot(slugs):
    from dotenv import load_dotenv
    from motor.motor_asyncio import AsyncIOMotorClient
    load_dotenv("backend/.env")

    async def run():
        c = AsyncIOMotorClient(os.environ["MONGO_URL"])
        db = c[os.environ["DB_NAME"]]
        docs = await db.products.find({"slug": {"$in": list(slugs)}}).to_list(5000)
        return docs
    return asyncio.run(run())


def main():
    if not os.path.exists(XLSX):
        print(f"{R}File tidak ditemukan: {XLSX}{X}")
        return 1
    print(f"{C}{B}{'=' * 74}{X}")
    print(f"{C}{B}  POC — MATRIKS HARGA TIER + AKTIVASI MASSAL (file asli klien){X}")
    print(f"{C}{B}{'=' * 74}{X}")

    H = login(ADMIN)
    HC = login(CUSTOMER)

    head("1. POST /analyze — baca file 6.426 baris")
    with open(XLSX, "rb") as f:
        ra = requests.post(f"{BASE}/admin/products/io/analyze", headers=H, timeout=600,
                           files={"file": (os.path.basename(XLSX), f,
                                           "application/vnd.openxmlformats-officedocument."
                                           "spreadsheetml.sheet")})
    if not ok("analyze = 200", ra.status_code == 200, f"HTTP {ra.status_code}"):
        return 1
    an = ra.json()
    rows = an["rows"]
    mapping = an["suggested_mapping"]
    ok("6426 baris terbaca", len(rows) == 6426, f"{len(rows)} baris")
    ok("28 kolom terpetakan otomatis",
       sum(1 for v in mapping.values() if v) == 28,
       f"{sum(1 for v in mapping.values() if v)} field")
    ok("kolom harga terpetakan", bool(mapping.get("variant_price")),
       f"-> {mapping.get('variant_price')}")

    head("2. POST /tiers — deteksi tier & dimensi efektif")
    rt = requests.post(f"{BASE}/admin/products/io/tiers", headers=H, timeout=600,
                       json={"rows": rows, "mapping": mapping})
    if not ok("tiers = 200", rt.status_code == 200, f"HTTP {rt.status_code} {rt.text[:200]}"):
        return 1
    tz = rt.json()
    tiers = tz["tiers"]
    dims = tz["dimensions"]
    combos = tz["combos"]
    dim_order = [d["name"] for d in dims]
    tier_col = tz["tier_column"]
    ok("kolom tier terdeteksi otomatis = 'tags'", tier_col == "tags", f"{tier_col}")
    ok("4 tier terdeteksi", len(tiers) == 4, f"{[t['label'] for t in tiers]}")
    counts = {t["label"]: t["products"] for t in tiers}
    ok("jumlah produk per tier TEPAT",
       counts == {"CP01": 532, "CP02": 417, "CP03": 107, "EXCLUSIVE": 15}, f"{counts}")
    ok("baris per tier TEPAT",
       {t["label"]: t["rows"] for t in tiers}
       == {"CP01": 3192, "CP02": 2502, "CP03": 642, "EXCLUSIVE": 90})
    ok("dimensi efektif = Ukuran + Tipe (bukan 4)", dim_order == ["Ukuran", "Tipe"], f"{dim_order}")
    ok("nilai Ukuran urut numerik", dims[0]["values"] == ["35ml", "60ml", "100ml"],
       f"{dims[0]['values']}")
    ok("nilai Tipe", dims[1]["values"] == ["Standard", "Super"], f"{dims[1]['values']}")
    ok("6 kombinasi dimensi (bukan kartesian palsu)", len(combos) == 6,
       f"{[c['label'] for c in combos]}")
    ok("setiap kombinasi mencakup 1071 baris",
       all(c["rows"] == 1071 for c in combos), f"{[c['rows'] for c in combos]}")
    ok("summary: 1071 produk, 0 tanpa tier, 6426 tanpa harga",
       tz["summary"]["products"] == 1071 and tz["summary"]["rows_without_tier"] == 0
       and tz["summary"]["rows_without_price"] == 6426, f"{tz['summary']}")
    ok("total sel matriks = 24", tz["summary"]["cells"] == 24, f"{tz['summary']['cells']}")
    ok("kandidat kolom tier dilaporkan untuk UI", len(tz["tier_column_candidates"]) >= 1,
       f"{[c['column'] for c in tz['tier_column_candidates']]}")

    head("3. Terapkan matriks 4x6 + default (stok 0, status archived) -> /validate")
    matrix = {}
    for t in tiers:
        matrix[t["label"]] = {}
        for c in combos:
            size = c["values"]["Ukuran"]
            typ = c["values"]["Tipe"]
            matrix[t["label"]][c["key"]] = (
                TIER_BASE[t["label"]] * SIZE_MULT[size] // 100 * TYPE_MULT[typ] // 100)
    expected_cells = {(t, k): v for t, row in matrix.items() for k, v in row.items()}
    ok("24 sel matriks terbentuk", len(expected_cells) == 24, f"{len(expected_cells)} sel")
    ok("semua sel unik per tier (drift terdeteksi bila tertukar)",
       len({v for v in matrix['CP01'].values()}) == 6)

    stats = apply_bulk_fill(rows, mapping, dim_order, tier_col, matrix,
                            overwrite_price=False,
                            force_values={"variant_stock": 0, "status": "archived"},
                            fill_if_empty={"concentration": "EDP"})
    ok("6426 harga terisi", stats["price_filled"] == 6426, f"{stats}")
    ok("status & stok DIPAKSA di semua baris (12852 sel)", stats["forced"] == 12852, f"{stats}")
    ok("konsentrasi kosong terisi EDP", stats["filled_if_empty"] == 6426, f"{stats}")
    ok("0 baris terlewat (tanpa tier/kombinasi/sel)",
       stats["rows_skipped_no_tier"] == 0 and stats["rows_skipped_no_combo"] == 0
       and stats["rows_skipped_no_cell"] == 0, f"{stats}")

    rv = requests.post(f"{BASE}/admin/products/io/validate", headers=H, timeout=900,
                       json={"rows": rows, "mapping": mapping})
    ok("validate = 200", rv.status_code == 200, f"HTTP {rv.status_code}")
    sm = rv.json().get("summary", {}) if rv.status_code == 200 else {}
    ok("0 baris error setelah matriks diterapkan", sm.get("error") == 0, f"{sm}")
    ok("1071 produk siap diimpor", sm.get("products") == 1071, f"{sm}")

    head("4. POST /commit — impor 1.071 produk sebagai draft")
    slugs = [r[mapping["slug"]] for r in rows if r.get(mapping["slug"])]
    slugs = list(OrderedDict.fromkeys(slugs))
    rc = requests.post(f"{BASE}/admin/products/io/commit", headers=H, timeout=1800,
                       json={"rows": rows, "mapping": mapping, "mode": "add-only"})
    ok("commit = 200", rc.status_code == 200, f"HTTP {rc.status_code} {rc.text[:200]}")
    cd = rc.json() if rc.status_code == 200 else {}
    ok("1071 produk dibuat, 0 gagal",
       cd.get("created") == 1071 and int(cd.get("failed") or 0) == 0,
       f"created={cd.get('created')} updated={cd.get('updated')} "
       f"skipped={cd.get('skipped')} failed={cd.get('failed')}")
    ok("row_errors = 0", int(cd.get("row_errors") or 0) == 0)

    head("5. Verifikasi DB: status, stok, harga per sel matriks, SKU, ml")
    docs = db_snapshot(slugs)
    ok("1071 dokumen produk di DB", len(docs) == 1071, f"{len(docs)} dokumen")
    n_var = sum(len(d.get("variants") or []) for d in docs)
    ok("6426 varian tersimpan", n_var == 6426, f"{n_var} varian")
    ok("SEMUA produk berstatus archived",
       all(d.get("status") == "archived" for d in docs))
    ok("SEMUA stok = 0",
       all(int(v.get("stock") or 0) == 0 for d in docs for v in (d.get("variants") or [])))
    ok("SEMUA varian punya SKU",
       all(v.get("sku") for d in docs for v in (d.get("variants") or [])))
    ok("SKU unik per produk",
       all(len({v["sku"] for v in d["variants"]}) == len(d["variants"]) for d in docs))
    ok("options = ['Ukuran','Tipe'] di semua produk",
       all([o["name"] for o in (d.get("options") or [])] == ["Ukuran", "Tipe"] for d in docs))

    # Harga: bandingkan setiap varian dengan sel matriks miliknya (tier dari tags produk).
    mism = []
    for d in docs:
        tier = extract_tier(", ".join(d.get("tags") or []))
        for v in d.get("variants") or []:
            key = "|".join(v["options"][n] for n in dim_order)
            exp = expected_cells.get((tier, key))
            if exp is None or int(v.get("price") or 0) != int(exp):
                mism.append((d["slug"], tier, key, v.get("price"), exp))
    ok("harga SETIAP varian persis sesuai sel matriks (0 drift)", not mism,
       f"{len(mism)} mismatch, contoh={mism[:2]}")
    ok("harga berbeda antar ukuran (matriks tidak kolaps)",
       len({v["price"] for v in docs[0]["variants"]}) == 6,
       f"{sorted({v['price'] for v in docs[0]['variants']})}")

    head("6. Storefront: produk draft TIDAK boleh tampil")
    r1 = requests.get(f"{BASE}/products/{slugs[0]}", timeout=30)
    ok("PDP produk archived -> 404", r1.status_code == 404, f"HTTP {r1.status_code}")
    pub = requests.get(f"{BASE}/products", timeout=60, params={"limit": 1})
    total_pub = int(pub.headers.get("X-Total-Count") or 0)
    ok("katalog publik masih 12 produk (draft tersembunyi)", total_pub == 12, f"{total_pub}")

    head("7. POST /admin/products/bulk-status — aktivasi massal")
    r409 = requests.post(f"{BASE}/admin/products/bulk-status", headers=H, timeout=300,
                         json={"status": "active", "filter_status": "archived",
                               "confirm_count": 999999})
    ok("confirm_count tidak cocok -> 409 (pengaman)", r409.status_code == 409,
       f"HTTP {r409.status_code}")
    rb = requests.post(f"{BASE}/admin/products/bulk-status", headers=H, timeout=300,
                       json={"status": "active", "filter_status": "archived",
                             "confirm_count": 1071})
    ok("bulk-status = 200", rb.status_code == 200, f"HTTP {rb.status_code} {rb.text[:200]}")
    bd = rb.json() if rb.status_code == 200 else {}
    ok("1071 produk diaktifkan", bd.get("matched") == 1071 and bd.get("modified") == 1071,
       f"{bd}")
    r2 = requests.get(f"{BASE}/products/{slugs[0]}", timeout=30)
    ok("PDP produk aktif -> 200", r2.status_code == 200, f"HTTP {r2.status_code}")
    if r2.status_code == 200:
        p = r2.json()
        ok("PDP membawa 6 varian", len(p.get("variants") or []) == 6)
        ok("price_min/max terisi & berbeda",
           int(p.get("price_min") or 0) > 0 and p.get("price_max") != p.get("price_min"),
           f"min={p.get('price_min')} max={p.get('price_max')}")
    pub2 = requests.get(f"{BASE}/products", timeout=60, params={"limit": 1})
    ok("katalog publik jadi 1083 produk (12 + 1071)",
       int(pub2.headers.get("X-Total-Count") or 0) == 1083,
       f"{pub2.headers.get('X-Total-Count')}")

    head("8. Arsipkan kembali via ids (cakupan kedua)")
    ids = [d["id"] for d in docs[:50]]
    rb2 = requests.post(f"{BASE}/admin/products/bulk-status", headers=H, timeout=300,
                        json={"status": "archived", "ids": ids})
    ok("bulk-status by ids = 200", rb2.status_code == 200, f"HTTP {rb2.status_code}")
    ok("50 produk diarsipkan",
       rb2.status_code == 200 and rb2.json().get("modified") == 50,
       f"{rb2.json() if rb2.status_code == 200 else ''}")

    head("9. Adversarial & RBAC — wajib TANPA 5xx")
    cases = [
        ("tiers tanpa token", requests.post(f"{BASE}/admin/products/io/tiers",
                                            json={"rows": [], "mapping": {}}, timeout=30), (401, 403)),
        ("tiers sebagai customer", requests.post(f"{BASE}/admin/products/io/tiers", headers=HC,
                                                 json={"rows": [], "mapping": {}}, timeout=30), (403,)),
        ("bulk-status tanpa token", requests.post(f"{BASE}/admin/products/bulk-status",
                                                  json={"status": "active", "filter_status": "all"},
                                                  timeout=30), (401, 403)),
        ("bulk-status sebagai customer", requests.post(f"{BASE}/admin/products/bulk-status",
                                                       headers=HC,
                                                       json={"status": "active",
                                                             "filter_status": "all"},
                                                       timeout=30), (403,)),
        ("bulk-status status invalid", requests.post(f"{BASE}/admin/products/bulk-status",
                                                     headers=H, json={"status": "hapus"},
                                                     timeout=30), (422, 400)),
        ("bulk-status tanpa cakupan", requests.post(f"{BASE}/admin/products/bulk-status",
                                                    headers=H, json={"status": "active"},
                                                    timeout=30), (400,)),
        ("tiers rows bukan list", requests.post(f"{BASE}/admin/products/io/tiers", headers=H,
                                                json={"rows": "bukan-list", "mapping": {}},
                                                timeout=30), (422, 400)),
        ("tiers kolom tier ngawur", requests.post(f"{BASE}/admin/products/io/tiers", headers=H,
                                                  json={"rows": rows[:60], "mapping": mapping,
                                                        "tier_column": "kolom-tidak-ada"},
                                                  timeout=60), (200,)),
        ("tiers rows kosong", requests.post(f"{BASE}/admin/products/io/tiers", headers=H,
                                            json={"rows": [], "mapping": {}}, timeout=30), (200,)),
        ("tiers baris berisi nested dict", requests.post(
            f"{BASE}/admin/products/io/tiers", headers=H,
            json={"rows": [{"a": {"b": 1}, "tags": ["Tier CP01"]}], "mapping": mapping},
            timeout=30), (200,)),
    ]
    for label, resp, allowed in cases:
        ok(f"{label} -> {resp.status_code}", resp.status_code in allowed and resp.status_code < 500,
           f"diharapkan {allowed}")

    head("10. Matriks kosong / harga negatif — tetap ditolak validator")
    sub = [dict(r) for r in rows[:12]]
    for r0 in sub:
        r0[mapping["variant_price"]] = "0"
    st = apply_bulk_fill(sub, mapping, dim_order, tier_col, {}, overwrite_price=False)
    ok("matriks kosong -> 0 harga terisi & dilaporkan", st["price_filled"] == 0
       and st["rows_skipped_no_cell"] == 12, f"{st}")
    for r0 in sub:
        r0[mapping["variant_price"]] = "-5000"
    rvn = requests.post(f"{BASE}/admin/products/io/validate", headers=H, timeout=120,
                        json={"rows": sub, "mapping": mapping})
    ok("harga negatif -> semua baris error (bukan 5xx)",
       rvn.status_code == 200 and rvn.json()["summary"]["error"] == 12,
       f"HTTP {rvn.status_code} {rvn.json().get('summary') if rvn.status_code == 200 else ''}")

    head("11. Cleanup — hapus 1.071 produk uji dari Mongo")
    n, left = purge(slugs)
    ok("produk uji dihapus permanen", n == 1071, f"{n} dihapus")
    ok("katalog kembali 12 produk", left == 12, f"{left} produk tersisa")

    print(f"\n{C}{B}{'=' * 74}{X}")
    print(f"  {G}PASS: {PASS}{X}    {R}FAIL: {FAIL}{X}")
    print(f"{C}{B}{'=' * 74}{X}")
    if FAIL == 0:
        print(f"{G}{B}  POC LULUS — matriks tier & aktivasi massal terbukti di skala penuh.{X}\n")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
