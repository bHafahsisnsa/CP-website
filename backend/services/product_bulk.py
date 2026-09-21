"""services/product_bulk.py — I/O file (CSV/XLSX) + commit import produk. Epic E10.

- read_table(): parse bytes CSV/XLSX -> (headers, rows) SEMUA sebagai string
  (hindari koersi pandas yang merusak SKU/ml). BOM-safe.
- to_csv_bytes()/to_xlsx_bytes(): tulis baris (satu per varian) untuk export/template.
- template_rows()/INSTRUCTIONS: contoh baris typed + typeless + panduan.
- commit(): upsert produk (add-only|upsert) memakai write-path admin_products
  (clean_variants + validasi invarian + auto-SKU). Row-level: baris valid diproses.
"""
import csv
import io

from openpyxl import Workbook, load_workbook

from services import admin_products as ap
from services.product_io import EXPORT_COLUMNS, OPTION_SLOTS, product_to_rows, slugify

MAX_ROWS = 20000  # katalog besar (mis. 1.000+ produk x 6 varian) harus tetap muat

INSTRUCTIONS = [
    "PANDUAN IMPOR PRODUK — Collector Parfum (Format Varian N-Dimensi / Shopify-style)",
    "",
    "• Satu BARIS = satu VARIAN. Produk dengan beberapa varian ditulis di beberapa baris",
    "  dengan kolom 'slug' / 'name' yang SAMA (varian dikelompokkan otomatis).",
    "• Kolom WAJIB: name, category, variant_price, dan minimal satu DIMENSI UKURAN.",
    "• DIMENSI (maks 4): pasangan kolom option1_name/option1_value … option4_name/option4_value.",
    "  Contoh: option1_name='Konsentrasi', option1_value='EDP'; option2_name='Ukuran', option2_value='50ml'.",
    "• WAJIB ada satu dimensi UKURAN — nama mengandung 'Ukuran'/'Size'/'ml'/'Volume' dan",
    "  nilainya mengandung angka > 0 (mis. '50ml'). Dari sini sistem menurunkan ml varian.",
    "• Nama dimensi (optionX_name) harus SAMA di semua baris satu produk; kombinasi nilai WAJIB UNIK.",
    "• 'category' harus slug kategori yang sudah ada (mis. amber, floral, woody).",
    "• 'variant_sku' OPSIONAL — dibuat otomatis oleh sistem bila kosong.",
    "• 'variant_compare_at_price' OPSIONAL — harga coret, harus > variant_price.",
    "• 'gender' opsional (Pria/Wanita/Unisex, default Unisex). 'status' active/archived.",
    "• Kolom boleh tidak baku — sistem mencocokkan otomatis (smart mapping).",
    "• File LAMA berkolom 'variant_type'/'variant_ml' tetap DIDUKUNG (kompatibilitas mundur).",
]


def _cell_str(v):
    if v is None:
        return ""
    if isinstance(v, float) and v.is_integer():
        return str(int(v))
    return str(v).strip()


def read_table(filename, data):
    """Parse bytes -> (headers, rows[list[dict]]) semua string. Dukung .csv & .xlsx."""
    name = (filename or "").lower()
    if name.endswith(".xlsx") or name.endswith(".xlsm"):
        wb = load_workbook(io.BytesIO(data), read_only=True, data_only=True)
        ws = wb.active
        rows_iter = ws.iter_rows(values_only=True)
        headers = []
        for raw in rows_iter:
            headers = [_cell_str(c) for c in raw]
            break
        headers = [h for h in headers]
        out = []
        for raw in rows_iter:
            if raw is None:
                continue
            vals = list(raw) + [None] * (len(headers) - len(raw))
            row = {headers[i]: _cell_str(vals[i]) for i in range(len(headers)) if headers[i]}
            if any(v for v in row.values()):
                out.append(row)
            if len(out) >= MAX_ROWS:
                break
        wb.close()
        return [h for h in headers if h], out
    # CSV (BOM-safe)
    text = data.decode("utf-8-sig", errors="replace")
    reader = csv.DictReader(io.StringIO(text))
    headers = [h.strip() for h in (reader.fieldnames or []) if h is not None]
    out = []
    for r in reader:
        row = {(k.strip() if k else k): _cell_str(v) for k, v in r.items() if k is not None}
        if any(v for v in row.values()):
            out.append(row)
        if len(out) >= MAX_ROWS:
            break
    return headers, out


