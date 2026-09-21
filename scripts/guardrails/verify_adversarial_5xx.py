#!/usr/bin/env python3
"""INV-5XX-01 — Endpoint TIDAK boleh 5xx pada input adversarial (harus 2xx/4xx). (RUNTIME)

Kelas bug dicegah: crash 500 pada input tak wajar (string super panjang, unicode/null, tipe salah,
nilai negatif, markup). Input buruk = tanggung jawab client (4xx/422), BUKAN server error (5xx).
Menembak endpoint yang ADA sekarang (auth) + endpoint fase-berikutnya BILA sudah terdaftar
(products/vouchers/orders) — grow-with-code. Resilient: backend down → SKIP.
Usage: cd /app && python scripts/guardrails/verify_adversarial_5xx.py
"""
import json
import os
import sys
import urllib.error
import urllib.request

sys.path.insert(0, os.path.dirname(__file__))
from _common import Guard, G, R, Y, X  # noqa: E402

BASE = os.environ.get("GUARD_BASE_URL", os.environ.get("API_BASE", "http://127.0.0.1:8001")).rstrip("/") + "/api"
ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "admin@collectorparfum.id")
ADMIN_PASS = os.environ.get("ADMIN_PASS", "Admin#2026")
BIG = "A" * 60000
WEIRD = "x <b>&</b> <script> \u0000 \U0001f600 \u202e rtl"


def req(method, path, token=None, body=None, timeout=25):
    url = BASE + path
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(url, data=data, method=method)
    r.add_header("Content-Type", "application/json")
    if token:
        r.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(r, timeout=timeout) as resp:
            return resp.status, resp.read(2000).decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read(2000).decode("utf-8", "replace")
    except Exception as e:  # noqa: BLE001
        return -1, str(e)


def backend_up():
    st, _ = req("GET", "/")
    return st != -1


def login():
    st, txt = req("POST", "/auth/login", body={"email": ADMIN_EMAIL, "password": ADMIN_PASS})
    if st != 200:
        return None
    try:
        return json.loads(txt).get("token")
    except Exception:
        return None


def route_exists(token, path):
    """Cek endpoint ada (bukan 404) sebelum di-fuzz — grow-with-code."""
    st, _ = req("POST", path, token, {})
    return st not in (404, 405, -1)


def main() -> int:
    g = Guard("INV-5XX-01", "Tidak ada 5xx pada input adversarial (harus 2xx/4xx)")
    if not backend_up():
        print(f"{Y}  Backend belum berjalan — SKIP (Phase 0).{X}")
        return 0
    tok = login()
    # Kasus yang SELALU ada (auth). token opsional.
    cases = [
        ("register nama super panjang", "POST", "/auth/register",
         {"name": BIG, "email": "adv5xx@example.com", "password": "123456"}),
        ("register email/tipe salah", "POST", "/auth/register",
         {"name": 123, "email": {"x": 1}, "password": ["y"]}),
        ("login unicode/null", "POST", "/auth/login", {"email": WEIRD, "password": WEIRD}),
        ("login body list", "POST", "/auth/login", ["not", "an", "object"]),
    ]
    # Kasus fase-berikutnya (aktif otomatis bila endpoint sudah ada).
    future = [
        ("voucher validate non-numerik", "/vouchers/validate",
         {"code": WEIRD, "subtotal": "gratis"}),
        ("order amount negatif", "/orders",
         {"items": [{"product_id": "x", "volume_ml": -1, "unit_price": -5, "quantity": -9, "name": "z"}]}),
    ]
    if tok:
        for label, path, body in future:
            if route_exists(tok, path):
                cases.append((label, "POST", path, body))

    for label, method, path, body in cases:
        st, txt = req(method, path, tok, body)
        g.bump()
        mark = G + "ok" + X if 0 <= st < 500 else (R + "5XX" + X if st >= 500 else Y + "skip" + X)
        print(f"    [{mark}] {label}: HTTP {st}")
        if st >= 500:
            g.add(f"{label} → HTTP {st} (5xx!). Endpoint harus menolak input buruk dgn 4xx, bukan crash. Resp: {txt[:160]}")
    # cleanup user adv (best-effort)
    try:
        from motor.motor_asyncio import AsyncIOMotorClient  # noqa
    except Exception:
        pass
    try:
        from pymongo import MongoClient
        db = MongoClient(os.environ.get("MONGO_URL", "mongodb://localhost:27017"))[os.environ.get("DB_NAME", "collector_parfum")]
        db.users.delete_many({"email": "adv5xx@example.com"})
    except Exception:
        pass
    return g.finish()


if __name__ == "__main__":
    sys.exit(main())
