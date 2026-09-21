#!/usr/bin/env python3
"""verify_data_integrity.py — POST-SEED INTEGRITY GATE (Collector Parfum).

Menangkap bug data yang lolos HTTP 200. WAJIB jalan di DB BERSIH (sesudah seed_reset).
Invarian domain e-commerce (lihat memory/INVARIANTS.md):
  INV-1  order.subtotal == Σ(item.unit_price * qty)
  INV-2  order.total   == subtotal - discount + shipping.price + cod_fee ; total >= 0
  INV-3  order.discount konsisten dgn voucher (percent/flat, capped subtotal)
  INV-4  product: setiap volume.stock >= 0 (anti-oversell) & price > 0
  INV-5  order.payment_status derivasi konsisten dgn paid_amount vs total
  INV-6  order.status ∈ himpunan sah
  INV-7  order.code UNIK (number-series)
  INV-8  order.items[].product_id → products (FK) [dicek juga verify_schema]
  INV-9  voucher.type ∈ {percent,flat} & value > 0 (percent 1..100)
  INV-10 cod_fee > 0 hanya bila payment.group == 'cod'
  INV-11 shipping_methods.price >= 0 ; payment_methods.fee >= 0
Concept must_have_data=False = belum diseed di fase fondasi (produk/order) — dilewati mulus.
Usage: cd /app && python scripts/verify_data_integrity.py
Exit 0 = valid. !=0 = INTEGRITY VIOLATION.
"""
import asyncio
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
try:
    from dotenv import load_dotenv
    load_dotenv(ROOT / "backend" / ".env")
except Exception:
    pass
from motor.motor_asyncio import AsyncIOMotorClient  # noqa: E402

sys.path.insert(0, str(ROOT / "backend"))
from services.pricing import compute_pricing, voucher_discount  # noqa: E402  (PRICING SSOT — referensi tunggal)

G, Y, R, C, B, X = "\033[92m", "\033[93m", "\033[91m", "\033[96m", "\033[1m", "\033[0m"
MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "collector_parfum")
ORDER_STATUSES = {"pending", "paid", "packed", "shipped", "completed", "cancelled"}
results = {"pass": 0, "fail": 0, "warn": 0}


@dataclass
class Concept:
    name: str
    canonical: str
    must_have_data: bool = True
    legacy_must_be_empty: list = field(default_factory=list)


CONCEPTS = [
    Concept("users", "users", True, ["customer", "customers", "staff"]),
    Concept("categories", "categories", True, ["category", "kategori"]),
    Concept("vouchers", "vouchers", True, ["voucher", "promo", "promos", "coupons"]),
    Concept("shipping_methods", "shipping_methods", True, ["shipping", "couriers", "ongkir"]),
    Concept("payment_methods", "payment_methods", True, ["payment", "payments"]),
    Concept("settings", "settings", True, ["config", "configuration"]),
    Concept("counters", "counters", True, ["counter", "sequences"]),
    # Fase business-logic (belum diseed di fondasi):
    Concept("products", "products", False, ["product", "items", "catalog", "parfums", "perfumes"]),
    Concept("orders", "orders", False, ["order", "pesanan", "transactions", "checkout"]),
    Concept("addresses", "addresses", False, ["address", "alamat"]),
    Concept("reviews", "reviews", False, ["review", "testimonials", "ulasan"]),
    Concept("wishlists", "wishlists", False, ["wishlist", "favorites"]),
    Concept("carts", "carts", False, ["cart", "basket"]),
    Concept("voucher_redemptions", "voucher_redemptions", False, []),  # E2: ditulis E3 saat order dibuat
    Concept("media_assets", "media_assets", False, []),  # E5: media library (referensi URL)
    Concept("audit_logs", "audit_logs", False, []),      # E5: jejak audit (INV-M1)
    Concept("payment_proofs", "payment_proofs", False, []),  # E6: bukti bayar (verifikasi manual)
    Concept("analytics_events", "analytics_events", False, []),  # E7: event first-party (read-mostly)
    Concept("content", "content", True, []),  # E9: CMS section (default ter-seed → wajib ada)
    Concept("content_revisions", "content_revisions", False, []),  # E9+: history revisi CMS
]


def line(tag, color, msg, detail=""):
    print(f"  {color}[{tag}]{X} {msg}" + (f"  {color}{detail}{X}" if detail else ""))