def _rows_for_all(products):
    rows = []
    for p in products:
        rows.extend(product_to_rows(p))
    return rows


def to_csv_bytes(products):
    rows = _rows_for_all(products)
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=EXPORT_COLUMNS, extrasaction="ignore")
    w.writeheader()
    for r in rows:
        w.writerow({k: r.get(k, "") for k in EXPORT_COLUMNS})
    return buf.getvalue().encode("utf-8-sig")


def to_xlsx_bytes(products, with_instructions=False):
    wb = Workbook()
    ws = wb.active
    ws.title = "Produk"
    ws.append(EXPORT_COLUMNS)
    for r in _rows_for_all(products):
        ws.append([r.get(k, "") for k in EXPORT_COLUMNS])
    # lebar kolom nyaman dibaca
    for i, col in enumerate(EXPORT_COLUMNS, start=1):
        ws.column_dimensions[chr(64 + i) if i <= 26 else "A"].width = max(12, min(28, len(col) + 4))
    if with_instructions:
        info = wb.create_sheet("Panduan")
        for line in INSTRUCTIONS:
            info.append([line])
        info.column_dimensions["A"].width = 90
    out = io.BytesIO()
    wb.save(out)
    return out.getvalue()


def _tpl_row(product_fields, dims, *, price, stock, compare="", sku=""):
    """Bangun 1 baris template N-dimensi.

    dims: list pasangan (nama_dimensi, nilai) hingga OPTION_SLOTS (mis. [("Konsentrasi","EDP"),("Ukuran","50ml")]).
    Slot option yang tak terpakai ditulis kosong. Kolom variant_* diisi eksplisit.
    """
    row = {k: "" for k in EXPORT_COLUMNS}
    row.update(product_fields)
    for i in range(OPTION_SLOTS):
        nm, vl = dims[i] if i < len(dims) else ("", "")
        row[f"option{i + 1}_name"] = nm
        row[f"option{i + 1}_value"] = vl
    row["variant_price"] = price
    row["variant_compare_at_price"] = compare
    row["variant_stock"] = stock
    row["variant_sku"] = sku
    return row


def template_rows():
    """Contoh baris N-dimensi: 1 produk 2-dimensi (Konsentrasi × Ukuran) + 1 produk 3-dimensi
    (Konsentrasi × Tipe × Ukuran). Semua kolom dimensi memakai option{i}_name/value."""
    reguler = {
        "slug": "contoh-parfum-reguler", "name": "Contoh Parfum Reguler",
        "brand": "Collector", "category": "floral", "concentration": "EDT",
        "gender": "Wanita", "description": "Contoh produk 2 dimensi (Konsentrasi × Ukuran).",
        "tags": "Floral, Fresh", "best_seller": "false", "is_new": "false", "status": "active",
    }
    signature = {
        "slug": "contoh-parfum-signature", "name": "Contoh Parfum Signature",
        "brand": "Collector", "category": "amber", "concentration": "EDP",
        "gender": "Unisex", "description": "Contoh produk 3 dimensi (Konsentrasi × Tipe × Ukuran).",
        "tags": "Woody, Oud", "best_seller": "false", "is_new": "true", "status": "active",
    }
    return [
        # Produk 1 — 2 dimensi, 2 varian.
        _tpl_row(reguler, [("Konsentrasi", "EDT"), ("Ukuran", "30ml")], price="150000", stock="20"),
        _tpl_row(reguler, [("Konsentrasi", "EDT"), ("Ukuran", "50ml")], price="250000", stock="12"),
        # Produk 2 — 3 dimensi (matriks Tipe × Ukuran), 2 varian.
        _tpl_row(signature, [("Konsentrasi", "EDP"), ("Tipe", "Standard"), ("Ukuran", "50ml")],
                 price="450000", stock="10"),
        _tpl_row(signature, [("Konsentrasi", "EDP"), ("Tipe", "Premium"), ("Ukuran", "100ml")],
                 price="850000", compare="990000", stock="5"),
    ]


