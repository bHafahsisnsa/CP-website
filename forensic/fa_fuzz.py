#!/usr/bin/env python3
"""fa_fuzz.py — FORENSIC: payload fuzzing (input adversarial).

Kirim payload RUSAK ke endpoint POST yang ada (auth/register, auth/login).
KONTRAK: server harus menolak dengan 4xx/422 — TIDAK BOLEH 5xx (crash).
Menangkap RC: validasi lemah, unhandled exception, type confusion.
Usage: cd /app && python forensic/fa_fuzz.py   (exit 1 bila ada 5xx)
"""
import asyncio
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
try:
    from dotenv import load_dotenv
    load_dotenv(ROOT / "backend" / ".env")
except Exception:
    pass
try:
    import httpx
except ImportError:
    os.system("pip install httpx -q")
    import httpx

API = os.environ.get("API_BASE", "http://localhost:8001").rstrip("/")
G, Y, R, B, X = "\033[92m", "\033[93m", "\033[91m", "\033[1m", "\033[0m"

BIG = "A" * 20000
FUZZ_BODIES = [
    {}, None, [], "raw-string", 12345,
    {"email": None, "password": None},
    {"email": 123, "password": {"x": 1}},
    {"email": "not-an-email", "password": "x"},
    {"email": "fuzz_probe@example.com", "password": BIG},
    {"name": BIG, "email": "fuzz_probe@example.com", "password": "123456"},
    {"email": "'; DROP TABLE users;--", "password": "x"},
    {"email": "<script>alert(1)</script>@x.co", "password": "x"},
    {"email": "fuzz_probe@example.com", "password": "x", "role": "admin"},  # privilege injection attempt
]
TARGETS = ["/api/auth/register", "/api/auth/login"]


async def main():
    err5xx, checked = [], 0
    async with httpx.AsyncClient() as client:
        for path in TARGETS:
            for body in FUZZ_BODIES:
                checked += 1
                try:
                    r = await client.post(API + path, json=body, timeout=15)
                    if r.status_code >= 500:
                        err5xx.append((path, r.status_code, str(body)[:60], r.text[:100]))
                except Exception as e:
                    err5xx.append((path, "EXC", str(body)[:60], str(e)[:100]))
    print(f"\n{B}FA_FUZZ — {checked} payload rusak dikirim{X}")
    # Probe bebas efek samping: hapus user yang mungkin lolos dibuat oleh payload valid.
    try:
        from motor.motor_asyncio import AsyncIOMotorClient
        c = AsyncIOMotorClient(os.environ.get("MONGO_URL", "mongodb://localhost:27017"))
        db = c[os.environ.get("DB_NAME", "collector_parfum")]
        u = await db.users.find_one({"email": "fuzz_probe@example.com"}, {"id": 1, "_id": 0})
        await db.users.delete_many({"email": "fuzz_probe@example.com"})
        if u:
            await db.sessions.delete_many({"user_id": u.get("id")})
        c.close()
    except Exception:
        pass
    if err5xx:
        print(f"{R}{B}=== 5xx / CRASH (BUG) ==={X}")
        for p, sc, body, msg in err5xx:
            print(f"  {R}[{sc}] {p}  body={body}{X}\n        {msg}")
        return 1
    print(f"  {G}✓ Tidak ada 5xx — validasi menolak input rusak dengan benar.{X}")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