def _report(name, violators, total):
    if violators:
        results["fail"] += 1
        line("FAIL", R, f"{name}", f"{len(violators)}/{total} langgar: {violators[:5]}")
    else:
        results["pass"] += 1
        line("PASS", G, f"{name}", f"({total} diperiksa)")


async def layer_recon(db):
    print(f"\n{C}{B}L1 — Rekonsiliasi koleksi (DB clean-seed){X}")
    for c in CONCEPTS:
        n = await db[c.canonical].count_documents({})
        if c.must_have_data and n == 0:
            results["fail"] += 1
            line("FAIL", R, f"{c.name}: '{c.canonical}' KOSONG", "→ seed GAP / DRIFT")
        else:
            results["pass"] += 1
            suffix = "" if c.must_have_data else " (opsional fase fondasi)"
            line("PASS", G, f"{c.name}: '{c.canonical}' = {n} dok{suffix}")
        for legacy in c.legacy_must_be_empty:
            if legacy == c.canonical:
                continue
            ln = await db[legacy].count_documents({})
            if ln > 0:
                results["fail"] += 1
                line("FAIL", R, f"{c.name}: koleksi alias '{legacy}' berisi {ln} dok", "→ DRIFT AKTIF")


async def layer_config(db):
    print(f"\n{C}{B}L2 — Invarian konfigurasi (voucher/shipping/payment){X}")
    vouchers = await db.vouchers.find({}, {"_id": 0}).to_list(1000)
    bad_v = []
    for v in vouchers:
        t, val = v.get("type"), v.get("value", 0)
        if t not in {"percent", "flat", "free_shipping"} or not isinstance(val, (int, float)) or val <= 0:
            bad_v.append(v.get("code"))
        elif t == "percent" and not (1 <= val <= 100):
            bad_v.append(v.get("code"))
    _report("INV-9 voucher.type/value sah (percent/flat/free_shipping)", bad_v, len(vouchers))

    # INV-9b: bound limit voucher (anti negative — RC-E12)
    bad_lim = [v.get("code") for v in vouchers
               if int(v.get("usage_limit", 0) or 0) < 0 or int(v.get("per_user_limit", 0) or 0) < 0
               or int(v.get("used_count", 0) or 0) < 0 or int(v.get("min_spend", 0) or 0) < 0]
    _report("INV-9b voucher limit/min_spend >= 0", bad_lim, len(vouchers))

    ships = await db.shipping_methods.find({}, {"_id": 0}).to_list(1000)
    _report("INV-11a shipping.price >= 0",
            [s.get("id") for s in ships if int(s.get("price", 0) or 0) < 0], len(ships))

    pays = await db.payment_methods.find({}, {"_id": 0}).to_list(1000)
    bad_p = [p.get("id") for p in pays
             if int(p.get("fee", 0) or 0) < 0 or p.get("group") not in {"transfer", "ewallet", "cod"}]
    _report("INV-11b payment.fee>=0 & group sah", bad_p, len(pays))


async def layer_products(db):
    prods = await db.products.find({}, {"_id": 0}).to_list(10000)
    if not prods:
        print(f"\n{C}{B}L3 — Invarian produk{X}")
        print(f"  {Y}(belum ada produk — fase business-logic){X}")
        return
    print(f"\n{C}{B}L3 — Invarian produk{X}")
    bad_stock, bad_price = [], []
    for p in prods:
        vols = p.get("volumes") or []
        if any(int(v.get("stock", 0) or 0) < 0 for v in vols):
            bad_stock.append(p.get("slug"))
        if any(int(v.get("price", 0) or 0) <= 0 for v in vols) or int(p.get("price", 0) or 0) <= 0:
            bad_price.append(p.get("slug"))
    _report("INV-4a product volume.stock >= 0", bad_stock, len(prods))
    _report("INV-4b product price > 0", bad_price, len(prods))

    # --- E1 Catalog invariants (varian = matriks (type, ml)) ---
    badC1, badC2 = [], []
    for p in prods:
        vols = p.get("volumes") or []
        keys = [(str(v.get("type", "") or ""), v.get("ml")) for v in vols]
        if len(vols) < 1 or len(keys) != len(set(keys)):
            badC1.append(p.get("slug"))
        cap = p.get("compare_at_price")
        if cap is not None and int(cap or 0) <= int(p.get("price", 0) or 0):
            badC2.append(p.get("slug"))
    _report("INV-C1 product punya >=1 varian & (type,ml) unik", badC1, len(prods))
    _report("INV-C2 compare_at_price null atau > price", badC2, len(prods))


