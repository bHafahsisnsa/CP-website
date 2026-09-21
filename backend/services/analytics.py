"""services/analytics.py — first-party analytics events + admin aggregates (Epic E7).

Privacy-first: event PUBLIK, TANPA PII (email/telepon/IP mentah dibuang; INV-G3), meta dibatasi.
Rate-limit ringan in-memory (anti spam, best-effort). Agregat admin READ-only & bounded
(anti N+1: grouping in-memory tanpa await di dalam loop). Tidak ada math bisnis baru.
"""
import time
from collections import defaultdict

from core_utils import new_id, now_iso

EVENT_TYPES = {"page_view", "product_view", "add_to_cart", "begin_checkout",
               "purchase", "search", "view_cart", "wa_click"}
FUNNEL_ORDER = ["page_view", "product_view", "add_to_cart", "begin_checkout", "purchase"]
_PII_KEYS = {"email", "phone", "telepon", "ip", "name", "nama", "address", "alamat", "password"}
_MAX_META_KEYS = 12
_MAX_STR = 200
EVENTS_MAX = 50000
TOP_MAX = 10

# Rate limit ringan: {client_key: [timestamps]} — best-effort, in-memory.
_RL = defaultdict(list)
_RL_WINDOW = 10.0   # detik
_RL_MAX = 40        # maksimum event / window / client


def _rate_ok(client_key: str) -> bool:
    now = time.time()
    bucket = _RL[client_key]
    cutoff = now - _RL_WINDOW
    while bucket and bucket[0] < cutoff:
        bucket.pop(0)
    if len(bucket) >= _RL_MAX:
        return False
    bucket.append(now)
    if len(_RL) > 5000:   # jaga memori: batasi jumlah klien terlacak
        _RL.clear()
    return True


def _scrub_meta(meta):
    """Buang PII & batasi ukuran meta (INV-G3). Hanya scalar pendek non-PII dipertahankan."""
    if not isinstance(meta, dict):
        return {}
    out = {}
    for k, v in list(meta.items())[:_MAX_META_KEYS]:
        kl = str(k).lower()
        if any(p in kl for p in _PII_KEYS):
            continue
        if isinstance(v, bool) or isinstance(v, (int, float)):
            out[str(k)[:40]] = v
        elif isinstance(v, str):
            s = v.strip()[:_MAX_STR]
            if "@" in s:   # buang yang tampak seperti email
                continue
            out[str(k)[:40]] = s
    return out


async def record_event(db, payload, client_key="anon"):
    """Simpan event first-party. Tak pernah 5xx — input buruk didiamkan (return ok)."""
    etype = str(payload.get("type") or "").strip()
    if etype not in EVENT_TYPES:
        return {"ok": True, "stored": False}
    if not _rate_ok(client_key):
        return {"ok": True, "stored": False, "throttled": True}
    doc = {
        "id": new_id("evt"),
        "type": etype,
        "path": str(payload.get("path") or "")[:300],
        "product_id": (str(payload.get("product_id"))[:60] if payload.get("product_id") else None),
        "order_code": (str(payload.get("order_code"))[:40] if payload.get("order_code") else None),
        "session_hint": (str(payload.get("session_hint"))[:64] if payload.get("session_hint") else None),
        "meta": _scrub_meta(payload.get("meta")),
        "created_at": now_iso(),
    }
    try:
        await db.analytics_events.insert_one(doc)
    except Exception:
        return {"ok": True, "stored": False}
    return {"ok": True, "stored": True}


async def aggregates(db, range_days=30):
    """Funnel + top produk + konversi (READ-only, bounded, in-memory grouping)."""
    events = await db.analytics_events.find(
        {}, {"_id": 0, "type": 1, "product_id": 1, "order_code": 1}
    ).to_list(EVENTS_MAX)
    funnel = {k: 0 for k in FUNNEL_ORDER}
    prod_views = defaultdict(int)
    prod_carts = defaultdict(int)
    for e in events:              # in-memory grouping (tanpa await → bukan N+1)
        t = e.get("type")
        if t in funnel:
            funnel[t] += 1
        if t == "product_view" and e.get("product_id"):
            prod_views[e["product_id"]] += 1
        elif t == "add_to_cart" and e.get("product_id"):
            prod_carts[e["product_id"]] += 1
    pviews_sorted = sorted(prod_views.items(), key=lambda x: x[1], reverse=True)[:TOP_MAX]
    ids = [pid for pid, _ in pviews_sorted]
    name_map = {}
    if ids:
        prods = await db.products.find(
            {"id": {"$in": ids}}, {"_id": 0, "id": 1, "name": 1, "slug": 1}
        ).to_list(TOP_MAX)
        name_map = {p["id"]: p for p in prods}
    top_products = [{
        "product_id": pid, "views": n, "carts": prod_carts.get(pid, 0),
        "name": (name_map.get(pid) or {}).get("name", pid),
        "slug": (name_map.get(pid) or {}).get("slug"),
    } for pid, n in pviews_sorted]
    denom = funnel["begin_checkout"] or funnel["page_view"] or 0
    conversion = round((funnel["purchase"] / denom) * 100, 2) if denom else 0.0
    total_orders = await db.orders.count_documents({})
    return {
        "range_days": range_days,
        "funnel": [{"step": k, "count": funnel[k]} for k in FUNNEL_ORDER],
        "totals": {"events": len(events), "orders": total_orders},
        "conversion_rate": conversion,
        "top_products": top_products,
    }
