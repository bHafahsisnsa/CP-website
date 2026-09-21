"""routers/admin_orders.py — Admin proses pesanan (Epic E5 BR-6). Router TIPIS.

GET /api/admin/orders?status         -> [Order,...] (semua user)
GET /api/admin/orders/{code}          -> Order
PUT /api/admin/orders/{code}/status   -> Order   (HANYA via transition_order; ilegal -> 400)

Admin = pemanggil transition_order (SSOT lifecycle) — BUKAN jalur kedua ubah status (anti RC-E7).
Dijaga require_role('admin').
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from admin_schemas import OrderStatusInput
from core_utils import safe_doc
from db import get_db
from dependencies import get_current_user, require_role
from schemas import ORDER_STATUSES
from services import orders as orders_svc
from services.audit import log_action

router = APIRouter(prefix="/admin", tags=["admin"],
                   dependencies=[Depends(require_role("admin"))])

LIST_MAX = 500


@router.get("/orders")
async def list_orders(status: Optional[str] = Query(default=None)):
    db = get_db()
    filt = {}
    if status in ORDER_STATUSES:
        filt["status"] = status
    docs = await db.orders.find(filt).sort([("created_at", -1)]).to_list(LIST_MAX)
    return [safe_doc(d) for d in docs]


@router.get("/orders/{code}")
async def get_order(code: str):
    db = get_db()
    doc = await db.orders.find_one({"code": code})
    if not doc:
        raise HTTPException(status_code=404, detail="Pesanan tidak ditemukan")
    return safe_doc(doc)


@router.put("/orders/{code}/status")
async def set_status(code: str, payload: OrderStatusInput, admin=Depends(get_current_user)):
    db = get_db()
    doc = await db.orders.find_one({"code": code})
    if not doc:
        raise HTTPException(status_code=404, detail="Pesanan tidak ditemukan")
    try:
        result = await orders_svc.transition_order(db, doc, payload.status)
    except orders_svc.InvalidTransition as e:
        raise HTTPException(status_code=400, detail=str(e))
    await log_action(admin["id"], "status", "orders", code, {"to": payload.status})
    return result
