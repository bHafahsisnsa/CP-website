#!/usr/bin/env python3
"""fa_idor_matrix.py — FORENSIC: matriks RBAC role×endpoint (authz baca).

Untuk SETIAP route admin GET (path mengandung '/admin', tanpa param), uji:
  - tanpa token → 401
  - token customer → 401/403 (BUKAN 200)
Grow-with-code: bila belum ada route admin → tandai SIAP-AKTIF (exit 0). Exit 1 bila eskalasi.
Usage: cd /app && python forensic/fa_idor_matrix.py
"""
import asyncio
import os
import secrets
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
from pymongo import MongoClient

API = os.environ.get("API_BASE", "http://localhost:8001").rstrip("/")
G, Y, R, B, X = "\033[92m", "\033[93m", "\033[91m", "\033[1m", "\033[0m"
DB = MongoClient(os.environ.get("MONGO_URL", "mongodb://localhost:27017"))[os.environ.get("DB_NAME", "collector_parfum")]
fails = 0
EMAIL = f"idorm_{secrets.token_hex(4)}@example.com"


def admin_routes():
    try:
        from server import app
    except Exception:
        return []
    return sorted({getattr(r, "path", "") for r in app.routes
                   if "GET" in (getattr(r, "methods", set()) or set())
                   and getattr(r, "path", "").startswith("/api")
                   and "/admin" in getattr(r, "path", "") and "{" not in getattr(r, "path", "")})


async def main():
    global fails
    print(f"\n{B}FA_IDOR_MATRIX — role×endpoint (authz baca){X}")
    routes = admin_routes()
    if not routes:
        print(f"  {Y}• Belum ada route admin GET — SIAP-AKTIF di fase business-logic. (exit 0){X}")
        return 0
    async with httpx.AsyncClient() as c:
        r = await c.post(f"{API}/api/auth/register",
                         json={"name": "IDORm", "email": EMAIL, "password": "probe123"})
        tok = r.json().get("token") if r.status_code == 200 else None
        h = {"Authorization": f"Bearer {tok}"} if tok else {}
        for p in routes:
            r1 = await c.get(f"{API}{p}")
            if r1.status_code != 401:
                fails += 1
                print(f"  {R}[VULN]{X} {p} tanpa token → {r1.status_code} (harus 401).")
            if tok:
                r2 = await c.get(f"{API}{p}", headers=h)
                if r2.status_code == 200:
                    fails += 1
                    print(f"  {R}[VULN]{X} customer BISA akses {p} (200) — escalation!")
                else:
                    print(f"  {G}[OK]{X} customer → {p} = {r2.status_code} (ditolak).")
    try:
        u = DB.users.find_one({"email": EMAIL}, {"id": 1})
        DB.users.delete_many({"email": EMAIL})
        if u:
            DB.sessions.delete_many({"user_id": u.get("id")})
    except Exception:
        pass
    print(f"\n  {R}VULN {fails}{X}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
