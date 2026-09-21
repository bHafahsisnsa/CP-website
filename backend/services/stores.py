"""services/stores.py — Lokasi toko offline + Google Reviews (manual/kurasi + Google Places).

Arsitektur konsisten dgn SSOT app:
  - Koleksi `store_locations` : daftar cabang toko offline (embed peta tanpa API key).
  - Koleksi `store_reviews`   : ulasan KURASI MANUAL (editable admin) — sumber default.
  - Config (settings singleton): maps_mode(embed|js), reviews_source(manual|google),
    google_maps_api_key (client, JS maps), google_places_api_key (server, reviews),
    google_place_id (default), store_rating_avg/count (ringkasan tampilan), stores_intro.

Google Reviews ASLI (Places API) DISIAPKAN tapi TIDAK aktif tanpa key. Bila
reviews_source == 'google' & key+place_id ada → fetch server-side (cache TTL), gagal → fallback manual.
Uang/angka bounded; semua mutasi admin diaudit.
"""
from core_utils import money, new_id, now_iso, safe_doc
from services.audit import log_action
from services.stores_google import fetch_google_reviews, invalidate_cache

LIST_MAX = 200

_CONFIG_KEYS = (
    "maps_mode", "reviews_source", "google_maps_api_key", "google_places_api_key",
    "google_place_id", "store_rating_avg", "store_rating_count", "stores_intro",
)
_CONFIG_DEFAULT = {
    "maps_mode": "embed",
    "reviews_source": "manual",
    "google_maps_api_key": "",
    "google_places_api_key": "",
    "google_place_id": "",
    "store_rating_avg": 0.0,
    "store_rating_count": 0,
    "stores_intro": "Kunjungi butik Collector Parfum. Tim kami siap membantu Anda menemukan aroma yang tepat.",
}


# ============================== CONFIG ==============================
async def get_config(db):
    doc = await db.settings.find_one({"id": "store"}) or {}
    out = dict(_CONFIG_DEFAULT)
    for k in _CONFIG_KEYS:
        if doc.get(k) is not None:
            out[k] = doc[k]
    return out


async def update_config(db, actor_id, data):
    updates = {}
    for k in ("maps_mode", "reviews_source"):
        v = data.get(k)
        if v is not None:
            updates[k] = str(v)
    for k in ("google_maps_api_key", "google_places_api_key", "google_place_id", "stores_intro"):
        if data.get(k) is not None:
            updates[k] = str(data[k])[:2000]
    if data.get("rating_avg") is not None:
        try:
            updates["store_rating_avg"] = max(0.0, min(5.0, round(float(data["rating_avg"]), 1)))
        except (TypeError, ValueError):
            pass
    if data.get("rating_count") is not None:
        updates["store_rating_count"] = max(0, int(money(data["rating_count"])))
    if updates:
        updates["updated_at"] = now_iso()
        await db.settings.update_one({"id": "store"}, {"$set": updates}, upsert=True)
        invalidate_cache()  # config berubah → invalidasi cache reviews
        await log_action(actor_id, "update", "settings", "store_config")
    return await get_config(db)


async def public_config(db):
    """Config yang aman dibagikan ke storefront. `maps_api_key` HANYA saat mode 'js'
    (kunci client Maps JS; dibatasi HTTP-referrer di Google Cloud). Kunci Places (server) TAK dibagikan."""
    cfg = await get_config(db)
    maps_mode = cfg.get("maps_mode") or "embed"
    return {
        "maps_mode": maps_mode,
        "reviews_source": cfg.get("reviews_source") or "manual",
        "maps_api_key": (cfg.get("google_maps_api_key") or "") if maps_mode == "js" else "",
        "rating": {
            "avg": float(cfg.get("store_rating_avg") or 0),
            "count": int(cfg.get("store_rating_count") or 0),
        },
        "intro": cfg.get("stores_intro") or "",
    }


# ============================== LOCATIONS ==============================
def _clean_location(data, existing=None):
    e = existing or {}
    def s(key, cap, default=""):
        v = data.get(key)
        if v is None:
            v = e.get(key, default)
        return str(v)[:cap]

    def fnum(key):
        v = data.get(key)
        if v is None:
            return e.get(key)
        try:
            return float(v)
        except (TypeError, ValueError):
            return None

    return {
        "name": s("name", 160),
        "address": s("address", 400),
        "phone": s("phone", 60),
        "whatsapp": s("whatsapp", 60),
        "hours": s("hours", 400),
        "maps_query": s("maps_query", 400),
        "map_url": s("map_url", 1000),
        "embed_url": s("embed_url", 2000),
        "place_id": s("place_id", 200),
        "lat": fnum("lat"),
        "lng": fnum("lng"),
        "photo": s("photo", 1000),
        "order": int(data.get("order", e.get("order", 0)) or 0),
        "active": bool(data.get("active", e.get("active", True))),
    }


async def list_locations_public(db):
    docs = await db.store_locations.find({"active": True}).sort([("order", 1), ("name", 1)]).to_list(LIST_MAX)
    return [safe_doc(d) for d in docs]


