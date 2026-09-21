"""services/product_import.py — SMART IMPORT produk (mapping kolom cerdas + validasi).

FUNGSI MURNI (tanpa I/O DB):
  - suggest_mapping(headers): cocokkan header file bebas -> field kanonik (deterministik).
  - build_row/validate_row/validate_and_group: normalisasi + validasi per-baris (row-level)
    lalu kelompokkan menjadi produk + options[]/variants[] siap-upsert (satu baris = satu varian).

Model VARIAN N-dimensi (Shopify-style): tiap dimensi = pasangan kolom option{i}_name/value
(hingga 4 dimensi). Tetap kompatibel dengan file LAMA (variant_type + variant_ml): bila kolom
option tidak ada, dimensi diturunkan dari Konsentrasi (produk) + Tipe (variant_type) + Ukuran (ml).

Sengaja TANPA LLM: pencocokan berbasis kamus sinonim + substring + fuzzy difflib agar
deterministik, gratis, dan mutation-proof. Dipakai router admin import (preview & commit).
"""
import difflib
import re
from typing import Dict, List, Optional

from services.product_io import (
    OPTION_SLOTS, norm_concentration, norm_gender, norm_status, parse_bool, parse_list,
    parse_ml, parse_money, parse_int, slugify,
)

SIZE_HINTS = ("ukuran", "size", "ml", "volume")


def _is_size_name(name) -> bool:
    n = str(name or "").lower()
    return any(h in n for h in SIZE_HINTS)


# Kolom kanonik + sinonim (dinormalisasi: lowercase + hapus non-alfanumerik).
CANONICAL_SPEC: Dict[str, List[str]] = {
    "slug": ["slug", "produkslug", "productslug", "handle", "permalink"],
    "name": ["name", "nama", "namaproduk", "productname", "title", "judul", "product"],
    "brand": ["brand", "merek", "merk"],
    "category": ["category", "kategori", "categoryslug", "kat", "koleksi", "collection"],
    "concentration": ["concentration", "konsentrasi", "conc", "tipeparfum", "jenisparfum"],
    "gender": ["gender", "jeniskelamin", "untuk", "targetgender"],
    "description": ["description", "deskripsi", "desc", "keterangan", "detail"],
    "ingredients": ["ingredients", "bahan", "komposisi", "kandungan"],
    "tags": ["tags", "tag", "label", "keywords"],
    "occasions": ["occasions", "occasion", "momen", "acara", "kesempatan", "occasionslug"],
    "characters": ["characters", "character", "karakter", "sifat", "mood", "characterslug"],
    "best_seller": ["bestseller", "terlaris", "unggulan", "featured"],
    "is_new": ["isnew", "baru", "new", "produkbaru"],
    "status": ["status", "aktif", "state"],
    "images": ["images", "image", "gambar", "foto", "imageurl", "imageurls", "picture"],
    "video_url": ["videourl", "video", "youtube"],
    # --- dimensi varian N-dimensi (Shopify-style) ---
    "option1_name": ["option1name", "opsi1nama", "namaopsi1", "namadimensi1", "dimensi1nama", "opt1name"],
    "option1_value": ["option1value", "opsi1nilai", "nilaiopsi1", "dimensi1nilai", "opt1value", "value1"],
    "option2_name": ["option2name", "opsi2nama", "namaopsi2", "namadimensi2", "dimensi2nama", "opt2name"],
    "option2_value": ["option2value", "opsi2nilai", "nilaiopsi2", "dimensi2nilai", "opt2value", "value2"],
    "option3_name": ["option3name", "opsi3nama", "namaopsi3", "namadimensi3", "dimensi3nama", "opt3name"],
    "option3_value": ["option3value", "opsi3nilai", "nilaiopsi3", "dimensi3nilai", "opt3value", "value3"],
    "option4_name": ["option4name", "opsi4nama", "namaopsi4", "namadimensi4", "dimensi4nama", "opt4name"],
    "option4_value": ["option4value", "opsi4nilai", "nilaiopsi4", "dimensi4nilai", "opt4value", "value4"],
    # --- legacy variant (tetap didukung utk file lama) ---
    "variant_type": ["varianttype", "type", "tipe", "tipevarian", "varian", "variant", "variantname"],
    "variant_ml": ["variantml", "ml", "ukuran", "size", "volume", "isi", "mililiter"],
    "variant_price": ["variantprice", "price", "harga", "hargajual", "unitprice", "sellingprice"],
    "variant_compare_at_price": ["variantcompareatprice", "compareatprice", "hargacoret",
                                 "hargaasli", "hargasebelumdiskon", "compareprice", "originalprice",
                                 "hargalama"],
    "variant_stock": ["variantstock", "stock", "stok", "qty", "quantity", "jumlah", "persediaan"],
    "variant_sku": ["variantsku", "sku", "kodesku", "kode", "barcode", "kodeproduk"],
}

