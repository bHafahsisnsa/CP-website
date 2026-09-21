#!/usr/bin/env python3
"""fa_idor.py — FORENSIC: RBAC / IDOR / privilege escalation.

Memastikan:
  1. Endpoint terproteksi menolak TANPA token (401).
  2. Role `customer` TIDAK bisa mengakses route admin (mengandung '/admin') → 401/403, bukan 200.
  3. Token customer menghasilkan role='customer' (bukan admin) — anti privilege injection.
Route admin ditemukan otomatis dari server.app; bila belum ada, ditandai
SEBAGAI SIAP-AKTIF di fase business-logic (tetap exit 0, bukan gagal).
Usage: cd /app && python forensic/fa_idor.py   (exit 1 bila escalation terdeteksi)
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

API = os.environ.get("API_BASE", "http://localhost:8001").rstrip("/")
G, Y, R, B, X = "\033[92m", "\033[93m", "\033[91m", "\033[1m", "\033[0m"
fails = []


def admin_get_routes():
    try:
        from server import app
    except Exception:
        return []
    out = []
    for r in app.routes:
        m = getattr(r, "methods", set()) or set()
        p = getattr(r, "path", "")
        if "GET" in m and p.startswith("/api") and "/admin" in p and "{" not in p:
            out.append(p)
    return sorted(set(out))


async def cleanup():
    """Probe harus bebas efek samping: hapus user & sesi yang dibuat probe."""
    try:
        from motor.motor_asyncio import AsyncIOMotorClient
        c = AsyncIOMotorClient(os.environ.get("MONGO_URL", "mongodb://localhost:27017"))
        db = c[os.environ.get("DB_NAME", "collector_parfum")]
        users = await db.users.find({"email": {"$regex": "^idor_"}}, {"id": 1, "_id": 0}).to_list(500)
        ids = [u["id"] for u in users]
        await db.users.delete_many({"email": {"$regex": "^idor_"}})
        if ids:
            await db.sessions.delete_many({"user_id": {"$in": ids}})
        c.close()
    except Exception:
        pass


async def customer_token(client):
    email = f"idor_{secrets.token_hex(4)}@example.com"
    r = await client.post(API + "/api/auth/register",
                          json={"name": "IDOR Probe", "email": email, "password": "probe123"}, timeout=15)
    if r.status_code == 200:
        return r.json().get("token"), r.json().get("user", {})
    return None, {}


async def main():
    async with httpx.AsyncClient() as client:
        # 1. protected tanpa token
        r = await client.get(API + "/api/auth/me", timeout=15)
        if r.status_code != 401:
            fails.append(f"/api/auth/me tanpa token = HTTP {r.status_code} (harus 401)")
        else:
            print(f"  {G}✓{X} /api/auth/me tanpa token → 401")

        # 2. token customer
        token, user = await customer_token(client)
        if not token:
            print(f"  {Y}! tidak bisa membuat customer probe — skip cek eskalasi{X}")
        else:
            role = user.get("role")
            if role != "customer":
                fails.append(f"register menghasilkan role='{role}' (harus 'customer') — privilege injection!")
            else:
                print(f"  {G}✓{X} register → role='customer' (anti privilege injection)")
            h = {"Authorization": f"Bearer {token}"}
            admin_routes = admin_get_routes()
            if not admin_routes:
                print(f"  {Y}• belum ada route admin GET — cek eskalasi SIAP-AKTIF di fase berikutnya{X}")
            for p in admin_routes:
                rr = await client.get(API + p, headers=h, timeout=15)
                if rr.status_code == 200:
                    fails.append(f"customer BISA akses admin route {p} (HTTP 200) — IDOR/escalation!")
                else:
                    print(f"  {G}✓{X} customer → {p} = HTTP {rr.status_code} (ditolak)")

    print(f"\n{B}FA_IDOR{X}")
    await cleanup()
    if fails:
        print(f"{R}{B}=== PELANGGARAN RBAC/IDOR ==={X}")
        for f in fails:
            print(f"  {R}[VULN] {f}{X}")
        return 1
    print(f"  {G}✓ Tidak ada eskalasi hak akses terdeteksi.{X}")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
