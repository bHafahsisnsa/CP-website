"""routers/admin_payments.py — Verifikasi bukti bayar sisi ADMIN (Epic E6). Router TIPIS.

GET /api/admin/payments?status              -> [PaymentProof,...]
PUT /api/admin/payments/{pid}/verify {approve, note?} -> Order  (approve → record_payment via SSOT)
Dijaga require_role('admin'). Verifikasi idempoten; order terminal → 400 (INV-P2).
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from db import get_db
from dependencies import get_current_user, require_role
from schemas import VerifyProofInput
from services import payments as svc

router = APIRouter(prefix="/admin", tags=["admin"],
                   dependencies=[Depends(require_role("admin"))])


@router.get("/payments")
async def list_payments(status: Optional[str] = Query(default=None)):
    return await svc.list_proofs(get_db(), status=status)


@router.put("/payments/{pid}/verify")
async def verify_payment(pid: str, payload: VerifyProofInput, admin=Depends(get_current_user)):
    order, err = await svc.verify_proof(get_db(), admin["id"], pid, payload.approve, payload.note)
    if err == "notfound":
        raise HTTPException(status_code=404, detail="Bukti/pesanan tidak ditemukan")
    if err == "terminal":
        raise HTTPException(status_code=400, detail="Pesanan sudah final — pembayaran ditolak")
    if err == "processed":
        raise HTTPException(status_code=400, detail="Bukti sudah diproses sebelumnya")
    return order