REQUIRED_FIELDS = ("name", "category", "variant_price")  # ukuran divalidasi per-baris


def norm_key(text) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(text or "").lower())


def suggest_mapping(headers: List[str]) -> Dict[str, Optional[str]]:
    """Cocokkan header file (bebas) -> field kanonik. Kembalikan {canonical: header|None}.

    Strategi (deterministik): exact synonym -> substring -> fuzzy difflib (>=0.82).
    Satu header hanya dipetakan ke satu field (skor tertinggi menang).
    """
    norm_headers = [(h, norm_key(h)) for h in headers]

    def score(canon: str, nh: str) -> float:
        best = 0.0
        for s in CANONICAL_SPEC[canon]:
            ns = norm_key(s)
            if nh == ns:
                return 1.0
            if nh and ns and (nh in ns or ns in nh):
                best = max(best, 0.9)
            best = max(best, difflib.SequenceMatcher(None, nh, ns).ratio())
        return best

    candidates = []
    for canon in CANONICAL_SPEC:
        for (h, nh) in norm_headers:
            candidates.append((score(canon, nh), canon, h))
    candidates.sort(key=lambda x: (-x[0], x[1]))

    mapping: Dict[str, Optional[str]] = {}
    assigned, used = set(), set()
    for sc, canon, h in candidates:
        if sc < 0.82 or canon in assigned or h in used:
            continue
        mapping[canon] = h
        assigned.add(canon)
        used.add(h)
    for canon in CANONICAL_SPEC:
        mapping.setdefault(canon, None)
    return mapping


def _get(row: dict, mapping: Dict[str, Optional[str]], canon: str, default=""):
    h = mapping.get(canon)
    if not h:
        return default
    val = row.get(h, default)
    return default if val is None else val


def build_row(row: dict, mapping: Dict[str, Optional[str]]) -> dict:
    """Ekstrak 1 baris mentah -> dict ternormalisasi (product + variant + variant_options)."""
    concentration = norm_concentration(_get(row, mapping, "concentration", ""))
    variant_type = str(_get(row, mapping, "variant_type", "")).strip()[:60]
    variant_ml = parse_ml(_get(row, mapping, "variant_ml", ""))

    # Kolom dimensi (Shopify-style) — hingga OPTION_SLOTS pasang.
    pairs = []
    for i in range(1, OPTION_SLOTS + 1):
        nm = str(_get(row, mapping, f"option{i}_name", "")).strip()[:60]
        vl = str(_get(row, mapping, f"option{i}_value", "")).strip()[:60]
        if nm and vl:
            pairs.append([nm, vl])

    if pairs:
        seen: Dict[str, int] = {}
        variant_options: List[list] = []
        for nm, vl in pairs:
            if nm in seen:
                variant_options[seen[nm]][1] = vl
            else:
                seen[nm] = len(variant_options)
                variant_options.append([nm, vl])
    else:
        # Fallback legacy: Konsentrasi + Tipe(bila ada) + Ukuran(dari ml).
        variant_options = [["Konsentrasi", concentration]]
        if variant_type:
            variant_options.append(["Tipe", variant_type])
        variant_options.append(["Ukuran", (f"{variant_ml}ml" if variant_ml > 0 else "")])

    return {
        "slug": str(_get(row, mapping, "slug", "")).strip(),
        "name": str(_get(row, mapping, "name", "")).strip(),
        "brand": str(_get(row, mapping, "brand", "") or "Collector").strip() or "Collector",
        "category": str(_get(row, mapping, "category", "")).strip(),
        "concentration": concentration,
        "gender": norm_gender(_get(row, mapping, "gender", "")),
        "description": str(_get(row, mapping, "description", "")).strip(),
        "ingredients": str(_get(row, mapping, "ingredients", "")).strip(),
        "tags": parse_list(_get(row, mapping, "tags", "")),
        "occasions": parse_list(_get(row, mapping, "occasions", "")),
        "characters": parse_list(_get(row, mapping, "characters", "")),
        "best_seller": parse_bool(_get(row, mapping, "best_seller", "")),
        "is_new": parse_bool(_get(row, mapping, "is_new", "")),
        "status": norm_status(_get(row, mapping, "status", "active")),
        "images": parse_list(_get(row, mapping, "images", "")),
        "video_url": str(_get(row, mapping, "video_url", "")).strip(),
        "variant_type": variant_type,
        "variant_ml": variant_ml,
        "variant_price": parse_money(_get(row, mapping, "variant_price", "")),
        "variant_compare_at_price": parse_money(_get(row, mapping, "variant_compare_at_price", ""), 0),
        "variant_stock": parse_int(_get(row, mapping, "variant_stock", ""), 0),
        "variant_sku": str(_get(row, mapping, "variant_sku", "")).strip()[:60],
        "variant_options": variant_options,
    }