async def layer_reviews(db):
    prods = await db.products.find({}, {"_id": 0, "id": 1, "rating_avg": 1, "rating_count": 1}).to_list(10000)
    reviews = await db.reviews.find({}, {"_id": 0}).to_list(20000)
    print(f"\n{C}{B}L5 — Invarian review/rating (E1){X}")
    if not prods and not reviews:
        print(f"  {Y}(belum ada produk/review — fase business-logic){X}")
        return
    prod_ids = {p["id"] for p in prods}

    # INV-8: review.product_id (bila diset) -> products.id
    badFK = [r.get("id") for r in reviews
             if r.get("product_id") and r.get("product_id") not in prod_ids]
    _report("INV-8 review.product_id -> products (FK)", badFK, len(reviews))

    # INV-C3: rating_avg == mean(published reviews), rating_count == count
    pub = {}
    for r in reviews:
        if r.get("status") == "published" and r.get("product_id"):
            pub.setdefault(r["product_id"], []).append(int(r.get("rating", 0) or 0))
    badC3 = []
    for p in prods:
        arr = pub.get(p["id"], [])
        exp_cnt = len(arr)
        exp_avg = round(sum(arr) / exp_cnt, 1) if exp_cnt else 0.0
        cur_cnt = int(p.get("rating_count", 0) or 0)
        cur_avg = round(float(p.get("rating_avg", 0) or 0), 1)
        if cur_cnt != exp_cnt or abs(cur_avg - exp_avg) > 0.05:
            badC3.append(p["id"])
    _report("INV-C3 rating_avg/count == mean published reviews", badC3, len(prods))


def _expected_discount(subtotal, voucher, shipping_price=0):
    """Referensi diskon via PRICING SSOT (services.pricing.voucher_discount).
    Checkout (E3) & verifier ini WAJIB memakai formula yang sama (anti RC-E1/E2)."""
    return voucher_discount(voucher, subtotal, shipping_price)


async def layer_orders(db):
    orders = await db.orders.find({}, {"_id": 0}).to_list(20000)
    print(f"\n{C}{B}L4 — Invarian order (referensi: services.pricing SSOT){X}")
    if not orders:
        print(f"  {Y}(belum ada order — fase business-logic){X}")
        return
    vouchers = {v["code"]: v for v in await db.vouchers.find({}, {"_id": 0}).to_list(1000)}
    prod_cat = {p["id"]: p.get("category")
                for p in await db.products.find({}, {"id": 1, "category": 1, "_id": 0}).to_list(20000)}

    def _eligible_subtotal(voucher, items, full_subtotal):
        """Subtotal item yang MEMENUHI scope voucher (scope-aware INV-3, E3).
        Item snapshot punya `category`; fallback ke products map bila absen."""
        scope = (voucher or {}).get("scope") or {}
        cat = scope.get("category")
        pids = set(scope.get("product_ids") or [])
        if not (cat or pids):
            return full_subtotal
        total = 0
        for it in items:
            it_cat = it.get("category") or prod_cat.get(it.get("product_id"))
            if (cat and it_cat == cat) or (it.get("product_id") in pids):
                total += int(it.get("unit_price", 0) or 0) * int(it.get("quantity", 0) or 0)
        return total

    v1, v2, v3, v5, v6, v10 = [], [], [], [], [], []
    codes = {}
    for o in orders:
        code = o.get("code", o.get("id"))
        codes[code] = codes.get(code, 0) + 1
        items = o.get("items", [])
        subtotal = sum(int(i.get("unit_price", 0) or 0) * int(i.get("quantity", 0) or 0) for i in items)
        if subtotal != int(o.get("subtotal", 0) or 0):
            v1.append(code)
        ship = int((o.get("shipping") or {}).get("price", 0) or 0)
        cod_fee = int(o.get("cod_fee", 0) or 0)
        disc = int(o.get("discount", 0) or 0)
        total = int(o.get("subtotal", 0) or 0) - disc + ship + cod_fee
        if total != int(o.get("total", 0) or 0) or int(o.get("total", 0) or 0) < 0:
            v2.append(code)
        # INV-3: diskon tersimpan == PRICING SSOT (voucher_discount) atas subtotal ELIGIBLE (scope-aware).
        vc = o.get("voucher_code")
        if vc:
            voucher = vouchers.get(vc)
            eligible = _eligible_subtotal(voucher, items, int(o.get("subtotal", 0) or 0))
            ref_disc = voucher_discount(voucher, eligible, ship)
            if disc != ref_disc:
                v3.append(code)
        paid = int(o.get("paid_amount", 0) or 0)
        tot = int(o.get("total", 0) or 0)
        exp_ps = "belum_bayar" if paid <= 0 else ("lunas" if paid >= tot and tot > 0 else "dp")
        if o.get("payment_status") != exp_ps:
            v5.append(code)
        if o.get("status") not in ORDER_STATUSES:
            v6.append(code)
        grp = (o.get("payment") or {}).get("group")
        if cod_fee > 0 and grp != "cod":
            v10.append(code)
    _report("INV-1 subtotal == Σ(unit_price*qty)", v1, len(orders))
    _report("INV-2 total == subtotal-discount+ship+cod & >=0", v2, len(orders))
    _report("INV-3 discount == voucher_discount SSOT (scope-aware)", v3, len(orders))
    _report("INV-5 payment_status derivasi", v5, len(orders))
    _report("INV-6 status ∈ enum", v6, len(orders))
    _report("INV-10 cod_fee>0 hanya bila COD", v10, len(orders))
    dup = [c for c, n in codes.items() if n > 1]
    _report("INV-7 order.code UNIK", dup, len(orders))


