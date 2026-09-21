#!/usr/bin/env python3
"""seed_data.py — seed DATA REFERENSI/KONFIGURASI Collector Parfum (idempotent).

FASE FONDASI: hanya men-seed data infra & konfigurasi yang menjadi acuan aplikasi:
  users (admin + customer demo), categories, vouchers, shipping_methods,
  payment_methods, settings, counters.
Produk & order SENGAJA belum di-seed (itu ranah fase business-logic).

Idempotent: aman dijalankan berulang (upsert by natural key). Uang = integer rupiah.
Usage: cd /app && python scripts/seed_data.py
"""
import asyncio
import os
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))
try:
    from dotenv import load_dotenv
    load_dotenv(ROOT / "backend" / ".env")
except Exception:
    pass

from motor.motor_asyncio import AsyncIOMotorClient  # noqa: E402
from core_utils import hash_password, new_id, now_iso  # noqa: E402
from services.product_io import clean_variants  # noqa: E402  (SSOT normalisasi varian + auto-SKU)
from services import variants as V  # noqa: E402  (SSOT model N-dimensi options/variants)

G, Y, R, C, B, X = "\033[92m", "\033[93m", "\033[91m", "\033[96m", "\033[1m", "\033[0m"
MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "collector_parfum")

ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "admin@collectorparfum.id")
ADMIN_PASS = os.environ.get("ADMIN_PASS", "Admin#2026")
CUST_EMAIL = os.environ.get("CUST_EMAIL", "customer@collectorparfum.id")
CUST_PASS = os.environ.get("CUST_PASS", "Customer#2026")

CATEGORIES = [
    {"slug": "citrus", "name": "Citrus", "desc": "Segar, ceria, penuh energi pagi."},
    {"slug": "floral", "name": "Floral", "desc": "Anggun, romantis, klasik."},
    {"slug": "woody", "name": "Woody", "desc": "Hangat, tenang, membumi."},
    {"slug": "gourmand", "name": "Gourmand", "desc": "Manis, addictive, cozy."},
    {"slug": "fresh", "name": "Fresh Aquatic", "desc": "Sejuk, bersih, effortless."},
    {"slug": "amber", "name": "Amber & Oud", "desc": "Mewah, sensual, timeless."},
]

# Facet MULTI: Occasion (8) — kunci `icon` = nama ikon lucide-react (dipetakan di FE).
OCCASIONS = [
    {"slug": "office", "name": "Office", "icon": "briefcase", "desc": "Rapi & profesional untuk keseharian kerja.", "order": 1},
    {"slug": "gym", "name": "Gym", "icon": "dumbbell", "desc": "Segar & bertenaga saat aktif bergerak.", "order": 2},
    {"slug": "date-night", "name": "Date Night", "icon": "wine", "desc": "Sensual & memikat untuk momen berdua.", "order": 3},
    {"slug": "daily-wear", "name": "Daily Wear", "icon": "sun", "desc": "Ringan & effortless untuk setiap hari.", "order": 4},
    {"slug": "traveling", "name": "Traveling", "icon": "plane", "desc": "Fleksibel menemani perjalanan.", "order": 5},
    {"slug": "evening", "name": "Evening", "icon": "moon", "desc": "Elegan & dalam untuk malam hari.", "order": 6},
    {"slug": "party", "name": "Party", "icon": "party-popper", "desc": "Berani & menonjol di keramaian.", "order": 7},
    {"slug": "wedding", "name": "Wedding", "icon": "gem", "desc": "Anggun & berkesan untuk hari istimewa.", "order": 8},
]

# Facet MULTI: Character aroma (12) — kunci `icon` = nama ikon lucide-react.
CHARACTERS = [
    {"slug": "fresh", "name": "Fresh", "icon": "leaf", "desc": "Sejuk, bersih, menyegarkan.", "order": 1},
    {"slug": "floral", "name": "Floral", "icon": "flower-2", "desc": "Anggun & romantis penuh bunga.", "order": 2},
    {"slug": "gourmand", "name": "Gourmand", "icon": "ice-cream", "desc": "Manis, hangat, addictive.", "order": 3},
    {"slug": "woody", "name": "Woody", "icon": "tree-pine", "desc": "Hangat, membumi, berkarakter.", "order": 4},
    {"slug": "citrus", "name": "Citrus", "icon": "citrus", "desc": "Ceria & penuh energi jeruk.", "order": 5},
    {"slug": "musky", "name": "Musky", "icon": "feather", "desc": "Lembut, clean, dekat di kulit.", "order": 6},
    {"slug": "aquatic", "name": "Aquatic", "icon": "waves", "desc": "Sejuknya angin laut.", "order": 7},
    {"slug": "spicy", "name": "Spicy", "icon": "flame", "desc": "Hangat berapi dengan rempah.", "order": 8},
    {"slug": "rose", "name": "Rose", "icon": "flower", "desc": "Mawar yang sensual & dewasa.", "order": 9},
    {"slug": "powdery", "name": "Powdery", "icon": "cloud", "desc": "Halus seperti bedak & sutra.", "order": 10},
    {"slug": "green", "name": "Green", "icon": "sprout", "desc": "Segar dedaunan & herbal.", "order": 11},
    {"slug": "amber-oud", "name": "Amber & Oud", "icon": "sparkles", "desc": "Mewah, sensual, timeless.", "order": 12},
]

