"""routers/account.py — Akun pelanggan (Epic E4). Router TIPIS, semua owner-scoped.

  PUT    /api/account/profile {name?, phone?}   -> User (tanpa password_hash)
  GET    /api/addresses                          -> [Address]        (milik user)
  POST   /api/addresses {..}                      -> Address
  PUT    /api/addresses/{id} {..}                 -> Address          (404 bila bukan pemilik)
  DELETE /api/addresses/{id}                      -> {ok:true}        (404 bila bukan pemilik)
  POST   /api/addresses/{id}/default              -> [Address]        (set default tunggal)
  GET    /api/wishlist                            -> {product_ids:[...]}
  POST   /api/wishlist/toggle {product_id}        -> {product_ids:[...]}
  POST   /api/wishlist/merge {product_ids:[...]}  -> {product_ids:[...]}

Semua endpoint WAJIB Bearer (get_current_user). user_id diambil dari sesi (anti-IDOR).
"""
from fastapi import APIRouter, Depends, HTTPException

from db import get_db
from dependencies import get_current_user
from schemas import AddressInput, ProfileUpdate, WishlistMerge, WishlistToggle
from services import account as svc
from services.audit import log_action

router = APIRouter(tags=["account"])


@router.put("/account/profile")
async def update_profile(payload: ProfileUpdate, user=Depends(get_current_user)):
    db = get_db()
    result = await svc.update_profile(db, user["id"], name=payload.name, phone=payload.phone)
    await log_action(user["id"], "update", "users", user["id"])
    return result


@router.get("/addresses")
async def list_addresses(user=Depends(get_current_user)):
    return await svc.list_addresses(get_db(), user["id"])


@router.post("/addresses")
async def create_address(payload: AddressInput, user=Depends(get_current_user)):
    db = get_db()
    addr = await svc.create_address(db, user["id"], payload.model_dump())
    await log_action(user["id"], "create", "addresses", addr["id"])
    return addr


@router.put("/addresses/{addr_id}")
async def update_address(addr_id: str, payload: AddressInput, user=Depends(get_current_user)):
    db = get_db()
    addr = await svc.update_address(db, user["id"], addr_id, payload.model_dump())
    if not addr:
        raise HTTPException(status_code=404, detail="Alamat tidak ditemukan")
    await log_action(user["id"], "update", "addresses", addr_id)
    return addr


@router.post("/addresses/{addr_id}/default")
async def set_default_address(addr_id: str, user=Depends(get_current_user)):
    result = await svc.set_default_address(get_db(), user["id"], addr_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Alamat tidak ditemukan")
    return result


@router.delete("/addresses/{addr_id}")
async def delete_address(addr_id: str, user=Depends(get_current_user)):
    db = get_db()
    ok = await svc.delete_address(db, user["id"], addr_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Alamat tidak ditemukan")
    await log_action(user["id"], "delete", "addresses", addr_id)
    return {"ok": True}


@router.get("/wishlist")
async def get_wishlist(user=Depends(get_current_user)):
    ids = await svc.get_wishlist(get_db(), user["id"])
    return {"product_ids": ids}


@router.post("/wishlist/toggle")
async def toggle_wishlist(payload: WishlistToggle, user=Depends(get_current_user)):
    db = get_db()
    try:
        ids = await svc.toggle_wishlist(db, user["id"], payload.product_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"product_ids": ids}


@router.post("/wishlist/merge")
async def merge_wishlist(payload: WishlistMerge, user=Depends(get_current_user)):
    ids = await svc.merge_wishlist(get_db(), user["id"], payload.product_ids)
    return {"product_ids": ids}
