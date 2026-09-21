#!/usr/bin/env python3
"""test_e2_core.py — POC/unit+integration test untuk Epic E2 (Pricing SSOT + Voucher).

Membuktikan CORE E2 bekerja SEBELUM wiring UI:
  A. UNIT  — services.pricing.compute_pricing / voucher_discount (pure, edge cases).
  B. DB    — services.vouchers.evaluate_voucher terhadap voucher ter-seed.
  C. HTTP  — POST /api/vouchers/validate + GET /api/vouchers (kontrak + no 5xx).

Usage: cd /app && python scripts/test_e2_core.py
Exit 0 = semua lulus.
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

from motor.motor_asyncio import AsyncIOMotorClient  # noqa: E402
from services.pricing import compute_pricing, voucher_discount  # noqa: E402
from services import vouchers as vsvc  # noqa: E402

try:
    import httpx
except ImportError:
    os.system("pip install httpx -q")
    import httpx

G, R, Y, B, X = "\033[92m", "\033[91m", "\033[93m", "\033[1m", "\033[0m"
API = os.environ.get("API_BASE", "http://localhost:8001").rstrip("/")
MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "collector_parfum")

_p = {"pass": 0, "fail": 0}


def check(name, cond, detail=""):
    if cond:
        _p["pass"] += 1
        print(f"  {G}[PASS]{X} {name}")
    else:
        _p["fail"] += 1
        print(f"  {R}[FAIL]{X} {name}  {Y}{detail}{X}")


def items(*pairs):
    return [{"unit_price": p, "quantity": q} for p, q in pairs]


def unit_tests():
    print(f"\n{B}A. UNIT — compute_pricing / voucher_discount{X}")
    # subtotal
    r = compute_pricing(items((100000, 2), (50000, 1)))
    check("subtotal = Σ(price*qty)", r["subtotal"] == 250000, r)
    check("no voucher → discount 0", r["discount"] == 0)
    check("total = subtotal (no ship/cod)", r["total"] == 250000)

    # percent capped
    v_pct = {"type": "percent", "value": 10, "min_spend": 0}
    check("percent 10% of 250000 = 25000", voucher_discount(v_pct, 250000) == 25000)
    v_pct_big = {"type": "percent", "value": 100, "min_spend": 0}
    check("percent 100% capped to subtotal", voucher_discount(v_pct_big, 250000) == 250000)

    # rounding 33% of 100000 = 33000
    check("percent rounding 33% of 100000 = 33000",
          voucher_discount({"type": "percent", "value": 33, "min_spend": 0}, 100000) == 33000)
    # 15% of 685000 = 102750
    check("percent 15% of 685000 = 102750",
          voucher_discount({"type": "percent", "value": 15, "min_spend": 0}, 685000) == 102750)

    # flat clamp
    check("flat > subtotal clamped",
          voucher_discount({"type": "flat", "value": 999999, "min_spend": 0}, 250000) == 250000)
    check("flat normal",
          voucher_discount({"type": "flat", "value": 50000, "min_spend": 0}, 250000) == 50000)

    # min_spend
    check("min_spend not met → 0",
          voucher_discount({"type": "flat", "value": 50000, "min_spend": 300000}, 250000) == 0)
    check("min_spend met → applies",
          voucher_discount({"type": "flat", "value": 50000, "min_spend": 300000}, 300000) == 50000)

    # free_shipping
    check("free_shipping = shipping_price",
          voucher_discount({"type": "free_shipping", "value": 1, "min_spend": 0}, 250000, 22000) == 22000)
    check("free_shipping zero shipping → 0",
          voucher_discount({"type": "free_shipping", "value": 1, "min_spend": 0}, 250000, 0) == 0)

    # compute_pricing with free_shipping → total = subtotal + cod (shipping offset)
    r = compute_pricing(items((250000, 1)),
                        voucher={"type": "free_shipping", "value": 1, "min_spend": 0},
                        shipping={"price": 22000})
    check("free_shipping: total offsets shipping", r["total"] == 250000, r)
    check("free_shipping: discount == shipping_price", r["discount"] == 22000, r)

    # cod fee only when group=cod (INV-10)
    r = compute_pricing(items((100000, 1)), shipping=20000, payment_group="cod", cod_fee=4000)
    check("cod_fee applied when group=cod", r["cod_fee"] == 4000 and r["total"] == 124000, r)
    r = compute_pricing(items((100000, 1)), shipping=20000, payment_group="transfer", cod_fee=4000)
    check("cod_fee ignored when group!=cod", r["cod_fee"] == 0 and r["total"] == 120000, r)

    # total floored at 0 (discount == subtotal, shipping only)
    r = compute_pricing(items((100000, 1)),
                        voucher={"type": "flat", "value": 100000, "min_spend": 0})
    check("total floored at 0 when discount==subtotal", r["total"] == 0, r)

    # adversarial: garbage inputs don't crash
    try:
        compute_pricing([{"unit_price": "x", "quantity": None}], voucher={"type": "bogus", "value": -5})
        check("adversarial input handled (no crash)", True)
    except Exception as e:
        check("adversarial input handled (no crash)", False, str(e))


async def db_tests():
    print(f"\n{B}B. DB — evaluate_voucher (voucher ter-seed){X}")
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]

    r = await vsvc.evaluate_voucher(db, "WELCOME10", 250000)
    check("WELCOME10 valid, 10% = 25000", r["valid"] and r["discount"] == 25000, r)

    r = await vsvc.evaluate_voucher(db, "welcome10", 250000)  # lowercase normalized
    check("code normalized uppercase", r["valid"], r)

    r = await vsvc.evaluate_voucher(db, "COLLECTOR50", 250000)
    check("COLLECTOR50 below min_spend → invalid+reason",
          (not r["valid"]) and r["reason"], r)
    r = await vsvc.evaluate_voucher(db, "COLLECTOR50", 300000)
    check("COLLECTOR50 at min_spend → valid 50000", r["valid"] and r["discount"] == 50000, r)

    r = await vsvc.evaluate_voucher(db, "ONGKIRGRATIS", 200000, shipping=22000)
    check("ONGKIRGRATIS free_shipping discount == shipping", r["valid"] and r["discount"] == 22000, r)
    r = await vsvc.evaluate_voucher(db, "ONGKIRGRATIS", 100000, shipping=22000)
    check("ONGKIRGRATIS below min_spend → invalid", not r["valid"], r)

    r = await vsvc.evaluate_voucher(db, "EXPIRED2024", 250000)
    check("EXPIRED2024 → invalid (kedaluwarsa)", (not r["valid"]) and "kedaluwarsa" in (r["reason"] or ""), r)

    r = await vsvc.evaluate_voucher(db, "TIDAKADA", 250000)
    check("unknown code → invalid (not crash)", not r["valid"], r)

    # scope: AMBEROUD15 only amber items
    amber_items = [{"product_id": "prd_x", "category": "amber", "unit_price": 685000, "quantity": 1}]
    r = await vsvc.evaluate_voucher(db, "AMBEROUD15", 685000, items=amber_items)
    check("AMBEROUD15 amber items → 15% = 102750", r["valid"] and r["discount"] == 102750, r)
    non_amber = [{"product_id": "prd_y", "category": "floral", "unit_price": 500000, "quantity": 1}]
    r = await vsvc.evaluate_voucher(db, "AMBEROUD15", 500000, items=non_amber)
    check("AMBEROUD15 non-amber items → invalid", not r["valid"], r)

    vl = await vsvc.list_active_vouchers(db)
    codes = {v["code"] for v in vl}
    check("list_active_vouchers excludes EXPIRED2024", "EXPIRED2024" not in codes, codes)
    check("list_active_vouchers includes WELCOME10", "WELCOME10" in codes, codes)
    client.close()


async def http_tests():
    print(f"\n{B}C. HTTP — /api/vouchers/validate + /api/vouchers{X}")
    async with httpx.AsyncClient() as client:
        try:
            r = await client.post(f"{API}/api/vouchers/validate",
                                  json={"code": "WELCOME10", "subtotal": 250000}, timeout=15)
            check("POST validate 200", r.status_code == 200, r.status_code)
            d = r.json()
            check("validate contract keys", all(k in d for k in ("valid", "code", "discount", "reason")), d)
            check("validate WELCOME10 discount 25000", d.get("discount") == 25000, d)
        except Exception as e:
            check("POST validate reachable", False, str(e))

        # adversarial payloads → NEVER 5xx
        adversarials = [
            {"code": 12345, "subtotal": "abc"},
            {"code": None},
            {},
            {"code": "'; DROP TABLE--", "subtotal": -999},
            {"code": "X" * 500, "subtotal": 10**12},
        ]
        no5xx = True
        for payload in adversarials:
            try:
                rr = await client.post(f"{API}/api/vouchers/validate", json=payload, timeout=15)
                if rr.status_code >= 500:
                    no5xx = False
                    print(f"    {R}5xx on {payload}: {rr.status_code}{X}")
            except Exception as e:
                no5xx = False
                print(f"    {R}exc on {payload}: {e}{X}")
        check("adversarial validate never 5xx", no5xx)

        try:
            r = await client.get(f"{API}/api/vouchers", timeout=15)
            check("GET /api/vouchers 200 + array", r.status_code == 200 and isinstance(r.json(), list), r.status_code)
        except Exception as e:
            check("GET /api/vouchers reachable", False, str(e))


async def main():
    print(f"{B}{'='*62}\n  E2 CORE TEST (Pricing SSOT + Voucher)\n{'='*62}{X}")
    unit_tests()
    await db_tests()
    await http_tests()
    print(f"\n{B}{'='*62}{X}\n  {G}PASS {_p['pass']}{X} | {R}FAIL {_p['fail']}{X}\n{B}{'='*62}{X}")
    return 1 if _p["fail"] else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
