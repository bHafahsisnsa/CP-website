"""routers/vouchers.py — Voucher publik (Epic E2).

Kontrak (respons = OBJEK/ARRAY telanjang):
  POST /api/vouchers/validate {code, subtotal, shipping?, user_id?, items?}
       -> {valid, code, type, value, discount, label, min_spend, reason?}
       (invalid/kedaluwarsa/over-limit → valid=false + reason; TIDAK PERNAH 5xx)
  GET  /api/vouchers -> [Voucher, ...]   (aktif & belum kedaluwarsa; untuk Voucher Center)

Router TIPIS: I/O + validasi ringan. Logika di services/vouchers.py + services/pricing.py.
Diskon pada respons SAMA dengan yang dihitung checkout (E3) — satu formula (RC-E1/E2).
"""
from fastapi import APIRouter, Depends

from db import get_db
from dependencies import get_optional_user
from schemas import VoucherValidateIn, VoucherValidateOut
from services import vouchers as svc

router = APIRouter(tags=["vouchers"])


@router.post("/vouchers/validate", response_model=VoucherValidateOut)
async def validate_voucher(payload: VoucherValidateIn, user=Depends(get_optional_user)):
    db = get_db()
    user_id = payload.user_id or (user.get("id") if user else None)
    items = [i.model_dump() if hasattr(i, "model_dump") else dict(i) for i in (payload.items or [])]
    result = await svc.evaluate_voucher(
        db,
        code=payload.code,
        subtotal=payload.subtotal,
        shipping=payload.shipping,
        user_id=user_id,
        items=items or None,
    )
    return result


@router.get("/vouchers")
async def list_vouchers():
    db = get_db()
    return await svc.list_active_vouchers(db)
