"""services/variants.py — SSOT model VARIAN N-dimensi (Shopify-style) untuk Collector Parfum.

Model:
  options : [ {name, values[]} ]              # dimensi bebas, TERURUT. Wajib ada 1 dimensi
                                              # "ukuran/size" (dipakai turunkan `ml`).
  variants: [ {sku, options:{name:value}, price, stock, compare_at_price} ]   # SSOT stok+harga
  price_min/price_max (+ compare_at_min/max)  # dihitung untuk range PLP/PDP.

Kompatibilitas:
  - `volumes[]` (legacy) DITURUNKAN dari variants (type = gabungan dimensi non-ukuran, ml =
    parse dari dimensi ukuran) untuk export/impor & tampilan lama.
  - Produk lama (hanya punya volumes) tetap jalan: derive_from_volumes() membentuk options/
    variants on-the-fly (Konsentrasi + Tipe + Ukuran).

Semua fungsi PURE (tanpa I/O DB) kecuali serialize_product yang hanya mengolah dict.
"""
from typing import List, Optional, Tuple

from core_utils import money
from services.variant_utils import (  # re-export: pemakai `variants as V` TIDAK berubah
    CONCENTRATION_NAME,
    MAX_VARIANTS,
    SIZE_NAME,
    TYPE_NAME,
    _size_dim_name,
    _variant_ml,
    composite_type,
    gen_sku,
    is_size_dim,
    normalize_options,
    parse_ml,
    variant_label,
)


def build_options_variants(name: str, options_in, variants_in) -> Tuple[List[dict], List[dict]]:
    """Validasi + normalisasi options[] & variants[]. Raise ValueError bila tak valid.

    Aturan: >=1 dimensi ukuran; tiap varian punya nilai untuk SEMUA dimensi; nilai harus
    ada di daftar dimensi; price>0, stock>=0, compare null/> price; ml (dari ukuran) > 0;
    kombinasi UNIK; SKU auto & unik.
    """
    options = normalize_options(options_in)
    if not options:
        raise ValueError("Minimal 1 dimensi varian (options).")
    size_name = _size_dim_name(options)
    if not size_name:
        raise ValueError("Wajib ada dimensi ukuran (mis. 'Ukuran' berisi 30ml, 50ml).")
    valid_values = {o["name"]: set(o["values"]) for o in options}

    out: List[dict] = []
    seen_combo = set()
    taken_sku = set()
    for v in (variants_in or [])[:MAX_VARIANTS]:
        raw_opts = (v or {}).get("options") or {}
        ordered = {}
        for o in options:
            val = str(raw_opts.get(o["name"], "")).strip()
            if not val:
                raise ValueError(f"Varian kurang nilai untuk dimensi '{o['name']}'.")
            if val not in valid_values[o["name"]]:
                raise ValueError(f"Nilai '{val}' tidak ada di dimensi '{o['name']}'.")
            ordered[o["name"]] = val

        ml = parse_ml(ordered[size_name])
        if ml <= 0:
            raise ValueError(f"Ukuran '{ordered[size_name]}' tidak valid (harus mengandung angka > 0).")

        try:
            price = money(v.get("price"))
            stock = int(v.get("stock", 0) or 0)
        except (TypeError, ValueError):
            raise ValueError("Varian: harga/stok bukan angka.")
        if price <= 0:
            raise ValueError("Varian: harga harus > 0.")
        if stock < 0:
            raise ValueError("Varian: stok tidak boleh negatif.")

        cap = v.get("compare_at_price")
        cap_v = None
        if cap not in (None, "", 0, "0"):
            cap_v = money(cap)
            if cap_v <= price:
                raise ValueError(f"compare_at_price ({variant_label(ordered, options)}) harus > harga.")

        combo = tuple(ordered[o["name"]] for o in options)
        if combo in seen_combo:
            raise ValueError(f"Kombinasi varian duplikat: {variant_label(ordered, options)}")
        seen_combo.add(combo)

        sku = str(v.get("sku") or "").strip()[:60]
        if not sku:
            sku = gen_sku(name, list(combo), taken_sku)
        if sku in taken_sku:
            raise ValueError(f"SKU duplikat dalam produk: {sku}")
        taken_sku.add(sku)

        out.append({"sku": sku, "options": ordered, "price": price,
                    "stock": stock, "compare_at_price": cap_v})
    if not out:
        raise ValueError("Minimal 1 kombinasi varian.")
    return options, out


