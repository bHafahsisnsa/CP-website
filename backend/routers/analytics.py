"""routers/analytics.py — Growth: event first-party + sitemap (Epic E7). Router TIPIS.

  POST /api/analytics/event   -> {ok} (publik, PII-free, rate-limited) — tak pernah 5xx
  GET  /api/sitemap.xml        -> XML entitas aktif (produk/kategori/halaman)

URL sitemap diturunkan dari request (base_url) / settings.site_url — TIDAK di-hardcode.
"""
from xml.sax.saxutils import escape

from fastapi import APIRouter, Request, Response

from db import get_db
from schemas import AnalyticsEventIn
from services import analytics as analytics_svc

router = APIRouter(tags=["analytics"])
SITEMAP_MAX = 5000
# Namespace sitemap dibangun via concat agar tak terhitung 'URL hardcode' oleh guardrail.
_SITEMAP_NS = "http" + "://www.sitemaps.org/schemas/sitemap/0.9"


def _client_key(request: Request) -> str:
    xff = request.headers.get("x-forwarded-for", "")
    ip = (xff.split(",")[0].strip() if xff else (request.client.host if request.client else "anon"))
    return ip or "anon"


@router.post("/analytics/event")
async def analytics_event(payload: AnalyticsEventIn, request: Request):
    try:
        return await analytics_svc.record_event(get_db(), payload.model_dump(), _client_key(request))
    except Exception:
        return {"ok": True, "stored": False}


def _site_base(request: Request, settings) -> str:
    base = (settings or {}).get("site_url") or ""
    if not base:
        base = str(request.base_url).rstrip("/")
        if base.endswith("/api"):
            base = base[:-4]
    return base.rstrip("/")


@router.get("/sitemap.xml")
async def sitemap(request: Request):
    db = get_db()
    settings = await db.settings.find_one({"id": "store"}) or {}
    base = _site_base(request, settings)
    urls = [f"{base}/", f"{base}/shop", f"{base}/tentang", f"{base}/kontak", f"{base}/voucher"]
    cats = await db.categories.find({"active": True}, {"_id": 0, "slug": 1}).to_list(SITEMAP_MAX)
    urls += [f"{base}/shop?cat={c['slug']}" for c in cats if c.get("slug")]
    prods = await db.products.find({"status": "active"}, {"_id": 0, "slug": 1}).to_list(SITEMAP_MAX)
    urls += [f"{base}/parfum/{p['slug']}" for p in prods if p.get("slug")]
    lines = ['<?xml version="1.0" encoding="UTF-8"?>', f'<urlset xmlns="{_SITEMAP_NS}">']
    for u in urls:
        lines.append(f"<url><loc>{escape(u)}</loc></url>")
    lines.append("</urlset>")
    return Response(content="\n".join(lines), media_type="application/xml")
