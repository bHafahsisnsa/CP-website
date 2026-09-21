#!/usr/bin/env python3
"""validate_compliance.py — kepatuhan file/naming/env/prefix (Collector Parfum).

CHECK 1  Batas ukuran file (FE pages/components <=500, hooks <=300, css <=400;
         BE routers <=800, services/util <=300, schemas <=400). data/lib/ui dikecualikan.
CHECK 2  Debug print tertinggal di backend routers/services (`print(`), console.log di FE (WARN).
CHECK 3  Hardcode URL backend / secret di backend routers/services & FE (harus via env).
CHECK 4  Semua router ter-include di server.py (tidak ada router yatim).
CHECK 5  db.py membaca MONGO_URL & DB_NAME dari environment (bukan hardcode).
Exit 1 bila ada pelanggaran KRITIS (bukan WARN).
Usage: cd /app && python scripts/validate_compliance.py
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BACKEND = ROOT / "backend"
FE = ROOT / "frontend" / "src"
G, Y, R, C, B, X = "\033[92m", "\033[93m", "\033[91m", "\033[96m", "\033[1m", "\033[0m"
fails, warns = [], []


def F(msg):
    fails.append(msg)
    print(f"  {R}[FAIL]{X} {msg}")


def W(msg):
    warns.append(msg)
    print(f"  {Y}[WARN]{X} {msg}")


def check_sizes():
    print(f"\n{C}{B}CHECK 1 — ukuran file{X}")
    if FE.exists():
        for f in FE.rglob("*.js"):
            s = str(f).replace("\\", "/")
            if "/components/ui/" in s or "/data/" in s or "/lib/" in s:
                continue
            n = len(f.read_text(errors="ignore").splitlines())
            limit = 300 if "/hooks/" in s else 500
            if n > limit:
                F(f"FE {f.relative_to(ROOT)}: {n} baris > {limit}")
        for f in FE.rglob("*.css"):
            n = len(f.read_text(errors="ignore").splitlines())
            if n > 400:
                F(f"FE {f.relative_to(ROOT)}: {n} baris > 400 (css)")
    if BACKEND.exists():
        for f in (BACKEND / "routers").glob("*.py") if (BACKEND / "routers").exists() else []:
            n = len(f.read_text(errors="ignore").splitlines())
            if n > 800:
                F(f"BE routers/{f.name}: {n} > 800")
        for f in (BACKEND / "services").glob("*.py") if (BACKEND / "services").exists() else []:
            n = len(f.read_text(errors="ignore").splitlines())
            if n > 300:
                F(f"BE services/{f.name}: {n} > 300")
        for f in BACKEND.glob("*.py"):
            n = len(f.read_text(errors="ignore").splitlines())
            limit = 400 if f.name == "schemas.py" else 300
            if n > limit:
                W(f"BE {f.name}: {n} > {limit}")
    if not fails:
        print(f"  {G}[OK]{X} semua file dalam batas")


def check_debug_prints():
    print(f"\n{C}{B}CHECK 2 — debug artefak{X}")
    for sub in ("routers", "services"):
        d = BACKEND / sub
        if not d.exists():
            continue
        for f in d.glob("*.py"):
            for i, ln in enumerate(f.read_text(errors="ignore").splitlines(), 1):
                if re.match(r"\s*print\(", ln):
                    F(f"BE {sub}/{f.name}:{i} `print(` tertinggal (pakai logger)")
    if FE.exists():
        for f in FE.rglob("*.js"):
            if "/components/ui/" in str(f).replace("\\", "/"):
                continue
            for i, ln in enumerate(f.read_text(errors="ignore").splitlines(), 1):
                if re.search(r"console\.log\(", ln):
                    W(f"FE {f.name}:{i} console.log tertinggal")
    if not any("print(" in x for x in fails):
        print(f"  {G}[OK]{X} tidak ada print debug di backend routers/services")


def check_hardcode():
    print(f"\n{C}{B}CHECK 3 — hardcode URL/secret{X}")
    for sub in ("routers", "services"):
        d = BACKEND / sub
        if not d.exists():
            continue
        for f in d.glob("*.py"):
            for i, ln in enumerate(f.read_text(errors="ignore").splitlines(), 1):
                if ln.strip().startswith("#"):
                    continue
                if re.search(r"[\'\"]https?://", ln):
                    F(f"BE {sub}/{f.name}:{i} URL hardcode — gunakan os.environ")
                if re.search(r"(SECRET|API_KEY|PASSWORD)\s*=\s*[\'\"][^\'\"]{6,}", ln):
                    F(f"BE {sub}/{f.name}:{i} secret hardcode")
    if FE.exists():
        for f in FE.rglob("*.js"):
            s = str(f).replace("\\", "/")
            if "/components/ui/" in s or "/lib/" in s or "/data/" in s:
                continue
            for i, ln in enumerate(f.read_text(errors="ignore").splitlines(), 1):
                if re.search(r"[\'\"]https?://(localhost|127\.0\.0\.1)", ln):
                    F(f"FE {f.name}:{i} localhost hardcode — gunakan REACT_APP_BACKEND_URL")
    if not any("hardcode" in x for x in fails):
        print(f"  {G}[OK]{X} tidak ada URL/secret hardcode")


def check_router_wiring():
    print(f"\n{C}{B}CHECK 4 — router ter-include{X}")
    server = BACKEND / "server.py"
    routers_dir = BACKEND / "routers"
    if not server.exists() or not routers_dir.exists():
        print(f"  {Y}(skip){X}")
        return
    stxt = server.read_text(errors="ignore")
    orphan = []
    for f in routers_dir.glob("*.py"):
        if f.name in ("__init__.py",):
            continue
        mod = f.stem
        if mod not in stxt:
            orphan.append(mod)
    if orphan:
        F(f"router yatim (tak di-include di server.py): {orphan}")
    else:
        print(f"  {G}[OK]{X} semua router ter-include")


def check_env_usage():
    print(f"\n{C}{B}CHECK 5 — env usage{X}")
    dbpy = BACKEND / "db.py"
    if dbpy.exists():
        t = dbpy.read_text(errors="ignore")
        if "MONGO_URL" in t and "DB_NAME" in t and "os.environ" in t:
            print(f"  {G}[OK]{X} db.py membaca MONGO_URL & DB_NAME dari environment")
        else:
            F("db.py tidak membaca MONGO_URL/DB_NAME dari environment")


def main():
    print(f"\n{B}{'='*60}{X}\n  VALIDATE COMPLIANCE\n{B}{'='*60}{X}")
    check_sizes()
    check_debug_prints()
    check_hardcode()
    check_router_wiring()
    check_env_usage()
    print(f"\n{B}{'='*60}{X}\n  {R}FAIL {len(fails)}{X} | {Y}WARN {len(warns)}{X}\n{B}{'='*60}{X}")
    if fails:
        print(f"  {R}{B}COMPLIANCE VIOLATION.{X}\n")
        return 1
    print(f"  {G}{B}COMPLIANCE OK.{X}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