async def list_locations_admin(db):
    docs = await db.store_locations.find({}).sort([("order", 1), ("name", 1)]).to_list(LIST_MAX)
    return [safe_doc(d) for d in docs]


async def create_location(db, actor_id, data):
    doc = {"id": new_id("loc"), **_clean_location(data), "created_at": now_iso()}
    if not doc["name"] or not doc["address"]:
        raise ValueError("Nama & alamat wajib diisi")
    await db.store_locations.insert_one(doc)
    await log_action(actor_id, "create", "store_locations", doc["id"])
    return safe_doc(doc)


async def update_location(db, actor_id, lid, data):
    existing = await db.store_locations.find_one({"id": lid})
    if not existing:
        return None
    updates = _clean_location(data, existing)
    if not updates["name"] or not updates["address"]:
        raise ValueError("Nama & alamat wajib diisi")
    updates["updated_at"] = now_iso()
    await db.store_locations.update_one({"id": lid}, {"$set": updates})
    await log_action(actor_id, "update", "store_locations", lid)
    return safe_doc(await db.store_locations.find_one({"id": lid}))


async def delete_location(db, actor_id, lid):
    existing = await db.store_locations.find_one({"id": lid}, {"_id": 1})
    if not existing:
        return None
    await db.store_locations.delete_one({"id": lid})
    await log_action(actor_id, "delete", "store_locations", lid)
    return {"deleted": True, "id": lid}


# ============================== MANUAL REVIEWS ==============================
def _clean_review(data, existing=None):
    e = existing or {}
    try:
        rating = int(data.get("rating", e.get("rating", 5)))
    except (TypeError, ValueError):
        rating = 5
    rating = max(1, min(5, rating))
    return {
        "author": str(data.get("author", e.get("author", "")))[:120],
        "rating": rating,
        "text": str(data.get("text", e.get("text", "")))[:2000],
        "location": str(data.get("location", e.get("location", "")))[:120],
        "relative_time": str(data.get("relative_time", e.get("relative_time", "")))[:80],
        "avatar": str(data.get("avatar", e.get("avatar", "")))[:1000],
        "active": bool(data.get("active", e.get("active", True))),
    }


async def list_reviews_admin(db):
    docs = await db.store_reviews.find({}).sort([("created_at", -1)]).to_list(LIST_MAX)
    return [safe_doc(d) for d in docs]


async def create_review(db, actor_id, data):
    clean = _clean_review(data)
    if not clean["author"]:
        raise ValueError("Nama pengulas wajib diisi")
    doc = {"id": new_id("srv"), "source": "manual", **clean, "created_at": now_iso()}
    await db.store_reviews.insert_one(doc)
    await log_action(actor_id, "create", "store_reviews", doc["id"])
    return safe_doc(doc)


async def update_review(db, actor_id, rid, data):
    existing = await db.store_reviews.find_one({"id": rid})
    if not existing:
        return None
    updates = _clean_review(data, existing)
    updates["updated_at"] = now_iso()
    await db.store_reviews.update_one({"id": rid}, {"$set": updates})
    await log_action(actor_id, "update", "store_reviews", rid)
    return safe_doc(await db.store_reviews.find_one({"id": rid}))


async def delete_review(db, actor_id, rid):
    existing = await db.store_reviews.find_one({"id": rid}, {"_id": 1})
    if not existing:
        return None
    await db.store_reviews.delete_one({"id": rid})
    await log_action(actor_id, "delete", "store_reviews", rid)
    return {"deleted": True, "id": rid}


async def _manual_reviews(db):
    docs = await db.store_reviews.find({"active": True}).sort([("created_at", -1)]).to_list(LIST_MAX)
    out = []
    for d in docs:
        out.append({
            "author": d.get("author", ""),
            "rating": int(d.get("rating", 5)),
            "text": d.get("text", ""),
            "location": d.get("location", ""),
            "relative_time": d.get("relative_time", ""),
            "avatar": d.get("avatar", ""),
            "source": "manual",
        })
    return out


async def public_reviews(db):
    """{source, summary:{avg,count}, reviews:[...]}. Manual = default; google bila dikonfigurasi."""
    cfg = await get_config(db)
    manual = await _manual_reviews(db)
    manual_summary = {
        "avg": float(cfg.get("store_rating_avg") or 0),
        "count": int(cfg.get("store_rating_count") or 0),
    }
    if (cfg.get("reviews_source") == "google"
            and cfg.get("google_places_api_key") and cfg.get("google_place_id")):
        g = fetch_google_reviews(cfg["google_places_api_key"], cfg["google_place_id"])
        if g and g.get("reviews"):
            return {"source": "google", "summary": g["summary"], "reviews": g["reviews"]}
    return {"source": "manual", "summary": manual_summary, "reviews": manual}


__all__ = [
    "get_config", "update_config", "public_config",
    "list_locations_public", "list_locations_admin",
    "create_location", "update_location", "delete_location",
    "list_reviews_admin", "create_review", "update_review", "delete_review",
    "public_reviews",
]
