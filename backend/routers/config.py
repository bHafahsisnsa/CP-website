"""routers/config.py — Konfigurasi toko publik (ongkir, pembayaran, settings). Epic E3.

  GET /api/shipping-methods -> [ShippingMethod,...]  (aktif)
  GET /api/payment-methods  -> [PaymentMethod,...]   (aktif; FE mengelompokkan by group)
  GET /api/settings         -> {store_name, currency, cod_fee, ...}  (subset publik)

Data berasal dari koleksi seeded kita sendiri (BUKAN gateway eksternal). Kredensial
integrasi nyata (kurir/pembayaran) — bila kelak ditambah — disimpan di settings admin,
TIDAK di-hardcode. Router TIPIS + bounded.
"""
from fastapi import APIRouter

from core_utils import safe_doc
from db import get_db

router = APIRouter(tags=["config"])

LIST_MAX = 100
_PUBLIC_SETTINGS = ("id", "store_name", "currency", "cod_fee", "free_shipping_threshold",
                    "support_email", "support_phone",
                    # Growth & Analytics (E7) — dipakai FE untuk WA, SEO, sosial, GA4.
                    "whatsapp_number", "site_url", "seo_title", "seo_description", "og_image",
                    "social_instagram", "social_tiktok", "social_facebook", "ga_measurement_id",
                    # Label merek storefront (Inspired by) — dipakai PLP/PDP/QuickView.
                    "inspired_by_enabled", "inspired_by_label", "house_brands")


@router.get("/shipping-methods")
async def shipping_methods():
    db = get_db()
    docs = await db.shipping_methods.find({"active": True}).sort([("price", 1)]).to_list(LIST_MAX)
    return [safe_doc(d) for d in docs]


@router.get("/payment-methods")
async def payment_methods():
    db = get_db()
    docs = await db.payment_methods.find({"active": True}).to_list(LIST_MAX)
    return [safe_doc(d) for d in docs]


@router.get("/settings")
async def settings():
    db = get_db()
    doc = await db.settings.find_one({"id": "store"}) or {}
    clean = safe_doc(doc)
    return {k: clean.get(k) for k in _PUBLIC_SETTINGS if k in clean}
