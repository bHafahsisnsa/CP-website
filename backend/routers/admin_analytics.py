"""routers/admin_analytics.py — Admin Growth: analytics aggregates + CRM segments (Epic E7).

Semua di bawah /api/admin dan DIJAGA require_role('admin') (RC-E10). READ-only
(tak ada mutasi → tak ada audit). Data diturunkan dari events/orders (SSOT).
"""
from fastapi import APIRouter, Depends

from db import get_db
from dependencies import require_role
from services import analytics as analytics_svc
from services import crm as crm_svc

router = APIRouter(prefix="/admin", tags=["admin-growth"],
                   dependencies=[Depends(require_role("admin"))])


@router.get("/analytics")
async def analytics(range: int = 30):
    r = max(1, min(int(range or 30), 365))
    return await analytics_svc.aggregates(get_db(), r)


@router.get("/crm/segments")
async def crm_segments(type: str = ""):
    return await crm_svc.segments(get_db(), str(type or "")[:40])
