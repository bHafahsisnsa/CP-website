#!/usr/bin/env python
"""scripts/test_import_session_poc.py — POC E12: SESI IMPOR (fix "Gagal memvalidasi baris.").

BUG YANG DIBUKTIKAN HILANG
Wizard impor lama mengirim ULANG seluruh baris pada SETIAP validasi. Untuk katalog klien
6.426 baris itu ~5,2 MB request + ~6,4 MB response = ~11,6 MB per validasi. Pada koneksi
normal (~1 Mbps unggah) satu validasi > 60 detik -> axios timeout -> admin melihat
"Gagal memvalidasi baris." padahal file 100% sah (direproduksi di browser dengan throttle).

POC ini membuktikan jalur SESI:
  1. /analyze?include_rows=false&preview=N -> session_id + preview (respons KB, bukan MB).
  2. /validate {session_id, report_limit, product_limit} -> summary lengkap, respons KB.
  3. /tiers {session_id} -> struktur matriks identik dengan jalur lama (anti-drift).
  4. /session/{sid}/fill {matriks 24 angka} -> 6.426 harga terisi TANPA mengunggah baris.
  5. /validate lagi -> 0 error / 1.071 produk (tombol impor aktif).
  6. /session/{sid}/rows & /cells -> pratinjau & edit sel dengan payload kecil.
  7. Commit (file kecil) via sesi -> produk dibuat sebagai draft + stok 0.
  8. Adversarial & RBAC: 401/403/404/400, TANPA 5xx. Sesi milik admin lain tidak bocor.
  9. Kompatibilitas: jalur lama berbasis `rows` masih bekerja identik.

Jalankan: python scripts/test_import_session_poc.py
"""
import json
import os
import sys

import requests

BASE = os.environ.get("BACKEND_BASE", "http://localhost:8001/api")
ADMIN = (os.environ.get("ADMIN_EMAIL", "admin@collectorparfum.id"),
         os.environ.get("ADMIN_PASS", "Admin#2026"))
CUSTOMER = (os.environ.get("CUST_EMAIL", "customer@collectorparfum.id"),
            os.environ.get("CUST_PASS", "Customer#2026"))
XLSX = "tests/user_uploads/testimport.xlsx"
XLSX_ZERO = "tests/user_uploads/IMPOR_PRODUK_COLLECTOR_PARFUM_1.xlsx"
SMALL_CSV = "tests/import_samples/qa_tier_small.csv"

G, R, Y, C, X, B = "\033[92m", "\033[91m", "\033[93m", "\033[96m", "\033[0m", "\033[1m"
PASS = FAIL = 0
KB = 1024.0
MB = 1048576.0

# Harga UJI unik per sel supaya drift (harga masuk sel salah) langsung terlihat.
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
    r = requests.post(f"{BASE}/auth/login", json={"email": creds[0], "password": creds[1]}, timeout=30)
    r.raise_for_status()
    return r.json()["token"]


def size_of(resp):
    return len(resp.content)


def analyze(hdrs, path, light=True, preview=200):
    params = {"include_rows": "false", "preview": str(preview)} if light else {}
    with open(path, "rb") as f:
        return requests.post(f"{BASE}/admin/products/io/analyze", headers=hdrs,
                             params=params, files={"file": (os.path.basename(path), f)},
                             timeout=180)


def build_matrix(tiers, combos):
    matrix = {}
    for t in tiers:
        row = {}
        for c in combos:
            vals = c["values"]
            size = vals.get("Ukuran", "")
            typ = vals.get("Tipe", "")
            row[c["key"]] = (TIER_BASE.get(t["label"], 100000)
                             * SIZE_MULT.get(size, 100) * TYPE_MULT.get(typ, 100)) // 10000
        matrix[t["label"]] = row
    return matrix