VOUCHERS = [
    {"code": "WELCOME10", "type": "percent", "value": 10, "label": "Diskon 10% pembeli baru",
     "min_spend": 0, "usage_limit": 0, "per_user_limit": 1,
     "campaign": {"id": "cmp_welcome", "name": "Selamat Datang", "theme": "champagne"}},
    {"code": "ONGKIRGRATIS", "type": "free_shipping", "value": 1, "label": "Gratis Ongkir",
     "min_spend": 150000, "usage_limit": 0, "per_user_limit": 0,
     "campaign": {"id": "cmp_ongkir", "name": "Gratis Ongkir", "theme": "market-blue"}},
    {"code": "COLLECTOR50", "type": "flat", "value": 50000, "label": "Potongan Rp 50.000",
     "min_spend": 300000, "usage_limit": 100, "per_user_limit": 0,
     "campaign": {"id": "cmp_collector", "name": "Collector Deals", "theme": "brass"}},
    {"code": "AMBEROUD15", "type": "percent", "value": 15, "label": "Diskon 15% koleksi Amber & Oud",
     "min_spend": 0, "usage_limit": 0, "per_user_limit": 0, "scope": {"category": "amber"},
     "campaign": {"id": "cmp_amber", "name": "Amber & Oud", "theme": "amber"}},
    {"code": "GRANDLAUNCH", "type": "flat", "value": 75000, "label": "Grand Launch Rp 75.000",
     "min_spend": 500000, "usage_limit": 50, "per_user_limit": 1,
     "starts_at": "__NOW__", "ends_at": "__FUTURE__",
     "campaign": {"id": "cmp_launch", "name": "Grand Launch", "theme": "champagne"}},
    {"code": "EXPIRED2024", "type": "percent", "value": 20, "label": "Promo lampau (kedaluwarsa)",
     "min_spend": 0, "usage_limit": 0, "per_user_limit": 0, "ends_at": "__PAST__"},
]

# Jendela waktu dinamis (di-resolve saat seed).
_NOW_DT = datetime.now(timezone.utc)
_ISO_NOW = _NOW_DT.isoformat()
_ISO_FUTURE = (_NOW_DT + timedelta(days=30)).isoformat()
_ISO_PAST = (_NOW_DT - timedelta(days=5)).isoformat()
_WINDOW = {"__NOW__": _ISO_NOW, "__FUTURE__": _ISO_FUTURE, "__PAST__": _ISO_PAST}

SHIPPING = [
    {"id": "jne-reg", "name": "JNE Reguler", "eta": "2–4 hari", "price": 22000},
    {"id": "jne-yes", "name": "JNE YES", "eta": "1–2 hari", "price": 32000},
    {"id": "jnt-exp", "name": "J&T Express", "eta": "2–3 hari", "price": 21000},
    {"id": "sicepat", "name": "SiCepat REG", "eta": "2–3 hari", "price": 20000},
    {"id": "anteraja", "name": "AnterAja Reguler", "eta": "2–4 hari", "price": 19000},
]

PAYMENTS = [
    {"id": "bca", "group": "transfer", "name": "Transfer BCA", "extra": "Verifikasi manual", "fee": 0},
    {"id": "bni", "group": "transfer", "name": "Transfer BNI", "extra": "Verifikasi manual", "fee": 0},
    {"id": "mandiri", "group": "transfer", "name": "Transfer Mandiri", "extra": "Verifikasi manual", "fee": 0},
    {"id": "shopeepay", "group": "ewallet", "name": "ShopeePay", "extra": "Cashback s.d. 5%", "fee": 0},
    {"id": "ovo", "group": "ewallet", "name": "OVO", "extra": "", "fee": 0},
    {"id": "gopay", "group": "ewallet", "name": "GoPay", "extra": "", "fee": 0},
    {"id": "dana", "group": "ewallet", "name": "DANA", "extra": "", "fee": 0},
    {"id": "cod", "group": "cod", "name": "Bayar di Tempat (COD)", "extra": "Biaya tambahan Rp 4.000", "fee": 4000},
]

SETTINGS = {
    "id": "store",
    "store_name": "Collector Parfum",
    "currency": "IDR",
    "cod_fee": 4000,
    "free_shipping_threshold": 0,
    "low_stock_threshold": 5,
    "support_email": "cs@collectorparfum.com",
    "support_phone": "+62 857-2000-0105",
    # --- Growth & Analytics (Epic E7) ---
    "whatsapp_number": "6285720000105",   # WhatsApp CS utama (wa.me)
    "site_url": "",                        # kosong => sitemap pakai base URL request
    "seo_title": "Collector Parfum — Parfum Refill Bandung Sejak 1970",
    "seo_description": "Distributor parfum refill di Bandung sejak 1970. Biang impor pilihan, variasi aroma luas, ukuran 30–100 ml. Kirim ke seluruh Indonesia, Brunei & Malaysia.",
    "og_image": "",
    "social_instagram": "https://instagram.com/collectorparfum",
    "social_tiktok": "https://tiktok.com/@collectorparfum",
    "social_facebook": "https://facebook.com/collectorparfum",
    "ga_measurement_id": "",               # GA4 (opsional; diisi belakangan oleh admin)
    # --- Label merek storefront ---
    # Katalog memuat produk "inspired by" merek luar. Agar jujur & aman secara legal,
    # merek non-rumah ditampilkan sebagai "Inspired by <merek>".
    "inspired_by_enabled": True,
    "inspired_by_label": "Inspired by",
    "house_brands": ["Collector Parfum", "Collector"],
}

