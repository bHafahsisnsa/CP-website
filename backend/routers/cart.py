"""routers/cart.py — Server cart (opsional, untuk user login). Epic E3.

  GET /api/cart          -> Cart (milik user login)
  PUT /api/cart {items, voucher_code?, note?} -> Cart

Guest tidak memakai endpoint ini (FE pakai localStorage). Owner-scoped by session.
"""
from fastapi import APIRouter, Depends

from db import get_db
from dependencies import get_current_user
from schemas import CartPayload
from services import cart as svc

router = APIRouter(tags=["cart"])


@router.get("/cart")
async def get_cart(user=Depends(get_current_user)):
    db = get_db()
    return await svc.get_cart(db, user["id"])


@router.put("/cart")
async def put_cart(payload: CartPayload, user=Depends(get_current_user)):
    db = get_db()
    items = [i.model_dump() for i in payload.items]
    return await svc.save_cart(db, user["id"], items=items,
                               voucher_code=payload.voucher_code, note=payload.note)
