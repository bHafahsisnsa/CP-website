"""routers/health.py — health & root.

GET /api/            : root (dipakai gate.sh untuk deteksi backend UP).
GET /api/health      : ringkasan status service + koneksi DB.
"""
from fastapi import APIRouter

from core_utils import now_iso
from db import get_db

router = APIRouter(tags=["health"])


@router.get("/")
async def root():
    return {"service": "collector-parfum", "status": "ok", "message": "Collector Parfum API"}


@router.get("/health")
async def health():
    db = get_db()
    db_ok = True
    try:
        await db.command("ping")
    except Exception:
        db_ok = False
    return {"status": "ok" if db_ok else "degraded", "db": db_ok, "time": now_iso()}
