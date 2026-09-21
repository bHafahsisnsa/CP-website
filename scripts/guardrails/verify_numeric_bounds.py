#!/usr/bin/env python3
"""INV-NUM-01 — Field numerik uang/kuantitas WAJIB ber-bound (ge=/gt=). (STATIK, jalan sekarang)

Kelas bug dicegah: 'negative-value' (harga/stok/qty/amount menerima nilai negatif → total kacau,
stok negatif, refund/abuse). Scan AST backend/schemas.py; tiap field int/float harus punya
Field(..., ge=/gt=) ATAU terdaftar di ALLOW_UNBOUNDED (dengan alasan). Field baru yang lupa
dibatasi => gate MERAH otomatis.
Usage: cd /app && python scripts/guardrails/verify_numeric_bounds.py
"""
import ast
import os
import re
import sys

sys.path.insert(0, os.path.dirname(__file__))
from _common import BACKEND, Guard  # noqa: E402

# Field numerik yang MEMANG boleh tak-berbound (bukan uang/kuantitas) — wajib beralasan.
ALLOW_UNBOUNDED = {
    # (kosong untuk domain parfum: semua uang/kuantitas harus ge=/gt=)
}


def is_numeric(ann: str) -> bool:
    return bool(re.search(r"\b(int|float)\b", ann))


def main() -> int:
    g = Guard("INV-NUM-01", "Field numerik uang/kuantitas wajib ber-bound (ge=/gt=)")
    schemas = BACKEND / "schemas.py"
    if not schemas.exists():
        g.add("backend/schemas.py tidak ada.")
        return g.finish()
    txt = schemas.read_text(encoding="utf-8", errors="ignore")
    tree = ast.parse(txt)
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        for stmt in node.body:
            if not isinstance(stmt, ast.AnnAssign) or not isinstance(stmt.target, ast.Name):
                continue
            ann = ast.unparse(stmt.annotation)
            if not is_numeric(ann):
                continue
            # 'bool' adalah subclass int di Python; lewati field boolean murni.
            if re.search(r"\bbool\b", ann):
                continue
            key = f"{node.name}.{stmt.target.id}"
            val = ast.unparse(stmt.value) if stmt.value is not None else ""
            bounded = bool(re.search(r"\b(ge|gt)\s*=", val))
            g.bump()
            if bounded or key in ALLOW_UNBOUNDED:
                continue
            g.add(f"{key} ({ann}) TANPA ge=/gt= → menerima nilai negatif. "
                  f"Tambahkan Field(..., ge=0) di schemas.py, atau daftarkan di ALLOW_UNBOUNDED dgn alasan.")
    return g.finish()


if __name__ == "__main__":
    sys.exit(main())
