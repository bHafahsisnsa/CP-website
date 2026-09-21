"""routers/admin_config.py — Admin config: kurir, metode bayar, settings (Epic E5 BR-7). Router TIPIS.

GET/POST /api/admin/shipping-methods ; PUT/DELETE /api/admin/shipping-methods/{id}
GET/POST /api/admin/payment-methods  ; PUT/DELETE /api/admin/payment-methods/{id}
GET/PUT  /api/admin/settings
Dijaga require_role('admin') di tingkat router (prefix /admin).
"""
from fastapi import APIRouter, Depends, HTTPException

from admin_schemas import AdminPaymentInput, AdminSettingsInput, AdminShippingInput
from db import get_db
from dependencies import get_current_user, require_role
from services import admin_config as svc

router = APIRouter(prefix="/admin", tags=["admin"],
                   dependencies=[Depends(require_role("admin"))])


@router.get("/shipping-methods")
async def list_shipping():
    return await svc.list_shipping(get_db())


@router.post("/shipping-methods")
async def create_shipping(payload: AdminShippingInput, admin=Depends(get_current_user)):
    return await svc.create_shipping(get_db(), admin["id"], payload.model_dump())


@router.put("/shipping-methods/{sid}")
async def update_shipping(sid: str, payload: AdminShippingInput, admin=Depends(get_current_user)):
    res = await svc.update_shipping(get_db(), admin["id"], sid, payload.model_dump())
    if res is None:
        raise HTTPException(status_code=404, detail="Metode kirim tidak ditemukan")
    return res


@router.delete("/shipping-methods/{sid}")
async def delete_shipping(sid: str, admin=Depends(get_current_user)):
    res = await svc.delete_shipping(get_db(), admin["id"], sid)
    if res is None:
        raise HTTPException(status_code=404, detail="Metode kirim tidak ditemukan")
    return res


@router.get("/payment-methods")
async def list_payments():
    return await svc.list_payments(get_db())


@router.post("/payment-methods")
async def create_payment(payload: AdminPaymentInput, admin=Depends(get_current_user)):
    return await svc.create_payment(get_db(), admin["id"], payload.model_dump())


@router.put("/payment-methods/{pid}")
async def update_payment(pid: str, payload: AdminPaymentInput, admin=Depends(get_current_user)):
    res = await svc.update_payment(get_db(), admin["id"], pid, payload.model_dump())
    if res is None:
        raise HTTPException(status_code=404, detail="Metode bayar tidak ditemukan")
    return res


@router.delete("/payment-methods/{pid}")
async def delete_payment(pid: str, admin=Depends(get_current_user)):
    res = await svc.delete_payment(get_db(), admin["id"], pid)
    if res is None:
        raise HTTPException(status_code=404, detail="Metode bayar tidak ditemukan")
    return res


@router.get("/settings")
async def get_settings():
    return await svc.get_settings(get_db())


@router.put("/settings")
async def update_settings(payload: AdminSettingsInput, admin=Depends(get_current_user)):
    return await svc.update_settings(get_db(), admin["id"], payload.model_dump())
