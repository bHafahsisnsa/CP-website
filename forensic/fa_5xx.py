#!/usr/bin/env python3
"""fa_5xx.py — FORENSIC: adversarial GET sweep.

Hit setiap GET /api dengan param sampah (id tak ada, karakter aneh, query junk).
KONTRAK: TIDAK BOLEH 5xx — not-found harus 404, bukan crash.
Usage: cd /app && python forensic/fa_5xx.py   (exit 1 bila ada 5xx)
"""
import asyncio
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
try:
    from dotenv import load_dotenv
    load_dotenv(ROOT / "backend" / ".env")
except Exception:
    pass
sys.path.insert(0, str(ROOT / "backend"))
try:
    import httpx
except ImportError:
    os.system("pip install httpx -q")
    import httpx

API = os.environ.get("API_BASE", "http://localhost:8001").rstrip("/")
ADMIN = {"email": os.environ.get("ADMIN_EMAIL", "admin@collectorparfum.id"),
         "password": os.environ.get("ADMIN_PASS", "Admin#2026")}
G, Y, R, B, X = "\033[92m", "\033[93m", "\033[91m", "\033[1m", "\033[0m"
JUNK = ["__nope__", "../../etc/passwd", "%00", "1 OR 1=1", "💥", "-1", "null"]


def get_routes():
    try:
        from server import app
    except Exception as e:
        print(f"{Y}server.app tak bisa di-import ({e}).{X}")
        return None
    out = []
    for r in app.routes:
        m = getattr(r, "methods", set()) or set()
        p = getattr(r, "path", "")
        if "GET" in m and p.startswith("/api"):
            out.append(p)
    return sorted(set(out))


async def main():
    routes = get_routes()
    if routes is None:
        return 0
    err5xx = []
    async with httpx.AsyncClient() as client:
        token = None
        try:
            r = await client.post(API + "/api/auth/login", json=ADMIN, timeout=15)
            token = r.json().get("token")
        except Exception:
            pass
        h = {"Authorization": f"Bearer {token}"} if token else {}
        tested = 0
        for path in routes:
            params = re.findall(r"\{([^}]+)\}", path)
            variants = []
            if params:
                for junk in JUNK:
                    filled = path
                    for pr in params:
                        filled = filled.replace("{" + pr + "}", junk)
                    variants.append(filled)
            else:
                variants = [path + "?q=" + JUNK[3], path + "?limit=-999&skip=abc"]
            for v in variants:
                tested += 1
                try:
                    resp = await client.get(API + v, headers=h, timeout=20)
                    if resp.status_code >= 500:
                        err5xx.append((v, resp.status_code, resp.text[:100]))
                except Exception as e:
                    err5xx.append((v, "EXC", str(e)[:100]))
    print(f"\n{B}FA_5XX — {tested} request adversarial ke {len(routes)} route{X}")
    if err5xx:
        print(f"{R}{B}=== 5xx (BUG) ==={X}")
        for p, sc, msg in err5xx:
            print(f"  {R}[{sc}] {p}{X}\n        {msg}")
        return 1
    print(f"  {G}✓ Tidak ada 5xx pada input adversarial.{X}")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
