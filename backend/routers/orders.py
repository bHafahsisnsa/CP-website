"""routers/orders.py — Checkout & Orders (Epic E3). Router TIPIS.

Kontrak (respons = OBJEK/ARRAY telanjang):
  POST /api/orders {items, address, shipping_id, payment:{group,method_id}, voucher_code?, note?}
       -> Order        (409 stok konflik; 400 input/voucher/transisi)
  GET  /api/orders                 -> [Order,...]  (WAJIB login; milik user saja)
  GET  /api/orders/{code}          -> Order        (pemilik saja; 404 utk non-pemilik → IDOR-safe)
  POST /api/orders/{code}/cancel   -> Order        (pemilik saja; pending/paid/packed → cancelled)

Guest checkout diizinkan (Bearer opsional) — order tanpa user_id. Baca list wajib login.
Logika di services/orders.py (SSOT). Diskon & total selalu dihitung server (RC-E1).
"""
from fastapi import APIRouter, Depends, Header, HTTPException

from db import get_db
from dependencies import get_current_user, get_optional_user
from schemas import CreateOrderRequest
from services import orders as svc
from services.audit import log_action

router = APIRouter(tags=["orders"])


@router.post("/orders")
async def create_order(payload: CreateOrderRequest, user=Depends(get_optional_user)):
    db = get_db()
    items_in = [i.model_dump() for i in payload.items]
    try:
        order = await svc.create_order(
            db,
            user=user,
            items_in=items_in,
            address=payload.address.model_dump(),
            shipping_id=payload.shipping_id,
            payment=payload.payment.model_dump(),
            voucher_code=payload.voucher_code,
            note=payload.note,
        )
    except svc.StockConflict as e:
        raise HTTPException(status_code=409, detail={
            "message": "Stok tidak mencukupi",
            "product_id": e.item.get("product_id"),
            "variant_type": e.item.get("variant_type", ""),
            "volume_ml": e.item.get("volume_ml"),
            "available": e.available,
        })
    except svc.OrderError as e:
        raise HTTPException(status_code=400, detail=str(e))
    await log_action((user or {}).get("id", "guest"), "create", "orders", order.get("code", ""))
    return order


@router.get("/orders")
async def list_orders(user=Depends(get_current_user)):
    db = get_db()
    return await svc.list_orders_for_user(db, user["id"])


@router.get("/orders/{code}")
async def get_order(code: str, user=Depends(get_optional_user)):
    db = get_db()
    order = await svc.get_order_for_user(db, code, user)
    if not order:
        raise HTTPException(status_code=404, detail="Pesanan tidak ditemukan")
    return order


@router.post("/orders/{code}/cancel")
async def cancel_order(code: str, user=Depends(get_current_user)):
    """Pemilik membatalkan pesanannya (pending/paid/packed → cancelled).
    Owner-scoped: order milik user lain → 404 (IDOR-safe)."""
    db = get_db()
    doc = await db.orders.find_one({"code": code})
    if not doc or doc.get("user_id") != user["id"]:
        raise HTTPException(status_code=404, detail="Pesanan tidak ditemukan")
    try:
        result = await svc.transition_order(db, doc, "cancelled")
    except svc.InvalidTransition as e:
        raise HTTPException(status_code=400, detail=str(e))
    await log_action(user["id"], "cancel", "orders", code)
    return result