async def layer_redemptions(db):
    """L6 — Invarian voucher_redemptions (E2; ditulis E3 saat order dibuat)."""
    reds = await db.voucher_redemptions.find({}, {"_id": 0}).to_list(20000)
    print(f"\n{C}{B}L6 — Invarian voucher_redemptions (E2){X}")
    if not reds:
        print(f"  {Y}(belum ada redemption — aktif penuh saat order dibuat di E3){X}")
        return
    codes = {v["code"] for v in await db.vouchers.find({}, {"code": 1, "_id": 0}).to_list(1000)}
    order_codes = {o["code"] for o in await db.orders.find({}, {"code": 1, "_id": 0}).to_list(20000)}
    bad_fk = [r.get("id") for r in reds if r.get("voucher_code") not in codes]
    _report("INV-R1 redemption.voucher_code -> vouchers (FK)", bad_fk, len(reds))
    bad_ord = [r.get("id") for r in reds if r.get("order_code") not in order_codes]
    _report("INV-R2 redemption.order_code -> orders (FK)", bad_ord, len(reds))
    bad_disc = [r.get("id") for r in reds if int(r.get("discount", 0) or 0) < 0]
    _report("INV-R3 redemption.discount >= 0", bad_disc, len(reds))


async def layer_account(db):
    """L7 — Invarian akun pelanggan (E4): alamat & wishlist."""
    print(f"\n{C}{B}L7 — Invarian akun (alamat & wishlist, E4){X}")
    user_ids = {u["id"] for u in await db.users.find({}, {"id": 1, "_id": 0}).to_list(20000)}
    prod_ids = {p["id"] for p in await db.products.find({}, {"id": 1, "_id": 0}).to_list(20000)}

    addresses = await db.addresses.find({}, {"_id": 0}).to_list(20000)
    if addresses:
        # INV-A1: <= 1 alamat default per user
        by_user = {}
        for a in addresses:
            if a.get("is_default"):
                by_user[a.get("user_id")] = by_user.get(a.get("user_id"), 0) + 1
        multi_default = [u for u, n in by_user.items() if n > 1]
        _report("INV-A1 <=1 alamat default per user", multi_default, len(addresses))
        bad_owner = [a.get("id") for a in addresses if a.get("user_id") not in user_ids]
        _report("INV-A2a address.user_id -> users (FK)", bad_owner, len(addresses))
    else:
        print(f"  {Y}(belum ada alamat){X}")

    wishlists = await db.wishlists.find({}, {"_id": 0}).to_list(20000)
    if wishlists:
        bad_wowner = [w.get("id") for w in wishlists if w.get("user_id") not in user_ids]
        _report("INV-A2b wishlist.user_id -> users (FK)", bad_wowner, len(wishlists))
        dup = [w.get("id") for w in wishlists
               if len(w.get("product_ids", [])) != len(set(w.get("product_ids", [])))]
        _report("INV-A3a wishlist.product_ids UNIK (dedupe)", dup, len(wishlists))
        dangling = [w.get("id") for w in wishlists
                    if any(pid not in prod_ids for pid in w.get("product_ids", []))]
        _report("INV-A3b wishlist.product_ids -> products (FK)", dangling, len(wishlists))
        # user_id unik per wishlist (satu wishlist per user)
        seen = {}
        for w in wishlists:
            seen[w.get("user_id")] = seen.get(w.get("user_id"), 0) + 1
        multi_w = [u for u, n in seen.items() if n > 1]
        _report("INV-A3c <=1 wishlist per user", multi_w, len(wishlists))
    else:
        print(f"  {Y}(belum ada wishlist){X}")


