"""services/product_tiers.py — Deteksi TIER HARGA + dimensi efektif untuk ISI HARGA MASSAL.

Masalah nyata yang dipecahkan: file katalog klien sering datang dengan `variant_price = 0`
(harga belum ditetapkan) tetapi punya penanda TIER harga per produk (mis. kolom `tags`
berisi "Floral, Unisex, Tier CP02", atau kolom QC "Tier Harga" berisi "CP [01]").
Karena setiap produk punya kombinasi dimensi yang sama (mis. Ukuran x Tipe), seluruh harga
bisa ditentukan dari matriks kecil: TIER x KOMBINASI DIMENSI.

Modul ini MURNI (tanpa I/O DB) dan TIDAK menghitung/menyimpan harga — hanya melaporkan
struktur (tier, dimensi efektif, kombinasi) supaya UI wizard bisa merender matriksnya.
Parsing dimensi memakai `build_row()` dari services.product_import (SATU SSOT, anti-drift).
"""
import re
from typing import Dict, List, Optional

from services.product_import import _is_size_name, build_row
from services.product_io import parse_ml, slugify

MAX_ROWS = 30000          # batas defensif payload analisis
MAX_TIERS = 60            # lebih dari ini bukan "tier" (kemungkinan kolom teks bebas)
MAX_COMBOS = 240          # batas sel matriks yang wajar untuk dirender UI
MAX_DIM_VALUES = 40
MAX_CANDIDATES = 8
MIN_COVERAGE = 0.5        # kolom kandidat harus mengandung tier di >=50% baris
COMBO_SEP = " \u00b7 "    # "35ml · Standard"
COMBO_KEY_SEP = "|"

# "Tier CP02" / "tier: 2" -> ambil sisanya.
_TIER_TOKEN_RE = re.compile(r"^\s*tier\s*(?:harga)?\s*[:\-]?\s*(.+?)\s*$", re.I)
# "CP01" / "CP [01]" / "CP 1" -> (huruf, angka).
_CODE_RE = re.compile(r"^\s*([A-Za-z]{1,6})\s*\[?\s*(\d{1,3})\s*\]?\s*$")
_SPLIT_RE = re.compile(r"[,;|/\n]+")


def _clean_tier(raw) -> str:
    """Normalisasi label tier: 'CP [01]' & 'CP1' -> 'CP01'; sisanya UPPER + rapat spasi."""
    s = re.sub(r"\s+", " ", str(raw or "").strip())
    if not s:
        return ""
    m = _CODE_RE.match(s)
    if m:
        return f"{m.group(1).upper()}{int(m.group(2)):02d}"
    return s.upper()[:40]


def extract_tier(value) -> str:
    """Ambil label tier dari SATU nilai sel. Mendukung daftar dipisah koma/pipe.

    Prioritas: token yang menyebut kata "tier" (paling eksplisit), lalu token berpola
    kode (CP01 / CP [01]). Kembalikan "" bila tidak ada.
    """
    txt = str(value if value is not None else "")
    if not txt.strip():
        return ""
    tokens = _SPLIT_RE.split(txt)
    for tok in tokens:
        m = _TIER_TOKEN_RE.match(tok)
        if m:
            label = _clean_tier(m.group(1))
            if label:
                return label
    for tok in tokens:
        t = tok.strip()
        if _CODE_RE.match(t):
            return _clean_tier(t)
    return ""


def _headers_of(rows: List[dict]) -> List[str]:
    seen: List[str] = []
    for r in rows[:50]:
        if not isinstance(r, dict):
            continue
        for k in r:
            ks = str(k)
            if ks and ks not in seen:
                seen.append(ks)
    return seen


def detect_tier_columns(rows: List[dict], headers: Optional[List[str]] = None,
                        sample: int = 800) -> List[dict]:
    """Cari kolom yang paling mungkin memuat tier harga. Deterministik, tanpa LLM."""
    hs = headers or _headers_of(rows)
    sample_rows = [r for r in rows[:sample] if isinstance(r, dict)]
    n = len(sample_rows) or 1
    out = []
    for h in hs:
        labels: Dict[str, int] = {}
        hit = 0
        for r in sample_rows:
            lab = extract_tier(r.get(h))
            if lab:
                hit += 1
                labels[lab] = labels.get(lab, 0) + 1
        if not hit:
            continue
        cov = hit / n
        if cov < MIN_COVERAGE or len(labels) > MAX_TIERS:
            continue
        out.append({"column": h, "coverage": round(cov, 4), "tiers": len(labels)})
    out.sort(key=lambda x: (-x["coverage"], x["tiers"], x["column"]))
    return out[:MAX_CANDIDATES]


def _sorted_values(name: str, values: List[str]) -> List[str]:
    """Dimensi ukuran diurutkan numerik (35ml < 60ml < 100ml); lainnya urut kemunculan."""
    if _is_size_name(name):
        return sorted(values, key=lambda v: (parse_ml(v), str(v)))
    return list(values)