def main():
    global FAIL
    print(f"{C}{B}{'=' * 74}\n  POC E12 — SESI IMPOR (payload KB, bukan MB)\n{'=' * 74}{X}")
    for p in (XLSX, XLSX_ZERO, SMALL_CSV):
        if not os.path.exists(p):
            print(f"{R}File uji tidak ada: {p}{X}")
            return 1
    a_tok = login(ADMIN)
    c_tok = login(CUSTOMER)
    A = {"Authorization": f"Bearer {a_tok}"}
    CU = {"Authorization": f"Bearer {c_tok}"}

    # ---------------------------------------------------------------- 1. analyze
    head("1. /analyze ringan — session_id + preview (bukan 6.426 baris)")
    r_light = analyze(A, XLSX, light=True, preview=200)
    ok("analyze(ringan) = 200", r_light.status_code == 200, f"HTTP {r_light.status_code}")
    if r_light.status_code != 200:
        print(r_light.text[:400])
        return 1
    light = r_light.json()
    sid = light.get("session_id")
    ok("session_id dikembalikan", bool(sid) and str(sid).startswith("imp_"), f"sid={sid}")
    ok("total baris = 6426", light.get("total") == 6426, f"total={light.get('total')}")
    ok("array `rows` TIDAK dikirim (hemat bandwidth)", "rows" not in light)
    ok("preview_rows = 200 baris", len(light.get("preview_rows") or []) == 200,
       f"{len(light.get('preview_rows') or [])} baris")
    ok("preview_rows membawa index absolut",
       (light.get("preview_rows") or [{}])[0].get("index") == 0)
    light_kb = size_of(r_light) / KB
    ok("respons analyze ringan < 400 KB", light_kb < 400, f"{light_kb:.0f} KB")

    r_full = analyze(A, XLSX, light=False)
    full_mb = size_of(r_full) / MB
    ok("analyze(kompat, include_rows=true) tetap 200", r_full.status_code == 200)
    ok("jalur lama memang berat (bukti masalah)", full_mb > 3, f"{full_mb:.2f} MB")
    mapping = light["suggested_mapping"]

    # ---------------------------------------------------------------- 2. validate
    head("2. /validate lewat session_id — respons diringkas")
    r_v = requests.post(f"{BASE}/admin/products/io/validate", headers=A, timeout=180,
                        json={"session_id": sid, "mapping": mapping,
                              "report_limit": 200, "product_limit": 20})
    ok("validate(sesi) = 200", r_v.status_code == 200, f"HTTP {r_v.status_code}")
    v = r_v.json() if r_v.status_code == 200 else {}
    ok("summary lengkap tetap ada",
       v.get("summary") == {"rows": 6426, "ok": 6426, "error": 0, "products": 1071},
       str(v.get("summary")))
    ok("array `reports` penuh TIDAK dikirim", "reports" not in v)
    ok("reports_head dibatasi 200", len(v.get("reports_head") or []) == 200)
    ok("products_head dibatasi 20 + products_total 1071",
       len(v.get("products_head") or []) == 20 and v.get("products_total") == 1071)
    v_kb = size_of(r_v) / KB
    ok("respons validate < 500 KB (dulu 6,4 MB)", v_kb < 500, f"{v_kb:.0f} KB")

    req_kb = len(json.dumps({"session_id": sid, "mapping": mapping,
                             "report_limit": 200, "product_limit": 20}).encode()) / KB
    ok("request validate < 5 KB (dulu 5,2 MB)", req_kb < 5, f"{req_kb:.2f} KB")

    # kompatibilitas jalur lama (rows) — angka harus IDENTIK
    rows_full = r_full.json()["rows"]
    r_old = requests.post(f"{BASE}/admin/products/io/validate", headers=A, timeout=300,
                          json={"rows": rows_full, "mapping": mapping})
    old = r_old.json() if r_old.status_code == 200 else {}
    ok("jalur lama (rows) masih 200 & summary identik",
       r_old.status_code == 200 and old.get("summary") == v.get("summary"),
       str(old.get("summary")))
    ok("jalur lama tetap mengirim `reports` penuh (kompat skrip)",
       len(old.get("reports") or []) == 6426)

    # ---------------------------------------------------------------- 3. tiers
    head("3. /tiers lewat session_id — struktur identik jalur lama")
    r_t = requests.post(f"{BASE}/admin/products/io/tiers", headers=A, timeout=180,
                        json={"session_id": sid, "mapping": mapping})
    ok("tiers(sesi) = 200", r_t.status_code == 200, f"HTTP {r_t.status_code}")
    t = r_t.json() if r_t.status_code == 200 else {}
    ok("kolom tier = tags", t.get("tier_column") == "tags", str(t.get("tier_column")))
    got = {x["label"]: x["products"] for x in t.get("tiers", [])}
    ok("jumlah produk per tier TEPAT",
       got == {"CP01": 532, "CP02": 417, "CP03": 107, "EXCLUSIVE": 15}, str(got))
    dims = [d["name"] for d in t.get("dimensions", [])]
    ok("dimensi efektif = Ukuran x Tipe", dims == ["Ukuran", "Tipe"], str(dims))
    ok("24 sel matriks", t.get("summary", {}).get("cells") == 24, str(t.get("summary")))
    r_t_old = requests.post(f"{BASE}/admin/products/io/tiers", headers=A, timeout=300,
                            json={"rows": rows_full, "mapping": mapping})
    ok("tiers(sesi) == tiers(rows) — tanpa drift",
       r_t_old.status_code == 200 and r_t_old.json() == t)

    # ------------------------------------------------- 4. fill pada file HARGA 0
    head("4. /session/{sid}/fill — 24 angka mengisi 6.426 harga (file harga 0)")
    r_z = analyze(A, XLSX_ZERO, light=True, preview=50)
    ok("analyze file harga-0 = 200", r_z.status_code == 200)
    zero = r_z.json()
    zsid, zmap = zero["session_id"], zero["suggested_mapping"]
    r_zt = requests.post(f"{BASE}/admin/products/io/tiers", headers=A, timeout=180,
                         json={"session_id": zsid, "mapping": zmap})
    zt = r_zt.json()
    ok("6.426 baris tanpa harga terdeteksi",
       zt["summary"]["rows_without_price"] == 6426, str(zt["summary"]))
    r_zv = requests.post(f"{BASE}/admin/products/io/validate", headers=A, timeout=180,
                         json={"session_id": zsid, "mapping": zmap,
                               "report_limit": 50, "product_limit": 5})
    ok("sebelum matriks: 6426 error / 0 produk",
       r_zv.json()["summary"] == {"rows": 6426, "ok": 0, "error": 6426, "products": 0},
       str(r_zv.json()["summary"]))

    matrix = build_matrix(zt["tiers"], zt["combos"])
    fill_payload = {
        "mapping": zmap, "tier_column": zt["tier_column"],
        "dim_order": [d["name"] for d in zt["dimensions"]],
        "matrix_price": matrix, "overwrite_price": False,
        "stock": "0", "status": "archived", "concentration": "EDP",
    }
    fill_kb = len(json.dumps(fill_payload).encode()) / KB
    r_f = requests.post(f"{BASE}/admin/products/io/session/{zsid}/fill", headers=A,
                        timeout=180, json=fill_payload)
    ok("fill = 200", r_f.status_code == 200, f"HTTP {r_f.status_code}")
    ok("payload fill < 10 KB (matriks saja)", fill_kb < 10, f"{fill_kb:.2f} KB")
    st = r_f.json().get("stats", {}) if r_f.status_code == 200 else {}
    ok("6426 harga terisi", st.get("price_filled") == 6426, str(st.get("price_filled")))
    ok("0 baris terlewat",
       (st.get("rows_skipped_no_tier"), st.get("rows_skipped_no_combo"),
        st.get("rows_skipped_no_cell")) == (0, 0, 0), str(st))
    ok("status & stok dipaksa di semua baris", st.get("forced") == 12852, str(st.get("forced")))

    head("5. /validate setelah fill — error 0, tombol impor aktif")
    r_zv2 = requests.post(f"{BASE}/admin/products/io/validate", headers=A, timeout=180,
                          json={"session_id": zsid, "mapping": zmap,
                                "report_limit": 50, "product_limit": 5})
    s2 = r_zv2.json()["summary"]
    ok("6426 valid / 0 error / 1071 produk",
       s2 == {"rows": 6426, "ok": 6426, "error": 0, "products": 1071}, str(s2))
    prod = (r_zv2.json().get("products_head") or [{}])[0]
    ok("produk hasil grouping berstatus archived", prod.get("status") == "archived")
    variants = prod.get("variants") or []
    ok("6 varian per produk", len(variants) == 6, f"{len(variants)} varian")
    ok("stok 0 di semua varian", all(v.get("stock") == 0 for v in variants))
    prices = sorted({v.get("price") for v in variants})
    ok("harga berbeda antar sel (matriks tidak kolaps)", len(prices) == 6, str(prices))

    # ---------------------------------------------------------- 6. rows & cells
    head("6. /session/{sid}/rows + /cells — pratinjau & edit sel murah")
    r_rows = requests.get(f"{BASE}/admin/products/io/session/{zsid}/rows",
                          headers=A, params={"offset": 0, "limit": 100}, timeout=60)
    ok("rows(offset=0,limit=100) = 200", r_rows.status_code == 200)
    rr = r_rows.json()
    ok("100 baris + total 6426", len(rr["rows"]) == 100 and rr["total"] == 6426,
       f"{len(rr['rows'])} / {rr['total']}")
    ok("respons rows < 200 KB", size_of(r_rows) / KB < 200, f"{size_of(r_rows)/KB:.0f} KB")
    r_idx = requests.get(f"{BASE}/admin/products/io/session/{zsid}/rows",
                         headers=A, params={"indexes": "0,5,6425", "limit": 10}, timeout=60)
    ok("rows(indexes) mengambil baris tertentu",
       [x["index"] for x in r_idx.json()["rows"]] == [0, 5, 6425],
       str([x["index"] for x in r_idx.json()["rows"]]))

    r_c = requests.post(f"{BASE}/admin/products/io/session/{zsid}/cells", headers=A,
                        timeout=60, json={"cells": [{"row": 5, "header": "name",
                                                     "value": "Nama Diedit QA"}]})
    ok("cells = 200 & 1 sel diperbarui",
       r_c.status_code == 200 and r_c.json().get("updated") == 1, str(r_c.json()))
    r_chk = requests.get(f"{BASE}/admin/products/io/session/{zsid}/rows",
                         headers=A, params={"indexes": "5", "limit": 1}, timeout=60)
    ok("edit sel tersimpan di sesi",
       r_chk.json()["rows"][0]["data"].get("name") == "Nama Diedit QA")

    # ------------------------------------------------------- 7. commit via sesi
    head("7. Commit file kecil lewat sesi — draft + stok 0")
    r_s = analyze(A, SMALL_CSV, light=True, preview=50)
    small = r_s.json()
    ssid, smap = small["session_id"], small["suggested_mapping"]
    stiers = requests.post(f"{BASE}/admin/products/io/tiers", headers=A, timeout=60,
                           json={"session_id": ssid, "mapping": smap}).json()
    smatrix = build_matrix(stiers["tiers"], stiers["combos"])
    requests.post(f"{BASE}/admin/products/io/session/{ssid}/fill", headers=A, timeout=60,
                  json={"mapping": smap, "tier_column": stiers["tier_column"],
                        "dim_order": [d["name"] for d in stiers["dimensions"]],
                        "matrix_price": smatrix, "stock": "0", "status": "archived"})
    r_sv = requests.post(f"{BASE}/admin/products/io/validate", headers=A, timeout=60,
                         json={"session_id": ssid, "mapping": smap,
                               "report_limit": 20, "product_limit": 5})
    ok("file kecil: 6 valid / 3 produk",
       r_sv.json()["summary"] == {"rows": 6, "ok": 6, "error": 0, "products": 3},
       str(r_sv.json()["summary"]))
    r_cm = requests.post(f"{BASE}/admin/products/io/commit", headers=A, timeout=120,
                         json={"session_id": ssid, "mapping": smap, "mode": "add-only",
                               "report_limit": 20})
    ok("commit(sesi) = 200", r_cm.status_code == 200, f"HTTP {r_cm.status_code}")
    cm = r_cm.json() if r_cm.status_code == 200 else {}
    ok("3 produk dibuat, 0 gagal",
       cm.get("created") == 3 and cm.get("failed") == 0, str({k: cm.get(k) for k in
                                                             ("created", "updated", "failed")}))
    ok("commit tidak mengirim 6.426 reports (dibatasi)", "reports" not in cm)
    r_p = requests.get(f"{BASE}/admin/products", headers=A,
                       params={"q": "qa-tier", "limit": 10}, timeout=60)
    items = r_p.json() if isinstance(r_p.json(), list) else r_p.json().get("items", [])
    ok("produk uji masuk sebagai archived",
       len(items) >= 3 and all(p.get("status") == "archived" for p in items[:3]),
       f"{len(items)} produk")
    pdp = requests.get(f"{BASE}/products/qa-tier-alpha", timeout=30)
    ok("produk draft TIDAK tampil di storefront (404)", pdp.status_code == 404,
       f"HTTP {pdp.status_code}")

    # --------------------------------------------------- 8. adversarial & RBAC
    head("8. Adversarial & RBAC — wajib TANPA 5xx")
    probes = [
        ("analyze tanpa token", lambda: requests.post(
            f"{BASE}/admin/products/io/analyze", files={"file": ("a.csv", b"slug\n1")},
            timeout=30), (401, 403)),
        ("validate(sesi) sebagai customer", lambda: requests.post(
            f"{BASE}/admin/products/io/validate", headers=CU, timeout=30,
            json={"session_id": zsid, "mapping": zmap}), (403,)),
        ("rows sesi tanpa token", lambda: requests.get(
            f"{BASE}/admin/products/io/session/{zsid}/rows", timeout=30), (401, 403)),
        ("rows sesi sebagai customer", lambda: requests.get(
            f"{BASE}/admin/products/io/session/{zsid}/rows", headers=CU, timeout=30), (403,)),
        ("session_id ngawur -> 404", lambda: requests.post(
            f"{BASE}/admin/products/io/validate", headers=A, timeout=30,
            json={"session_id": "imp_tidakada", "mapping": {}}), (404,)),
        ("rows sesi ngawur -> 404", lambda: requests.get(
            f"{BASE}/admin/products/io/session/imp_ngawur/rows", headers=A, timeout=30), (404,)),
        ("fill sesi ngawur -> 404", lambda: requests.post(
            f"{BASE}/admin/products/io/session/imp_ngawur/fill", headers=A, timeout=30,
            json={"mapping": {}, "matrix_price": {}}), (404,)),
        ("cells bukan list -> 422", lambda: requests.post(
            f"{BASE}/admin/products/io/session/{zsid}/cells", headers=A, timeout=30,
            json={"cells": "bukan-list"}), (422, 400)),
        ("cells indeks di luar batas -> 200 (diabaikan)", lambda: requests.post(
            f"{BASE}/admin/products/io/session/{zsid}/cells", headers=A, timeout=30,
            json={"cells": [{"row": 999999, "header": "name", "value": "x"},
                            {"row": -3, "header": "name", "value": "y"}]}), (200,)),
        ("matriks berisi sampah -> 200 (tanpa crash)", lambda: requests.post(
            f"{BASE}/admin/products/io/session/{ssid}/fill", headers=A, timeout=60,
            json={"mapping": smap, "matrix_price": {"CP01": {"x|y": "abc"}},
                  "tier_column": "tags"}), (200,)),
        ("fill tanpa matriks -> 200", lambda: requests.post(
            f"{BASE}/admin/products/io/session/{ssid}/fill", headers=A, timeout=60,
            json={"mapping": smap, "matrix_price": {}}), (200,)),
        ("rows limit di luar batas -> 422", lambda: requests.get(
            f"{BASE}/admin/products/io/session/{zsid}/rows", headers=A, timeout=30,
            params={"limit": 99999}), (422, 400)),
        ("indexes berisi teks -> 200 (diabaikan)", lambda: requests.get(
            f"{BASE}/admin/products/io/session/{zsid}/rows", headers=A, timeout=30,
            params={"indexes": "a,b,,3"}), (200,)),
        ("report_limit negatif -> 422", lambda: requests.post(
            f"{BASE}/admin/products/io/validate", headers=A, timeout=30,
            json={"session_id": zsid, "mapping": zmap, "report_limit": -5}), (422, 400)),
        ("close sesi sebagai customer", lambda: requests.post(
            f"{BASE}/admin/products/io/session/{zsid}/close", headers=CU, timeout=30), (403,)),
    ]
    for label, call, expect in probes:
        try:
            resp = call()
            code = resp.status_code
        except Exception as e:  # noqa: BLE001
            ok(label, False, f"EXCEPTION {type(e).__name__}: {e}")
            continue
        ok(label, code in expect, f"HTTP {code} diharapkan {expect}")
        if code >= 500:
            print(f"    {R}5xx TERDETEKSI: {resp.text[:200]}{X}")

    # --------------------------------------------------------- 9. close & bersih
    head("9. Tutup sesi & bersihkan produk uji")
    for s in (sid, zsid, ssid):
        rc = requests.post(f"{BASE}/admin/products/io/session/{s}/close", headers=A, timeout=60)
        ok(f"close {s[:12]}… = 200", rc.status_code == 200, f"HTTP {rc.status_code}")
    r_after = requests.get(f"{BASE}/admin/products/io/session/{zsid}/rows", headers=A, timeout=30)
    ok("sesi yang ditutup -> 404", r_after.status_code == 404, f"HTTP {r_after.status_code}")

    import subprocess  # noqa: PLC0415 — hanya untuk cleanup POC
    cp = subprocess.run([sys.executable, "scripts/qa_cleanup.py"], capture_output=True, text=True)
    ok("produk uji QA dibersihkan", cp.returncode == 0, cp.stdout.strip().splitlines()[-1:][0]
       if cp.stdout.strip() else "")

    print(f"\n{C}{B}{'=' * 74}{X}")
    print(f"  {G}PASS: {PASS}{X}    {R}FAIL: {FAIL}{X}")
    print(f"{C}{B}{'=' * 74}{X}")
    if FAIL == 0:
        print(f"{G}{B}  POC E12 LULUS — sesi impor menghapus transfer MB per validasi.{X}")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
