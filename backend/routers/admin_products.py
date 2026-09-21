"""routers/admin_products.py — Admin CRUD produk (Epic E5 BR-2). Router TIPIS.

GET  /api/admin/products?status&q     -> [Product,...] (termasuk archived)
GET  /api/admin/products/{pid}         -> Product
POST /api/admin/products               -> Product
PUT  /api/admin/products/{pid}         -> Product
DELETE /api/admin/products/{pid}       -> {archived:true}   (soft-delete, INV-M2)
POST /api/admin/products/{pid}/restore -> {archived:false}
POST /api/admin/products/bulk-status   -> {matched, modified} (aktifkan/arsipkan massal)
Semua dijaga require_role('admin'). Pricing tetap SSOT (services/pricing.py).
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response

from admin_schemas import AdminProductInput, BulkProductStatusInput
from db import get_db
from dependencies import get_current_user, require_role
from services import admin_products as svc

router = APIRouter(prefix="/admin", tags=["admin"],
                   dependencies=[Depends(require_role("admin"))])


@router.get("/products")
async def list_products(response: Response,
                        status: Optional[str] = Query(default=None),
                        q: Optional[str] = Query(default=None),
                        limit: Optional[int] = Query(default=None),
                        skip: Optional[int] = Query(default=None)):
    items, total = await svc.list_products(get_db(), status=status, q=q,
                                           limit=limit or svc.LIST_MAX, skip=skip or 0)
    # Total dikirim via header (kontrak sama dengan GET /api/products publik).
    response.headers["X-Total-Count"] = str(total)
    return items


@router.post("/products/bulk-status")
async def bulk_product_status(payload: BulkProductStatusInput, admin=Depends(get_current_user)):
    """Aktifkan / arsipkan BANYAK produk sekaligus (cakupan: ids ATAU filter daftar admin)."""
    try:
        res = await svc.bulk_set_status(
            get_db(), admin["id"], status=payload.status, ids=payload.ids,
            filter_status=payload.filter_status, q=payload.q,
            confirm_count=payload.confirm_count,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if res.get("conflict"):
        raise HTTPException(
            status_code=409,
            detail=(f"Jumlah produk berubah (kini {res['matched']}, Anda melihat "
                    f"{res['expected']}). Muat ulang daftar lalu ulangi."),
        )
    return res


@router.get("/products/{pid}")
async def get_product(pid: str):
    prod = await svc.get_product(get_db(), pid)
    if not prod:
        raise HTTPException(status_code=404, detail="Produk tidak ditemukan")
    return prod


@router.post("/products")
async def create_product(payload: AdminProductInput, admin=Depends(get_current_user)):
    try:
        return await svc.create_product(get_db(), admin["id"], payload.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/products/{pid}")
async def update_product(pid: str, payload: AdminProductInput, admin=Depends(get_current_user)):
    try:
        prod = await svc.update_product(get_db(), admin["id"], pid, payload.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not prod:
        raise HTTPException(status_code=404, detail="Produk tidak ditemukan")
    return prod


@router.delete("/products/{pid}")
async def archive_product(pid: str, admin=Depends(get_current_user)):
    res = await svc.archive_product(get_db(), admin["id"], pid)
    if res is None:
        raise HTTPException(status_code=404, detail="Produk tidak ditemukan")
    return res


@router.post("/products/{pid}/restore")
async def restore_product(pid: str, admin=Depends(get_current_user)):
    res = await svc.restore_product(get_db(), admin["id"], pid)
    if res is None:
        raise HTTPException(status_code=404, detail="Produk tidak ditemukan")
    return res
