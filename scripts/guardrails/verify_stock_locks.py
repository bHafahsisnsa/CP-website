#!/usr/bin/env python3
"""INV-RACE-01 — Reservasi/mutasi STOK wajib di-serial (stock_lock) + atomik. (STATIK)

Kelas bug dicegah: RC-E3 oversell (TOCTOU) — dua checkout paralel membeli unit terakhir → stok negatif.

Dua lapis (grow-with-code):
  (1) AUTO-DISCOVERY — tiap fungsi router MUTATING (post/put/patch/delete) yang menurunkan stok
      (memanggil helper `decrement_stock(` / `reserve_stock(` / `adjust_stock(`) WAJIB memegang
      `stock_lock(` ATAU memakai update atomik ber-guard (`$inc` dgn filter `stock >= qty`).
      Menangkap write-path BARU otomatis saat checkout/admin-stock dibuat.
  (2) REGISTRY REGRESSION — jalur reservasi yang diketahui harus TETAP terkunci (anchor).

Saat belum ada jalur stok (fase fondasi) → 0 cek → PASS. Aktif otomatis di fase business-logic.
Usage: cd /app && python scripts/guardrails/verify_stock_locks.py
"""
import ast
import os
import re
import sys

sys.path.insert(0, os.path.dirname(__file__))
from _common import BACKEND, Guard  # noqa: E402

DECREMENTERS = ("decrement_stock(", "reserve_stock(", "adjust_stock(", "deduct_stock(")
MUTATING = ("post", "put", "patch", "delete")
ATOMIC_GUARD = re.compile(r"\$inc[^\n]*stock|update_one\([^\n]*stock[^\n]*\$gte|find_one_and_update[^\n]*stock")

# Aman-by-design (tak menurunkan stok baru) — wajib beralasan.
ALLOW = {}

# Jalur reservasi stok yang DIKETAHUI — harus tetap memegang lock/atomik (diisi di fase 2).
REGISTRY = {
    # "orders.create_order": "stock_lock",
}


def route_method(node):
    for dec in node.decorator_list:
        try:
            s = ast.unparse(dec)
        except Exception:
            s = ""
        m = re.search(r"router\.(get|post|put|patch|delete)", s)
        if m:
            return m.group(1)
    return None


def funcs(path):
    fp = BACKEND / path
    txt = fp.read_text(encoding="utf-8", errors="ignore")
    tree = ast.parse(txt)
    lines = txt.splitlines()
    out = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.AsyncFunctionDef, ast.FunctionDef)):
            start = node.lineno - 1
            end = getattr(node, "end_lineno", start + 80)
            out.append((node.name, route_method(node), "\n".join(lines[start:end])))
    return out


def main() -> int:
    g = Guard("INV-RACE-01", "Mutasi stok wajib di-serial (stock_lock) atau atomik ber-guard")
    routers_dir = BACKEND / "routers"
    seen = {}
    if routers_dir.exists():
        for f in sorted(routers_dir.glob("*.py")):
            module = f.stem
            for name, method, src in funcs(f"routers/{f.name}"):
                key = f"{module}.{name}"
                seen[key] = src
                if method not in MUTATING or key in ALLOW:
                    continue
                decs = any(x in src for x in DECREMENTERS)
                if not decs:
                    continue
                g.bump()
                has_lock = "stock_lock(" in src
                has_atomic = bool(ATOMIC_GUARD.search(src))
                if not (has_lock or has_atomic):
                    g.add(f"{key}: menurunkan stok TANPA stock_lock/atomic-guard → risiko TOCTOU oversell (RC-E3). "
                          f"Bungkus dgn `async with stock_lock(db, product_id):` atau `$inc` ber-filter `stock>=qty`.")
    # Registry regression
    for key, need in REGISTRY.items():
        g.bump()
        src = seen.get(key)
        if src is None:
            g.add(f"REGISTRY: jalur stok '{key}' tak ditemukan (rename/hapus?). Perbarui REGISTRY & pastikan penguncian ada.")
        elif (need + "(") not in src and not ATOMIC_GUARD.search(src):
            g.add(f"REGISTRY: '{key}' kehilangan `{need}`/atomic-guard (REGRESI penguncian!).")
    return g.finish()


if __name__ == "__main__":
    sys.exit(main())
