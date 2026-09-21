#!/usr/bin/env python3
"""fa_static.py — FORENSIC: analisis statik backend (anti tech-debt & jebakan runtime).

Mendeteksi pola berbahaya SEBELUM runtime:
  HIGH (exit 1): datetime naif (datetime.now()/utcnow() tanpa tz) di router/service,
                 eval(/exec(, `except:` telanjang, `.to_list(None)` unbounded.
  WARN         : `except Exception: pass` (menelan error), TODO/FIXME, print( di router/service.
Usage: cd /app && python forensic/fa_static.py
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BACKEND = ROOT / "backend"
G, Y, R, B, X = "\033[92m", "\033[93m", "\033[91m", "\033[1m", "\033[0m"
high, warn = [], []

NAIVE_DT = re.compile(r"datetime\.(now\(\s*\)|utcnow\(\))")
BARE_EXCEPT = re.compile(r"^\s*except\s*:\s*$")


def scan():
    for f in BACKEND.rglob("*.py"):
        sp = str(f).replace("\\", "/")
        # Lewati cache & FILE TEST (bukan kode produksi): backend_test.py, test_*.py, /tests/
        if "__pycache__" in sp or "/tests/" in sp:
            continue
        if f.name.endswith("_test.py") or f.name.startswith("test_") or f.name == "backend_test.py":
            continue
        rel = f.relative_to(ROOT)
        lines = f.read_text(encoding="utf-8", errors="ignore").splitlines()
        in_router_svc = ("/routers/" in str(f).replace("\\", "/")) or ("/services/" in str(f).replace("\\", "/"))
        for i, ln in enumerate(lines, 1):
            if NAIVE_DT.search(ln) and "timezone" not in ln:
                high.append(f"{rel}:{i} datetime naif tanpa tz → pakai datetime.now(timezone.utc).")
            if "eval(" in ln or re.search(r"\bexec\(", ln):
                high.append(f"{rel}:{i} eval/exec — bahaya injeksi.")
            if BARE_EXCEPT.match(ln):
                high.append(f"{rel}:{i} `except:` telanjang — sembunyikan bug. Tangkap tipe spesifik.")
            if ".to_list(None)" in ln:
                high.append(f"{rel}:{i} .to_list(None) unbounded — beri limit.")
            if re.search(r"except\s+Exception\s*:\s*$", ln) and i < len(lines) and lines[i].strip() == "pass":
                warn.append(f"{rel}:{i} `except Exception: pass` menelan error (audit best-effort? beri komentar).")
            if re.search(r"#\s*(TODO|FIXME)", ln, re.I):
                warn.append(f"{rel}:{i} TODO/FIXME tertinggal.")
            if in_router_svc and re.match(r"\s*print\(", ln):
                warn.append(f"{rel}:{i} print( di router/service — pakai logger.")


def main():
    print(f"\n{B}FA_STATIC — analisis statik backend{X}")
    scan()
    print(f"\n{B}HIGH{X}")
    for h in high:
        print(f"  {R}[HIGH]{X} {h}")
    if not high:
        print(f"  {G}none{X}")
    print(f"\n{B}WARN{X}")
    for w in warn[:30]:
        print(f"  {Y}[WARN]{X} {w}")
    if not warn:
        print(f"  {G}none{X}")
    print(f"\n  {R}HIGH {len(high)}{X} | {Y}WARN {len(warn)}{X}")
    return 1 if high else 0


if __name__ == "__main__":
    sys.exit(main())
