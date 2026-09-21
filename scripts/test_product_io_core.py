#!/usr/bin/env python3
"""test_product_io_core.py — POC/core test Export & Smart Import produk (Epic E10).

Cakupan:
  A. Export CSV + XLSX (auth admin) parseable & memuat varian noir (typed).
  B. Template CSV + XLSX terunduh.
  C. Analyze: header non-baku -> suggested_mapping benar + rows.
  D. Validate: baris valid + invalid -> products/reports/summary row-level.
  E. Commit add-only: buat produk baru (typed) -> tampil di storefront (Type+Size).
  F. Commit upsert: update harga produk yg sama -> berubah, tak duplikat.
  G. Round-trip: export -> re-import (upsert) -> tak korup (jumlah produk stabil).

Usage: cd /app && python scripts/test_product_io_core.py   (exit 0 = PASS)
"""
import asyncio
import io
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
import csv as csvmod
import httpx
from motor.motor_asyncio import AsyncIOMotorClient

from services.product_io import (
    parse_money, parse_int, parse_ml, parse_bool, parse_list, slugify, gen_variant_sku,
)
from services.product_import import suggest_mapping, validate_and_group

API = os.environ.get("API_BASE", "http://localhost:8001").rstrip("/")
MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "test_database")
ADMIN = {"email": os.environ.get("ADMIN_EMAIL", "admin@collectorparfum.id"),
         "password": os.environ.get("ADMIN_PASS", "Admin#2026")}
G, R, B, X = "\033[92m", "\033[91m", "\033[1m", "\033[0m"
passed = failed = 0


def ok(m):
    global passed
    passed += 1
    print(f"  {G}[OK]{X} {m}")


def bad(m):
    global failed
    failed += 1
    print(f"  {R}[FAIL]{X} {m}")


def _optval(row, dim_name):
    """Ambil nilai dimensi (Shopify-style) dari baris export: cari option{i}_name==dim_name."""
    for i in range(1, 5):
        if row.get(f"option{i}_name") == dim_name:
            return row.get(f"option{i}_value")
    return None


