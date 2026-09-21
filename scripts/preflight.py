#!/usr/bin/env python3
"""preflight.py — ANTI-DUPLIKASI / ANTI-ASUMSI (alat bantu).

Jalankan SEBELUM membangun fitur:
    python scripts/preflight.py "<kata-kunci>"   (mis. "product", "order", "voucher")
Menjawab dari SSOT + codebase nyata: koleksi kanonik/alias, route backend, komponen FE.
EXISTS = REUSE. NEW = daftarkan ke gate terkait (docs/07 §7). Selalu exit 0.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ROUTERS = ROOT / "backend" / "routers"
FRONTEND = ROOT / "frontend" / "src"
G, Y, R, C, B, X = "\033[92m", "\033[93m", "\033[91m", "\033[96m", "\033[1m", "\033[0m"

sys.path.insert(0, str(ROOT / "scripts"))
try:
    from verify_contract import CANONICAL_COLLECTIONS, DANGEROUS_ALIASES
except Exception:
    CANONICAL_COLLECTIONS, DANGEROUS_ALIASES = set(), {}


def find_routes(keyword):
    hits = []
    pat = re.compile(r'@router\.(get|post|put|patch|delete)\([\'"]([^\'"]+)[\'"]')
    if not ROUTERS.exists():
        return hits
    for f in ROUTERS.glob("*.py"):
        for m in pat.finditer(f.read_text(errors="ignore")):
            if keyword.lower() in m.group(2).lower() or keyword.lower() in f.name.lower():
                hits.append(f"{m.group(1).upper():6} {m.group(2)}   [{f.name}]")
    return hits


def grep_fe(keyword):
    hits = []
    if not FRONTEND.exists():
        return hits
    for f in FRONTEND.rglob("*.js"):
        if "/components/ui/" in str(f).replace("\\", "/"):
            continue
        if keyword.lower() in f.name.lower():
            hits.append(f"{f.relative_to(ROOT)}  (nama file cocok)")
            continue
        try:
            if keyword.lower() in f.read_text(errors="ignore").lower():
                hits.append(str(f.relative_to(ROOT)))
        except Exception:
            pass
    return hits


def main():
    if len(sys.argv) < 2:
        print(f"{Y}Usage: python scripts/preflight.py \"<kata-kunci>\"{X}")
        return 0
    kw = sys.argv[1].strip().lower()
    print(f"\n{B}{C}{'='*60}{X}\n{B}  PREFLIGHT '{kw}' (anti-duplikasi){X}\n{B}{C}{'='*60}{X}")

    print(f"\n{B}1) KOLEKSI{X}")
    if kw in DANGEROUS_ALIASES:
        print(f"  {R}[TERLARANG]{X} '{kw}' alias → gunakan kanonik: {B}{DANGEROUS_ALIASES[kw]}{X}")
    matched = [c for c in sorted(CANONICAL_COLLECTIONS) if kw in c or c in kw]
    for c in matched:
        print(f"  {G}[KANONIK ADA]{X} '{c}' → REUSE")
    if not matched and kw not in DANGEROUS_ALIASES:
        print(f"  {Y}[tak ada kanonik cocok]{X} → bila domain baru, daftarkan di verify_contract + 03_DATA_MODEL")

    print(f"\n{B}2) ROUTE BACKEND{X}")
    routes = find_routes(kw)
    if routes:
        for r in routes:
            print(f"  {G}[ADA]{X} {r}")
    else:
        print(f"  {Y}(belum ada) → tambah router baru + include di server.ROUTERS{X}")

    print(f"\n{B}3) FRONTEND{X}")
    fe = grep_fe(kw)
    if fe:
        for h in fe[:15]:
            print(f"  {G}[ADA]{X} {h}")
    else:
        print(f"  {Y}(belum ada) → tambah page/komponen + apiClient call{X}")

    print(f"\n{B}KEPUTUSAN:{X} ADA → REUSE. NEW → daftarkan ke gate terkait (docs/07 §7).\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
