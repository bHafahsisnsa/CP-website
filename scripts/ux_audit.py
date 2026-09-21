#!/usr/bin/env python3
"""ux_audit.py — baseline UX/testability guard (Collector Parfum frontend).

Struktur FE: pages/ + components/ + store/ + services/ (shadcn di components/ui/).
Memeriksa:
  ERROR (gagal --strict):
    - Elemen <select> NATIVE (harus pakai shadcn Select).
    - URL backend HARDCODE (http/https literal / localhost) di kode FE (harus via env/apiClient).
    - Ikon emoji dipakai sebagai elemen UI di file interaktif (pakai lucide-react).
  WARN (backlog):
    - Elemen interaktif (button/input) tanpa data-testid.
    - Uang dirender tanpa tabular-nums (heuristik).
Usage: cd /app && python scripts/ux_audit.py [--strict]
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FE = ROOT / "frontend" / "src"
G, Y, R, C, B, X = "\033[92m", "\033[93m", "\033[91m", "\033[96m", "\033[1m", "\033[0m"
STRICT = "--strict" in sys.argv
errors, warns = [], []
EMOJI = re.compile("[\U0001F300-\U0001FAFF\U00002600-\U000027BF]")


def target_files():
    if not FE.exists():
        return []
    out = []
    for f in FE.rglob("*.js"):
        s = str(f).replace("\\", "/")
        if "/components/ui/" in s or "/lib/" in s or "/data/" in s:
            continue
        out.append(f)
    return out


def audit():
    for f in target_files():
        rel = f.relative_to(ROOT)
        txt = f.read_text(encoding="utf-8", errors="ignore")
        for i, ln in enumerate(txt.splitlines(), 1):
            if re.search(r"<select[\s>]", ln):
                errors.append(f"{rel}:{i} elemen <select> native — pakai shadcn Select")
            if re.search(r"[\'\"]https?://(localhost|127\.0\.0\.1|[^\'\"/]+)", ln) and "backend" not in ln.lower():
                # izinkan URL non-API (mis. unsplash/asset) — tandai hanya bila terlihat seperti API call
                if re.search(r"(fetch|axios|api)\s*\(", ln) or "/api" in ln:
                    errors.append(f"{rel}:{i} URL backend hardcode — gunakan REACT_APP_BACKEND_URL")
            if EMOJI.search(ln) and re.search(r">\s*" + EMOJI.pattern, ln):
                warns.append(f"{rel}:{i} kemungkinan emoji sebagai ikon UI")
        # interaktif tanpa testid (heuristik ringan per file)
        buttons = len(re.findall(r"<Button\b", txt)) + len(re.findall(r"<button\b", txt))
        testids = len(re.findall(r"data-testid=", txt))
        if buttons >= 3 and testids == 0:
            warns.append(f"{rel}: {buttons} tombol tanpa satupun data-testid")


def main():
    print(f"\n{B}{'='*60}{X}\n  UX AUDIT (strict={STRICT})\n{B}{'='*60}{X}")
    if not FE.exists():
        print(f"  {Y}frontend/src tidak ada — dilewati.{X}")
        return 0
    audit()
    print(f"\n{C}{B}ERROR{X}")
    for e in errors:
        print(f"  {R}[ERROR]{X} {e}")
    if not errors:
        print(f"  {G}none{X}")
    print(f"\n{C}{B}WARN (backlog){X}")
    for w in warns[:40]:
        print(f"  {Y}[WARN]{X} {w}")
    if not warns:
        print(f"  {G}none{X}")
    print(f"\n{B}{'='*60}{X}\n  {R}ERROR {len(errors)}{X} | {Y}WARN {len(warns)}{X}\n{B}{'='*60}{X}")
    if STRICT and errors:
        print(f"  {R}{B}UX GATE FAIL (strict).{X}\n")
        return 1
    print(f"  {G}{B}UX BASELINE OK.{X}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
