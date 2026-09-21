"""services/catalog.py — logika read-path katalog (Epic E1).

Prinsip:
- Query TERBATAS (bounded .to_list(limit)) + clamp param → anti unbounded / adversarial 5xx.
- Filter/sort/paginate DILAKUKAN DI SERVER (bukan kirim seluruh katalog ke browser).
- `q` di-escape (re.escape) agar karakter regex aneh tak memicu error.
- rating_avg/rating_count = nilai derivasi tersimpan (di-seed dari reviews) → tanpa N+1.
- safe_doc menutup _id + field sensitif; uang tetap integer rupiah.
"""
import re
from typing import Optional

from core_utils import safe_doc
from services import variants as V

# Batas aman.
LIMIT_DEFAULT = 24
LIMIT_MAX = 100
REVIEWS_MAX = 500
CATEGORIES_MAX = 200

# Peta sort publik -> spesifikasi Mongo (whitelist; nilai tak dikenal -> 'featured').
SORT_SPECS = {
    "featured": [("best_seller", -1), ("is_new", -1), ("created_at", -1)],
    "newest": [("is_new", -1), ("created_at", -1)],
    "best": [("best_seller", -1), ("created_at", -1)],
    "low": [("price", 1), ("created_at", -1)],
    "high": [("price", -1), ("created_at", -1)],
}


def parse_int(value, default=0, lo=None, hi=None):
    """Konversi aman -> int lalu clamp. Nilai sampah -> default (tak pernah error)."""
    try:
        n = int(str(value).strip())
    except (TypeError, ValueError):
        n = default
    if lo is not None and n < lo:
        n = lo
    if hi is not None and n > hi:
        n = hi
    return n


def _multi(value):
    """CSV -> list bersih (dukung filter multi-facet dari storefront)."""
    if not value:
        return []
    return [v.strip() for v in str(value).split(",") if v.strip()]


def _truthy(value):
    """Interpretasi param boolean dari query string (1/true/yes)."""
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def build_product_filter(*, category=None, gender=None, concentration=None,
                         tag=None, occasion=None, character=None, q=None,
                         min_price=None, max_price=None,
                         best_seller=None, is_new=None):
    """Susun filter Mongo untuk /api/products (hanya status=active)."""
    filt = {"status": "active"}
    cats, genders, concs, tags = _multi(category), _multi(gender), _multi(concentration), _multi(tag)
    occs, chars = _multi(occasion), _multi(character)
    if cats:
        filt["category"] = {"$in": cats}
    if genders:
        filt["gender"] = {"$in": genders}
    if concs:
        filt["concentration"] = {"$in": concs}
    if tags:
        filt["tags"] = {"$in": tags}
    if occs:
        filt["occasions"] = {"$in": occs}
    if chars:
        filt["characters"] = {"$in": chars}
    if _truthy(best_seller):
        filt["best_seller"] = True
    if _truthy(is_new):
        filt["is_new"] = True

    price_cond = {}
    if min_price is not None:
        price_cond["$gte"] = parse_int(min_price, 0, lo=0)
    if max_price is not None:
        mx = parse_int(max_price, 0, lo=0)
        if mx > 0:
            price_cond["$lte"] = mx
    if price_cond:
        filt["price"] = price_cond

    if q and str(q).strip():
        safe = re.escape(str(q).strip()[:80])
        rx = {"$regex": safe, "$options": "i"}
        filt["$or"] = [{"name": rx}, {"brand": rx}, {"tags": rx}, {"description": rx}]
    return filt


def resolve_sort(sort):
    return SORT_SPECS.get((sort or "featured").strip().lower(), SORT_SPECS["featured"])


async def list_products(db, *, filt, sort_spec, skip=0, limit=LIMIT_DEFAULT):
    """Kembalikan (items, total). Bounded — aman untuk N+1 & performa."""
    skip = parse_int(skip, 0, lo=0, hi=100000)
    limit = parse_int(limit, LIMIT_DEFAULT, lo=1, hi=LIMIT_MAX)
    total = await db.products.count_documents(filt)
    cursor = db.products.find(filt).sort(sort_spec).skip(skip).limit(limit)
    docs = await cursor.to_list(limit)
    return [V.serialize_product(safe_doc(d)) for d in docs], total


async def get_product_by_slug(db, slug: str):
    if not slug:
        return None
    doc = await db.products.find_one({"slug": slug, "status": "active"})
    return V.serialize_product(safe_doc(doc)) if doc else None


async def list_categories(db):
    docs = await db.categories.find({"active": True}).sort([("name", 1)]).to_list(CATEGORIES_MAX)
    return [safe_doc(d) for d in docs]


async def list_occasions(db):
    docs = await db.occasions.find({"active": True}).sort([("order", 1), ("name", 1)]).to_list(CATEGORIES_MAX)
    return [safe_doc(d) for d in docs]


async def list_characters(db):
    docs = await db.characters.find({"active": True}).sort([("order", 1), ("name", 1)]).to_list(CATEGORIES_MAX)
    return [safe_doc(d) for d in docs]


async def list_reviews(db, product_id: Optional[str] = None):
    filt = {"status": "published"}
    if product_id and str(product_id).strip():
        filt["product_id"] = str(product_id).strip()
    docs = await db.reviews.find(filt).sort([("created_at", -1)]).to_list(REVIEWS_MAX)
    return [safe_doc(d) for d in docs]