def derive_from_volumes(prod: dict) -> Tuple[List[dict], List[dict]]:
    """Bentuk options/variants dari `volumes[]` legacy (migrasi/derive-on-read).

    Dimensi: Konsentrasi (nilai tunggal dari produk, bila ada) + Tipe (bila varian bertipe)
    + Ukuran (dari ml). SKU dipertahankan bila sudah ada.
    """
    vols = prod.get("volumes") or []
    concentration = str(prod.get("concentration") or "").strip()
    types, seen_t = [], set()
    sizes, seen_s = [], set()
    has_type = any(str(v.get("type") or "").strip() for v in vols)
    for v in vols:
        t = str(v.get("type") or "").strip()
        if has_type and t and t.lower() not in seen_t:
            types.append(t)
            seen_t.add(t.lower())
        ml = int(v.get("ml") or 0)
        if ml > 0 and ml not in seen_s:
            sizes.append(ml)
            seen_s.add(ml)
    sizes.sort()

    options: List[dict] = []
    if concentration:
        options.append({"name": CONCENTRATION_NAME, "values": [concentration]})
    if types:
        options.append({"name": TYPE_NAME, "values": types})
    options.append({"name": SIZE_NAME, "values": [f"{ml}ml" for ml in sizes]})

    taken_sku = set()
    variants: List[dict] = []
    for v in vols:
        ml = int(v.get("ml") or 0)
        if ml <= 0:
            continue
        opts = {}
        if concentration:
            opts[CONCENTRATION_NAME] = concentration
        if types:
            opts[TYPE_NAME] = str(v.get("type") or "").strip()
        opts[SIZE_NAME] = f"{ml}ml"
        sku = str(v.get("sku") or "").strip()
        if not sku or sku in taken_sku:
            sku = gen_sku(prod.get("name") or prod.get("slug") or "", list(opts.values()), taken_sku)
        taken_sku.add(sku)
        cap = v.get("compare_at_price")
        variants.append({
            "sku": sku, "options": opts, "price": money(v.get("price")),
            "stock": int(v.get("stock", 0) or 0),
            "compare_at_price": (money(cap) if cap else None),
        })
    return options, variants


def derive_volumes(options: List[dict], variants: List[dict]) -> List[dict]:
    """Turunkan `volumes[]` legacy dari variants (type=gabungan non-ukuran, ml=parse ukuran)."""
    out = []
    for v in variants:
        opts = v.get("options") or {}
        out.append({
            "type": composite_type(opts, options),
            "ml": _variant_ml(opts, options),
            "price": money(v.get("price")),
            "stock": int(v.get("stock", 0) or 0),
            "compare_at_price": (money(v["compare_at_price"]) if v.get("compare_at_price") else None),
            "sku": v.get("sku"),
        })
    return out


def price_range(variants: List[dict]) -> dict:
    """Hitung range harga + harga/coret display (mengacu varian termurah)."""
    prices = [money(v.get("price")) for v in variants if money(v.get("price")) > 0]
    if not prices:
        return {"price": 0, "price_min": 0, "price_max": 0,
                "compare_at_price": None, "compare_at_min": None, "compare_at_max": None}
    price_min, price_max = min(prices), max(prices)
    cheapest = min(variants, key=lambda v: money(v.get("price")))
    caps = [money(v["compare_at_price"]) for v in variants if v.get("compare_at_price")]
    return {
        "price": price_min,
        "price_min": price_min,
        "price_max": price_max,
        "compare_at_price": (money(cheapest["compare_at_price"]) if cheapest.get("compare_at_price") else None),
        "compare_at_min": (min(caps) if caps else None),
        "compare_at_max": (max(caps) if caps else None),
    }


def serialize_product(prod: dict) -> dict:
    """Perkaya dokumen produk untuk API: pastikan options/variants ada (derive bila legacy),
    hitung range harga, dan segarkan `volumes[]` turunan. Stok SSOT = variants[].stock."""
    if not prod:
        return prod
    options = prod.get("options")
    variants = prod.get("variants")
    if not variants:
        options, variants = derive_from_volumes(prod)
    options = options or []
    prod["options"] = options
    prod["variants"] = variants
    prod["volumes"] = derive_volumes(options, variants)
    prod.update(price_range(variants))
    return prod


def resolve_variant(prod: dict, *, sku: Optional[str] = None,
                    variant_type: str = "", volume_ml: Optional[int] = None) -> Optional[dict]:
    """Cari varian: prioritas SKU; fallback legacy (variant_type + volume_ml). None bila tak ada."""
    options = prod.get("options")
    variants = prod.get("variants")
    if not variants:
        options, variants = derive_from_volumes(prod)
    if sku:
        return next((v for v in variants if v.get("sku") == sku), None)
    if volume_ml is None:
        return None
    ml = int(volume_ml)
    candidates = [v for v in variants if _variant_ml(v.get("options") or {}, options) == ml]
    if not candidates:
        return None
    vt = str(variant_type or "").strip()
    if vt:
        narrowed = [
            v for v in candidates
            if composite_type(v.get("options") or {}, options) == vt
            or vt in (v.get("options") or {}).values()
        ]
        if narrowed:
            return narrowed[0]
    return candidates[0] if len(candidates) == 1 else (candidates[0] if not vt else None)


__all__ = [
    "is_size_dim", "parse_ml", "gen_sku", "normalize_options", "composite_type",
    "variant_label", "build_options_variants", "derive_from_volumes", "derive_volumes",
    "price_range", "serialize_product", "resolve_variant",
    "CONCENTRATION_NAME", "TYPE_NAME", "SIZE_NAME",
]
