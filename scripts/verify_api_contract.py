#!/usr/bin/env python3
"""verify_api_contract.py — FE↔BE contract verifier (Collector Parfum).

Mencegah RC-F4 (drift FE↔BE) SEBELUM UI rusak:
  CHECK A — tidak ada route backend duplikat (method+path sama).
  CHECK B — setiap panggilan API di frontend (via services/apiClient / axios `${API}/...`)
            menuju route backend yang ADA. Segmen akhir path harus LITERAL.
  CHECK C — peringatan bila FE memakai path dinamis pada segmen akhir (${action}) yang
            menyulitkan verifikasi kontrak.
Frontend Collector Parfum berstruktur pages/ + components/ + store/ + services/.
Usage: cd /app && python scripts/verify_api_contract.py
Exit 0 = OK. 1 = drift.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BACKEND = ROOT / "backend"
FRONTEND = ROOT / "frontend" / "src"
G, Y, R, C, B, X = "\033[92m", "\033[93m", "\033[91m", "\033[96m", "\033[1m", "\033[0m"

METHOD_RE = re.compile(r'@router\.(get|post|put|patch|delete)\(\s*[\'"]([^\'"]*)[\'"]')
PREFIX_RE = re.compile(r'APIRouter\(\s*prefix\s*=\s*[\'"]([^\'"]+)[\'"]')
# panggilan FE: axios.get(`${API}/products`) atau api.post(`${API}/auth/login`) dst.
FE_CALL_RE = re.compile(r'`\$\{API\}(/[^`]*)`')
FE_CALL_RE2 = re.compile(r'(?:axios|api|apiClient)\.(?:get|post|put|patch|delete)\(\s*[\'"](/api/[^\'"?]+)')


def backend_routes():
    """Kumpulkan {(METHOD, fullpath)} dari router (prefix router + prefix /api global)."""
    routes = []
    dupes = {}
    routers_dir = BACKEND / "routers"
    if not routers_dir.exists():
        return routes, dupes
    for f in sorted(routers_dir.glob("*.py")):
        txt = f.read_text(encoding="utf-8", errors="ignore")
        prefixes = PREFIX_RE.findall(txt)
        local_prefix = prefixes[0] if prefixes else ""
        for method, path in METHOD_RE.findall(txt):
            full = "/api" + local_prefix + path
            full = full.rstrip("/") or "/api"
            key = (method.upper(), full)
            routes.append((key, f.name))
            dupes.setdefault(key, []).append(f.name)
    return routes, dupes


def normalize(path):
    """Ganti segmen dinamis {x} / :x / ${x} menjadi wildcard untuk pencocokan.

    PENTING: pola `${...}` HARUS diganti lebih dulu daripada `{...}`. Bila `{...}`
    dijalankan lebih dulu, bagian dalam `${expr}` ikut terganti dan menyisakan `$`
    (mis. '/api/products/${slug}' -> '/api/products/$*') sehingga gagal cocok dengan
    route backend '/api/products/{slug}' -> '/api/products/*'.
    """
    path = re.sub(r'\$\{[^}]+\}', "*", path)
    path = re.sub(r'\{[^}]+\}', "*", path)
    path = re.sub(r':[A-Za-z_][A-Za-z0-9_]*', "*", path)
    return path.rstrip("/") or "/api"


def fe_calls():
    calls = []
    if not FRONTEND.exists():
        return calls
    for f in FRONTEND.rglob("*.js"):
        if "/components/ui/" in str(f).replace("\\", "/"):
            continue
        txt = f.read_text(encoding="utf-8", errors="ignore")
        for m in FE_CALL_RE.finditer(txt):
            calls.append(("/api" + m.group(1), f.name))
        for m in FE_CALL_RE2.finditer(txt):
            calls.append((m.group(1), f.name))
    return calls


def main():
    print(f"\n{C}{B}{'='*62}{X}\n{B}  VERIFY API CONTRACT (FE↔BE){X}\n{C}{B}{'='*62}{X}")
    routes, dupes = backend_routes()
    fails = 0

    print(f"\n{B}CHECK A — route duplikat{X}")
    dup_found = {k: v for k, v in dupes.items() if len(v) > 1}
    if dup_found:
        fails += 1
        for (method, path), files in dup_found.items():
            print(f"  {R}[DUP]{X} {method} {path}  <- {files}")
    else:
        print(f"  {G}[OK]{X} {len(routes)} route, tanpa duplikat")

    norm_routes = {(m, normalize(p)) for (m, p), _ in routes}
    all_paths = {normalize(p) for (m, p), _ in routes}

    print(f"\n{B}CHECK B — panggilan FE → route backend{X}")
    calls = fe_calls()
    if not calls:
        print(f"  {Y}(frontend belum memanggil API — storefront masih data lokal. Dilewati.){X}")
    else:
        missing = []
        for path, fname in calls:
            npath = normalize(path)
            if npath not in all_paths:
                missing.append((path, fname))
        if missing:
            fails += 1
            for path, fname in missing:
                print(f"  {R}[MISSING]{X} FE '{path}' ({fname}) tak ada route backend cocok")
        else:
            print(f"  {G}[OK]{X} {len(calls)} panggilan FE termapping ke backend")

    print(f"\n{B}CHECK C — path dinamis di segmen akhir (WARN){X}")
    warned = 0
    for path, fname in calls:
        if re.search(r'\$\{[^}]+\}$', path):
            print(f"  {Y}[WARN]{X} {fname}: '{path}' segmen akhir dinamis (sulit diverifikasi)")
            warned += 1
    if not warned:
        print(f"  {G}[OK]{X} tidak ada path dinamis di segmen akhir")

    print(f"\n{C}{B}{'='*62}{X}")
    if fails:
        print(f"  {R}{B}API CONTRACT DRIFT: {fails}{X}\n")
        return 1
    print(f"  {G}{B}API CONTRACT OK.{X}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