async def layer_audit(db):
    """L8 — Invarian audit & media (E5). INV-M1: setiap entri audit terstruktur benar.

    Audit best-effort (tak boleh menggagalkan request), tetapi ENTRI yang tertulis WAJIB
    punya actor_id/action/entity (jejak yang bisa diaudit). Media = referensi URL (V1).
    """
    print(f"\n{C}{B}L8 — Invarian audit & media (E5){X}")
    logs = await db.audit_logs.find({}, {"_id": 0}).to_list(50000)
    if logs:
        bad = [row.get("id") for row in logs
               if not row.get("actor_id") or not row.get("action") or not row.get("entity")]
        _report("INV-M1 audit_logs terstruktur (actor/action/entity)", bad, len(logs))
    else:
        print(f"  {Y}(belum ada audit_logs — terisi saat aksi admin/otentikasi terjadi){X}")

    media = await db.media_assets.find({}, {"_id": 0}).to_list(20000)
    if media:
        bad_m = [m.get("id") for m in media
                 if not m.get("url") or m.get("kind") not in {"image", "video"}]
        _report("INV-M4 media_assets punya url & kind sah", bad_m, len(media))
    else:
        print(f"  {Y}(belum ada media_assets){X}")


async def layer_payments(db):
    """L9 — Invarian pembayaran (E6). INV-P1 rekonsiliasi & INV-P2 terminal.

    - Bukti terstruktur: order_code (FK ada), amount>0, status sah.
    - INV-P1 (non-COD): paid_amount == Σ bukti `verified` (uang tak muncul dari udara).
    - INV-P2: tak ada bukti `verified` pada order `cancelled`.
    """
    print(f"\n{C}{B}L9 — Invarian pembayaran (E6){X}")
    proofs = await db.payment_proofs.find({}, {"_id": 0}).to_list(50000)
    orders = await db.orders.find({}, {"_id": 0}).to_list(50000)
    by_code = {o.get("code"): o for o in orders}

    bad_struct = [p.get("id") for p in proofs
                  if not p.get("order_code") or int(p.get("amount", 0) or 0) <= 0
                  or p.get("status") not in {"pending", "verified", "rejected"}
                  or p.get("order_code") not in by_code]
    _report("bukti bayar terstruktur (FK/amount/status)", bad_struct, len(proofs))

    # INV-P1: rekonsiliasi paid_amount (kecualikan COD — uang tunai tanpa bukti transfer)
    verified_sum = {}
    for p in proofs:
        if p.get("status") == "verified":
            verified_sum[p["order_code"]] = verified_sum.get(p["order_code"], 0) + int(p.get("amount", 0) or 0)
    v_recon = []
    for o in orders:
        if (o.get("payment") or {}).get("group") == "cod":
            continue
        if int(o.get("paid_amount", 0) or 0) != verified_sum.get(o.get("code"), 0):
            v_recon.append(o.get("code"))
    _report("INV-P1 paid_amount == Σ bukti verified (non-COD)", v_recon, len(orders))

    # INV-P2: tak ada bukti verified pada order cancelled
    v_term = [p.get("id") for p in proofs
              if p.get("status") == "verified"
              and (by_code.get(p.get("order_code"), {}) or {}).get("status") == "cancelled"]
    _report("INV-P2 tak ada bukti verified pada order cancelled", v_term, len(proofs))


