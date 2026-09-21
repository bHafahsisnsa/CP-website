"""services/stores_google.py — integrasi Google Places reviews (server-side, cache TTL).

Dipisah dari services/stores.py agar tiap modul services tetap ramping (guardrail <=300
baris). Best-effort: kegagalan fetch mengembalikan None agar pemanggil fallback ke
ulasan manual (kurasi admin). URL endpoint dibaca dari `external_urls` (env-overridable).
"""
import time

import httpx

from external_urls import GOOGLE_PLACES_URL

_CACHE_TTL = 600  # 10 menit
_reviews_cache = {}  # place_id -> (ts, payload)


def invalidate_cache():
    """Kosongkan cache reviews (dipanggil saat config toko berubah)."""
    _reviews_cache.clear()


def fetch_google_reviews(api_key, place_id):
    """Ambil rating + up to 5 reviews via Places API Details (server-side, cache TTL).
    Best-effort: kegagalan mengembalikan None agar pemanggil fallback ke manual."""
    now = time.time()
    cached = _reviews_cache.get(place_id)
    if cached and (now - cached[0]) < _CACHE_TTL:
        return cached[1]
    try:
        params = {
            "place_id": place_id,
            "fields": "rating,user_ratings_total,reviews",
            "reviews_sort": "newest",
            "language": "id",
            "key": api_key,
        }
        r = httpx.get(GOOGLE_PLACES_URL, params=params, timeout=8.0)
        data = r.json()
        if data.get("status") != "OK":
            return None
        result = data.get("result", {}) or {}
        reviews = []
        for rv in (result.get("reviews") or [])[:5]:
            reviews.append({
                "author": rv.get("author_name", ""),
                "rating": int(rv.get("rating", 5)),
                "text": rv.get("text", ""),
                "location": "",
                "relative_time": rv.get("relative_time_description", ""),
                "avatar": rv.get("profile_photo_url", ""),
                "source": "google",
            })
        payload = {
            "reviews": reviews,
            "summary": {
                "avg": float(result.get("rating") or 0),
                "count": int(result.get("user_ratings_total") or 0),
            },
        }
        _reviews_cache[place_id] = (now, payload)
        return payload
    except Exception:
        return None


__all__ = ["fetch_google_reviews", "invalidate_cache"]
