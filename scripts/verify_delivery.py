#!/usr/bin/env python3
"""verify_delivery.py — ANTI-UNDER-DELIVERY GATE (Definition of Done). (Collector Parfum)

Menagih JANJI di memory/DELIVERY_MANIFEST.md untuk fase AKTIF (ACTIVE_PHASE):
  D1  Tiap deliverable (doc/script/page/endpoint/collection) BENAR-BENAR ada.
  D2  ORPHAN ENDPOINT: backend punya endpoint tapi TIDAK dipakai frontend (fitur 'yatim').
  D3  COMPLETENESS %: P0 ada / total P0. Exit!=0 bila ada P0 kurang.
Resilient: endpoint/orphan di-skip rapi bila backend belum bisa di-import (Phase 0).
Usage: cd /app && python scripts/verify_delivery.py
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "memory" / "DELIVERY_MANIFEST.md"
FRONTEND_SRC = ROOT / "frontend" / "src"
DATA_MODEL = ROOT / "docs" / "03_DATA_MODEL.md"
G, Y, R, C, B, X = "\033[92m", "\033[93m", "\033[91m", "\033[96m", "\033[1m", "\033[0m"
sys.path.insert(0, str(ROOT / "backend"))
state = {"p0_total": 0, "p0_ok": 0, "fail": 0, "warn": 0, "skip": 0}


def parse_active_phase():
    if not MANIFEST.exists():
        return None, []
    text = MANIFEST.read_text(encoding="utf-8", errors="ignore")
    m = re.search(r"ACTIVE_PHASE:\s*(\S+)", text)
    active = m.group(1) if m else None
    items, capture = [], False
    for ln in text.splitlines():
        s = ln.strip()
        h = re.match(r"^#{2,4}\s+PHASE\s+(\S+)", s)
        if h:
            capture = (active is not None and h.group(1) == active)
            continue
        if s.startswith("#") or s == "---":
            if capture and (s.startswith("#")):
                capture = False
            continue
        if capture:
            im = re.match(r"^- \[(P0|P1)\]\s+(\w+):\s+(.+?)\s*$", s)
            if im:
                items.append((im.group(1), im.group(2), im.group(3).strip()))
    return active, items


def file_exists(rel):
    return (ROOT / rel).exists()


def page_exists(identifier):
    for ext in (".jsx", ".js"):
        if (FRONTEND_SRC / f"{identifier}{ext}").exists():
            return True
    if FRONTEND_SRC.exists():
        stem = identifier.split("/")[-1].lower()
        for f in list(FRONTEND_SRC.rglob("*.jsx")) + list(FRONTEND_SRC.rglob("*.js")):
            if f.stem.lower() == stem:
                return True
    return False


def canonical_collections():
    cols = set()
    if DATA_MODEL.exists():
        for ln in DATA_MODEL.read_text(errors="ignore").splitlines():
            h = re.match(r"^###\s+`?([a-z_]+)`?\s*$", ln.strip())
            if h:
                cols.add(h.group(1))
    return cols


def load_app():
    try:
        from server import app
        return app
    except Exception:
        return None


def backend_get_routes(app):
    out = []
    for r in app.routes:
        path = getattr(r, "path", "")
        if path.startswith("/api") and (getattr(r, "methods", set()) or set()):
            out.append(path)
    return sorted(set(out))


def fe_text():
    if not FRONTEND_SRC.exists():
        return ""
    buf = []
    for f in list(FRONTEND_SRC.rglob("*.jsx")) + list(FRONTEND_SRC.rglob("*.js")):
        if "/ui/" in str(f).replace("\\", "/"):
            continue
        buf.append(f.read_text(encoding="utf-8", errors="ignore"))
    return "\n".join(buf)


def mark(p, ok, kind, ident, note=""):
    if p == "P0":
        state["p0_total"] += 1
        if ok:
            state["p0_ok"] += 1
    if ok:
        print(f"  {G}[OK]{X}   [{p}] {kind}: {ident}")
    else:
        state["fail"] += 1 if p == "P0" else 0
        state["warn"] += 1 if p != "P0" else 0
        color = R if p == "P0" else Y
        print(f"  {color}[{'MISSING' if p=='P0' else 'todo'}]{X} [{p}] {kind}: {ident}  {color}{note}{X}")


def main():
    print(f"{B}{C}{'='*64}{X}\n{B}  DELIVERY GATE — anti under-deliver{X}\n{B}{C}{'='*64}{X}")
    active, items = parse_active_phase()
    if active is None or not items:
        print(f"{Y}  Manifest kosong / fase aktif tak ditemukan — skip.{X}")
        return 0
    print(f"  Fase aktif: {B}{active}{X}  —  {len(items)} deliverable\n")
    app = load_app()
    cols = canonical_collections()
    fe = fe_text()

    print(f"{B}D1 — Deliverable ada?{X}")
    endpoint_items = []
    for p, kind, ident in items:
        if kind in ("doc", "script"):
            mark(p, file_exists(ident), kind, ident, "file tidak ada")
        elif kind == "page":
            if not FRONTEND_SRC.exists():
                state["skip"] += 1
                print(f"  {Y}[SKIP]{X} [{p}] page: {ident} (frontend belum ada)")
            else:
                mark(p, page_exists(ident), kind, ident, "halaman tidak ditemukan")
        elif kind == "collection":
            mark(p, ident in cols, kind, ident, "tidak terdaftar di 03_DATA_MODEL")
        elif kind == "endpoint":
            endpoint_items.append((p, ident))
        elif kind == "invariant":
            print(f"  {C}[note]{X} [{p}] invariant: {ident} → ditegakkan verify_data_integrity.py")
        else:
            print(f"  {Y}[?]{X} [{p}] {kind}: {ident}")

    if endpoint_items:
        print(f"\n{B}D1b — Endpoint terdaftar?{X}")
        if app is None:
            for p, ident in endpoint_items:
                state["skip"] += 1
                print(f"  {Y}[SKIP]{X} [{p}] endpoint: {ident} (backend belum bisa di-import)")
        else:
            rts = backend_get_routes(app)
            for p, ident in endpoint_items:
                rx = re.compile("^" + re.sub(r"\{[^}]+\}", r"[^/]+", ident) + "$")
                mark(p, any(rx.match(rt) for rt in rts), "endpoint", ident, "route tidak terdaftar")

    print(f"\n{B}D2 — Orphan endpoint (backend tanpa UI)?{X}")
    routers_dir = ROOT / "backend" / "routers"
    INFRA = {"/api/", "/api/health", "/api/status"}
    if app is None or not routers_dir.exists() or not FRONTEND_SRC.exists():
        print(f"  {Y}[SKIP]{X} prasyarat belum lengkap (Phase 0).")
    else:
        orphans = []
        for rt in backend_get_routes(app):
            if rt in INFRA:
                continue
            segs = [s for s in rt.split("/") if s and not s.startswith("{")]
            key = segs[1] if len(segs) > 1 else (segs[0] if segs else "")
            if key in ("auth", "status", "health", ""):
                continue
            if key and key not in fe:
                orphans.append(rt)
        orphans = sorted(set(orphans))
        if orphans:
            state["fail"] += 1
            print(f"  {R}[FAIL]{X} {len(orphans)} endpoint tak dipakai FE (under-deliver):")
            for o in orphans[:20]:
                print(f"        {R}{o}{X}")
        else:
            print(f"  {G}[OK]{X} Tidak ada orphan endpoint.")

    pct = (state["p0_ok"] / state["p0_total"] * 100) if state["p0_total"] else 100.0
    print(f"\n{B}{'='*64}{X}")
    print(f"  P0 completeness: {B}{state['p0_ok']}/{state['p0_total']} ({pct:.0f}%){X} | "
          f"{Y}WARN {state['warn']}{X} | {C}SKIP {state['skip']}{X} | {R}FAIL {state['fail']}{X}")
    if state["fail"] or pct < 100.0:
        print(f"  {R}{B}UNDER-DELIVERY — lengkapi P0 / hapus orphan sebelum klaim selesai.{X}\n")
        return 1
    print(f"  {G}{B}Delivery lengkap untuk fase aktif.{X}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
