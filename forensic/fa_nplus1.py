#!/usr/bin/env python3
"""fa_nplus1.py — FORENSIC: deteksi N+1 query (heuristik statik).

Menandai `await db.<coll>....` di dalam blok `for`/`while` pada router/service — pola klasik
N+1 (query per item). Solusi: batukan dengan `$in`/aggregate. WARN (bukan hard-fail) agar tak
false-positive, tapi wajib direview. Exit 0 (laporan); pakai --strict utk exit 1 bila ada temuan.
Usage: cd /app && python forensic/fa_nplus1.py [--strict]
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BACKEND = ROOT / "backend"
G, Y, R, B, X = "\033[92m", "\033[93m", "\033[91m", "\033[1m", "\033[0m"
STRICT = "--strict" in sys.argv
hits = []


def scan():
    for sub in ("routers", "services"):
        d = BACKEND / sub
        if not d.exists():
            continue
        for f in d.glob("*.py"):
            lines = f.read_text(encoding="utf-8", errors="ignore").splitlines()
            for i, ln in enumerate(lines):
                if re.match(r"\s*(for|while)\b", ln):
                    indent = len(ln) - len(ln.lstrip())
                    for j in range(i + 1, min(i + 12, len(lines))):
                        nxt = lines[j]
                        if nxt.strip() and (len(nxt) - len(nxt.lstrip())) <= indent:
                            break
                        if re.search(r"await\s+db\.[a-z_]+\.(find|count|aggregate|update|insert|delete)", nxt):
                            hits.append(f"{f.name}:{j+1} query DB di dalam loop (baris for/while {i+1}) → kemungkinan N+1.")


def main():
    print(f"\n{B}FA_NPLUS1 — deteksi N+1 (heuristik statik){X}")
    scan()
    for h in hits:
        print(f"  {Y}[N+1?]{X} {h}")
    if not hits:
        print(f"  {G}✓ Tidak ada pola N+1 terdeteksi di router/service.{X}")
    print(f"\n  temuan: {len(hits)}")
    return 1 if (STRICT and hits) else 0


if __name__ == "__main__":
    sys.exit(main())