def _tier_sort_key(label: str):
    """Urut natural: CP01 < CP02 < CP10 < EXCLUSIVE (angka dulu, lalu alfabet)."""
    m = _CODE_RE.match(label)
    if m:
        return (0, m.group(1).upper(), int(m.group(2)), label)
    return (1, label, 0, label)


def analyze_tiers(rows, mapping, tier_column: Optional[str] = None) -> dict:
    """Laporkan struktur matriks harga massal untuk satu batch baris impor.

    Kembalikan: kolom tier terpilih + kandidat, daftar tier (jumlah baris & produk),
    dimensi EFEKTIF (yang benar-benar berisi nilai) + kombinasi yang benar-benar muncul,
    serta ringkasan baris tanpa tier / tanpa harga.
    """
    rows = [r for r in list(rows or [])[:MAX_ROWS] if isinstance(r, dict)]
    mapping = dict(mapping or {})
    headers = _headers_of(rows)
    candidates = detect_tier_columns(rows, headers)
    col = tier_column if (tier_column and tier_column in headers) else (
        candidates[0]["column"] if candidates else None)

    dim_order: List[str] = []
    dim_values: Dict[str, List[str]] = {}
    combo_rows: Dict[str, dict] = {}
    tier_rows: Dict[str, int] = {}
    tier_products: Dict[str, set] = {}
    cell_rows: Dict[str, Dict[str, dict]] = {}
    products: set = set()
    rows_without_tier = 0
    rows_without_price = 0

    for raw in rows:
        r = build_row(raw, mapping)
        pkey = (r["slug"] or slugify(r["name"])) if (r["slug"] or r["name"]) else ""
        if pkey:
            products.add(pkey)
        zero_price = r["variant_price"] <= 0
        if zero_price:
            rows_without_price += 1

        row_key = None
        eff = [(str(n).strip(), str(v).strip())
               for n, v in r["variant_options"] if str(n).strip() and str(v).strip()]
        if eff:
            names = [n for n, _ in eff]
            if not dim_order:
                dim_order = names
                dim_values = {n: [] for n in names}
            for n, v in eff:
                bucket = dim_values.get(n)
                if bucket is not None and v not in bucket and len(bucket) < MAX_DIM_VALUES:
                    bucket.append(v)
            if names == dim_order:
                vd = dict(eff)
                key = COMBO_KEY_SEP.join(vd[n] for n in dim_order)
                row_key = key
                slot = combo_rows.get(key)
                if slot is None and len(combo_rows) < MAX_COMBOS:
                    slot = combo_rows[key] = {"values": {n: vd[n] for n in dim_order}, "rows": 0}
                if slot is not None:
                    slot["rows"] += 1

        label = extract_tier(raw.get(col)) if col else ""
        if label:
            tier_rows[label] = tier_rows.get(label, 0) + 1
            tier_products.setdefault(label, set()).add(pkey)
            # Jumlah baris per SEL matriks (tier x kombinasi) supaya UI bisa menghitung
            # pratinjau "akan mengisi N harga" TANPA menyimpan 6.426 baris di browser.
            if row_key is not None and len(cell_rows.get(label, ())) < MAX_COMBOS:
                cell = cell_rows.setdefault(label, {}).setdefault(row_key, {"rows": 0, "zero": 0})
                cell["rows"] += 1
                if zero_price:
                    cell["zero"] += 1
        else:
            rows_without_tier += 1

    dimensions = [{"name": n, "values": _sorted_values(n, dim_values.get(n, []))}
                  for n in dim_order]
    combos = [
        {"key": k, "values": v["values"], "rows": v["rows"],
         "label": COMBO_SEP.join(v["values"][n] for n in dim_order)}
        for k, v in sorted(
            combo_rows.items(),
            key=lambda kv: [
                _sorted_values(n, dim_values.get(n, [])).index(kv[1]["values"][n])
                if kv[1]["values"][n] in dim_values.get(n, []) else 99
                for n in dim_order
            ],
        )
    ]
    tiers = [{"label": t, "rows": tier_rows[t], "products": len(tier_products.get(t, ()))}
             for t in sorted(tier_rows, key=_tier_sort_key)][:MAX_TIERS]

    return {
        "tier_column": col,
        "tier_column_candidates": candidates,
        "tiers": tiers,
        "dimensions": dimensions,
        "combos": combos,
        "cell_rows": cell_rows,
        "summary": {
            "rows": len(rows),
            "products": len(products),
            "rows_without_tier": rows_without_tier,
            "rows_without_price": rows_without_price,
            "cells": len(tiers) * len(combos),
        },
    }


__all__ = ["extract_tier", "detect_tier_columns", "analyze_tiers",
           "COMBO_KEY_SEP", "COMBO_SEP", "MAX_TIERS", "MAX_COMBOS"]
