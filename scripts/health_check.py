#!/usr/bin/env python3
"""health_check.py — Automated Health Check (Collector Parfum).

Verifikasi endpoint kritis: cek ISI (bukan hanya status 200).
Kontrak: login → {"token": "..."}; list → ARRAY langsung.
Daftar CRITICAL_ENDPOINTS TUMBUH seiring fitur (lihat docs/07 §7).
Usage: cd /app && python scripts/health_check.py
Exit 1 jika ada FAIL.
"""
import asyncio
import os
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
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

API = os.environ.get("API_BASE", "http://localhost:8001").rstrip("/")
ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "admin@collectorparfum.id")
ADMIN_PASS = os.environ.get("ADMIN_PASS", "Admin#2026")
G, Y, R, C, X, B = "\033[92m", "\033[93m", "\033[91m", "\033[96m", "\033[0m", "\033[1m"

# (path, min_items, desc). min_items=-1 -> cek status saja (bukan list).
# needs_auth=True -> pakai token admin.
CRITICAL_ENDPOINTS = [
    ("/api/", -1, "Health root", False),
    ("/api/health", -1, "Health detail", False),
    ("/api/auth/me", -1, "Auth: current user", True),
    # E1 Catalog (read-path)
    ("/api/products", 1, "Catalog: products list", False),
    ("/api/products/noir-oud-intense", -1, "Catalog: product detail", False),
    ("/api/categories", 1, "Catalog: categories", False),
    ("/api/reviews", 1, "Catalog: reviews", False),
    # E2 Vouchers
    ("/api/vouchers", 1, "Vouchers: active list", False),
    # E3 Cart/Checkout/Orders (config + owner-scoped)
    ("/api/shipping-methods", 1, "Config: shipping methods", False),
    ("/api/payment-methods", 1, "Config: payment methods", False),
    ("/api/settings", -1, "Config: store settings", False),
    ("/api/orders", -1, "Orders: own list (auth)", True),
    # E4 Account (owner-scoped)
    ("/api/addresses", -1, "Account: addresses (auth)", True),
    ("/api/wishlist", -1, "Account: wishlist (auth)", True),
    # E5 Admin Backoffice (role admin; token admin dipakai get_token)
    ("/api/admin/dashboard", -1, "Admin: dashboard", True),
    ("/api/admin/products", 1, "Admin: products list", True),
    ("/api/admin/categories", 1, "Admin: categories", True),
    ("/api/admin/vouchers", 1, "Admin: vouchers", True),
    ("/api/admin/orders", -1, "Admin: orders list", True),
    ("/api/admin/reviews", -1, "Admin: reviews moderation", True),
    ("/api/admin/media", -1, "Admin: media library", True),
    ("/api/admin/settings", -1, "Admin: store settings", True),
    ("/api/admin/payments", -1, "Admin: payment proofs (E6)", True),
    # E7 Growth & Analytics
    ("/api/sitemap.xml", -1, "Growth: sitemap.xml", False),
    ("/api/admin/analytics", -1, "Admin: analytics aggregates (E7)", True),
    ("/api/admin/crm/segments", -1, "Admin: CRM segments (E7)", True),
    # E9 Storefront CMS
    ("/api/content", -1, "CMS: konten storefront (E9)", False),
    ("/api/admin/content", -1, "Admin: CMS content (E9)", True),
    ("/api/admin/content/schema", -1, "Admin: CMS schema (E9)", True),
]


def extract_count(data):
    if isinstance(data, list):
        return len(data)
    if isinstance(data, dict):
        for k in ("items", "data", "rows", "results"):
            if isinstance(data.get(k), list):
                return len(data[k])
        return -1
    return -1


async def get_token(client):
    try:
        r = await client.post(f"{API}/api/auth/login",
                              json={"email": ADMIN_EMAIL, "password": ADMIN_PASS}, timeout=15)
        if r.status_code == 200:
            return r.json().get("token")
        print(f"{R}  LOGIN GAGAL HTTP {r.status_code}: {r.text[:160]}{X}")
    except Exception as e:
        print(f"{R}  LOGIN ERROR: {e}{X}")
    return None


