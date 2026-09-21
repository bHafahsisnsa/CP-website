"""services/product_fill.py — ISI MASSAL baris impor (matriks TIER x KOMBINASI DIMENSI).

KENAPA MODUL INI ADA (bug nyata, bukan optimasi prematur):
Wizard impor dulu menyimpan 6.426 baris di memori browser dan MENGIRIM ULANG semuanya
(~5,2 MB) setiap kali validasi/menerapkan harga. Pada koneksi normal (~1 Mbps unggah)
satu putaran memindahkan ~11,6 MB sehingga axios timeout dan admin melihat
"Gagal memvalidasi baris." padahal filenya sah. Sekarang baris disimpan di SESI server
(services/product_io_session.py) dan admin hanya mengirim MATRIKS (mis. 24 angka).
Agar itu mungkin, logika terap harus ada di server — inilah SSOT-nya.

Modul MURNI (tanpa I/O DB). Cermin 1:1 dari frontend `importBulkFill.js`; parsing dimensi
memakai `build_row()` dari services.product_import supaya tidak ada drift.

DUA semantik yang TIDAK boleh disatukan (temuan POC):
  - fill_if_empty : hanya mengisi sel kosong atau "0"  (mis. concentration)
  - force_values  : SELALU menimpa (mis. status), karena file klien sudah menulis
                    `status=active` di semua baris sehingga mode "isi bila kosong"
                    tak akan pernah membuat produk menjadi draft.
"""
from typing import Any, Dict, List, Optional, Tuple

from services.product_import import build_row
from services.product_tiers import COMBO_KEY_SEP, extract_tier

MAX_CELLS = 4000          # batas defensif jumlah sel matriks yang diterima
MAX_PATCH_CELLS = 2000    # batas jumlah sel yang boleh di-edit dalam satu patch
PRICE_FIELD = "variant_price"
COMPARE_FIELD = "variant_compare_at_price"


def parse_rupiah(value) -> int:
    """'Rp 385.000' | '385,000' | 385000 -> 385000 (0 bila kosong/tidak sah)."""
    if value is None or value == "":
        return 0
    if isinstance(value, bool):
        return 0
    if isinstance(value, (int, float)):
        return int(value)
    s = str(value).strip()
    neg = s.startswith("-")
    digits = "".join(ch for ch in s if ch.isdigit())
    if not digits:
        return 0
    n = int(digits)
    return -n if neg else n


def row_pairs(raw: dict, mapping: dict) -> Dict[str, str]:
    """Pasangan {namaDimensi: nilai} satu baris — hanya yang terpetakan DAN berisi."""
    r = build_row(raw if isinstance(raw, dict) else {}, mapping or {})
    out: Dict[str, str] = {}
    for name, val in r["variant_options"]:
        n = str(name or "").strip()
        v = str(val or "").strip()
        if n and v:
            out[n] = v
    return out


def row_combo_key(raw: dict, mapping: dict, dim_order: List[str]) -> Optional[str]:
    """Kunci kombinasi dimensi satu baris mengikuti urutan dimensi dari /tiers."""
    pairs = row_pairs(raw, mapping)
    if len(pairs) != len(dim_order or []):
        return None
    if any(n not in pairs for n in dim_order):
        return None
    return COMBO_KEY_SEP.join(pairs[n] for n in dim_order)


def effective_dim_order(rows: List[dict], mapping: dict, sample: int = 300) -> List[str]:
    """Dimensi EFEKTIF: pasangan option{i} yang terpetakan DAN berisi nilai di data."""
    for raw in (rows or [])[:sample]:
        names = list(row_pairs(raw, mapping).keys())
        if names:
            return names
    return []


def _clean_matrix(matrix) -> Dict[str, Dict[str, int]]:
    """Normalisasi {tier: {comboKey: harga}} -> hanya nilai > 0, dengan batas jumlah sel."""
    out: Dict[str, Dict[str, int]] = {}
    if not isinstance(matrix, dict):
        return out
    cells = 0
    for tier, row in matrix.items():
        if not isinstance(row, dict):
            continue
        bucket: Dict[str, int] = {}
        for key, val in row.items():
            price = parse_rupiah(val)
            if price > 0:
                bucket[str(key)] = price
                cells += 1
                if cells >= MAX_CELLS:
                    break
        if bucket:
            out[str(tier)] = bucket
        if cells >= MAX_CELLS:
            break
    return out


def count_cells(matrix) -> int:
    return sum(len(v) for v in _clean_matrix(matrix).values())


def _blank_stats() -> Dict[str, int]:
    return {
        "price_filled": 0, "compare_filled": 0, "rows_skipped_no_tier": 0,
        "rows_skipped_no_combo": 0, "rows_skipped_no_cell": 0,
        "filled_if_empty": 0, "forced": 0,
    }


