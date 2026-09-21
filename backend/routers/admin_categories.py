"""routers/admin_categories.py — Admin CRUD kategori (Epic E5 BR-3). Router TIPIS.

GET/POST /api/admin/categories ; PUT/DELETE /api/admin/categories/{cid}.
FK-safe: hapus diblok bila dipakai produk (400). Dijaga require_role('admin').
"""
from fastapi import APIRouter, Depends, HTTPException

from admin_schemas import AdminCategoryInput
from db import get_db
from dependencies import get_current_user, require_role
from services import admin_taxonomy as svc

router = APIRouter(prefix="/admin", tags=["admin"],
                   dependencies=[Depends(require_role("admin"))])


@router.get("/categories")
async def list_categories():
    return await svc.list_categories(get_db())


@router.post("/categories")
async def create_category(payload: AdminCategoryInput, admin=Depends(get_current_user)):
    try:
        return await svc.create_category(get_db(), admin["id"], payload.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/categories/{cid}")
async def update_category(cid: str, payload: AdminCategoryInput, admin=Depends(get_current_user)):
    cat = await svc.update_category(get_db(), admin["id"], cid, payload.model_dump())
    if not cat:
        raise HTTPException(status_code=404, detail="Kategori tidak ditemukan")
    return cat


@router.delete("/categories/{cid}")
async def delete_category(cid: str, admin=Depends(get_current_user)):
    try:
        res = await svc.delete_category(get_db(), admin["id"], cid)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if res is None:
        raise HTTPException(status_code=404, detail="Kategori tidak ditemukan")
    return res
