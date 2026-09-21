"""routers/admin_facets.py — Admin CRUD facet taksonomi: Occasions & Characters.

Mirror pola admin_categories (router TIPIS). FK-safe: hapus diblok bila slug masih
dipakai produk pada array occasions/characters (400). Dijaga require_role('admin').

Koleksi:
  - occasions  -> product_field 'occasions'  (id prefix 'occ')
  - characters -> product_field 'characters' (id prefix 'chr')
"""
from fastapi import APIRouter, Depends, HTTPException

from admin_schemas import AdminFacetInput
from db import get_db
from dependencies import get_current_user, require_role
from services import admin_taxonomy as svc

router = APIRouter(prefix="/admin", tags=["admin"],
                   dependencies=[Depends(require_role("admin"))])


# ---------------- Occasions ----------------
@router.get("/occasions")
async def list_occasions():
    return await svc.list_facets(get_db(), "occasions")


@router.post("/occasions")
async def create_occasion(payload: AdminFacetInput, admin=Depends(get_current_user)):
    return await svc.create_facet(get_db(), "occasions", "occ", admin["id"], payload.model_dump())


@router.put("/occasions/{fid}")
async def update_occasion(fid: str, payload: AdminFacetInput, admin=Depends(get_current_user)):
    res = await svc.update_facet(get_db(), "occasions", "occasions", admin["id"], fid, payload.model_dump())
    if not res:
        raise HTTPException(status_code=404, detail="Occasion tidak ditemukan")
    return res


@router.delete("/occasions/{fid}")
async def delete_occasion(fid: str, admin=Depends(get_current_user)):
    try:
        res = await svc.delete_facet(get_db(), "occasions", "occasions", admin["id"], fid)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if res is None:
        raise HTTPException(status_code=404, detail="Occasion tidak ditemukan")
    return res


# ---------------- Characters ----------------
@router.get("/characters")
async def list_characters():
    return await svc.list_facets(get_db(), "characters")


@router.post("/characters")
async def create_character(payload: AdminFacetInput, admin=Depends(get_current_user)):
    return await svc.create_facet(get_db(), "characters", "chr", admin["id"], payload.model_dump())


@router.put("/characters/{fid}")
async def update_character(fid: str, payload: AdminFacetInput, admin=Depends(get_current_user)):
    res = await svc.update_facet(get_db(), "characters", "characters", admin["id"], fid, payload.model_dump())
    if not res:
        raise HTTPException(status_code=404, detail="Character tidak ditemukan")
    return res


@router.delete("/characters/{fid}")
async def delete_character(fid: str, admin=Depends(get_current_user)):
    try:
        res = await svc.delete_facet(get_db(), "characters", "characters", admin["id"], fid)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if res is None:
        raise HTTPException(status_code=404, detail="Character tidak ditemukan")
    return res