def apply_bulk_fill(rows: List[dict], mapping: dict, dim_order: List[str],
                    tier_column: Optional[str], matrix,
                    overwrite_price: bool = False, price_field: str = PRICE_FIELD,
                    fill_if_empty: Optional[dict] = None,
                    force_values: Optional[dict] = None,
                    stats: Optional[dict] = None) -> Tuple[List[dict], Dict[str, int]]:
    """Terapkan matriks + nilai kolom lain ke rows (IMMUTABLE — kembalikan list baru)."""
    mapping = dict(mapping or {})
    st = stats if stats is not None else _blank_stats()
    mtx = _clean_matrix(matrix)
    price_header = mapping.get(price_field)
    is_compare = price_field == COMPARE_FIELD
    fill_entries = [(k, v) for k, v in (fill_if_empty or {}).items()
                    if v not in ("", None)]
    force_entries = [(k, v) for k, v in (force_values or {}).items()
                     if v not in ("", None)]

    out: List[dict] = []
    for raw in rows or []:
        nxt = dict(raw) if isinstance(raw, dict) else {}
        for canon, val in fill_entries:
            header = mapping.get(canon)
            if not header:
                continue
            cur = str(nxt.get(header, "") or "").strip()
            if cur in ("", "0"):
                nxt[header] = str(val)
                st["filled_if_empty"] += 1
        for canon, val in force_entries:
            header = mapping.get(canon)
            if not header:
                continue
            nxt[header] = str(val)
            st["forced"] += 1

        if not price_header or not mtx:
            out.append(nxt)
            continue
        tier = extract_tier(nxt.get(tier_column)) if tier_column else ""
        if not tier:
            st["rows_skipped_no_tier"] += 1
            out.append(nxt)
            continue
        key = row_combo_key(nxt, mapping, dim_order or [])
        if not key:
            st["rows_skipped_no_combo"] += 1
            out.append(nxt)
            continue
        cell = mtx.get(tier, {}).get(key, 0)
        if cell <= 0:
            st["rows_skipped_no_cell"] += 1
            out.append(nxt)
            continue
        if overwrite_price or parse_rupiah(nxt.get(price_header)) <= 0:
            nxt[price_header] = str(cell)
            st["compare_filled" if is_compare else "price_filled"] += 1
        out.append(nxt)
    return out, st


def apply_fill_spec(rows: List[dict], mapping: dict, spec: dict,
                    dim_order: Optional[List[str]] = None) -> Tuple[List[dict], Dict[str, int]]:
    """Jalankan satu "Terapkan" dari wizard: matriks harga (+harga coret) & nilai kolom lain.

    spec: {tier_column, matrix_price, matrix_compare, overwrite_price,
           stock (str|None), status ('file'|'archived'|'active'), concentration}
    """
    spec = dict(spec or {})
    mapping = dict(mapping or {})
    order = list(dim_order or []) or effective_dim_order(rows, mapping)
    tier_column = spec.get("tier_column") or None

    force_values: Dict[str, Any] = {}
    stock = spec.get("stock")
    if stock not in ("", None):
        force_values["variant_stock"] = str(max(0, parse_rupiah(stock)))
    status = str(spec.get("status") or "file")
    if status in ("active", "archived"):
        force_values["status"] = status
    fill_if_empty: Dict[str, Any] = {}
    conc = str(spec.get("concentration") or "file")
    if conc in ("EDP", "EDT"):
        fill_if_empty["concentration"] = conc

    stats = _blank_stats()
    out, stats = apply_bulk_fill(
        rows, mapping, order, tier_column, spec.get("matrix_price"),
        overwrite_price=bool(spec.get("overwrite_price")),
        price_field=PRICE_FIELD, fill_if_empty=fill_if_empty,
        force_values=force_values, stats=stats,
    )
    if count_cells(spec.get("matrix_compare")) > 0 and mapping.get(COMPARE_FIELD):
        out, stats = apply_bulk_fill(
            out, mapping, order, tier_column, spec.get("matrix_compare"),
            overwrite_price=True, price_field=COMPARE_FIELD, stats=stats,
        )
    stats["dim_order"] = order  # type: ignore[assignment]
    stats["rows"] = len(out)
    return out, stats


def apply_cells(rows: List[dict], cells) -> Tuple[List[dict], int]:
    """Patch kecil dari tabel pratinjau: [{row: idx(0-based), header, value}]."""
    out = [dict(r) if isinstance(r, dict) else {} for r in (rows or [])]
    updated = 0
    for cell in list(cells or [])[:MAX_PATCH_CELLS]:
        if not isinstance(cell, dict):
            continue
        try:
            idx = int(cell.get("row"))
        except (TypeError, ValueError):
            continue
        header = str(cell.get("header") or "")
        if not header or idx < 0 or idx >= len(out):
            continue
        val = cell.get("value")
        out[idx][header] = "" if val is None else str(val)
        updated += 1
    return out, updated


__all__ = [
    "parse_rupiah", "row_pairs", "row_combo_key", "effective_dim_order",
    "count_cells", "apply_bulk_fill", "apply_fill_spec", "apply_cells",
    "PRICE_FIELD", "COMPARE_FIELD", "MAX_CELLS",
]
