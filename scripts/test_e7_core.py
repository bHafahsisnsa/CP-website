#!/usr/bin/env python3
"""test_e7_core.py — POC CORE E7 (Growth & Analytics). PROVE-BEFORE-BUILD.

  T1 Event first-party: page_view valid -> stored; tipe tak dikenal -> 200 & stored:false (tak 5xx).
  T2 PII scrub (INV-G3): meta {email,phone} dibuang; field aman dipertahankan.
  T3 Sitemap: GET /api/sitemap.xml -> 200 XML memuat URL produk & kategori aktif.
  T4 Settings publik diperluas: whatsapp_number/seo_title/ga_measurement_id ada di /api/settings.
  T5 Admin analytics: funnel 5 langkah + konversi; RBAC tanpa token -> 401/403.
  T6 Admin CRM: segments{} + rows[]; RBAC tanpa token -> 401/403.
  T7 Purchase event: tersimpan (order_code opsional) — dasar rekonsiliasi INV-G1.
  T8 Rate-limit: burst event -> sebagian throttled (best-effort, tak pernah 5xx).

Self-cleaning. Usage: cd /app && python scripts/test_e7_core.py
"""
import asyncio
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))
try:
    from dotenv import load_dotenv
    load_dotenv(ROOT / "backend" / ".env")
except Exception:
    pass
try:
    import httpx
except ImportError:
    os.system("pip install httpx -q")
    import httpx
from motor.motor_asyncio import AsyncIOMotorClient

API = os.environ.get("API_BASE", "http://localhost:8001").rstrip("/")
MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "collector_parfum")
ADMIN = {"email": "admin@collectorparfum.id", "password": "Admin#2026"}
TAG = "sid_e7test"
G, R, Y, B, X = "\033[92m", "\033[91m", "\033[93m", "\033[1m", "\033[0m"
passed = failed = 0


def ok(m):
    global passed
    passed += 1
    print(f"  {G}[PASS]{X} {m}")


def bad(m):
    global failed
    failed += 1
    print(f"  {R}[FAIL]{X} {m}")


async def login(c, creds):
    r = await c.post(f"{API}/api/auth/login", json=creds, timeout=15)
    return r.json()["token"] if r.status_code == 200 else None


async def ev(c, payload):
    return await c.post(f"{API}/api/analytics/event", json=payload, timeout=15)