def template_csv_bytes():
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=EXPORT_COLUMNS, extrasaction="ignore")
    w.writeheader()
    for r in template_rows():
        w.writerow(r)
    return buf.getvalue().encode("utf-8-sig")


def template_xlsx_bytes():
    wb = Workbook()
    ws = wb.active
    ws.title = "Template Produk"
    ws.append(EXPORT_COLUMNS)
    for r in template_rows():
        ws.append([r.get(k, "") for k in EXPORT_COLUMNS])
    info = wb.create_sheet("Panduan")
    for line in INSTRUCTIONS:
        info.append([line])
    info.column_dimensions["A"].width = 90
    out = io.BytesIO()
    wb.save(out)
    return out.getvalue()


def _payload(prod):
    """products (hasil validate_and_group) -> payload write-path admin_products (N-dimensi).

    CATATAN ANTI DATA-LOSS: `occasions`/`characters` HANYA disertakan bila file impor benar
    benar membawa nilainya. Bila key tidak ada, admin_products.update_product akan
    MEMPERTAHANKAN nilai lama (lihat PRESERVE_IF_ABSENT) sehingga export -> re-import dari
    file tanpa kolom facet tidak menghapus taksonomi produk.
    """
    payload = {
        "name": prod["name"], "slug": (prod.get("slug") or None),
        "brand": prod.get("brand", "Collector"), "category": prod["category"],
        "concentration": prod.get("concentration", "EDP"), "gender": prod.get("gender", "Unisex"),
        "description": prod.get("description", ""), "ingredients": prod.get("ingredients"),
        "tags": prod.get("tags", []), "best_seller": bool(prod.get("best_seller")),
        "is_new": bool(prod.get("is_new")), "status": prod.get("status", "active"),
        "images": prod.get("images", []), "video_url": prod.get("video_url"),
        "options": prod.get("options", []), "variants": prod.get("variants", []),
        "compare_at_price": None,
    }
    if prod.get("occasions"):
        payload["occasions"] = prod["occasions"]
    if prod.get("characters"):
        payload["characters"] = prod["characters"]
    return payload


async def commit(db, actor_id, products, mode="upsert"):
    """Upsert daftar produk. mode: 'add-only' | 'upsert'. Kembalikan ringkasan.

    Pada mode 'add-only' produk yang slug/nama-nya sudah ada akan DILEWATI. Detail produk
    yang dilewati (termasuk `status` produk yang sudah ada) dikembalikan lewat
    `skipped_details` supaya UI bisa menjelaskan ke admin: produk berstatus 'archived'
    TIDAK tampil di storefront walau barisnya "berhasil" dilewati.
    """
    created, updated, skipped, errors = 0, 0, 0, []
    skipped_details = []
    for prod in products:
        slug = prod.get("slug") or slugify(prod.get("name"))
        name = prod.get("name")
        try:
            proj = {"id": 1, "status": 1, "name": 1}
            existing = await db.products.find_one({"slug": slug}, proj)
            if not existing and prod.get("name"):
                existing = await db.products.find_one({"name": prod["name"]}, proj)
            if existing:
                if mode == "add-only":
                    skipped += 1
                    skipped_details.append({
                        "product": existing.get("name") or name,
                        "slug": slug,
                        "status": existing.get("status", "active"),
                    })
                    continue
                await ap.update_product(db, actor_id, existing["id"], _payload(prod))
                updated += 1
            else:
                await ap.create_product(db, actor_id, _payload(prod))
                created += 1
        except ValueError as e:
            errors.append({"product": name, "slug": slug, "error": str(e)})
        except Exception as e:  # pragma: no cover - defensive
            errors.append({"product": name, "slug": slug, "error": f"gagal simpan: {e}"})
    return {
        "created": created, "updated": updated, "skipped": skipped,
        "failed": len(errors), "errors": errors,
        "skipped_details": skipped_details,
        "skipped_archived": sum(1 for s in skipped_details if s["status"] == "archived"),
        "total_products": len(products),
    }
