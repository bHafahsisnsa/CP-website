#!/usr/bin/env python3
"""POC — Roundtrip Import/Export N-Dimensi (Shopify-style) untuk Collector Parfum.

Menguji (fungsi MURNI, tanpa DB) bahwa:
  1. Template CSV & XLSX yang dihasilkan backend TIDAK rusak (kolom dimensi terisi).
  2. read_table() mem-parse ulang template menjadi headers + rows.
  3. suggest_mapping() memetakan kolom option{i}_name/value dengan benar (auto).
  4. validate_and_group() menghasilkan produk dengan options[]/variants[] tanpa error.
  5. product_to_rows() (export) menghasilkan kolom Shopify-style yang konsisten (roundtrip).
  6. File uji N-dimensi (2D, 3D, 4D) dibuat untuk dipakai testing agent.

Juga menuliskan file contoh ke /app/tests/import_samples/ (csv & xlsx).
"""
import csv
import io
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from services import product_bulk as bulk  # noqa: E402
from services.product_io import EXPORT_COLUMNS, product_to_rows  # noqa: E402
from services.product_import import suggest_mapping, validate_and_group  # noqa: E402

CATS = {"amber", "floral", "woody", "fresh", "oriental", "citrus"}
OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "tests", "import_samples")

PASS, FAIL = 0, 0


