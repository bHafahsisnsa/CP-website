"""services/product_io.py — SSOT normalisasi VARIAN + parser + helper EXPORT produk.

FUNGSI MURNI (tanpa I/O DB) agar mudah di-unit-test & mutation-proof:
  - parser toleran (parse_money/int/ml/bool/list) + normalizer (gender/concentration/status),
  - gen_variant_sku(): SKU deterministik unik per varian (bila admin tak mengisi),
  - clean_variants(): validasi + normalisasi matriks varian (type × ml) + auto-SKU,
  - product_to_rows()/EXPORT_COLUMNS: mendatarkan produk -> baris (satu per varian) untuk export.

Smart Import (mapping kolom + validasi baris) ada di services/product_import.py.
Identitas varian runtime = (type, ml); `type=""` = produk tanpa dimensi tipe.
"""
import re
from typing import List

from core_utils import money

GENDERS = {"pria", "wanita", "unisex"}
CONCENTRATIONS = {"EDP", "EDT"}


def _alnum_upper(text, limit: int = 40) -> str:
    return re.sub(r"[^A-Z0-9]+", "", str(text or "").upper())[:limit]


def slugify(text) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", str(text or "").lower().strip()).strip("-")
    return s or "produk"


def parse_money(value, default=0) -> int:
    """'Rp 385.000' | '385,000' | 385000 | '' -> int rupiah (default bila kosong/invalid).

    Mempertahankan tanda negatif di depan (mis. '-50' -> -50) agar nilai adversarial
    negatif TIDAK diam-diam menjadi positif — validasi hilir (harga > 0) yang menolaknya.
    """
    if value is None:
        return default
    if isinstance(value, (int, float)):
        return int(value)
    s = str(value).strip()
    if not s:
        return default
    neg = s.startswith("-")
    digits = re.sub(r"[^\d]", "", s)
    if digits == "":
        return default
    try:
        n = int(digits)
        return -n if neg else n
    except ValueError:
        return default


def parse_int(value, default=0) -> int:
    if value is None:
        return default
    if isinstance(value, (int, float)):
        return int(value)
    s = re.sub(r"[^\d\-]", "", str(value).strip())
    if s in ("", "-"):
        return default
    try:
        return int(s)
    except ValueError:
        return default


def parse_ml(value) -> int:
    """'50 ml' | '50ml' | '50' -> 50 (0 bila invalid)."""
    return parse_int(value, 0)


def parse_bool(value) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "ya", "y", "on", "aktif", "iya"}


def parse_list(value) -> List[str]:
    """CSV / pipe / newline separated -> list bersih tanpa duplikat berurutan."""
    if value is None:
        return []
    raw = value if isinstance(value, list) else re.split(r"[,\|\n;]+", str(value))
    out = []
    for v in raw:
        v = str(v).strip()
        if v and v not in out:
            out.append(v)
    return out


def norm_gender(value) -> str:
    g = str(value or "").strip().lower()
    if g in ("pria", "male", "men", "man", "laki-laki", "l"):
        return "Pria"
    if g in ("wanita", "female", "women", "woman", "perempuan", "p"):
        return "Wanita"
    return "Unisex"  # opsional -> default


def norm_concentration(value) -> str:
    c = str(value or "").strip().upper().replace(" ", "")
    if c in ("EDT", "EAUDETOILETTE", "TOILETTE"):
        return "EDT"
    return "EDP"


def norm_status(value) -> str:
    s = str(value or "").strip().lower()
    if s in ("archived", "arsip", "nonaktif", "inactive", "arsipkan"):
        return "archived"
    return "active"


def gen_variant_sku(base: str, vtype: str, ml, taken: set) -> str:
    """SKU deterministik unik per varian. base=nama/slug produk; vtype=tipe (opsional)."""
    parts = [_alnum_upper(base, 12) or "PRD"]
    if vtype:
        parts.append(_alnum_upper(vtype, 8))
    parts.append(f"{int(ml)}ML")
    root = "-".join([p for p in parts if p])
    final, i = root, 2
    while final in taken:
        final = f"{root}-{i}"
        i += 1
    return final