async def layer_growth(db):
    """L10 — Invarian pertumbuhan/analitik (E7).

    INV-G1: event `purchase` tak mengarang order (order_code -> orders).
    INV-G3: event analitik bebas-PII (tak simpan email/telepon di meta/session_hint).
    INV-G4: setiap produk/kategori AKTIF punya SEO title (tersedia atau ter-default via name).
    (INV-G2 arsitektural: segmen CRM diturunkan dari orders — tak ada koleksi terpisah.)
    """
    print(f"\n{C}{B}L10 — Invarian growth & analytics (E7){X}")
    events = await db.analytics_events.find({}, {"_id": 0}).to_list(50000)
    order_codes = {o.get("code") for o in await db.orders.find({}, {"code": 1, "_id": 0}).to_list(50000)}
    if events:
        bad_g1 = [e.get("id") for e in events
                  if e.get("type") == "purchase" and e.get("order_code")
                  and e.get("order_code") not in order_codes]
        _report("INV-G1 purchase event.order_code -> orders", bad_g1, len(events))

        def _has_pii(e):
            blob = str(e.get("session_hint") or "")
            meta = e.get("meta") or {}
            if isinstance(meta, dict):
                for k, v in meta.items():
                    blob += f"|{k}={v}"
                    if any(p in str(k).lower() for p in ("email", "phone", "telepon", "password")):
                        return True
            return "@" in blob
        bad_g3 = [e.get("id") for e in events if _has_pii(e)]
        _report("INV-G3 analytics events bebas-PII", bad_g3, len(events))
    else:
        print(f"  {Y}(belum ada analytics_events — aktif penuh saat storefront mengirim event){X}")

    prods = await db.products.find({"status": "active"}, {"_id": 0, "name": 1, "seo": 1}).to_list(20000)
    bad_g4p = [i for i, p in enumerate(prods)
               if not ((p.get("seo") or {}).get("title") or p.get("name"))]
    _report("INV-G4a produk aktif punya SEO title/fallback", bad_g4p, len(prods))
    cats = await db.categories.find({"active": True}, {"_id": 0, "name": 1, "seo": 1}).to_list(2000)
    bad_g4c = [i for i, c in enumerate(cats)
               if not ((c.get("seo") or {}).get("title") or c.get("name"))]
    _report("INV-G4b kategori aktif punya SEO title/fallback", bad_g4c, len(cats))


async def layer_cms(db):
    """L11 — Invarian CMS storefront (E9).

    INV-C1: setiap section kanonik punya dokumen (default ter-seed).
    INV-C2: data tersimpan hanya berisi field yang dikenal skema (anti-injection).
    """
    print(f"\n{C}{B}L11 — Invarian storefront CMS (E9){X}")
    try:
        from content_registry import SECTIONS, SECTION_MAP
    except Exception as e:
        print(f"  {Y}(content_registry tak dapat diimpor: {e}){X}")
        return
    docs = await db.content.find({}, {"_id": 0, "id": 1, "data": 1}).to_list(500)
    have = {d["id"] for d in docs}
    missing = [s["key"] for s in SECTIONS if s["key"] not in have]
    _report("INV-C1 setiap section punya dokumen", missing, len(SECTIONS))
    bad_c2 = []
    for d in docs:
        sec = SECTION_MAP.get(d["id"])
        if not sec:
            bad_c2.append(d["id"])
            continue
        allowed = {f["name"] for f in sec["fields"]}
        extra = [k for k in (d.get("data") or {}) if k not in allowed]
        if extra:
            bad_c2.append(f"{d['id']}:{extra}")
    _report("INV-C2 data hanya field skema (anti-injection)", bad_c2, len(docs))


async def main():
    print(f"\n{B}{'='*62}{X}\n  DATA INTEGRITY (DB: {DB_NAME})\n{B}{'='*62}{X}")
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    await layer_recon(db)
    await layer_config(db)
    await layer_products(db)
    await layer_reviews(db)
    await layer_orders(db)
    await layer_redemptions(db)
    await layer_account(db)
    await layer_audit(db)
    await layer_payments(db)
    await layer_growth(db)
    await layer_cms(db)
    client.close()
    print(f"\n{B}{'='*62}{X}\n  {G}PASS {results['pass']}{X} | {Y}WARN {results['warn']}{X} | {R}FAIL {results['fail']}{X}\n{B}{'='*62}{X}")
    if results["fail"]:
        print(f"  {R}{B}INTEGRITY VIOLATION.{X}\n")
        return 1
    print(f"  {G}{B}INTEGRITY OK.{X}\n")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