# Pustaka media awal (Epic E5) — referensi URL (V1, tanpa upload nyata).
MEDIA_SEED = [
    {"id": "med_seed_studio_amber", "kind": "image",
     "url": "https://images.unsplash.com/photo-1541643600914-78b084683601?w=1200&q=80",
     "alt": "Botol parfum amber di atas meja studio", "width": 1200, "height": 1500},
    {"id": "med_seed_floral_light", "kind": "image",
     "url": "https://images.unsplash.com/photo-1592945403244-b3fbafd7f539?w=1200&q=80",
     "alt": "Parfum floral dengan pencahayaan lembut", "width": 1200, "height": 1500},
    {"id": "med_seed_woody_dark", "kind": "image",
     "url": "https://images.unsplash.com/photo-1615634260167-c8cdede054de?w=1200&q=80",
     "alt": "Parfum woody bernuansa gelap mewah", "width": 1200, "height": 1500},
    {"id": "med_seed_flatlay", "kind": "image",
     "url": "https://images.unsplash.com/photo-1594035910387-fea47794261f?w=1200&q=80",
     "alt": "Flatlay koleksi parfum", "width": 1200, "height": 1500},
]

# SEO default per kategori (dipakai penuh oleh E7; di E1 hanya disimpan).
CATEGORY_SEO = {
    "citrus": "Parfum citrus segar & ceria untuk energi harian.",
    "floral": "Parfum floral anggun & romantis, klasik sepanjang masa.",
    "woody": "Parfum woody hangat & membumi, elegan berkarakter.",
    "gourmand": "Parfum gourmand manis & cozy yang addictive.",
    "fresh": "Parfum fresh aquatic sejuk & bersih, effortless.",
    "amber": "Parfum amber & oud mewah, sensual, timeless.",
}

