#!/usr/bin/env python3
"""fa_dark_sweep.py — FORENSIC: endpoint 'gelap' (BE ada, FE tak memanggil).

Memetakan route backend yang TIDAK direferensikan di frontend → fitur yatim / dead code / risiko
akses tak terkelola. Melewati infra (/api/, health, auth) & path dinamis (dicocokkan via segmen literal).
Laporan (exit 0); pakai --strict utk exit 1 bila ada endpoint gelap non-infra.
Usage: cd /app && python forensic/fa_dark_sweep.py [--strict]
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FE = ROOT / "frontend" / "src"
G, Y, R, B, X = "\033[92m", "\033[93m", "\033[91m", "\033[1m", "\033[0m"
STRICT = "--strict" in sys.argv
sys.path.insert(0, str(ROOT / "backend"))


def routes():
    try:
        from server import app
    except Exception as e:
        print(f"{Y}server.app tak bisa di-import ({e}) — SKIP.{X}")
        return None
    return sorted({getattr(r, "path", "") for r in app.routes
                   if getattr(r, "path", "").startswith("/api")})


def fe_text():
    if not FE.exists():
        return ""
    return "\n".join(f.read_text(encoding="utf-8", errors="ignore")
                     for f in list(FE.rglob("*.js")) + list(FE.rglob("*.jsx"))
                     if "/components/ui/" not in str(f).replace("\\", "/"))


def main():
    rts = routes()
    if rts is None:
        return 0
    fe = fe_text()
    INFRA = {"/api/", "/api/health", "/api/status"}
    dark = []
    for rt in rts:
        if rt in INFRA:
            continue
        segs = [s for s in rt.split("/") if s and not s.startswith("{")]
        key = segs[1] if len(segs) > 1 else (segs[0] if segs else "")
        if key in ("auth", "health", "status", ""):
            continue
        if key and key not in fe:
            dark.append(rt)
    print(f"\n{B}FA_DARK_SWEEP — {len(rts)} route backend, cek referensi FE{X}")
    if dark:
        for d in sorted(set(dark)):
            print(f"  {Y}[DARK]{X} {d} — tak direferensikan frontend.")
    else:
        print(f"  {G}✓ Tidak ada endpoint gelap (semua non-infra dipakai FE).{X}")
    return 1 if (STRICT and dark) else 0


if __name__ == "__main__":
    sys.exit(main())
