"""external_urls.py — SSOT endpoint layanan eksternal (override via environment).

Semua URL pihak ketiga dibaca dari env dengan fallback default sehingga TIDAK ada
hardcode URL di `routers/` maupun `services/` (kepatuhan CHECK 3 validate_compliance).
"""
import os

GOOGLE_PLACES_URL = os.environ.get(
    "GOOGLE_PLACES_URL",
    "https://maps.googleapis.com/maps/api/place/details/json",
)