# ---------------- Katalog (Epic E1) — 12 produk kanonik ----------------
# Sinkron dengan storefront (frontend/src/data/products.js). Uang = integer rupiah.
# images sengaja KOSONG: storefront menurunkan bottle-art SVG generatif (parity 100%).
PRODUCTS_SEED = [
    {"slug": "noir-oud-intense", "name": "Noir Oud Intense", "category": "amber",
     "concentration": "EDP", "gender": "Unisex", "price": 685000, "compare_at_price": 850000,
     "best_seller": True, "is_new": False, "tags": ["Woody", "Oud", "Musk"],
     "volumes": [
         {"type": "Standard", "ml": 30, "price": 385000, "stock": 12},
         {"type": "Standard", "ml": 50, "price": 685000, "stock": 8, "compare_at_price": 850000},
         {"type": "Standard", "ml": 100, "price": 1150000, "stock": 4},
         {"type": "Premium", "ml": 30, "price": 485000, "stock": 6},
         {"type": "Premium", "ml": 50, "price": 785000, "stock": 5, "compare_at_price": 950000},
         {"type": "Premium", "ml": 100, "price": 1350000, "stock": 3},
     ],
     "notes": {"top": ["Bergamot Italia", "Lada Hitam"], "heart": ["Oud Cambodia", "Rose Turki"], "base": ["Musk Putih", "Amber", "Cendana"]},
     "description": "Aroma malam yang membekas — perpaduan oud dalam dengan sentuhan mawar dan musk yang menenangkan. Cocok untuk momen istimewa.",
     "performance": {"longevity": "Sangat Lama (8–10 jam)", "sillage": "Kuat", "season": "Malam & Musim Dingin"}},
    {"slug": "blanc-neroli-bloom", "name": "Blanc Neroli Bloom", "category": "floral",
     "concentration": "EDP", "gender": "Wanita", "price": 495000, "compare_at_price": None,
     "best_seller": True, "is_new": True, "tags": ["Neroli", "White Floral"],
     "volumes": [{"ml": 30, "price": 295000, "stock": 20}, {"ml": 50, "price": 495000, "stock": 15}, {"ml": 100, "price": 850000, "stock": 9}],
     "notes": {"top": ["Neroli", "Lemon Sisilia"], "heart": ["Melati", "Bunga Jeruk"], "base": ["Musk", "Amber Putih"]},
     "description": "Bouquet putih yang lembut dan bercahaya — segar dari pagi hingga sore, tanpa terasa berlebihan.",
     "performance": {"longevity": "Lama (6–8 jam)", "sillage": "Sedang", "season": "Sepanjang tahun"}},
    {"slug": "citra-bergamot-solar", "name": "Citra Bergamot Solar", "category": "citrus",
     "concentration": "EDT", "gender": "Unisex", "price": 385000, "compare_at_price": 450000,
     "best_seller": False, "is_new": True, "tags": ["Citrus", "Herbal"],
     "volumes": [{"ml": 30, "price": 225000, "stock": 30}, {"ml": 50, "price": 385000, "stock": 22}, {"ml": 100, "price": 665000, "stock": 11}],
     "notes": {"top": ["Bergamot", "Lemon", "Grapefruit"], "heart": ["Basil", "Teh Hijau"], "base": ["Kayu Cedar", "Musk"]},
     "description": "Segar seperti pagi Mediterania — ringan, ceria, dan penuh cahaya matahari.",
     "performance": {"longevity": "Sedang (5–6 jam)", "sillage": "Sedang", "season": "Musim Panas"}},
    {"slug": "velvet-vanilla-noir", "name": "Velvet Vanilla Noir", "category": "gourmand",
     "concentration": "EDP", "gender": "Wanita", "price": 545000, "compare_at_price": None,
     "best_seller": True, "is_new": False, "tags": ["Vanilla", "Sweet", "Cozy"],
     "volumes": [{"ml": 30, "price": 315000, "stock": 14}, {"ml": 50, "price": 545000, "stock": 10}, {"ml": 100, "price": 950000, "stock": 5}],
     "notes": {"top": ["Pir", "Bergamot"], "heart": ["Vanilla Madagascar", "Melati"], "base": ["Praline", "Musk", "Kayu Manis"]},
     "description": "Manis lembut yang addictive — hangat seperti pelukan di malam hari.",
     "performance": {"longevity": "Sangat Lama (8–10 jam)", "sillage": "Kuat", "season": "Musim Dingin"}},
    {"slug": "atlas-cedar-storm", "name": "Atlas Cedar Storm", "category": "woody",
     "concentration": "EDP", "gender": "Pria", "price": 625000, "compare_at_price": 720000,
     "best_seller": False, "is_new": False, "tags": ["Woody", "Spicy"],
     "volumes": [{"ml": 30, "price": 355000, "stock": 18}, {"ml": 50, "price": 625000, "stock": 12}, {"ml": 100, "price": 1085000, "stock": 6}],
     "notes": {"top": ["Kapulaga", "Bergamot"], "heart": ["Cedar Atlas", "Iris"], "base": ["Vetiver", "Amber", "Musk"]},
     "description": "Kayu cedar yang tegas dengan rempah lembut — modern, elegan, dan penuh karakter.",
     "performance": {"longevity": "Lama (7–9 jam)", "sillage": "Kuat", "season": "Musim Semi & Gugur"}},
    {"slug": "marine-driftwood", "name": "Marine Driftwood", "category": "fresh",
     "concentration": "EDT", "gender": "Pria", "price": 425000, "compare_at_price": None,
     "best_seller": False, "is_new": True, "tags": ["Aquatic", "Salty"],
     "volumes": [{"ml": 30, "price": 245000, "stock": 25}, {"ml": 50, "price": 425000, "stock": 16}, {"ml": 100, "price": 745000, "stock": 8}],
     "notes": {"top": ["Aksen Laut", "Mandarin"], "heart": ["Lavender", "Rosemary"], "base": ["Driftwood", "Ambergris"]},
     "description": "Sejuknya angin laut dan kayu apung — bersih, effortless, siap dipakai setiap hari.",
     "performance": {"longevity": "Sedang (5–7 jam)", "sillage": "Sedang", "season": "Musim Panas"}},
    {"slug": "rose-taipa-velvet", "name": "Rose Taipa Velvet", "category": "floral",
     "concentration": "EDP", "gender": "Wanita", "price": 715000, "compare_at_price": 895000,
     "best_seller": True, "is_new": False, "tags": ["Rose", "Musk"],
     "volumes": [{"ml": 30, "price": 415000, "stock": 10}, {"ml": 50, "price": 715000, "stock": 7}, {"ml": 100, "price": 1250000, "stock": 3}],
     "notes": {"top": ["Lychee", "Raspberry"], "heart": ["Rose Turki", "Peony"], "base": ["Patchouli", "Musk Merah"]},
     "description": "Mawar yang sensual dengan sentuhan buah beri — feminine, dewasa, dan penuh percaya diri.",
     "performance": {"longevity": "Lama (7–9 jam)", "sillage": "Kuat", "season": "Malam"}},
    {"slug": "kayu-sandal-rain", "name": "Kayu Sandal Rain", "category": "woody",
     "concentration": "EDP", "gender": "Unisex", "price": 565000, "compare_at_price": None,
     "best_seller": False, "is_new": False, "tags": ["Sandalwood", "Petrichor"],
     "volumes": [{"ml": 30, "price": 325000, "stock": 15}, {"ml": 50, "price": 565000, "stock": 11}, {"ml": 100, "price": 985000, "stock": 5}],
     "notes": {"top": ["Ozonic", "Bambu"], "heart": ["Cendana Mysore", "Teh Putih"], "base": ["Vetiver", "Musk Putih"]},
     "description": "Aroma hujan pertama di atas kayu cendana — meditatif dan nostalgia.",
     "performance": {"longevity": "Lama (6–8 jam)", "sillage": "Sedang", "season": "Sepanjang tahun"}},
    {"slug": "sunset-fig-jakarta", "name": "Sunset Fig Jakarta", "category": "gourmand",
     "concentration": "EDP", "gender": "Unisex", "price": 475000, "compare_at_price": 590000,
     "best_seller": False, "is_new": True, "tags": ["Fig", "Green", "Cozy"],
     "volumes": [{"ml": 30, "price": 275000, "stock": 22}, {"ml": 50, "price": 475000, "stock": 14}, {"ml": 100, "price": 825000, "stock": 7}],
     "notes": {"top": ["Daun Fig", "Bergamot"], "heart": ["Buah Fig", "Kelapa"], "base": ["Kayu Cedar", "Susu Almond"]},
     "description": "Manis buah fig dengan sentuhan hijau — hangat seperti senja di tepi kota.",
     "performance": {"longevity": "Sedang (5–7 jam)", "sillage": "Sedang", "season": "Musim Semi & Gugur"}},
    {"slug": "onyx-tobacco-leather", "name": "Onyx Tobacco Leather", "category": "amber",
     "concentration": "EDP", "gender": "Pria", "price": 745000, "compare_at_price": 895000,
     "best_seller": True, "is_new": False, "tags": ["Tobacco", "Leather", "Amber"],
     "volumes": [{"ml": 30, "price": 425000, "stock": 9}, {"ml": 50, "price": 745000, "stock": 6}, {"ml": 100, "price": 1295000, "stock": 3}],
     "notes": {"top": ["Rum", "Bergamot"], "heart": ["Daun Tembakau", "Kulit"], "base": ["Vanilla", "Amber", "Benzoin"]},
     "description": "Tembakau, kulit, dan rum — aroma penuh percaya diri untuk malam yang panjang.",
     "performance": {"longevity": "Sangat Lama (9–12 jam)", "sillage": "Sangat Kuat", "season": "Musim Dingin & Malam"}},
    {"slug": "iris-powder-silk", "name": "Iris Powder Silk", "category": "floral",
     "concentration": "EDP", "gender": "Wanita", "price": 585000, "compare_at_price": None,
     "best_seller": False, "is_new": False, "tags": ["Iris", "Powdery"],
     "volumes": [{"ml": 30, "price": 335000, "stock": 13}, {"ml": 50, "price": 585000, "stock": 9}, {"ml": 100, "price": 1020000, "stock": 4}],
     "notes": {"top": ["Aldehid", "Mandarin"], "heart": ["Iris Butter", "Violet"], "base": ["Musk Putih", "Kayu Cashmere"]},
     "description": "Iris seperti kain sutra — lembut, dingin, dan penuh anggun.",
     "performance": {"longevity": "Lama (6–8 jam)", "sillage": "Sedang", "season": "Sepanjang tahun"}},
    {"slug": "green-basil-lime", "name": "Green Basil Lime", "category": "citrus",
     "concentration": "EDT", "gender": "Unisex", "price": 355000, "compare_at_price": None,
     "best_seller": False, "is_new": True, "tags": ["Citrus", "Green"],
     "volumes": [{"ml": 30, "price": 205000, "stock": 28}, {"ml": 50, "price": 355000, "stock": 18}, {"ml": 100, "price": 620000, "stock": 9}],
     "notes": {"top": ["Jeruk Nipis", "Mint"], "heart": ["Basil", "Daun Verbena"], "base": ["Cedar", "Musk Bersih"]},
     "description": "Sesegar salad herbal di siang hari — ceria, ringan, dan effortless.",
     "performance": {"longevity": "Sedang (4–6 jam)", "sillage": "Sedang", "season": "Musim Panas"}},
]