def check(name, cond, detail=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  \033[92m✓\033[0m {name}")
    else:
        FAIL += 1
        print(f"  \033[91m✗\033[0m {name} — {detail}")


def _rows_from_csv(data: bytes):
    text = data.decode("utf-8-sig")
    return list(csv.DictReader(io.StringIO(text)))


def test_template_csv():
    print("\n[1] Template CSV — tidak rusak & bisa diimpor")
    data = bulk.template_csv_bytes()
    headers, rows = bulk.read_table("template.csv", data)
    check("header memuat option1_name..option3_value", all(
        c in headers for c in ["option1_name", "option1_value", "option2_name", "option2_value",
                               "option3_name", "option3_value"]),
        f"headers={headers}")
    check("tidak ada kolom legacy variant_type/variant_ml", not any(
        c in headers for c in ["variant_type", "variant_ml"]), f"headers={headers}")
    check("4 baris varian terbaca", len(rows) == 4, f"len={len(rows)}")

    mapping = suggest_mapping(headers)
    check("suggest_mapping option1_name->option1_name",
          mapping.get("option1_name") == "option1_name", mapping.get("option1_name"))
    check("suggest_mapping option2_value->option2_value",
          mapping.get("option2_value") == "option2_value", mapping.get("option2_value"))
    check("suggest_mapping variant_price termapping",
          mapping.get("variant_price") == "variant_price", mapping.get("variant_price"))

    products, reports = validate_and_group(rows, mapping, CATS)
    errs = [r for r in reports if r["status"] == "error"]
    check("semua baris VALID (0 error)", len(errs) == 0,
          "; ".join(f"row{r['row']}:{r['errors']}" for r in errs))
    check("menghasilkan 2 produk", len(products) == 2, f"n={len(products)}")

    reguler = next((p for p in products if p["slug"] == "contoh-parfum-reguler"), None)
    signature = next((p for p in products if p["slug"] == "contoh-parfum-signature"), None)
    check("produk reguler = 2 dimensi", reguler and len(reguler["options"]) == 2,
          reguler and [o["name"] for o in reguler["options"]])
    check("produk reguler = 2 varian", reguler and len(reguler["variants"]) == 2)
    check("produk signature = 3 dimensi", signature and len(signature["options"]) == 3,
          signature and [o["name"] for o in signature["options"]])
    check("produk signature = 2 varian", signature and len(signature["variants"]) == 2)
    check("ada dimensi Ukuran di reguler",
          reguler and any(o["name"].lower() == "ukuran" for o in reguler["options"]))
    return products


def test_template_xlsx():
    print("\n[2] Template XLSX — tidak rusak & bisa diimpor")
    data = bulk.template_xlsx_bytes()
    headers, rows = bulk.read_table("template.xlsx", data)
    check("header xlsx memuat option columns",
          "option1_name" in headers and "option3_value" in headers, f"headers={headers}")
    check("4 baris terbaca dari xlsx", len(rows) == 4, f"len={len(rows)}")
    mapping = suggest_mapping(headers)
    products, reports = validate_and_group(rows, mapping, CATS)
    errs = [r for r in reports if r["status"] == "error"]
    check("xlsx: 0 error", len(errs) == 0, str(errs))
    check("xlsx: 2 produk", len(products) == 2, f"n={len(products)}")


def test_export_roundtrip():
    print("\n[3] Export roundtrip — product_to_rows -> import lagi")
    prod = {
        "slug": "roundtrip-parfum", "name": "Roundtrip Parfum", "brand": "Collector",
        "category": "woody", "concentration": "EDP", "gender": "Unisex",
        "description": "Uji roundtrip", "ingredients": "", "tags": ["Woody"],
        "best_seller": False, "is_new": True, "status": "active", "images": [], "video_url": "",
        "options": [
            {"name": "Konsentrasi", "values": ["EDP"]},
            {"name": "Tipe", "values": ["Standard", "Premium"]},
            {"name": "Ukuran", "values": ["50ml", "100ml"]},
        ],
        "variants": [
            {"sku": "RT-STD-50", "options": {"Konsentrasi": "EDP", "Tipe": "Standard", "Ukuran": "50ml"},
             "price": 400000, "stock": 8, "compare_at_price": None},
            {"sku": "RT-PRM-100", "options": {"Konsentrasi": "EDP", "Tipe": "Premium", "Ukuran": "100ml"},
             "price": 800000, "stock": 4, "compare_at_price": 950000},
        ],
    }
    rows = product_to_rows(prod)
    check("export: 2 baris (1/varian)", len(rows) == 2, f"len={len(rows)}")
    check("export: kolom option3_name=Ukuran", rows[0]["option3_name"] == "Ukuran",
          rows[0].get("option3_name"))
    check("export: SKU dipertahankan", rows[0]["variant_sku"] == "RT-STD-50", rows[0].get("variant_sku"))
    # Import kembali
    mapping = suggest_mapping(list(EXPORT_COLUMNS))
    products, reports = validate_and_group(rows, mapping, CATS)
    errs = [r for r in reports if r["status"] == "error"]
    check("roundtrip: 0 error saat import ulang", len(errs) == 0, str(errs))
    check("roundtrip: 1 produk 3 dimensi",
          len(products) == 1 and len(products[0]["options"]) == 3,
          products and [o["name"] for o in products[0]["options"]])


def _write_csv(path, header, rows):
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=header, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)


def make_sample_files():
    print("\n[4] Membuat file uji N-dimensi untuk testing agent")
    os.makedirs(OUT_DIR, exist_ok=True)

    # 2D: Konsentrasi x Ukuran
    hdr2 = ["name", "category", "gender", "description",
            "option1_name", "option1_value", "option2_name", "option2_value",
            "variant_price", "variant_stock", "variant_sku"]
    rows2 = [
        {"name": "QA Mawar Fresh", "category": "floral", "gender": "Wanita",
         "description": "Uji 2 dimensi", "option1_name": "Konsentrasi", "option1_value": "EDT",
         "option2_name": "Ukuran", "option2_value": "30ml", "variant_price": "120000",
         "variant_stock": "15", "variant_sku": ""},
        {"name": "QA Mawar Fresh", "category": "floral", "gender": "Wanita",
         "description": "Uji 2 dimensi", "option1_name": "Konsentrasi", "option1_value": "EDT",
         "option2_name": "Ukuran", "option2_value": "50ml", "variant_price": "200000",
         "variant_stock": "10", "variant_sku": ""},
    ]
    _write_csv(os.path.join(OUT_DIR, "sample_2d.csv"), hdr2, rows2)

    # 3D: Konsentrasi x Tipe x Ukuran (matriks) — pakai header non-baku untuk uji smart mapping
    hdr3 = ["Nama Produk", "Kategori", "Untuk", "option1_name", "option1_value",
            "option2_name", "option2_value", "option3_name", "option3_value",
            "Harga", "Stok", "SKU", "Harga Coret"]
    rows3 = []
    for tipe, ukr, harga, stok, coret in [
        ("Standard", "50ml", "350000", "12", ""),
        ("Standard", "100ml", "600000", "8", ""),
        ("Premium", "50ml", "450000", "6", "500000"),
        ("Premium", "100ml", "820000", "4", "990000"),
    ]:
        rows3.append({
            "Nama Produk": "QA Oud Signature", "Kategori": "woody", "Untuk": "Unisex",
            "option1_name": "Konsentrasi", "option1_value": "EDP",
            "option2_name": "Tipe", "option2_value": tipe,
            "option3_name": "Ukuran", "option3_value": ukr,
            "Harga": harga, "Stok": stok, "SKU": "", "Harga Coret": coret,
        })
    _write_csv(os.path.join(OUT_DIR, "sample_3d.csv"), hdr3, rows3)

    # 4D: Konsentrasi x Edisi x Tipe x Ukuran
    hdr4 = ["name", "category", "option1_name", "option1_value", "option2_name", "option2_value",
            "option3_name", "option3_value", "option4_name", "option4_value",
            "variant_price", "variant_stock"]
    rows4 = []
    for edisi, tipe, ukr, harga, stok in [
        ("Classic", "Standard", "50ml", "500000", "5"),
        ("Classic", "Premium", "100ml", "900000", "3"),
        ("Limited", "Premium", "100ml", "1200000", "2"),
    ]:
        rows4.append({
            "name": "QA Amber Deluxe", "category": "amber",
            "option1_name": "Konsentrasi", "option1_value": "EDP",
            "option2_name": "Edisi", "option2_value": edisi,
            "option3_name": "Tipe", "option3_value": tipe,
            "option4_name": "Ukuran", "option4_value": ukr,
            "variant_price": harga, "variant_stock": stok,
        })
    _write_csv(os.path.join(OUT_DIR, "sample_4d.csv"), hdr4, rows4)

    # Legacy file (variant_type/variant_ml) — backward-compat
    hdrL = ["name", "category", "concentration", "variant_type", "variant_ml",
            "variant_price", "variant_stock"]
    rowsL = [
        {"name": "QA Legacy Musk", "category": "fresh", "concentration": "EDT",
         "variant_type": "", "variant_ml": "50", "variant_price": "180000", "variant_stock": "9"},
        {"name": "QA Legacy Musk", "category": "fresh", "concentration": "EDT",
         "variant_type": "", "variant_ml": "100", "variant_price": "320000", "variant_stock": "5"},
    ]
    _write_csv(os.path.join(OUT_DIR, "sample_legacy.csv"), hdrL, rowsL)

    # XLSX 3D (template-based) untuk uji upload xlsx
    xlsx = bulk.template_xlsx_bytes()
    with open(os.path.join(OUT_DIR, "sample_template.xlsx"), "wb") as f:
        f.write(xlsx)

    files = sorted(os.listdir(OUT_DIR))
    check("file sample dibuat (>=5)", len(files) >= 5, str(files))

    # Validasi tiap file sample bisa di-parse & 0 error (kecuali kategori)
    for fn in ["sample_2d.csv", "sample_3d.csv", "sample_4d.csv", "sample_legacy.csv"]:
        with open(os.path.join(OUT_DIR, fn), "rb") as f:
            data = f.read()
        headers, rows = bulk.read_table(fn, data)
        mapping = suggest_mapping(headers)
        products, reports = validate_and_group(rows, mapping, CATS)
        errs = [r for r in reports if r["status"] == "error"]
        check(f"{fn}: 0 error", len(errs) == 0, str([r["errors"] for r in errs]))
        check(f"{fn}: >=1 produk", len(products) >= 1, f"n={len(products)}")


if __name__ == "__main__":
    print("=" * 62)
    print("  POC — Import/Export N-Dimensi (Shopify-style)")
    print("=" * 62)
    test_template_csv()
    test_template_xlsx()
    test_export_roundtrip()
    make_sample_files()
    print("\n" + "=" * 62)
    print(f"  HASIL: {PASS} PASS / {FAIL} FAIL")
    print("=" * 62)
    sys.exit(0 if FAIL == 0 else 1)
