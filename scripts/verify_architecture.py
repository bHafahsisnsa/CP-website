#!/usr/bin/env python3
"""verify_architecture.py — performa & tech-debt (statik) untuk Collector Parfum.

Mendeteksi anti-pattern skalabilitas SEBELUM jadi masalah:
  - Unbounded query: .to_list(None) / .find(...).to_list() tanpa limit pada router.
  - N+1: `await db...` di dalam loop `for`.
  - Batas ukuran file: router <= 800, service/util <= 300 baris.
  - Kebocoran field sensitif: kembalikan password_hash.
Default: laporan (exit 0). --strict: exit 1 bila ada ERROR.
Usage: cd /app && python scripts/verify_architecture.py [--strict]
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BACKEND = ROOT / "backend"
G, Y, R, C, B, X = "\033[92m", "\033[93m", "\033[91m", "\033[96m", "\033[1m", "\033[0m"
STRICT = "--strict" in sys.argv
errors, warns = [], []


def E(msg):
    errors.append(msg)
    print(f"  {R}[ERROR]{X} {msg}")


def W(msg):
    warns.append(msg)
    print(f"  {Y}[WARN]{X} {msg}")


def scan_unbounded_and_nplus1():
    print(f"\n{C}{B}Query performance (unbounded / N+1){X}")
    routers = BACKEND / "routers"
    svcs = BACKEND / "services"
    files = []
    for d in (routers, svcs):
        if d.exists():
            files += list(d.glob("*.py"))
    hits = 0
    for f in files:
        lines = f.read_text(encoding="utf-8", errors="ignore").splitlines()
        for i, ln in enumerate(lines, 1):
            if ".to_list(None)" in ln:
                E(f"{f.name}:{i} unbounded .to_list(None) — beri limit")
                hits += 1
            # find(...).to_list(  tanpa argumen numerik -> unbounded
            if re.search(r"\.find\([^\n]*\)\.to_list\(\s*\)", ln):
                W(f"{f.name}:{i} .to_list() tanpa limit eksplisit")
            # N+1: await db... di dalam blok for (heuristik indentasi)
        # heuristik N+1
        for i in range(len(lines) - 1):
            if re.match(r"\s*for \w+ in ", lines[i]):
                block = lines[i + 1:i + 8]
                if any(re.search(r"await\s+db\.", b) for b in block):
                    W(f"{f.name}:{i+1} kemungkinan N+1 (await db.* di dalam for)")
    if hits == 0:
        print(f"  {G}[OK]{X} tidak ada unbounded .to_list(None) di router/service")


def scan_file_sizes():
    print(f"\n{C}{B}Batas ukuran file{X}")
    limits = {"routers": 800, "services": 300}
    for sub, limit in limits.items():
        d = BACKEND / sub
        if not d.exists():
            continue
        for f in d.glob("*.py"):
            n = len(f.read_text(encoding="utf-8", errors="ignore").splitlines())
            if n > limit:
                E(f"{sub}/{f.name}: {n} baris > {limit} — pecah (SRP)")
    # util backend top-level
    for f in BACKEND.glob("*.py"):
        n = len(f.read_text(encoding="utf-8", errors="ignore").splitlines())
        limit = 400 if f.name == "schemas.py" else 300
        if n > limit:
            W(f"{f.name}: {n} baris > {limit}")
    if not errors:
        print(f"  {G}[OK]{X} semua file dalam batas")


def scan_sensitive_leak():
    print(f"\n{C}{B}Kebocoran field sensitif{X}")
    leak = 0
    for f in BACKEND.rglob("*.py"):
        if "__pycache__" in str(f):
            continue
        txt = f.read_text(encoding="utf-8", errors="ignore")
        # kembalikan dokumen user tanpa safe_doc + menyebut password_hash secara literal di return
        for i, ln in enumerate(txt.splitlines(), 1):
            if re.search(r"return .*password_hash", ln):
                E(f"{f.name}:{i} mengembalikan password_hash")
                leak += 1
    if leak == 0:
        print(f"  {G}[OK]{X} tidak ada kebocoran password_hash pada return")


def main():
    print(f"\n{B}{'='*60}{X}\n  VERIFY ARCHITECTURE (strict={STRICT})\n{B}{'='*60}{X}")
    scan_unbounded_and_nplus1()
    scan_file_sizes()
    scan_sensitive_leak()
    print(f"\n{B}{'='*60}{X}\n  {R}ERROR {len(errors)}{X} | {Y}WARN {len(warns)}{X}\n{B}{'='*60}{X}")
    if STRICT and errors:
        print(f"  {R}{B}ARCHITECTURE GATE FAIL (strict).{X}\n")
        return 1
    print(f"  {G}{B}ARCHITECTURE OK.{X}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