# Assignment facet MULTI per produk (occasions + characters) — sumber tunggal
# agar mudah diedit. Slug harus ada di OCCASIONS / CHARACTERS di atas.
PRODUCT_FACETS = {
    "noir-oud-intense":    {"occasions": ["evening", "date-night", "party", "wedding"], "characters": ["amber-oud", "woody", "musky"]},
    "blanc-neroli-bloom":  {"occasions": ["office", "daily-wear", "date-night"],        "characters": ["floral", "fresh", "citrus"]},
    "citra-bergamot-solar":{"occasions": ["daily-wear", "gym", "office", "traveling"],  "characters": ["citrus", "fresh", "green"]},
    "velvet-vanilla-noir": {"occasions": ["date-night", "evening", "party"],            "characters": ["gourmand", "musky", "powdery"]},
    "atlas-cedar-storm":   {"occasions": ["office", "evening", "daily-wear"],           "characters": ["woody", "spicy", "green"]},
    "marine-driftwood":    {"occasions": ["gym", "daily-wear", "traveling"],            "characters": ["aquatic", "fresh", "woody"]},
    "rose-taipa-velvet":   {"occasions": ["date-night", "evening", "wedding", "party"], "characters": ["rose", "floral", "musky"]},
    "kayu-sandal-rain":    {"occasions": ["daily-wear", "office", "evening"],           "characters": ["woody", "green", "musky"]},
    "sunset-fig-jakarta":  {"occasions": ["daily-wear", "traveling", "evening"],        "characters": ["gourmand", "green", "woody"]},
    "onyx-tobacco-leather":{"occasions": ["evening", "party", "date-night", "wedding"], "characters": ["amber-oud", "spicy", "woody"]},
    "iris-powder-silk":    {"occasions": ["office", "wedding", "daily-wear", "evening"],"characters": ["powdery", "floral", "musky"]},
    "green-basil-lime":    {"occasions": ["gym", "daily-wear", "traveling", "office"],  "characters": ["citrus", "green", "fresh"]},
}

# Ulasan produk (published) — sumber tunggal untuk rating_avg/rating_count (INV-C3).
PRODUCT_REVIEWS = [
    ("noir-oud-intense", "Alika P.", "Jakarta", 5, "Oud-nya dalam tapi tetap elegan. Tahan seharian, cocok untuk acara malam."),
    ("noir-oud-intense", "Fajar A.", "Medan", 5, "Signature banget. Banyak yang nanya pakai parfum apa."),
    ("noir-oud-intense", "Dita M.", "Denpasar", 4, "Kuat di awal lalu settle jadi hangat. Suka!"),
    ("blanc-neroli-bloom", "Renata S.", "Bandung", 5, "Neroli-nya bersih dan bercahaya. Fresh tanpa bikin pusing."),
    ("blanc-neroli-bloom", "Kirana W.", "Yogyakarta", 5, "Pas untuk harian ke kantor, wangi bunga putihnya lembut."),
    ("velvet-vanilla-noir", "Bagas R.", "Surabaya", 5, "Vanilla praline-nya cozy banget, addictive untuk musim hujan."),
    ("velvet-vanilla-noir", "Dita M.", "Denpasar", 4, "Manis tapi tidak berlebihan, sillage-nya oke."),
    ("rose-taipa-velvet", "Kirana W.", "Yogyakarta", 5, "Mawar yang dewasa dan sensual. Kesan pertama sampai afternote balance."),
    ("rose-taipa-velvet", "Alika P.", "Jakarta", 4, "Feminine dan elegan, botolnya cantik."),
    ("atlas-cedar-storm", "Fajar A.", "Medan", 4, "Cocok dipakai kerja, elegan dan tidak overpowering."),
    ("onyx-tobacco-leather", "Bagas R.", "Surabaya", 5, "Tembakau-kulitnya maskulin dan berkelas untuk malam."),
    ("citra-bergamot-solar", "Renata S.", "Bandung", 4, "Segar seperti pagi Mediterania, ringan dan ceria."),
]

