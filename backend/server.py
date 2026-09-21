"""server.py — entrypoint FastAPI Collector Parfum.

Arsitektur: routers (THIN I/O) -> services (logika) -> Motor/MongoDB.
Semua route berada di bawah prefix '/api' (Kubernetes ingress).
JANGAN mengubah MONGO_URL / DB_NAME / CORS_ORIGINS di .env dari sini.
"""
import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import APIRouter, FastAPI
from starlette.middleware.cors import CORSMiddleware

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")

from db import close, get_db  # noqa: E402
from routers import account as account_router  # noqa: E402
from routers import admin as admin_router  # noqa: E402
from routers import admin_categories as admin_categories_router  # noqa: E402
from routers import admin_facets as admin_facets_router  # noqa: E402
from routers import admin_config as admin_config_router  # noqa: E402
from routers import admin_orders as admin_orders_router  # noqa: E402
from routers import admin_products as admin_products_router  # noqa: E402
from routers import admin_product_io as admin_product_io_router  # noqa: E402
from routers import admin_reviews as admin_reviews_router  # noqa: E402
from routers import admin_vouchers as admin_vouchers_router  # noqa: E402
from routers import auth as auth_router  # noqa: E402
from routers import cart as cart_router  # noqa: E402
from routers import catalog as catalog_router  # noqa: E402
from routers import config as config_router  # noqa: E402
from routers import health as health_router  # noqa: E402
from routers import orders as orders_router  # noqa: E402
from routers import payments as payments_router  # noqa: E402
from routers import admin_payments as admin_payments_router  # noqa: E402
from routers import analytics as analytics_router  # noqa: E402
from routers import admin_analytics as admin_analytics_router  # noqa: E402
from routers import content as content_router  # noqa: E402
from routers import admin_content as admin_content_router  # noqa: E402
from routers import admin_media as admin_media_router  # noqa: E402
from routers import media_public as media_public_router  # noqa: E402
from routers import vouchers as vouchers_router  # noqa: E402
from routers import stores as stores_router  # noqa: E402
from routers import admin_stores as admin_stores_router  # noqa: E402
from routers import admin_backup as admin_backup_router  # noqa: E402
from services import media as media_svc  # noqa: E402
from services import product_io_session as import_sessions_svc  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("collector_parfum")

app = FastAPI(title="Collector Parfum API", version="1.0.0")

# Router utama berprefix /api. Router domain di-include ke sini.
api_router = APIRouter(prefix="/api")

# Registry router — fase berikutnya menambah router domain di sini (products, orders, ...).
ROUTERS = [
    health_router.router,
    auth_router.router,
    # Penyaji berkas media lokal (self-healing) — PUBLIK, harus sebelum router lain
    # yang bisa menangkap path /media/*.
    media_public_router.router,
    catalog_router.router,
    vouchers_router.router,
    config_router.router,
    orders_router.router,
    cart_router.router,
    account_router.router,
    payments_router.router,
    # Growth & Analytics (Epic E7) — event first-party (publik) + sitemap.
    analytics_router.router,
    # Storefront CMS (Epic E9) — konten publik.
    content_router.router,
    # Lokasi toko offline + Google Reviews (publik).
    stores_router.router,
    # Admin backoffice (Epic E5) — semua dijaga require_role('admin').
    # Media Manager (E20) didaftarkan LEBIH DULU agar path spesifik
    # /admin/media/folders|assets|upload tidak tertelan route legacy.
    admin_media_router.router,
    admin_media_router.uploads_router,
    admin_router.router,
    admin_products_router.router,
    admin_product_io_router.router,
    admin_categories_router.router,
    admin_facets_router.router,
    admin_vouchers_router.router,
    admin_orders_router.router,
    admin_reviews_router.router,
    admin_config_router.router,
    admin_payments_router.router,
    admin_analytics_router.router,
    admin_content_router.router,
    admin_stores_router.router,
    # Backup & Restore data (admin-only).
    admin_backup_router.router,
]
for r in ROUTERS:
    api_router.include_router(r)

app.include_router(api_router)

# Berkas media dilayani oleh `routers/media_public.py` (GET /api/media/{path}).
# StaticFiles lama DIHAPUS agar bisa self-heal dari mirror MongoDB saat berkas
# hilang dari disk (penyebab broken image setelah rebuild/redeploy).

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get("CORS_ORIGINS", "*").split(","),
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Total-Count"],  # agar FE bisa membaca total untuk paginasi
)


@app.on_event("startup")
async def _startup():
    """Index pada field query panas + unik (performa & integritas)."""
    db = get_db()
    try:
        await db.users.create_index("email", unique=True)
        await db.users.create_index("id", unique=True)
        await db.sessions.create_index("token", unique=True)
        await db.sessions.create_index("user_id")
        await db.products.create_index("slug", unique=True)
        await db.products.create_index("category")
        await db.products.create_index("status")
        await db.categories.create_index("slug", unique=True)
        await db.occasions.create_index("slug", unique=True)
        await db.characters.create_index("slug", unique=True)
        await db.products.create_index("occasions")
        await db.products.create_index("characters")
        await db.vouchers.create_index("code", unique=True)
        await db.voucher_redemptions.create_index("voucher_code")
        await db.voucher_redemptions.create_index([("voucher_code", 1), ("user_id", 1)])
        await db.voucher_user_usage.create_index(
            [("voucher_code", 1), ("user_id", 1)], unique=True
        )
        await db.orders.create_index("code", unique=True)
        await db.orders.create_index("user_id")
        await db.orders.create_index("status")
        await db.addresses.create_index("user_id")
        await db.wishlists.create_index("user_id", unique=True)
        await db.carts.create_index("user_id", unique=True)
        await db.voucher_redemptions.create_index("order_code")
        await db.counters.create_index("name", unique=True)
        await db.media_assets.create_index("id", unique=True)
        # Media Manager (E20): folder bertingkat + indeks aset.
        await media_svc.ensure_indexes(db)
        await db.audit_logs.create_index("created_at")
        await db.audit_logs.create_index("entity")
        await db.payment_proofs.create_index("id", unique=True)
        await db.payment_proofs.create_index("order_code")
        await db.payment_proofs.create_index("status")
        await db.analytics_events.create_index("id", unique=True)
        await db.analytics_events.create_index("type")
        await db.analytics_events.create_index("created_at")
        await db.content.create_index("id", unique=True)
        await db.store_locations.create_index("id", unique=True)
        await db.store_locations.create_index("order")
        await db.store_reviews.create_index("id", unique=True)
        await db.backups.create_index("id", unique=True)
        await db.backups.create_index("created_at")
        # Sesi impor produk (E12): baris file disimpan sekali + kedaluwarsa otomatis.
        await import_sessions_svc.ensure_indexes(db)
        logger.info("Startup indexes ensured.")
    except Exception as e:  # index bentrok pada data lama tidak boleh menggagalkan boot
        logger.warning(f"Index setup warning: {e}")
    # Media Manager (E20): rapikan dokumen media warisan + folder standar (idempotent).
    try:
        res = await media_svc.migrate_legacy(db)
        created = await media_svc.ensure_default_folders(db)
        if res.get("migrated") or created:
            logger.info(f"Media migration: {res} default_folders={created}")
    except Exception as e:
        logger.warning(f"Media migration warning: {e}")


@app.on_event("shutdown")
async def _shutdown():
    close()