async def main():
    print(f"\n{B}{'='*64}{X}\n  EXPORT/IMPORT CORE  API={API}\n{B}{'='*64}{X}")
    db = AsyncIOMotorClient(MONGO_URL)[DB_NAME]
    slug_typed = "impor-uji-signature"
    await db.products.delete_many({"slug": {"$regex": "^(impor|fuzz)-uji"}})
    async with httpx.AsyncClient(timeout=40) as c:
        tok = (await c.post(f"{API}/api/auth/login", json=ADMIN)).json()["token"]
        h = {"Authorization": f"Bearer {tok}"}

        # A. Export CSV + XLSX
        print(f"\n{B}A. Export (N-dimensi){X}")
        rc = await c.get(f"{API}/api/admin/products/io/export?format=csv", headers=h)
        if rc.status_code == 200 and "noir-oud-intense" in rc.text and "option1_name" in rc.text:
            reader = list(csvmod.DictReader(io.StringIO(rc.content.decode("utf-8-sig"))))
            noir_rows = [r for r in reader if r["slug"] == "noir-oud-intense"]
            tipe_vals = {_optval(r, "Tipe") for r in noir_rows}
            if len(noir_rows) == 6 and tipe_vals == {"Standard", "Premium"}:
                ok(f"export CSV: {len(reader)} baris varian; noir 6 varian (Tipe Standard+Premium)")
            else:
                bad(f"export CSV noir varian salah: rows={len(noir_rows)} tipe={tipe_vals}")
        else:
            bad(f"export CSV gagal: {rc.status_code}")
        rx = await c.get(f"{API}/api/admin/products/io/export?format=xlsx", headers=h)
        if rx.status_code == 200 and rx.content[:2] == b"PK" and len(rx.content) > 2000:
            ok(f"export XLSX: {len(rx.content)} bytes (zip/xlsx valid)")
        else:
            bad(f"export XLSX gagal: {rx.status_code} len={len(rx.content)}")

        # B. Template
        print(f"\n{B}B. Template{X}")
        tcsv = await c.get(f"{API}/api/admin/products/io/template?format=csv", headers=h)
        txlsx = await c.get(f"{API}/api/admin/products/io/template?format=xlsx", headers=h)
        if tcsv.status_code == 200 and "option1_name" in tcsv.text and "Ukuran" in tcsv.text:
            ok("template CSV OK (N-dimensi: kolom option + dimensi Ukuran)")
        else:
            bad(f"template CSV gagal: {tcsv.status_code}")
        if txlsx.status_code == 200 and txlsx.content[:2] == b"PK":
            ok("template XLSX OK")
        else:
            bad(f"template XLSX gagal: {txlsx.status_code}")

        # C. Analyze (header non-baku)
        print(f"\n{B}C. Analyze — smart mapping header non-baku{X}")
        csv_text = (
            "Nama Produk,Kategori,Tipe,Ukuran (ml),Harga,Harga Coret,Stok,SKU,Gender,Deskripsi\n"
            "Impor Uji Signature,amber,Standard,50,Rp 450.000,,10,,Unisex,Parfum uji impor\n"
            "Impor Uji Signature,amber,Premium,100,850000,990000,5,,,Parfum uji impor\n"
            "Impor Uji Reguler,floral,,30,150000,,20,,Wanita,Reguler uji\n"
            ",amber,,50,100000,,1,,,baris tanpa nama (error)\n"
            "Impor Uji Salah,tidakada,,50,100000,,1,,,kategori tak dikenal (error)\n"
        )
        files = {"file": ("uji.csv", csv_text.encode("utf-8"), "text/csv")}
        ra = await c.post(f"{API}/api/admin/products/io/analyze", headers=h, files=files)
        if ra.status_code != 200:
            bad(f"analyze gagal: {ra.status_code} {ra.text[:150]}")
            mapping, rows = {}, []
        else:
            j = ra.json()
            mapping, rows = j["suggested_mapping"], j["rows"]
            need = {"name": "Nama Produk", "category": "Kategori", "variant_type": "Tipe",
                    "variant_ml": "Ukuran (ml)", "variant_price": "Harga",
                    "variant_compare_at_price": "Harga Coret", "variant_stock": "Stok"}
            if all(mapping.get(k) == v for k, v in need.items()) and j["total"] == 5:
                ok(f"analyze: mapping cerdas benar, {j['total']} baris")
            else:
                bad(f"analyze mapping salah: {[(k, mapping.get(k)) for k in need]}")

        # D. Validate
        print(f"\n{B}D. Validate — row-level{X}")
        rv = await c.post(f"{API}/api/admin/products/io/validate", headers=h,
                          json={"rows": rows, "mapping": mapping})
        if rv.status_code == 200:
            s = rv.json()["summary"]
            if s["ok"] == 3 and s["error"] == 2 and s["products"] == 2:
                ok(f"validate: {s['ok']} valid, {s['error']} error, {s['products']} produk")
            else:
                bad(f"validate summary salah: {s}")
        else:
            bad(f"validate gagal: {rv.status_code}")

        # E. Commit add-only
        print(f"\n{B}E. Commit add-only{X}")
        rco = await c.post(f"{API}/api/admin/products/io/commit", headers=h,
                           json={"rows": rows, "mapping": mapping, "mode": "add-only"})
        if rco.status_code == 200:
            res = rco.json()
            if res["created"] == 2 and res["failed"] == 0:
                ok(f"commit add-only: created={res['created']}, row_errors={res.get('row_errors')}")
            else:
                bad(f"commit add-only salah: {res}")
        else:
            bad(f"commit add-only gagal: {rco.status_code} {rco.text[:150]}")

        # verifikasi produk typed tampil di storefront (N-dimensi: Konsentrasi×Tipe×Ukuran)
        pr = await c.get(f"{API}/api/products/{slug_typed}")
        if pr.status_code == 200:
            pj = pr.json()
            vs = pj["variants"]
            tipes = {v["options"].get("Tipe") for v in vs}
            if tipes == {"Standard", "Premium"} and pj["price"] == 450000 and all(v.get("sku") for v in vs):
                ok("produk hasil impor tampil: Tipe Standard+Premium, harga 'mulai dari' 450000, SKU auto")
            else:
                bad(f"produk impor tak sesuai: tipes={tipes} price={pj['price']}")
        else:
            bad(f"produk impor tak ada di storefront: {pr.status_code}")

        # F. Commit upsert (ubah harga Standard 50 -> 480000)
        print(f"\n{B}F. Commit upsert{X}")
        rows2 = [dict(r) for r in rows]
        for r in rows2:
            if r.get("Tipe") == "Standard" and r.get("Ukuran (ml)") == "50":
                r["Harga"] = "480000"
        before = await db.products.count_documents({})
        rup = await c.post(f"{API}/api/admin/products/io/commit", headers=h,
                           json={"rows": rows2, "mapping": mapping, "mode": "upsert"})
        after = await db.products.count_documents({})
        if rup.status_code == 200:
            res = rup.json()
            pr2 = await c.get(f"{API}/api/products/{slug_typed}")
            std50 = next((v for v in pr2.json()["variants"]
                          if v["options"].get("Tipe") == "Standard" and v["options"].get("Ukuran") == "50ml"), None)
            if res["updated"] == 2 and res["created"] == 0 and before == after and std50 and std50["price"] == 480000:
                ok(f"commit upsert: updated=2, tanpa duplikat (produk {before}->{after}), harga Standard50=480000")
            else:
                bad(f"upsert salah: res={res} before={before} after={after} std50={std50}")
        else:
            bad(f"commit upsert gagal: {rup.status_code}")

        # G. Round-trip export -> re-import upsert
        print(f"\n{B}G. Round-trip export -> re-import{X}")
        exp = await c.get(f"{API}/api/admin/products/io/export?format=csv", headers=h)
        exp_rows = list(csvmod.DictReader(io.StringIO(exp.content.decode("utf-8-sig"))))
        cnt_before = await db.products.count_documents({})
        # mapping identitas: kolom sudah kanonik (header = EXPORT_COLUMNS)
        ident = {k: k for k in exp_rows[0].keys()}
        rr = await c.post(f"{API}/api/admin/products/io/commit", headers=h,
                          json={"rows": exp_rows, "mapping": ident, "mode": "upsert"})
        cnt_after = await db.products.count_documents({})
        if rr.status_code == 200 and cnt_before == cnt_after and rr.json()["failed"] == 0:
            ok(f"round-trip: {len(exp_rows)} baris re-import, produk stabil {cnt_before}=={cnt_after}, 0 gagal")
        else:
            bad(f"round-trip gagal: {rr.status_code} before={cnt_before} after={cnt_after} res={rr.json() if rr.status_code==200 else rr.text[:120]}")

        # ---------------------------------------------------------------------
        # H. FUZZ fungsi murni (parser + mapping + grouping) — deterministik, tak crash.
        # ---------------------------------------------------------------------
        print(f"\n{B}H. Fuzz fungsi murni{X}")
        pf = []
        money_cases = [("-50", -50), ("Rp 1.234.567", 1234567), ("385,000", 385000),
                       ("", 0), (None, 0), (3.14, 3), ("abc", 0), ("  ", 0),
                       (1000000000000, 1000000000000), ("-0", 0), (" -Rp 50.000", -50000)]
        for inp, exp in money_cases:
            if parse_money(inp) != exp:
                pf.append(f"money({inp!r})={parse_money(inp)}!={exp}")
        for inp, exp in [("-5", -5), ("10 pcs", 10), ("", 0), ("abc", 0), (None, 0), (7.9, 7)]:
            if parse_int(inp) != exp:
                pf.append(f"int({inp!r})={parse_int(inp)}!={exp}")
        for inp, exp in [("50 ml", 50), ("-10", -10), ("0", 0), ("", 0), ("xl", 0)]:
            if parse_ml(inp) != exp:
                pf.append(f"ml({inp!r})={parse_ml(inp)}!={exp}")
        for inp, exp in [("true", True), ("Ya", True), ("1", True), ("no", False), ("", False), ("aktif", True)]:
            if parse_bool(inp) != exp:
                pf.append(f"bool({inp!r})={parse_bool(inp)}!={exp}")
        if parse_list("a, b|c\nd;e") != ["a", "b", "c", "d", "e"]:
            pf.append("list.split")
        if parse_list(["x", " x ", "y"]) != ["x", "y"] or parse_list("") != [] or parse_list(None) != []:
            pf.append("list.dedup/empty")
        if slugify("Café Noir 50ml!!") != "caf-noir-50ml" or slugify("   ") != "produk":
            pf.append("slugify")
        if not pf:
            ok(f"parser toleran: {len(money_cases)+18} kasus adversarial benar (harga negatif TETAP negatif -> ditolak validasi)")
        else:
            bad("parser fuzz: " + "; ".join(pf[:6]))

        # H2 suggest_mapping tahan header kosong/duplikat/unicode/None
        m_empty = suggest_mapping([])
        m_std = suggest_mapping(["Nama Produk", "Kategori", "Ukuran (ml)", "Harga"])
        m_weird = suggest_mapping(["Harga", "Harga", "💰", "", "SKU", None])
        smf = []
        if any(v is not None for v in m_empty.values()):
            smf.append("empty!=None")
        for k, v in {"name": "Nama Produk", "category": "Kategori",
                     "variant_ml": "Ukuran (ml)", "variant_price": "Harga"}.items():
            if m_std.get(k) != v:
                smf.append(f"std.{k}={m_std.get(k)}")
        if m_weird.get("variant_sku") != "SKU":
            smf.append(f"weird.sku={m_weird.get('variant_sku')}")
        if not smf:
            ok("suggest_mapping tahan header kosong/duplikat/unicode/None (deterministik)")
        else:
            bad("suggest_mapping: " + "; ".join(smf))

        # H3 validate_and_group edge (row-level): dup/cap/neg/no-name/unknown-cat -> error; valid tetap diproses.
        jmp = {"name": "nm", "category": "cat", "variant_type": "tp",
               "variant_ml": "ml", "variant_price": "pr", "variant_compare_at_price": "cap"}
        fuzz_rows = [
            {"nm": "Fuzz A", "cat": "amber", "tp": "Std", "ml": "50", "pr": "100000", "cap": ""},
            {"nm": "Fuzz A", "cat": "amber", "tp": "Std", "ml": "50", "pr": "120000", "cap": ""},
            {"nm": "Fuzz A", "cat": "amber", "tp": "Premium", "ml": "100", "pr": "200000", "cap": "150000"},
            {"nm": "Fuzz B", "cat": "floral", "tp": "", "ml": "30", "pr": "-5", "cap": ""},
            {"nm": "", "cat": "amber", "tp": "", "ml": "50", "pr": "100000", "cap": ""},
            {"nm": "Fuzz C", "cat": "amber", "tp": "T" * 200, "ml": "50", "pr": "90000", "cap": ""},
            {"nm": "Fuzz A", "cat": "tidakada", "tp": "Deluxe", "ml": "200", "pr": "300000", "cap": ""},
        ]
        prods_f, reps_f = validate_and_group(fuzz_rows, jmp, {"amber", "floral"})
        statuses = [r["status"] for r in reps_f]
        pa = next((p for p in prods_f if p["name"] == "Fuzz A"), None)
        pc = next((p for p in prods_f if p["name"] == "Fuzz C"), None)
        ep, er = validate_and_group([], jmp, {"amber"})
        vgf = []
        if statuses != ["ok", "error", "error", "error", "error", "ok", "error"]:
            vgf.append(f"status={statuses}")
        if len(prods_f) != 2:
            vgf.append(f"products={len(prods_f)}")
        if not pa or len(pa["variants"]) != 1:
            vgf.append(f"FuzzA.variants={len(pa['variants']) if pa else None}")
        if not pc or len(pc["variants"][0]["options"].get("Tipe", "")) != 60:
            vgf.append("FuzzC.Tipe!=60")
        if ep != [] or er != []:
            vgf.append("empty!=([],[])")
        if not vgf:
            ok("validate_and_group: dup/cap/neg/no-name/unknown-cat -> error row-level; valid diproses; type dipotong 60; empty aman")
        else:
            bad("validate_and_group: " + "; ".join(vgf))

        # H4 SKU auto unik saat tabrakan
        s1 = gen_variant_sku("Prod", "Std", 50, set())
        s2 = gen_variant_sku("Prod", "Std", 50, {"PROD-STD-50ML"})
        s3 = gen_variant_sku("Prod", "Std", 50, {"PROD-STD-50ML", "PROD-STD-50ML-2"})
        if (s1, s2, s3) == ("PROD-STD-50ML", "PROD-STD-50ML-2", "PROD-STD-50ML-3"):
            ok("gen_variant_sku deterministik + unik saat tabrakan")
        else:
            bad(f"gen_variant_sku: {s1} {s2} {s3}")

        # ---------------------------------------------------------------------
        # I. ADVERSARIAL HTTP — endpoint tak boleh 5xx; input buruk -> 400/422 rapi.
        # ---------------------------------------------------------------------
        print(f"\n{B}I. Adversarial HTTP (no 5xx){X}")
        AZ = f"{API}/api/admin/products/io/analyze"
        r_empty = await c.post(AZ, headers=h, files={"file": ("k.csv", b"", "text/csv")})
        r_txt = await c.post(AZ, headers=h, files={"file": ("data.txt", b"a,b\n1,2", "text/plain")})
        r_badx = await c.post(AZ, headers=h, files={"file": ("rusak.xlsx", b"NOT_A_REAL_XLSX" * 20, "application/octet-stream")})
        if r_empty.status_code == 400 and r_txt.status_code == 400 and r_badx.status_code == 400:
            ok("analyze menolak rapi: file kosong/ekstensi salah/xlsx rusak -> 400 (bukan 5xx)")
        else:
            bad(f"analyze 400 gagal: empty={r_empty.status_code} txt={r_txt.status_code} badxlsx={r_badx.status_code}")

        messy = (
            'Nama Produk,Kategori,Ukuran (ml),Harga,Catatan\n'
            '"Parfum, Deluxe",amber,50,"Rp 1.234.000",catatan biasa\n'
            'Ragged Row,amber,30\n'
            'Extra,amber,50,100000,ok,KOLOM,EKSTRA\n'
            '\n'
        )
        r_messy = await c.post(AZ, headers=h, files={"file": ("messy.csv", messy.encode("utf-8-sig"), "text/csv")})
        r_hdr = await c.post(AZ, headers=h, files={"file": ("h.csv", b"name,category,variant_ml,variant_price\n", "text/csv")})
        if (r_messy.status_code == 200 and r_messy.json()["total"] == 3
                and r_hdr.status_code == 200 and r_hdr.json()["total"] == 0):
            ok("analyze CSV kacau (koma-terkutip/kolom kurang-lebih/baris kosong) & header-saja diparse aman")
        else:
            bad(f"analyze messy/header: messy={r_messy.status_code}/{r_messy.text[:80]} hdr={r_hdr.status_code}")

        VD = f"{API}/api/admin/products/io/validate"
        r_ve = await c.post(VD, headers=h, json={"rows": [], "mapping": {}})
        adv_rows = [
            {"nm": "Adv", "cat": "amber", "ml": "50", "pr": "-999"},
            {"nm": None, "cat": "amber", "ml": "abc", "pr": {"x": 1}},
            {"weird": ["nested", "list"]},
        ]
        adv_map = {"name": "nm", "category": "cat", "variant_ml": "ml", "variant_price": "pr"}
        r_adv = await c.post(VD, headers=h, json={"rows": adv_rows, "mapping": adv_map})
        ve_s = r_ve.json().get("summary", {}) if r_ve.status_code == 200 else {}
        adv_s = r_adv.json().get("summary", {}) if r_adv.status_code == 200 else {}
        if (r_ve.status_code == 200 and ve_s == {"rows": 0, "ok": 0, "error": 0, "products": 0}
                and r_adv.status_code == 200 and adv_s.get("error") == 3 and adv_s.get("products") == 0):
            ok("validate: rows kosong -> nol; baris adversarial (neg/None/dict/list) -> 3 error, 0 produk, tanpa 5xx")
        else:
            bad(f"validate adversarial: ve={r_ve.status_code}/{ve_s} adv={r_adv.status_code}/{adv_s}")

        CM = f"{API}/api/admin/products/io/commit"
        r_mode = await c.post(CM, headers=h, json={"rows": [], "mapping": {}, "mode": "bogus"})
        c0 = await db.products.count_documents({})
        r_allerr = await c.post(CM, headers=h, json={"rows": adv_rows, "mapping": adv_map, "mode": "add-only"})
        c1 = await db.products.count_documents({})
        ae = r_allerr.json() if r_allerr.status_code == 200 else {}
        if (r_mode.status_code == 400 and r_allerr.status_code == 200
                and ae.get("created") == 0 and ae.get("failed") == 0
                and ae.get("row_errors", 0) >= 3 and c0 == c1):
            ok(f"commit: mode invalid -> 400; semua-baris-error -> 0 dibuat/0 gagal, {ae.get('row_errors')} row_error, count stabil {c0}")
        else:
            bad(f"commit integritas: mode={r_mode.status_code} allerr={r_allerr.status_code}/{ae} count {c0}->{c1}")

        sweep = [
            (VD, {}), (VD, {"rows": "notalist", "mapping": {}}),
            (VD, {"rows": [123], "mapping": {}}), (VD, {"rows": [{"a": 1}], "mapping": "bad"}),
            (CM, {"rows": [{"a": 1}], "mapping": {}, "mode": "upsert"}),
            (CM, {"mode": "upsert"}),
        ]
        sweep_bad = []
        for url, body in sweep:
            rr2 = await c.post(url, headers=h, json=body)
            if rr2.status_code >= 500:
                sweep_bad.append(f"{url.rsplit('/', 1)[-1]}:{rr2.status_code}")
        if not sweep_bad:
            ok(f"sweep {len(sweep)} body rusak ke validate/commit -> semua < 500 (Pydantic/handler rapi)")
        else:
            bad("sweep 5xx: " + "; ".join(sweep_bad))

        # ---------------------------------------------------------------------
        # J. INTEGRITAS & KONKURENSI commit — tak korup, tak duplikat, tak 5xx.
        # ---------------------------------------------------------------------
        print(f"\n{B}J. Integritas & konkurensi commit{X}")
        await db.products.delete_many({"slug": {"$regex": "^fuzz-uji"}})
        jmap = {"slug": "slug", "name": "nm", "category": "cat", "variant_type": "tp",
                "variant_ml": "ml", "variant_price": "pr"}

        def jrows(std_price):
            return [
                {"slug": "fuzz-uji-konkuren", "nm": "Fuzz Uji Konkuren", "cat": "amber",
                 "tp": "Standard", "ml": "50", "pr": str(std_price)},
                {"slug": "fuzz-uji-konkuren", "nm": "Fuzz Uji Konkuren", "cat": "amber",
                 "tp": "Premium", "ml": "100", "pr": "800000"},
                {"slug": "fuzz-uji-konkuren", "nm": "Fuzz Uji Konkuren", "cat": "amber",
                 "tp": "Standard", "ml": "50", "pr": "999"},  # dup (Standard,50) -> error row
            ]

        # J1 integritas: add-only -> 1 produk (2 varian), 1 baris dup diisolasi, count += 1
        cbefore = await db.products.count_documents({})
        rj1 = await c.post(CM, headers=h, json={"rows": jrows(450000), "mapping": jmap, "mode": "add-only"})
        cafter = await db.products.count_documents({})
        pj = await c.get(f"{API}/api/products/fuzz-uji-konkuren")
        vols = pj.json().get("volumes", []) if pj.status_code == 200 else []
        j1 = rj1.json() if rj1.status_code == 200 else {}
        if (rj1.status_code == 200 and j1.get("created") == 1 and j1.get("failed") == 0
                and j1.get("row_errors", 0) == 1 and cafter == cbefore + 1 and len(vols) == 2):
            ok(f"integritas: 1 produk (2 varian) dibuat, 1 baris dup diisolasi (row_error), count {cbefore}->{cafter}")
        else:
            bad(f"integritas J1: res={j1 or rj1.status_code} vols={len(vols)} {cbefore}->{cafter}")

        # J2 konkurensi UPSERT produk yg SAMA: tak ada duplikat, count stabil, tak 5xx
        prices = [460000, 470000, 480000, 490000, 500000, 510000]
        base2 = await db.products.count_documents({})
        res2 = await asyncio.gather(*[
            c.post(CM, headers=h, json={"rows": jrows(p), "mapping": jmap, "mode": "upsert"})
            for p in prices
        ], return_exceptions=True)
        codes2 = [getattr(r, "status_code", "EXC") for r in res2]
        cnt_slug2 = await db.products.count_documents({"slug": "fuzz-uji-konkuren"})
        cnt_tot2 = await db.products.count_documents({})
        pj2 = await c.get(f"{API}/api/products/fuzz-uji-konkuren")
        std2 = next((v for v in pj2.json()["variants"]
                     if v["options"].get("Tipe") == "Standard" and v["options"].get("Ukuran") == "50ml"),
                    None) if pj2.status_code == 200 else None
        if (all(isinstance(x, int) and x < 500 for x in codes2) and cnt_slug2 == 1
                and cnt_tot2 == base2 and std2 and std2["price"] in prices):
            ok(f"konkurensi upsert x{len(prices)}: slug unik (1), total stabil {cnt_tot2}, harga Std={std2['price']} (salah satu input), tanpa 5xx")
        else:
            bad(f"konkurensi upsert: codes={codes2} slug={cnt_slug2} total={cnt_tot2}/{base2} std={std2}")

        # J3 konkurensi ADD-ONLY produk yg SUDAH ada: semua dilewati, tak ada duplikat/5xx
        base3 = await db.products.count_documents({})
        res3 = await asyncio.gather(*[
            c.post(CM, headers=h, json={"rows": jrows(450000), "mapping": jmap, "mode": "add-only"})
            for _ in range(5)
        ], return_exceptions=True)
        codes3 = [getattr(r, "status_code", "EXC") for r in res3]
        cnt_slug3 = await db.products.count_documents({"slug": "fuzz-uji-konkuren"})
        cnt_tot3 = await db.products.count_documents({})
        skip_ok = all(hasattr(r, "status_code") and r.status_code == 200 and r.json().get("created", 0) == 0 for r in res3)
        if (all(isinstance(x, int) and x < 500 for x in codes3) and cnt_slug3 == 1
                and cnt_tot3 == base3 and skip_ok):
            ok(f"konkurensi add-only x5 (produk ada): semua dilewati, tanpa duplikat (slug={cnt_slug3}), total stabil {cnt_tot3}")
        else:
            bad(f"konkurensi add-only: codes={codes3} slug={cnt_slug3} total={cnt_tot3}/{base3}")

    # cleanup produk uji
    await db.products.delete_many({"slug": {"$regex": "^(impor|fuzz)-uji"}})
    print(f"\n{B}{'='*64}{X}\n  {G}passed={passed}{X}  {R}failed={failed}{X}\n{B}{'='*64}{X}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