# Testimoni umum (tanpa product_id) untuk section Home.
GENERAL_TESTIMONIALS = [
    ("Alika P.", "Jakarta", 5, "Notes-nya sesuai deskripsi, tahan lama, dan botolnya cantik. Belanja di Collector Parfum udah kaya buka boutique."),
    ("Renata S.", "Bandung", 5, "Website-nya smooth banget, foto-fotonya editorial, dan checkoutnya cepat mirip di marketplace. Recommended."),
    ("Bagas R.", "Surabaya", 5, "Sampel dan kemasan rapi, aroma masih fresh saat sampai. Blanc Neroli Bloom jadi signature aku sekarang."),
    ("Dita M.", "Denpasar", 5, "Suka banget notes pyramid-nya jelas dan pengiriman on time. Bakal repeat order untuk hadiah teman."),
    ("Fajar A.", "Medan", 4, "Atlas Cedar Storm cocok dipakai kerja, elegan dan gak overpowering. Layanan CS-nya juga ramah."),
    ("Kirana W.", "Yogyakarta", 5, "Aroma Rose Taipa Velvet bikin banyak yang nanya. Kesan pertama sampai afternote-nya balance banget."),
]


STORE_LOCATIONS = [
    {"id": "loc_pasirkaliki", "name": "Collector Parfum — Pasir Kaliki",
     "address": "Jl. Pasir Kaliki No.148, Pasir Kaliki, Kec. Cicendo, Kota Bandung, Jawa Barat 40173",
     "phone": "+62 857-2000-0105", "whatsapp": "6285720000105",
     "hours": "Senin–Jumat 09.00–17.00 · Sabtu 09.00–14.00 WIB",
     "maps_query": "Collector Parfum, Jl. Pasir Kaliki No.148, Cicendo, Bandung",
     "map_url": "https://share.google/eiAbKJfPFlUCiZ9qc",
     "embed_url": "", "place_id": "", "lat": None, "lng": None, "order": 1, "active": True},
    {"id": "loc_gatotsubroto", "name": "Collector Parfum — Gatot Subroto",
     "address": "Jl. Gatot Subroto No.271, Cibangkong, Kec. Batununggal, Kota Bandung, Jawa Barat 40273",
     "phone": "+62 857-2000-0105", "whatsapp": "6285720000105",
     "hours": "Setiap hari 09.00 – 20.00",
     "maps_query": "Collector Parfum, Jl. Gatot Subroto No.271, Batununggal, Bandung",
     "map_url": "https://share.google/BPI8OKWxrVIjBXjRs",
     "embed_url": "", "place_id": "", "lat": None, "lng": None, "order": 2, "active": True},
    {"id": "loc_paledang", "name": "Collector Parfum — Paledang",
     "address": "Jl. Paledang No. 58, Kota Bandung, Jawa Barat",
     "phone": "+62 857-2000-0105", "whatsapp": "6285720000105",
     "hours": "Senin–Jumat 09.00–17.00 · Sabtu 09.00–14.00 WIB",
     "maps_query": "Collector Parfum, Jl. Paledang No. 58, Bandung",
     "map_url": "https://share.google/a0oqEbj5JelrQPQUZ",
     "embed_url": "", "place_id": "", "lat": None, "lng": None, "order": 3, "active": True},
]

STORE_REVIEWS = [
    ("Rizky Ananda", 5, "Toko parfum paling lengkap di Bandung! Pelayanan ramah, bisa tester dulu sebelum beli. Recommended banget.", "Bandung", "2 minggu lalu"),
    ("Putri Maharani", 5, "Datang ke cabang Pasir Kaliki, koleksinya banyak dan original semua. Stafnya bantuin cari aroma yang cocok.", "Pasir Kaliki", "1 bulan lalu"),
    ("Dimas Prasetyo", 4, "Harga bersaing, banyak pilihan inspired maupun original. Parkir agak susah kalau ramai, tapi worth it.", "Gatot Subroto", "3 minggu lalu"),
    ("Sarah Wijaya", 5, "Suka banget belanja di sini, tempatnya nyaman dan wangi. Kasih rekomendasi sesuai budget. Pasti balik lagi.", "Paledang", "1 minggu lalu"),
    ("Andi Kurniawan", 5, "Pelayanan cepat, produk sesuai deskripsi. Beli untuk hadiah dan si penerima suka banget aromanya.", "Bandung", "2 bulan lalu"),
    ("Nadia Safira", 4, "Banyak varian dan tester tersedia. Tempatnya bersih. Kadang antre pas weekend karena rame pembeli.", "Bandung", "1 bulan lalu"),
]

STORE_CONFIG = {
    "maps_mode": "embed",
    "reviews_source": "manual",
    "google_maps_api_key": "",
    "google_places_api_key": "",
    "google_place_id": "",
    "store_rating_avg": 4.5,
    "store_rating_count": 3751,
    "stores_intro": "Kunjungi butik Collector Parfum di Bandung. Cium langsung aromanya, konsultasi dengan tim kami, dan temukan parfum yang paling membekas untuk Anda.",
}


def _pid(slug):
    """Deterministik id produk berprefiks 'prd_' (idempotent lintas seed)."""
    return "prd_" + re.sub(r"[^a-z0-9]", "", slug.lower())[:20]


