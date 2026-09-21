#!/usr/bin/env python3
"""check_nav_map.py — GATE navigasi FE (cegah 'dead menu' & 'cross-page pollution').

Kelas bug dicegah (dari BUG_BACKLOG kn): menu mengarah ke rute yang TIDAK ADA (mati),
dan tautan internal statis yang menggantung. SSOT = route <Route> di App.js.

  N1 (dead link)  : setiap tautan internal STATIS (to="/x"/href="/x"/navigate("/x")) WAJIB
                    cocok dengan sebuah <Route path> (exact atau prefix rute dinamis). Link mati => MERAH.
  N2 (orphan page): rute yang tidak pernah ditautkan dari mana pun => WARN (informasi).

Abaikan: eksternal (http/mailto/tel), anchor '#', query/hash, path template dinamis (mengandung ${}).
Usage: cd /app && python scripts/check_nav_map.py
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FE = ROOT / "frontend" / "src"
APP = FE / "App.js"
G, Y, R, B, X = "\033[92m", "\033[93m", "\033[91m", "\033[1m", "\033[0m"


def routes():
    if not APP.exists():
        return []
    txt = APP.read_text(encoding="utf-8", errors="ignore")
    return re.findall(r'<Route\s+path=["\']([^"\']+)["\']', txt)


def route_matches(target, defined):
    for rt in defined:
        if rt in ("*", "/*"):
            continue
        # rute dinamis: /parfum/:slug -> regex
        rx = "^" + re.sub(r":[^/]+", r"[^/]+", rt) + "$"
        if re.match(rx, target):
            return True
    return False


def collect_links():
    links = []  # (target, file, is_static)
    if not FE.exists():
        return links
    pat = re.compile(r'(?:to|href)=["\'](/[^"\'`]*)["\']|navigate\(\s*["\'](/[^"\'`]*)["\']')
    tmpl = re.compile(r'(?:to|href)=\{`(/[^`]*)`\}|navigate\(\s*`(/[^`]*)`')
    for f in FE.rglob("*.js"):
        s = str(f).replace("\\", "/")
        if "/components/ui/" in s:
            continue
        txt = f.read_text(encoding="utf-8", errors="ignore")
        for m in pat.finditer(txt):
            tgt = m.group(1) or m.group(2)
            links.append((tgt.split("?")[0].split("#")[0], f.name, True))
        for m in tmpl.finditer(txt):
            tgt = m.group(1) or m.group(2)
            links.append((tgt, f.name, False))  # template dinamis
    return links


def main():
    print(f"\n{B}{'='*60}{X}\n  NAV-MAP GATE (dead link / orphan page)\n{B}{'='*60}{X}")
    if not APP.exists():
        print(f"  {Y}App.js tidak ada — SKIP.{X}")
        return 0
    defined = routes()
    if not defined:
        print(f"  {Y}Tidak ada <Route> terdeteksi — SKIP.{X}")
        return 0
    links = collect_links()
    dead = []
    linked = set()
    for tgt, fname, is_static in links:
        if not tgt or tgt == "/" or tgt.startswith(("http", "mailto", "tel", "#")):
            linked.add(tgt)
            continue
        # target template dinamis: cek prefix literal thd rute dinamis
        probe = tgt.split("${")[0].rstrip("/") if "${" in tgt else tgt
        matched = route_matches(tgt if "${" not in tgt else probe + "/x", defined) or \
            any(rt.startswith(probe) for rt in defined if probe)
        if matched:
            linked.add(tgt)
        elif is_static:
            dead.append((tgt, fname))
    dead = sorted(set(dead))
    print(f"\n{B}N1 — dead link (tautan statis tanpa route){X}")
    if dead:
        for tgt, fname in dead:
            print(f"  {R}[DEAD]{X} '{tgt}' di {fname} → tidak ada <Route path> yang cocok.")
    else:
        print(f"  {G}[OK]{X} {len(links)} tautan internal termapping ke route.")

    print(f"\n{B}N2 — orphan page (route tak pernah ditautkan) [info]{X}")
    static_targets = {t for (t, _, st) in links if st}
    tmpl_prefixes = [t.split("${")[0].rstrip("/") for (t, _, st) in links if not st]
    orphans = []
    for rt in defined:
        if rt in ("*", "/*", "/"):
            continue
        base = re.sub(r"/:.*$", "", rt)
        if rt in static_targets or any(base.startswith(p) or p.startswith(base) for p in tmpl_prefixes if p):
            continue
        orphans.append(rt)
    for rt in sorted(set(orphans)):
        print(f"  {Y}[orphan]{X} route '{rt}' tak ditautkan dari nav/komponen (cek IA).")
    if not orphans:
        print(f"  {G}[OK]{X} semua route tertaut.")

    print(f"\n{B}{'='*60}{X}")
    if dead:
        print(f"  {R}{B}NAV DRIFT: {len(dead)} dead link.{X}\n")
        return 1
    print(f"  {G}{B}NAV-MAP OK.{X}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