async def main():
    print(f"\n{B}{'='*64}{X}\n  TEST E7 CORE (Growth & Analytics)  API={API}\n{B}{'='*64}{X}")
    db = AsyncIOMotorClient(MONGO_URL)[DB_NAME]
    async with httpx.AsyncClient() as c:
        try:
            if (await c.get(f"{API}/api/", timeout=5)).status_code >= 500:
                raise Exception()
        except Exception:
            print(f"{R}Backend mati.{X}")
            return 1

        # ---------- T1 Event first-party ----------
        print(f"\n{B}T1 Event first-party{X}")
        r = await ev(c, {"type": "page_view", "path": "/", "session_hint": TAG, "meta": {"src": "e7"}})
        j = r.json() if r.status_code == 200 else {}
        ok("page_view valid → stored:true") if (r.status_code == 200 and j.get("stored")) else bad(f"page_view HTTP {r.status_code} {j}")
        r = await ev(c, {"type": "___unknown___", "session_hint": TAG})
        j = r.json() if r.status_code == 200 else {}
        ok("tipe tak dikenal → 200 & stored:false (tak 5xx)") if (r.status_code == 200 and j.get("stored") is False) else bad(f"bad-type HTTP {r.status_code} {j}")

        # ---------- T2 PII scrub (INV-G3) ----------
        print(f"\n{B}T2 PII scrub (INV-G3){X}")
        await ev(c, {"type": "search", "session_hint": TAG,
                     "meta": {"email": "leak@x.com", "phone": "0811", "note": "aman", "count": 3}})
        doc = await db.analytics_events.find_one({"session_hint": TAG, "type": "search"})
        meta = (doc or {}).get("meta", {})
        clean = "email" not in meta and "phone" not in meta and not any("@" in str(v) for v in meta.values())
        kept = meta.get("note") == "aman" and meta.get("count") == 3
        ok("email/telepon dibuang; field aman dipertahankan") if (clean and kept) else bad(f"scrub gagal: {meta}")

        # ---------- T3 Sitemap ----------
        print(f"\n{B}T3 Sitemap XML{X}")
        prod = await db.products.find_one({"status": "active"}, {"slug": 1})
        cat = await db.categories.find_one({"active": True}, {"slug": 1})
        r = await c.get(f"{API}/api/sitemap.xml", timeout=15)
        body = r.text if r.status_code == 200 else ""
        has_ct = "application/xml" in r.headers.get("content-type", "")
        good = r.status_code == 200 and has_ct and "<urlset" in body and \
            (not prod or f"/parfum/{prod['slug']}" in body) and (not cat or f"cat={cat['slug']}" in body)
        ok("sitemap 200 XML memuat URL produk & kategori") if good else bad(f"sitemap HTTP {r.status_code} ct={r.headers.get('content-type')}")

        # ---------- T4 Settings publik ----------
        print(f"\n{B}T4 Settings publik diperluas{X}")
        s = (await c.get(f"{API}/api/settings", timeout=15)).json()
        need = ("whatsapp_number", "seo_title", "seo_description", "ga_measurement_id",
                "social_instagram", "social_facebook")
        miss = [k for k in need if k not in s]
        ok("field growth ada di /api/settings") if not miss else bad(f"field hilang: {miss}")

        # ---------- T5 Admin analytics + RBAC ----------
        print(f"\n{B}T5 Admin analytics{X}")
        ta = await login(c, ADMIN)
        ha = {"Authorization": f"Bearer {ta}"}
        r = await c.get(f"{API}/api/admin/analytics", headers=ha, timeout=15)
        a = r.json() if r.status_code == 200 else {}
        funnel = a.get("funnel", [])
        steps = [f["step"] for f in funnel]
        pv = next((f["count"] for f in funnel if f["step"] == "page_view"), 0)
        good = r.status_code == 200 and steps == ["page_view", "product_view", "add_to_cart", "begin_checkout", "purchase"] \
            and pv >= 1 and "conversion_rate" in a and "top_products" in a
        ok("funnel 5 langkah + konversi + page_view>=1") if good else bad(f"analytics HTTP {r.status_code} {str(a)[:160]}")
        rn = await c.get(f"{API}/api/admin/analytics", timeout=15)
        ok("RBAC: analytics tanpa token → 401/403") if rn.status_code in (401, 403) else bad(f"RBAC analytics HTTP {rn.status_code}")

        # ---------- T6 Admin CRM + RBAC ----------
        print(f"\n{B}T6 Admin CRM segments{X}")
        r = await c.get(f"{API}/api/admin/crm/segments", headers=ha, timeout=15)
        cr = r.json() if r.status_code == 200 else {}
        good = r.status_code == 200 and isinstance(cr.get("segments"), dict) and isinstance(cr.get("rows"), list) \
            and isinstance(cr.get("thresholds"), dict)
        ok("segments{}, rows[], thresholds{}") if good else bad(f"crm HTTP {r.status_code} {str(cr)[:160]}")
        rn = await c.get(f"{API}/api/admin/crm/segments", timeout=15)
        ok("RBAC: crm tanpa token → 401/403") if rn.status_code in (401, 403) else bad(f"RBAC crm HTTP {rn.status_code}")

        # ---------- T7 Purchase event ----------
        print(f"\n{B}T7 Purchase event (dasar INV-G1){X}")
        r = await ev(c, {"type": "purchase", "session_hint": TAG, "meta": {"value": 250000}})
        j = r.json() if r.status_code == 200 else {}
        ok("purchase event tersimpan") if (r.status_code == 200 and j.get("stored")) else bad(f"purchase HTTP {r.status_code} {j}")

        # ---------- T8 Rate-limit ----------
        print(f"\n{B}T8 Rate-limit (best-effort){X}")
        throttled = False
        server_err = False
        for _ in range(60):
            rr = await ev(c, {"type": "page_view", "session_hint": TAG})
            if rr.status_code >= 500:
                server_err = True
                break
            if rr.json().get("throttled"):
                throttled = True
        if server_err:
            bad("rate-limit menyebabkan 5xx (tidak boleh)")
        else:
            ok("burst event → sebagian throttled, tanpa 5xx") if throttled else bad("tak ada event yang di-throttle pada burst 60x")

        # ---------- Cleanup ----------
        await db.analytics_events.delete_many({"session_hint": TAG})

    print(f"\n{B}{'='*64}{X}\n  {G}PASS {passed}{X} | {R}FAIL {failed}{X}\n{B}{'='*64}{X}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