async def upsert(coll, key, docs, label):
    n = 0
    for d in docs:
        d.setdefault("created_at", now_iso())
        await coll.update_one({key: d[key]}, {"$set": d}, upsert=True)
        n += 1
    print(f"  {G}✓{X} {label}: {n}")


async def seed_vouchers(db):
    """Seed voucher E2 (idempotent by code). `id`/`used_count` di-set hanya saat insert
    (via $setOnInsert) agar akumulasi pemakaian tidak ter-reset saat re-seed."""
    n = 0
    for v in VOUCHERS:
        code = v["code"]
        doc = {
            "code": code,
            "type": v["type"],
            "value": int(v["value"]),
            "label": v.get("label", ""),
            "min_spend": int(v.get("min_spend", 0)),
            "usage_limit": int(v.get("usage_limit", 0)),
            "per_user_limit": int(v.get("per_user_limit", 0)),
            "scope": v.get("scope") or {},
            "starts_at": _WINDOW.get(v.get("starts_at"), v.get("starts_at")),
            "ends_at": _WINDOW.get(v.get("ends_at"), v.get("ends_at")),
            "campaign": v.get("campaign"),
            "active": v.get("active", True),
        }
        await db.vouchers.update_one(
            {"code": code},
            {"$set": doc, "$setOnInsert": {"id": new_id("vcr"), "used_count": 0, "created_at": now_iso()}},
            upsert=True,
        )
        n += 1
    print(f"  {G}\u2713{X} vouchers: {n} (E2: window/scope/per-user/campaign)")


async def seed_user(db, email, password, name, role):
    existing = await db.users.find_one({"email": email})
    doc = {
        "name": name, "email": email, "role": role, "status": "active",
        "password_hash": hash_password(password), "phone": None,
    }
    if existing:
        # jangan ganti id; hanya pastikan role/status/hash konsisten dgn demo.
        await db.users.update_one({"email": email}, {"$set": doc})
        uid = existing["id"]
    else:
        doc["id"] = new_id("usr")
        doc["created_at"] = now_iso()
        await db.users.insert_one(doc)
        uid = doc["id"]
    print(f"  {G}✓{X} user {role}: {email}")
    return uid


async def seed_reviews(db):
    """Seed testimoni umum + ulasan produk (published). Idempotent by deterministic id.
    Kembalikan map product_id -> (rating_avg 1-desimal, rating_count) untuk INV-C3."""
    # Testimoni umum (product_id = None)
    gen_docs = []
    for idx, (name, city, rating, quote) in enumerate(GENERAL_TESTIMONIALS, 1):
        gen_docs.append({
            "id": f"rev_t{idx:03d}", "product_id": None, "user_id": None,
            "name": name, "city": city, "rating": int(rating), "quote": quote,
            "status": "published",
        })
    # Ulasan produk
    prod_docs = []
    agg = {}
    for idx, (slug, name, city, rating, quote) in enumerate(PRODUCT_REVIEWS, 1):
        pid = _pid(slug)
        prod_docs.append({
            "id": f"rev_p{idx:03d}", "product_id": pid, "user_id": None,
            "name": name, "city": city, "rating": int(rating), "quote": quote,
            "status": "published",
        })
        agg.setdefault(pid, []).append(int(rating))

    for d in gen_docs + prod_docs:
        d.setdefault("created_at", now_iso())
        await db.reviews.update_one({"id": d["id"]}, {"$set": d}, upsert=True)
    print(f"  {G}✓{X} reviews: {len(gen_docs)} testimoni + {len(prod_docs)} ulasan produk")

    ratings = {}
    for pid, arr in agg.items():
        ratings[pid] = (round(sum(arr) / len(arr), 1), len(arr))
    return ratings


async def seed_products(db, ratings):
    """Seed 12 produk kanonik (idempotent by slug; id prd_ deterministik).
    rating_avg/rating_count diturunkan dari reviews (INV-C3)."""
    n = 0
    for p in PRODUCTS_SEED:
        slug = p["slug"]
        pid = _pid(slug)
        avg, cnt = ratings.get(pid, (0.0, 0))
        seo = {
            "title": f"{p['name']} — Parfum {p['concentration']} | Collector Parfum",
            "description": p["description"][:155],
            "keywords": list(dict.fromkeys(p.get("tags", []) + [p["category"], "parfum", "collector parfum"])),
            "og_image": None,
        }
        vols = clean_variants([dict(v) for v in p["volumes"]], product_name=p["name"])
        # Migrasi ke model N-dimensi: Konsentrasi + Tipe(bila ada) + Ukuran (SSOT variants).
        options, variants = V.derive_from_volumes(
            {"volumes": vols, "concentration": p["concentration"], "name": p["name"]})
        vols_derived = V.derive_volumes(options, variants)
        rng = V.price_range(variants)
        disp_price = rng["price_min"]  # "mulai dari" (varian termurah)
        # Harga coret display: override eksplisit seed bila > harga termurah, else turunan.
        prod_cap = rng["compare_at_price"]
        if p.get("compare_at_price") and int(p["compare_at_price"]) > disp_price:
            prod_cap = int(p["compare_at_price"])
        facets = PRODUCT_FACETS.get(slug, {})
        doc = {
            "id": pid, "slug": slug, "name": p["name"], "brand": "Collector",
            "category": p["category"], "concentration": p["concentration"], "gender": p["gender"],
            "price": disp_price,
            "price_min": rng["price_min"], "price_max": rng["price_max"],
            "compare_at_price": prod_cap,
            "compare_at_min": rng["compare_at_min"], "compare_at_max": rng["compare_at_max"],
            "best_seller": bool(p["best_seller"]), "is_new": bool(p["is_new"]),
            "tags": p.get("tags", []),
            "occasions": facets.get("occasions", []),
            "characters": facets.get("characters", []),
            "volumes": vols_derived,
            "options": options,
            "variants": variants,
            "notes": p["notes"], "description": p["description"],
            "ingredients": "Alcohol Denat., Parfum (Fragrance), Aqua, dan bahan aromatik pilihan sesuai piramida aroma.",
            "performance": p["performance"],
            "images": [], "video_url": None, "seo": seo,
            "rating_avg": float(avg), "rating_count": int(cnt),
            "status": "active",
        }
        await db.products.update_one(
            {"slug": slug},
            {"$set": doc, "$setOnInsert": {"created_at": now_iso()}},
            upsert=True,
        )
        n += 1
    print(f"  {G}✓{X} products: {n}")