async def check(client, token, path, mn, needs_auth):
    h = {"Authorization": f"Bearer {token}"} if needs_auth else {}
    try:
        r = await client.get(f"{API}{path}", headers=h, timeout=15)
        sc = r.status_code
        if sc in (401, 403):
            return ("FAIL", f"Auth error HTTP {sc}")
        if sc >= 500:
            return ("FAIL", f"Server error HTTP {sc} — {r.text[:80]}")
        if sc == 404:
            return ("FAIL", "HTTP 404")
        if mn == -1:
            return ("PASS" if sc < 400 else "FAIL", "OK")
        data = r.json()
        n = extract_count(data)
        if sc >= 400:
            return ("FAIL", f"HTTP {sc}")
        if n == 0 or (n != -1 and n < mn):
            return ("WARN", f"{n} items (perlu seed?)")
        return ("PASS", f"{n} items")
    except httpx.TimeoutException:
        return ("FAIL", "TIMEOUT")
    except Exception as e:
        return ("FAIL", str(e)[:120])


async def run():
    print(f"\n{B}{'='*60}{X}\n  HEALTH CHECK  (API: {API})\n  {datetime.now():%Y-%m-%d %H:%M:%S}\n{B}{'='*60}{X}")
    async with httpx.AsyncClient(follow_redirects=True) as client:
        token = await get_token(client)
        if not token:
            print(f"{R}FATAL: tidak bisa login (backend up? sudah di-seed?).{X}")
            return 1
        print(f"{G}  ✓ Login berhasil\n{X}")
        p = w = f = 0
        for path, mn, desc, needs_auth in CRITICAL_ENDPOINTS:
            tag, detail = await check(client, token, path, mn, needs_auth)
            color = {"PASS": G, "WARN": Y, "FAIL": R}[tag]
            print(f"  {color}[{tag}]{X} {path:<26} {color}{detail}{X}")
            p += tag == "PASS"
            w += tag == "WARN"
            f += tag == "FAIL"
            await asyncio.sleep(0.03)

        # E2: voucher validate (POST) — cek ISI + no 5xx (kontrak discount dari server)
        try:
            rv = await client.post(f"{API}/api/vouchers/validate",
                                   json={"code": "WELCOME10", "subtotal": 250000}, timeout=15)
            jd = rv.json() if rv.status_code < 500 else {}
            if rv.status_code == 200 and jd.get("valid") and jd.get("discount") == 25000:
                print(f"  {G}[PASS]{X} {'/api/vouchers/validate':<26} {G}valid discount=25000{X}")
                p += 1
            else:
                print(f"  {R}[FAIL]{X} {'/api/vouchers/validate':<26} {R}HTTP {rv.status_code} {rv.text[:80]}{X}")
                f += 1
            # invalid code → valid=false, TIDAK 5xx
            rv2 = await client.post(f"{API}/api/vouchers/validate",
                                    json={"code": "NGARANG404", "subtotal": 1000}, timeout=15)
            if rv2.status_code == 200 and rv2.json().get("valid") is False:
                print(f"  {G}[PASS]{X} {'/api/vouchers/validate(bad)':<26} {G}valid=false + reason{X}")
                p += 1
            else:
                print(f"  {R}[FAIL]{X} {'/api/vouchers/validate(bad)':<26} {R}HTTP {rv2.status_code}{X}")
                f += 1
        except Exception as e:
            print(f"  {R}[FAIL]{X} /api/vouchers/validate {R}{str(e)[:100]}{X}")
            f += 1

        # E7: analytics event (POST) — publik, PII-free, tak pernah 5xx.
        try:
            re1 = await client.post(f"{API}/api/analytics/event",
                                    json={"type": "page_view", "path": "/", "meta": {"src": "healthcheck"}}, timeout=15)
            if re1.status_code == 200 and re1.json().get("ok") is True:
                print(f"  {G}[PASS]{X} {'/api/analytics/event':<26} {G}ok stored{X}")
                p += 1
            else:
                print(f"  {R}[FAIL]{X} {'/api/analytics/event':<26} {R}HTTP {re1.status_code}{X}")
                f += 1
            # tipe tak dikenal → tetap 200 (diabaikan), TIDAK 5xx
            re2 = await client.post(f"{API}/api/analytics/event",
                                    json={"type": "___nope___", "meta": {"x": 1}}, timeout=15)
            if re2.status_code == 200:
                print(f"  {G}[PASS]{X} {'/api/analytics/event(bad)':<26} {G}200 (diabaikan){X}")
                p += 1
            else:
                print(f"  {R}[FAIL]{X} {'/api/analytics/event(bad)':<26} {R}HTTP {re2.status_code}{X}")
                f += 1
        except Exception as e:
            print(f"  {R}[FAIL]{X} /api/analytics/event {R}{str(e)[:100]}{X}")
            f += 1
    print(f"\n{B}{'='*60}{X}\n  {G}PASS {p}{X} | {Y}WARN {w}{X} | {R}FAIL {f}{X}\n{B}{'='*60}{X}")
    return 1 if f else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(run()))
