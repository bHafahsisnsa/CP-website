"""routers/catalog.py — Katalog publik (read-path, Epic E1).

Kontrak (respons = ARRAY/OBJEK telanjang; TANPA envelope):
  GET /api/products?category&gender&concentration&min_price&max_price&q&tag&sort&limit&skip
      -> [Product, ...]   (hanya status=active) + header X-Total-Count
  GET /api/products/{slug} -> Product          (404 bila tak ada / archived)
  GET /api/categories      -> [Category, ...]  (hanya active)
  GET /api/reviews?product_id -> [Review, ...] (hanya published)

Router TIPIS: hanya I/O + validasi ringan; logika query ada di services/catalog.py.
Param numerik diterima sebagai string lalu di-clamp (services.parse_int) → tak pernah 5xx.
"""
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, Response

from db import get_db
from services import catalog as svc

router = APIRouter(tags=["catalog"])


@router.get("/products")
async def get_products(
    response: Response,
    category: Optional[str] = Query(default=None),
    gender: Optional[str] = Query(default=None),
    concentration: Optional[str] = Query(default=None),
    tag: Optional[str] = Query(default=None),
    occasion: Optional[str] = Query(default=None),
    character: Optional[str] = Query(default=None),
    q: Optional[str] = Query(default=None),
    min_price: Optional[str] = Query(default=None),
    max_price: Optional[str] = Query(default=None),
    best_seller: Optional[str] = Query(default=None),
    is_new: Optional[str] = Query(default=None),
    sort: Optional[str] = Query(default="featured"),
    limit: Optional[str] = Query(default=None),
    skip: Optional[str] = Query(default=None),
):
    db = get_db()
    filt = svc.build_product_filter(
        category=category, gender=gender, concentration=concentration,
        tag=tag, occasion=occasion, character=character, q=q,
        min_price=min_price, max_price=max_price,
        best_seller=best_seller, is_new=is_new,
    )
    items, total = await svc.list_products(
        db, filt=filt, sort_spec=svc.resolve_sort(sort),
        skip=skip if skip is not None else 0,
        limit=limit if limit is not None else svc.LIMIT_DEFAULT,
    )
    response.headers["X-Total-Count"] = str(total)
    return items


@router.get("/products/{slug}")
async def get_product(slug: str):
    db = get_db()
    product = await svc.get_product_by_slug(db, slug)
    if not product:
        raise HTTPException(status_code=404, detail="Produk tidak ditemukan")
    return product


@router.get("/categories")
async def get_categories():
    db = get_db()
    return await svc.list_categories(db)


@router.get("/occasions")
async def get_occasions():
    db = get_db()
    return await svc.list_occasions(db)


@router.get("/characters")
async def get_characters():
    db = get_db()
    return await svc.list_characters(db)


@router.get("/reviews")
async def get_reviews(product_id: Optional[str] = Query(default=None)):
    db = get_db()
    return await svc.list_reviews(db, product_id)
