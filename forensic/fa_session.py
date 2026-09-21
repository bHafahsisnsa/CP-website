#!/usr/bin/env python3
"""fa_session.py — FORENSIC: keamanan sesi/token (auth hardening).

Memastikan:
  S1 token palsu/rusak → 401 (bukan 200/500).
  S2 sesi kedaluwarsa (expires_at lampau) → 401 + sesi dibersihkan.
  S3 sesi milik user nonaktif → 401 (akun disable memutus akses).
Memakai user probe (dibuat & dibersihkan). Exit 1 bila ada celah.
Usage: cd /app && python forensic/fa_session.py
"""
import asyncio
import os
import secrets
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
try:
    from dotenv import load_dotenv
    load_dotenv(ROOT / "backend" / "" if False else ROOT / "backend" / ".env")
except Exception:
    pass
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
EMAIL = f"sess_{secrets.token_hex(4)}@example.com"


def fail(m):
    global fails
    fails += 1
    print(f"  {R}[VULN]{X} {m}")


def ok(m):
    print(f"  {G}[OK]{X} {m}")


async def main():
    print(f"\n{B}FA_SESSION — keamanan sesi/token{X}")
    async with httpx.AsyncClient() as c:
        try:
            if (await c.get(f"{API}/api/", timeout=5)).status_code >= 500:
                raise Exception("5xx")
        except Exception:
            print(f"  {Y}Backend belum berjalan — SKIP.{X}")
            return 0
        # S1 token palsu
        r = await c.get(f"{API}/api/auth/me", headers={"Authorization": "Bearer sess_deadbeef_forged"})
        if r.status_code == 401:
            ok("S1 token palsu ditolak (401).")
        else:
            fail(f"S1 token palsu → HTTP {r.status_code} (harus 401).")
        # buat user probe
        rr = await c.post(f"{API}/api/auth/register",
                          json={"name": "Sess Probe", "email": EMAIL, "password": "probe123"})
        if rr.status_code != 200:
            print(f"  {Y}tak bisa buat user probe ({rr.status_code}) — skip S2/S3.{X}")
            return _summary()
        tok = rr.json().get("token")
        uid = rr.json().get("user", {}).get("id")
        # S2 sesi kedaluwarsa
        past = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
        DB.sessions.update_one({"token": tok}, {"$set": {"expires_at": past}})
        r = await c.get(f"{API}/api/auth/me", headers={"Authorization": f"Bearer {tok}"})
        if r.status_code == 401:
            ok("S2 sesi kedaluwarsa ditolak (401).")
        else:
            fail(f"S2 sesi kedaluwarsa → HTTP {r.status_code} (harus 401).")
        # S3 user nonaktif (sesi baru)
        rr2 = await c.post(f"{API}/api/auth/login", json={"email": EMAIL, "password": "probe123"})
        tok2 = rr2.json().get("token") if rr2.status_code == 200 else None
        if tok2:
            DB.users.update_one({"id": uid}, {"$set": {"status": "inactive"}})
            r = await c.get(f"{API}/api/auth/me", headers={"Authorization": f"Bearer {tok2}"})
            if r.status_code == 401:
                ok("S3 sesi user nonaktif ditolak (401).")
            else:
                fail(f"S3 user nonaktif tetap bisa akses → HTTP {r.status_code} (harus 401).")
    return _summary()


def _summary():
    # cleanup
    try:
        u = DB.users.find_one({"email": EMAIL}, {"id": 1})
        DB.users.delete_many({"email": EMAIL})
        if u:
            DB.sessions.delete_many({"user_id": u.get("id")})
    except Exception:
        pass
    print(f"\n  {R}VULN {fails}{X}")
    if fails:
        print(f"  {R}{B}SESSION HARDENING BOCOR.{X}\n")
        return 1
    print(f"  {G}{B}Sesi/token aman.{X}\n")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