async def main():
    print(f"\n{C}{B}{'='*60}{X}\n  SEED — Collector Parfum (data referensi/konfigurasi)\n  DB: {DB_NAME}\n{C}{B}{'='*60}{X}")
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]

    # counters (number-series) — pastikan ada, jangan reset bila sudah jalan.
    await db.counters.update_one({"name": "orders"}, {"$setOnInsert": {"name": "orders", "seq": 0}}, upsert=True)
    print(f"  {G}✓{X} counters: orders")

    await seed_user(db, ADMIN_EMAIL, ADMIN_PASS, "Admin Collector", "admin")
    await seed_user(db, CUST_EMAIL, CUST_PASS, "Kolektor Demo", "customer")

    # categories (dengan SEO default)
    cats = []
    for c in CATEGORIES:
        seo = {"title": f"{c['name']} — Koleksi Parfum | Collector Parfum",
               "description": CATEGORY_SEO.get(c["slug"], c.get("desc", "")),
               "keywords": [c["slug"], "parfum", c["name"].lower()], "og_image": None}
        cats.append({"id": new_id("cat"), "active": True, "seo": seo, **c})
    await upsert(db.categories, "slug", cats, "categories")

    # facets multi: occasions & characters (idempotent by slug; id stabil across re-seed)
    occs = [{"id": new_id("occ"), "active": True, **o} for o in OCCASIONS]
    await upsert(db.occasions, "slug", occs, "occasions")
    chars = [{"id": new_id("chr"), "active": True, **ch} for ch in CHARACTERS]
    await upsert(db.characters, "slug", chars, "characters")

    # vouchers (Epic E2 — window/scope/per-user/campaign; used_count & id stabil across re-seed)
    await seed_vouchers(db)

    # shipping methods
    shp = [{"active": True, **s} for s in SHIPPING]
    await upsert(db.shipping_methods, "id", shp, "shipping_methods")

    # payment methods
    pay = [{"active": True, **p} for p in PAYMENTS]
    await upsert(db.payment_methods, "id", pay, "payment_methods")

    # settings (singleton)
    await db.settings.update_one({"id": "store"}, {"$set": SETTINGS}, upsert=True)
    print(f"  {G}✓{X} settings: store")

    # ---- Katalog (Epic E1): reviews dulu (untuk rating), lalu products ----
    ratings = await seed_reviews(db)
    await seed_products(db, ratings)

    # ---- Media library (Epic E5): referensi URL (idempotent by id) ----
    media = [{"owner_admin_id": None, **m} for m in MEDIA_SEED]
    await upsert(db.media_assets, "id", media, "media_assets")

    # ---- Storefront CMS (Epic E9): konten default per section (idempotent) ----
    # Section yang defaultnya BERUBAH di kode di-recreate dari registry agar seed/deploy
    # baru langsung memakai konten resmi Collector Parfum (sejarah 1970, kontak, FAQ, dll).
    # Section lain dibiarkan supaya hasil editan admin tidak hilang.
    REFRESH_SECTIONS = [
        "header", "footer", "announcement", "hero", "marquee_words", "story_strip",
        "trust", "video", "faq", "about", "contact",
    ]
    await db.content.delete_many({"id": {"$in": REFRESH_SECTIONS}})
    from services.content import seed_defaults as seed_content
    await seed_content(db)
    print(f"  {G}\u2713{X} content: {await db.content.count_documents({})} section")

    # ---- Lokasi toko offline + Google Reviews (kurasi manual) ----
    for loc in STORE_LOCATIONS:
        await db.store_locations.update_one(
            {"id": loc["id"]},
            {"$set": loc, "$setOnInsert": {"created_at": now_iso()}},
            upsert=True,
        )
    print(f"  {G}\u2713{X} store_locations: {len(STORE_LOCATIONS)}")
    for idx, (author, rating, text, loc, rel) in enumerate(STORE_REVIEWS, 1):
        rid = f"srv_seed{idx:03d}"
        await db.store_reviews.update_one(
            {"id": rid},
            {"$set": {"id": rid, "source": "manual", "author": author, "rating": int(rating),
                      "text": text, "location": loc, "relative_time": rel, "avatar": "", "active": True},
             "$setOnInsert": {"created_at": now_iso()}},
            upsert=True,
        )
    print(f"  {G}\u2713{X} store_reviews (kurasi): {len(STORE_REVIEWS)}")
    await db.settings.update_one({"id": "store"}, {"$set": STORE_CONFIG}, upsert=True)
    print(f"  {G}\u2713{X} store config: maps=embed, reviews=manual, rating {STORE_CONFIG['store_rating_avg']}·{STORE_CONFIG['store_rating_count']}")

    print(f"\n{G}{B}SEED SELESAI.{X}  Admin: {ADMIN_EMAIL} / {ADMIN_PASS}\n")
    client.close()
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
