#!/usr/bin/env python3
"""test_e6_core.py — POC CORE E6 (Payments). PROVE-BEFORE-BUILD.

  T1 Submit bukti (owner): amount<=0 -> 422; valid -> pending; list (owner).
  T2 Verify approve -> order paid + payment_status lunas + paid_amount==total (SSOT record_payment).
  T3 Idempoten: verify kedua -> 400 (processed); paid_amount TIDAK bertambah (anti double-count, INV-P1).
  T4 Reject: order tetap pending, payment_status belum_bayar, paid_amount 0.
  T5 Parsial (DP): bukti setengah -> dp (tetap pending); bukti sisa -> lunas + paid.
  T6 Terminal guard (INV-P2): verify bukti pada order cancelled -> 400; submit bukti pada terminal -> 400.
  T7 COD: submit bukti -> 400 (cod); cod_fee>0 (INV-10); complete COD -> paid_amount==total & lunas (uang saat kirim).
  T8 IDOR (RC-E10): user lain submit bukti pada order A -> 404.
  T9 Rekonsiliasi (INV-P1): paid_amount == Σ bukti verified.

Self-cleaning. Usage: cd /app && python scripts/test_e6_core.py
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
CUST = {"email": "customer@collectorparfum.id", "password": "Customer#2026"}
ADMIN = {"email": "admin@collectorparfum.id", "password": "Admin#2026"}
G, R, Y, B, X = "\033[92m", "\033[91m", "\033[93m", "\033[1m", "\033[0m"
passed = failed = 0
ADDR = {"name": "Bayar Uji", "phone": "0811", "street": "Jl Uji", "city": "Jakarta",
        "province": "DKI", "postal": "10000", "label": "Rumah"}


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


async def mk_order(c, headers, db, group="transfer", method_id="bca"):
    prod = await db.products.find_one({"status": "active", "volumes.type": ""}) \
        or await db.products.find_one({"status": "active"})
    vol = max([v for v in prod["volumes"] if str(v.get("type", "") or "") == ""] or prod["volumes"],
              key=lambda v: v.get("stock", 0))
    body = {"items": [{"product_id": prod["id"], "variant_type": str(vol.get("type", "") or ""),
                       "volume_ml": vol["ml"], "quantity": 1}],
            "address": ADDR, "shipping_id": "jne-reg",
            "payment": {"group": group, "method_id": method_id}}
    r = await c.post(f"{API}/api/orders", headers=headers, json=body)
    return r.json() if r.status_code == 200 else None


async def main():
    print(f"\n{B}{'='*64}{X}\n  TEST E6 CORE (Payments)  API={API}\n{B}{'='*64}{X}")
    db = AsyncIOMotorClient(MONGO_URL)[DB_NAME]
    codes = []
    async with httpx.AsyncClient() as c:
        try:
            if (await c.get(f"{API}/api/", timeout=5)).status_code >= 500:
                raise Exception()
        except Exception:
            print(f"{R}Backend mati.{X}")
            return 1
        tc = await login(c, CUST)
        ta = await login(c, ADMIN)
        hc = {"Authorization": f"Bearer {tc}"}
        ha = {"Authorization": f"Bearer {ta}"}
        cod_pm = await db.payment_methods.find_one({"group": "cod"})

        # ---------- T1 Submit bukti ----------
        print(f"\n{B}T1 Submit bukti bayar (owner){X}")
        o1 = await mk_order(c, hc, db)
        if not o1:
            bad("gagal buat order T1"); return 1
        codes.append(o1["code"])
        total = o1["total"]
        r = await c.post(f"{API}/api/orders/{o1['code']}/payment-proof", headers=hc, json={"amount": 0})
        ok("amount<=0 → 422 (Pydantic gt=0)") if r.status_code == 422 else bad(f"amount 0 HTTP {r.status_code}")
        r = await c.post(f"{API}/api/orders/{o1['code']}/payment-proof", headers=hc,
                         json={"amount": total, "ref": "TRX-1"})
        p1 = r.json() if r.status_code == 200 else None
        ok("submit bukti valid → status pending") if (p1 and p1["status"] == "pending") else bad(f"submit HTTP {r.status_code} {r.text[:120]}")
        lst = (await c.get(f"{API}/api/orders/{o1['code']}/payment-proofs", headers=hc)).json()
        ok("owner list bukti") if any(x["id"] == p1["id"] for x in lst) else bad("bukti tak ada di list owner")

        # ---------- T2 Verify approve ----------
        print(f"\n{B}T2 Admin verify approve → paid + lunas{X}")
        rv = await c.put(f"{API}/api/admin/payments/{p1['id']}/verify", headers=ha, json={"approve": True})
        od = rv.json() if rv.status_code == 200 else {}
        good = rv.status_code == 200 and od.get("status") == "paid" and od.get("payment_status") == "lunas" and od.get("paid_amount") == total
        ok(f"verify → paid/lunas/paid_amount={total}") if good else bad(f"verify HTTP {rv.status_code} {str(od)[:160]}")

        # ---------- T3 Idempoten ----------
        print(f"\n{B}T3 Idempotensi verifikasi (anti double-count){X}")
        rv2 = await c.put(f"{API}/api/admin/payments/{p1['id']}/verify", headers=ha, json={"approve": True})
        after = await db.orders.find_one({"code": o1["code"]})
        if rv2.status_code == 400 and int(after.get("paid_amount", 0)) == total:
            ok("verify kedua → 400 & paid_amount tak berubah")
        else:
            bad(f"idempotensi bocor: HTTP {rv2.status_code} paid={after.get('paid_amount')}")

        # ---------- T4 Reject ----------
        print(f"\n{B}T4 Reject bukti → order tak berubah{X}")
        o4 = await mk_order(c, hc, db)
        codes.append(o4["code"])
        pr = (await c.post(f"{API}/api/orders/{o4['code']}/payment-proof", headers=hc, json={"amount": o4["total"]})).json()
        rj = await c.put(f"{API}/api/admin/payments/{pr['id']}/verify", headers=ha, json={"approve": False, "note": "buram"})
        od4 = await db.orders.find_one({"code": o4["code"]})
        pf4 = await db.payment_proofs.find_one({"id": pr["id"]})
        if rj.status_code == 200 and od4["status"] == "pending" and od4["payment_status"] == "belum_bayar" \
                and int(od4["paid_amount"]) == 0 and pf4["status"] == "rejected":
            ok("reject → order pending/belum_bayar/paid=0, bukti rejected")
        else:
            bad(f"reject salah: status={od4['status']} ps={od4['payment_status']} paid={od4['paid_amount']} proof={pf4['status']}")

        # ---------- T5 Parsial (DP) ----------
        print(f"\n{B}T5 Pembayaran parsial (DP) → lunas bertahap{X}")
        o5 = await mk_order(c, hc, db)
        codes.append(o5["code"])
        half = o5["total"] // 2
        pa = (await c.post(f"{API}/api/orders/{o5['code']}/payment-proof", headers=hc, json={"amount": half})).json()
        await c.put(f"{API}/api/admin/payments/{pa['id']}/verify", headers=ha, json={"approve": True})
        mid = await db.orders.find_one({"code": o5["code"]})
        step1 = mid["status"] == "pending" and mid["payment_status"] == "dp"
        pb = (await c.post(f"{API}/api/orders/{o5['code']}/payment-proof", headers=hc, json={"amount": o5["total"] - half})).json()
        rvb = await c.put(f"{API}/api/admin/payments/{pb['id']}/verify", headers=ha, json={"approve": True})
        fin = rvb.json()
        if step1 and fin.get("status") == "paid" and fin.get("payment_status") == "lunas":
            ok(f"DP {half} → dp; pelunasan → paid+lunas")
        else:
            bad(f"DP salah: step1={step1} final={fin.get('status')}/{fin.get('payment_status')}")

        # ---------- T6 Terminal guard (INV-P2) ----------
        print(f"\n{B}T6 Guard terminal (INV-P2){X}")
        o6 = await mk_order(c, hc, db)
        codes.append(o6["code"])
        p6 = (await c.post(f"{API}/api/orders/{o6['code']}/payment-proof", headers=hc, json={"amount": o6["total"]})).json()
        await c.post(f"{API}/api/orders/{o6['code']}/cancel", headers=hc)  # jadikan terminal
        rv6 = await c.put(f"{API}/api/admin/payments/{p6['id']}/verify", headers=ha, json={"approve": True})
        ok("verify bukti pada order cancelled → 400") if rv6.status_code == 400 else bad(f"verify terminal HTTP {rv6.status_code}")
        rs6 = await c.post(f"{API}/api/orders/{o6['code']}/payment-proof", headers=hc, json={"amount": 1000})
        ok("submit bukti pada order terminal → 400") if rs6.status_code == 400 else bad(f"submit terminal HTTP {rs6.status_code}")

        # ---------- T7 COD ----------
        print(f"\n{B}T7 COD (uang saat kirim, INV-10){X}")
        if cod_pm:
            o7 = await mk_order(c, hc, db, group="cod", method_id=cod_pm["id"])
            if o7:
                codes.append(o7["code"])
                cod_fee = int(o7.get("cod_fee", 0) or 0)
                ok(f"cod_fee>0 hanya COD (fee={cod_fee})") if cod_fee > 0 else bad(f"cod_fee tidak diterapkan ({cod_fee})")
                rc7 = await c.post(f"{API}/api/orders/{o7['code']}/payment-proof", headers=hc, json={"amount": o7["total"]})
                ok("submit bukti transfer pada COD → 400") if rc7.status_code == 400 else bad(f"COD proof HTTP {rc7.status_code}")
                # jalankan lifecycle COD sampai completed (uang diterima saat kirim)
                for st in ("paid", "packed", "shipped", "completed"):
                    await c.put(f"{API}/api/admin/orders/{o7['code']}/status", headers=ha, json={"status": st})
                fin7 = await db.orders.find_one({"code": o7["code"]})
                if fin7["status"] == "completed" and fin7["payment_status"] == "lunas" and int(fin7["paid_amount"]) == o7["total"]:
                    ok("COD completed → paid_amount==total & lunas (tanpa bukti transfer)")
                else:
                    bad(f"COD completion salah: status={fin7['status']} ps={fin7['payment_status']} paid={fin7['paid_amount']}")
        else:
            print(f"  {Y}(tak ada metode COD di seed — lewati T7){X}")

        # ---------- T8 IDOR ----------
        print(f"\n{B}T8 IDOR bukti bayar (RC-E10){X}")
        o8 = await mk_order(c, hc, db)
        codes.append(o8["code"])
        # admin = user berbeda dari owner (customer) → submit bukti harus 404
        rb = await c.post(f"{API}/api/orders/{o8['code']}/payment-proof", headers=ha, json={"amount": 1000})
        ok("user lain submit bukti pada order A → 404") if rb.status_code == 404 else bad(f"IDOR bocor HTTP {rb.status_code}")

        # ---------- T9 Rekonsiliasi (INV-P1) ----------
        print(f"\n{B}T9 Rekonsiliasi INV-P1{X}")
        vsum = 0
        async for p in db.payment_proofs.find({"order_code": o5["code"], "status": "verified"}):
            vsum += int(p.get("amount", 0) or 0)
        o5doc = await db.orders.find_one({"code": o5["code"]})
        ok(f"paid_amount({o5doc['paid_amount']}) == Σ bukti verified({vsum})") if int(o5doc["paid_amount"]) == vsum else bad(f"rekonsiliasi rusak: {o5doc['paid_amount']} != {vsum}")

        # ---------- Cleanup ----------
        from services import stock
        for code in set(codes):
            o = await db.orders.find_one({"code": code})
            if o:
                if o.get("status") != "cancelled":
                    await stock.restore(db, o.get("items", []))
                await db.orders.delete_one({"code": code})
                await db.payment_proofs.delete_many({"order_code": code})
                await db.voucher_redemptions.delete_many({"order_code": code})

    print(f"\n{B}{'='*64}{X}\n  {G}PASS {passed}{X} | {R}FAIL {failed}{X}\n{B}{'='*64}{X}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