def _size_ml(variant_options) -> int:
    for name, val in variant_options:
        if _is_size_name(name):
            return parse_ml(val)
    return 0


def validate_row(r: dict, categories: set) -> List[str]:
    """Validasi 1 baris ternormalisasi. Kembalikan list pesan error (kosong = valid)."""
    errs = []
    if not r["name"]:
        errs.append("Nama produk wajib diisi")
    if _size_ml(r["variant_options"]) <= 0:
        errs.append("Wajib ada dimensi ukuran bernilai > 0 (mis. 'Ukuran' = 50ml, atau kolom variant_ml)")
    if r["variant_price"] <= 0:
        errs.append("Harga harus > 0")
    if r["variant_stock"] < 0:
        errs.append("Stok tidak boleh negatif")
    if not r["category"]:
        errs.append("Kategori wajib diisi")
    elif categories and r["category"] not in categories:
        errs.append(f"Kategori tidak dikenal: {r['category']}")
    for nm, vl in r["variant_options"]:
        if not nm or not vl:
            errs.append("Nama & nilai dimensi tidak boleh kosong")
            break
    cap = r["variant_compare_at_price"]
    if cap and cap <= r["variant_price"]:
        errs.append("Harga coret harus > harga jual")
    return errs


def validate_and_group(rows: List[dict], mapping: Dict[str, Optional[str]], categories: set):
    """Ubah baris mentah -> (products, reports).

    - products: list produk siap-upsert {slug?, name, category, ..., options:[...], variants:[...]}.
      Hanya berisi baris VALID; baris error TIDAK menghentikan proses (row-level).
    - reports: list {row, status, errors, name, variant, data} per baris (1-indexed).
    Grouping produk memakai kunci slug (atau slugify(name)); varian di-merge per produk.
    Set dimensi antar-baris satu produk WAJIB konsisten; kombinasi dimensi WAJIB unik.
    """
    products: Dict[str, dict] = {}
    reports = []
    seen_combo: Dict[str, set] = {}
    option_order: Dict[str, List[str]] = {}
    option_values: Dict[str, Dict[str, list]] = {}

    for idx, raw in enumerate(rows, start=1):
        r = build_row(raw, mapping)
        errs = validate_row(r, categories)
        pkey = (r["slug"] or slugify(r["name"])) if (r["slug"] or r["name"]) else ""
        vopts = r["variant_options"]
        vdict = {n: v for n, v in vopts}
        names = [n for n, _ in vopts]
        combo = None

        if pkey and not errs:
            established = option_order.get(pkey)
            if established is not None and set(names) != set(established):
                errs.append("Set dimensi tidak konsisten dengan baris lain di produk ini")
            else:
                order = established or names
                combo = tuple(vdict[n] for n in order)
                if combo in seen_combo.get(pkey, set()):
                    errs.append(f"Varian duplikat dalam file: {' / '.join(combo)}")

        reports.append({
            "row": idx,
            "status": "ok" if not errs else "error",
            "errors": errs,
            "name": r["name"],
            "variant": " / ".join(v for _, v in vopts),
            "data": r,
        })
        if errs or not pkey:
            continue

        if pkey not in option_order:
            option_order[pkey] = names
            option_values[pkey] = {n: [] for n in names}
        for n, v in vopts:
            if v not in option_values[pkey][n]:
                option_values[pkey][n].append(v)
        seen_combo.setdefault(pkey, set()).add(combo)

        variant = {
            "options": vdict,
            "price": r["variant_price"],
            "stock": r["variant_stock"],
            "compare_at_price": (r["variant_compare_at_price"] or None),
            "sku": (r["variant_sku"] or None),
        }
        if pkey not in products:
            products[pkey] = {
                "slug": r["slug"] or None,
                "name": r["name"], "brand": r["brand"], "category": r["category"],
                "concentration": r["concentration"], "gender": r["gender"],
                "description": r["description"], "ingredients": (r["ingredients"] or None),
                "tags": r["tags"], "best_seller": r["best_seller"], "is_new": r["is_new"],
                "occasions": r["occasions"], "characters": r["characters"],
                "status": r["status"], "images": r["images"],
                "video_url": (r["video_url"] or None),
                "variants": [variant],
            }
        else:
            products[pkey]["variants"].append(variant)

    for pkey, prod in products.items():
        prod["options"] = [{"name": n, "values": option_values[pkey][n]} for n in option_order[pkey]]

    return list(products.values()), reports
