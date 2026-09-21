"""routers/admin_reviews.py — Admin moderasi ulasan (Epic E5 BR-5). Router TIPIS.

GET /api/admin/reviews?status&product_id  -> [Review,...]
PUT /api/admin/reviews/{rid}/status        -> Review  (recompute rating produk, INV-C3)
Dijaga require_role('admin').
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from admin_schemas import ReviewStatusInput
from db import get_db
from dependencies import get_current_user, require_role
from services import admin_reviews as svc

router = APIRouter(prefix="/admin", tags=["admin"],
                   dependencies=[Depends(require_role("admin"))])


@router.get("/reviews")
async def list_reviews(status: Optional[str] = Query(default=None),
                       product_id: Optional[str] = Query(default=None)):
    return await svc.list_reviews(get_db(), status=status, product_id=product_id)


@router.put("/reviews/{rid}/status")
async def set_status(rid: str, payload: ReviewStatusInput, admin=Depends(get_current_user)):
    r = await svc.set_status(get_db(), admin["id"], rid, payload.status)
    if not r:
        raise HTTPException(status_code=404, detail="Ulasan tidak ditemukan")
    return r
