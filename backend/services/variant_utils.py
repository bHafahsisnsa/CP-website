"""services/variant_utils.py — primitif PURE model varian N-dimensi (tanpa I/O).

Dipisah dari services/variants.py agar tiap modul tetap ramping (guardrail <=300
baris). Semua simbol di-re-export oleh `services/variants.py` sehingga pemakai
(`from services import variants as V`) TIDAK berubah.
"""
import re
from typing import List, Optional

SIZE_HINTS = ("ukuran", "size", "ml", "volume")
CONCENTRATION_NAME = "Konsentrasi"
TYPE_NAME = "Tipe"
SIZE_NAME = "Ukuran"
MAX_OPTIONS = 4
MAX_VALUES = 20
MAX_VARIANTS = 100


def is_size_dim(name: str) -> bool:
    n = (name or "").strip().lower()
    return any(h in n for h in SIZE_HINTS)


def parse_ml(value) -> int:
    """'50ml' | '50 ml' | 50 -> 50 (0 bila tak ada angka)."""
    if isinstance(value, (int, float)):
        return int(value)
    m = re.search(r"\d+", str(value or ""))
    return int(m.group()) if m else 0


def _alnum_upper(text, limit: int = 12) -> str:
    return re.sub(r"[^A-Z0-9]+", "", str(text or "").upper())[:limit]


def gen_sku(base: str, opt_values: List[str], taken: set) -> str:
    """SKU deterministik unik dari nama produk + nilai tiap dimensi."""
    parts = [_alnum_upper(base) or "PRD"]
    for v in opt_values:
        parts.append(_alnum_upper(v, 8))
    root = "-".join(p for p in parts if p) or "PRD"
    final, i = root, 2
    while final in taken:
        final, i = f"{root}-{i}", i + 1
    return final


def normalize_options(options_in) -> List[dict]:
    """Bersihkan definisi opsi: nama trim, nilai unik non-kosong, buang opsi tanpa nilai."""
    out: List[dict] = []
    seen_names = set()
    for opt in (options_in or [])[:MAX_OPTIONS]:
        name = str((opt or {}).get("name", "")).strip()[:60]
        if not name or name.lower() in seen_names:
            continue
        values, seen_v = [], set()
        for v in ((opt or {}).get("values") or [])[:MAX_VALUES]:
            v = str(v).strip()[:60]
            if v and v.lower() not in seen_v:
                values.append(v)
                seen_v.add(v.lower())
        if not values:
            continue
        seen_names.add(name.lower())
        out.append({"name": name, "values": values})
    return out


def _size_dim_name(options: List[dict]) -> Optional[str]:
    for o in options:
        if is_size_dim(o["name"]):
            return o["name"]
    return None


def composite_type(variant_options: dict, options: List[dict]) -> str:
    """Gabungan nilai semua dimensi NON-ukuran (urut opsi) -> label `type` legacy."""
    parts = []
    for o in options:
        if is_size_dim(o["name"]):
            continue
        val = str(variant_options.get(o["name"], "")).strip()
        if val:
            parts.append(val)
    return " / ".join(parts)


def variant_label(variant_options: dict, options: List[dict]) -> str:
    """Label lengkap varian untuk tampilan (semua dimensi urut opsi)."""
    parts = []
    for o in options:
        val = str(variant_options.get(o["name"], "")).strip()
        if val:
            parts.append(val)
    return " / ".join(parts)


def _variant_ml(variant_options: dict, options: List[dict]) -> int:
    sd = _size_dim_name(options)
    return parse_ml(variant_options.get(sd)) if sd else 0


__all__ = [
    "SIZE_HINTS", "CONCENTRATION_NAME", "TYPE_NAME", "SIZE_NAME",
    "MAX_OPTIONS", "MAX_VALUES", "MAX_VARIANTS",
    "is_size_dim", "parse_ml", "gen_sku", "normalize_options",
    "composite_type", "variant_label",
]
