"""routers/admin_vouchers.py — Admin CRUD voucher (Epic E5 BR-4). Router TIPIS.

GET/POST /api/admin/vouchers ; PUT/DELETE /api/admin/vouchers/{vid}.
`used_count` system-owned (read-only). Hapus diblok bila sudah ada redemption (400).
Dijaga require_role('admin').
"""
from fastapi import APIRouter, Depends, HTTPException

from admin_schemas import AdminVoucherInput
from db import get_db
from dependencies import get_current_user, require_role
from services import admin_taxonomy as svc

router = APIRouter(prefix="/admin", tags=["admin"],
                   dependencies=[Depends(require_role("admin"))])


@router.get("/vouchers")
async def list_vouchers():
    return await svc.list_vouchers(get_db())


@router.post("/vouchers")
async def create_voucher(payload: AdminVoucherInput, admin=Depends(get_current_user)):
    try:
        return await svc.create_voucher(get_db(), admin["id"], payload.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/vouchers/{vid}")
async def update_voucher(vid: str, payload: AdminVoucherInput, admin=Depends(get_current_user)):
    try:
        v = await svc.update_voucher(get_db(), admin["id"], vid, payload.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not v:
        raise HTTPException(status_code=404, detail="Voucher tidak ditemukan")
    return v


@router.delete("/vouchers/{vid}")
async def delete_voucher(vid: str, admin=Depends(get_current_user)):
    try:
        res = await svc.delete_voucher(get_db(), admin["id"], vid)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if res is None:
        raise HTTPException(status_code=404, detail="Voucher tidak ditemukan")
    return res
