"""routers/payments.py — Bukti bayar sisi PELANGGAN (Epic E6). Router TIPIS, owner-scoped.

POST /api/orders/{code}/payment-proof {amount, ref?, image_url?} -> PaymentProof  (pemilik; 404 non-pemilik)
POST /api/orders/{code}/payment-proof/upload (multipart file)    -> {url}  (E20: upload berkas nyata)
GET  /api/orders/{code}/payment-proofs                          -> [PaymentProof,...] (pemilik atau admin)
Tidak auto-lunas: butuh verifikasi admin. Order terminal/COD → 400. Logika di services/payments.py.
"""
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from db import get_db
from dependencies import get_current_user
from schemas import PaymentProofInput
from services import media as media_svc
from services import payments as svc

router = APIRouter(tags=["payments"])


@router.post("/orders/{code}/payment-proof/upload")
async def upload_proof_image(code: str, file: UploadFile = File(...),
                             user=Depends(get_current_user)):
    """Unggah FOTO bukti transfer (E20). Owner-scoped: hanya pemilik pesanan/admin.

    Berkas disimpan lokal (folder 'Bukti Bayar') dan kembalikan {url} untuk dipakai
    pada POST /orders/{code}/payment-proof. Menggantikan input URL manual yang rapuh.
    """
    db = get_db()
    order = await db.orders.find_one({"code": code}, {"_id": 0, "user_id": 1})
    if not order:
        raise HTTPException(status_code=404, detail="Pesanan tidak ditemukan")
    if user.get("role") != "admin" and order.get("user_id") and order.get("user_id") != user["id"]:
        raise HTTPException(status_code=404, detail="Pesanan tidak ditemukan")
    try:
        folder = await media_svc.ensure_folder_by_name(db, "Bukti Bayar", user["id"])
        data = await file.read()
        asset = await media_svc.save_upload(
            db, data, file.filename or "bukti.jpg", file.content_type or "",
            user["id"], folder_id=folder, alt=f"Bukti bayar {code}",
        )
    except media_svc.MediaError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"url": asset["url"], "thumb_url": asset.get("thumb_url"), "id": asset["id"]}


@router.post("/orders/{code}/payment-proof")
async def submit_proof(code: str, payload: PaymentProofInput, user=Depends(get_current_user)):
    proof, err = await svc.submit_proof(get_db(), user, code, payload.model_dump())
    if err == "notfound":
        raise HTTPException(status_code=404, detail="Pesanan tidak ditemukan")
    if err == "terminal":
        raise HTTPException(status_code=400, detail="Pesanan sudah final — tak bisa unggah bukti")
    if err == "cod":
        raise HTTPException(status_code=400, detail="Pesanan COD tidak memerlukan bukti transfer")
    return proof


@router.get("/orders/{code}/payment-proofs")
async def list_order_proofs(code: str, user=Depends(get_current_user)):
    db = get_db()
    doc = await db.orders.find_one({"code": code})
    if not doc:
        raise HTTPException(status_code=404, detail="Pesanan tidak ditemukan")
    is_admin = user.get("role") == "admin"
    if not is_admin and doc.get("user_id") and doc.get("user_id") != user["id"]:
        raise HTTPException(status_code=404, detail="Pesanan tidak ditemukan")
    return await svc.list_proofs_for_order(db, code)