def clean_variants(volumes, product_name: str = "") -> List[dict]:
    """Validasi + normalisasi daftar varian. Raise ValueError bila tak valid.

    Aturan: ml>0, price>0, stock>=0, (type,ml) UNIK, compare_at_price null / > price,
    SKU auto-generate bila kosong & UNIK dalam produk. Kembalikan list ternormalisasi.
    """
    out: List[dict] = []
    seen = set()        # (type, ml)
    taken_sku = set()
    for v in (volumes or []):
        vtype = str(v.get("type", "") or "").strip()[:60]
        try:
            ml = int(v.get("ml"))
            price = money(v.get("price"))
            stock = int(v.get("stock", 0) or 0)
        except (TypeError, ValueError):
            raise ValueError("Varian tidak valid (ml/harga/stok bukan angka)")
        if ml <= 0 or price <= 0:
            raise ValueError("Varian: ml & harga harus > 0")
        if stock < 0:
            raise ValueError("Varian: stok tidak boleh negatif")
        key = (vtype, ml)
        if key in seen:
            raise ValueError(f"Varian duplikat: {(vtype + ' ') if vtype else ''}{ml}ml")
        seen.add(key)

        cap = v.get("compare_at_price")
        cap_v = None
        if cap not in (None, "", 0, "0"):
            cap_v = parse_money(cap)
            if cap_v <= price:
                raise ValueError(f"compare_at_price varian {vtype} {ml}ml harus > harga")

        sku = str(v.get("sku") or "").strip()[:60]
        if not sku:
            sku = gen_variant_sku(product_name, vtype, ml, taken_sku)
        if sku in taken_sku:
            raise ValueError(f"SKU duplikat dalam produk: {sku}")
        taken_sku.add(sku)

        out.append({"type": vtype, "ml": ml, "price": price, "stock": stock,
                    "compare_at_price": cap_v, "sku": sku})
    if not out:
        raise ValueError("Minimal 1 varian")
    return out


OPTION_SLOTS = 4

# Kolom ekspor kanonik (urutan tetap) — dipakai export & template.
# Model N-dimensi: tiap dimensi punya sepasang kolom (nama+nilai), Shopify-style.
EXPORT_COLUMNS = [
    "slug", "name", "brand", "category", "concentration", "gender",
    "description", "ingredients", "tags", "occasions", "characters",
    "best_seller", "is_new", "status",
    "images", "video_url",
    "option1_name", "option1_value", "option2_name", "option2_value",
    "option3_name", "option3_value", "option4_name", "option4_value",
    "variant_price", "variant_compare_at_price", "variant_stock", "variant_sku",
]


def product_to_rows(prod: dict) -> List[dict]:
    """Datarkan (flatten) 1 produk -> beberapa baris (satu per varian) untuk export.

    Tiap dimensi (options[]) dipetakan ke pasangan kolom option{i}_name/value; tiap
    varian (variants[]) = satu baris. Dokumen legacy (hanya volumes[]) diturunkan dulu.
    """
    base = {
        "slug": prod.get("slug", ""),
        "name": prod.get("name", ""),
        "brand": prod.get("brand", ""),
        "category": prod.get("category", ""),
        "concentration": prod.get("concentration", ""),
        "gender": prod.get("gender", ""),
        "description": prod.get("description", ""),
        "ingredients": prod.get("ingredients", "") or "",
        "tags": ", ".join(prod.get("tags", []) or []),
        # Facet taksonomi (slug) — disertakan agar round-trip export -> import LOSSLESS.
        "occasions": ", ".join(prod.get("occasions", []) or []),
        "characters": ", ".join(prod.get("characters", []) or []),
        "best_seller": "true" if prod.get("best_seller") else "false",
        "is_new": "true" if prod.get("is_new") else "false",
        "status": prod.get("status", "active"),
        "images": ", ".join(prod.get("images", []) or []),
        "video_url": prod.get("video_url", "") or "",
    }
    options = prod.get("options") or []
    variants = prod.get("variants")
    if not variants:
        from services.variants import derive_from_volumes  # lazy: hindari import cycle
        options, variants = derive_from_volumes(prod)
    rows = []
    for v in (variants or [{}]):
        row = dict(base)
        vopts = v.get("options") or {}
        for i in range(OPTION_SLOTS):
            name = options[i]["name"] if i < len(options) else ""
            row[f"option{i + 1}_name"] = name
            row[f"option{i + 1}_value"] = (vopts.get(name, "") if name else "")
        row.update({
            "variant_price": v.get("price", ""),
            "variant_compare_at_price": (v.get("compare_at_price") or ""),
            "variant_stock": v.get("stock", 0),
            "variant_sku": v.get("sku", "") or "",
        })
        rows.append(row)
    return rows
