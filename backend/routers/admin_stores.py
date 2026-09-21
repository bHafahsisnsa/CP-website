"""routers/admin_stores.py — Admin: lokasi toko, ulasan kurasi, config maps/reviews.

GET/POST /api/admin/store-locations ; PUT/DELETE /api/admin/store-locations/{id}
GET/POST /api/admin/store-reviews   ; PUT/DELETE /api/admin/store-reviews/{id}
GET/PUT  /api/admin/store-config
Dijaga require_role('admin') di tingkat router (prefix /admin).
"""
from fastapi import APIRouter, Depends, HTTPException

from admin_schemas import AdminStoreConfigInput, AdminStoreLocationInput, AdminStoreReviewInput
from db import get_db
from dependencies import get_current_user, require_role
from services import stores as svc

router = APIRouter(prefix="/admin", tags=["admin"],
                   dependencies=[Depends(require_role("admin"))])


# ---------------- Locations ----------------
@router.get("/store-locations")
async def list_locations():
    return await svc.list_locations_admin(get_db())


@router.post("/store-locations")
async def create_location(payload: AdminStoreLocationInput, admin=Depends(get_current_user)):
    try:
        return await svc.create_location(get_db(), admin["id"], payload.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/store-locations/{lid}")
async def update_location(lid: str, payload: AdminStoreLocationInput, admin=Depends(get_current_user)):
    try:
        res = await svc.update_location(get_db(), admin["id"], lid, payload.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if res is None:
        raise HTTPException(status_code=404, detail="Lokasi tidak ditemukan")
    return res


@router.delete("/store-locations/{lid}")
async def delete_location(lid: str, admin=Depends(get_current_user)):
    res = await svc.delete_location(get_db(), admin["id"], lid)
    if res is None:
        raise HTTPException(status_code=404, detail="Lokasi tidak ditemukan")
    return res


# ---------------- Manual Reviews ----------------
@router.get("/store-reviews")
async def list_reviews():
    return await svc.list_reviews_admin(get_db())


@router.post("/store-reviews")
async def create_review(payload: AdminStoreReviewInput, admin=Depends(get_current_user)):
    try:
        return await svc.create_review(get_db(), admin["id"], payload.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/store-reviews/{rid}")
async def update_review(rid: str, payload: AdminStoreReviewInput, admin=Depends(get_current_user)):
    res = await svc.update_review(get_db(), admin["id"], rid, payload.model_dump())
    if res is None:
        raise HTTPException(status_code=404, detail="Ulasan tidak ditemukan")
    return res


@router.delete("/store-reviews/{rid}")
async def delete_review(rid: str, admin=Depends(get_current_user)):
    res = await svc.delete_review(get_db(), admin["id"], rid)
    if res is None:
        raise HTTPException(status_code=404, detail="Ulasan tidak ditemukan")
    return res


# ---------------- Config ----------------
@router.get("/store-config")
async def get_store_config():
    return await svc.get_config(get_db())


@router.put("/store-config")
async def update_store_config(payload: AdminStoreConfigInput, admin=Depends(get_current_user)):
    return await svc.update_config(get_db(), admin["id"], payload.model_dump())
