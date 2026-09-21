"""routers/admin.py — Admin: dashboard & users (Epic E5). Router TIPIS.

Semua endpoint di bawah /api/admin dan DIJAGA require_role('admin') di tingkat router
(RC-E10). Logika di services/admin_*. Setiap mutasi diaudit oleh service (INV-M1).

CATATAN (E20): endpoint media library DIPINDAHKAN ke `routers/admin_media.py`
(SSOT Media Manager) — termasuk alias legacy GET/POST /api/admin/media dan
DELETE /api/admin/media/{mid}. Jangan mendefinisikannya lagi di sini.
"""
from fastapi import APIRouter, Depends

from db import get_db
from dependencies import require_role
from services import admin_config, admin_stats

router = APIRouter(prefix="/admin", tags=["admin"],
                   dependencies=[Depends(require_role("admin"))])


@router.get("/dashboard")
async def dashboard():
    return await admin_stats.dashboard(get_db())


@router.get("/users")
async def list_users():
    return await admin_config.list_users(get_db())
