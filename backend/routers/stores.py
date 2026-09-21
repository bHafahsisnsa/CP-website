"""routers/stores.py — Lokasi toko + ulasan (publik, read-path).

  GET /api/stores        -> {locations:[...], config:{maps_mode, reviews_source, maps_api_key?, rating, intro}}
  GET /api/store-reviews -> {source, summary:{avg,count}, reviews:[...]}

Router TIPIS. Data dari koleksi kita sendiri; Google Places (opsional) di-fetch server-side.
"""
from fastapi import APIRouter

from db import get_db
from services import stores as svc

router = APIRouter(tags=["stores"])


@router.get("/stores")
async def get_stores():
    db = get_db()
    return {
        "locations": await svc.list_locations_public(db),
        "config": await svc.public_config(db),
    }


@router.get("/store-reviews")
async def get_store_reviews():
    db = get_db()
    return await svc.public_reviews(db)
