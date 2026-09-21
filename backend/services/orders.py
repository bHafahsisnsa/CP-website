"""services/orders.py — SSOT ORDER LIFECYCLE + CREATE (Epic E3).

Pusat kebenaran alur pesanan:
  - create_order(): validasi → snapshot item → pricing SSOT (services.pricing) →
    stok atomik (services.stock) → redemption voucher atomik → kode unik (counters) → insert.
  - transition_order(): SATU-SATUNYA mutator status; `LEGAL_TRANSITIONS` = SSOT (docs/06).
    Transisi ilegal → InvalidTransition (400). cancel → kembalikan stok (RC-E6).
  - derive_payment_status(): INV-5 (belum_bayar/dp/lunas) — status TAK memaksa lunas (RC-E4).

Keputusan desain E3 (didokumentasikan):
  - Diskon voucher dihitung ulang server-side via services.vouchers.evaluate_voucher
    (scope-aware, SATU rumus dgn E2). Total NEVER dipercayakan ke klien (RC-E1).
  - Voucher DIANGGAP terpakai saat order dibuat (used_count++ + voucher_redemptions).
    Cancel mengembalikan STOK (bukan voucher) agar CE1 tetap konsisten
    (used_count == #orders-pakai-voucher == #redemptions). Refund voucher = epik lanjutan.
"""
from core_utils import money, new_id, next_sequence, now_iso, safe_doc
from services import stock
from services.order_helpers import (  # re-export: API publik modul ini TIDAK berubah
    InvalidTransition,
    OrderError,
    StockConflict,
    _build_snapshot,
    _claim_per_user_voucher,
    _clean_address,
    _release_per_user_voucher,
    derive_payment_status,
)
from services.pricing import compute_subtotal
from services.vouchers import evaluate_voucher

LEGAL_TRANSITIONS = {
    "pending": {"paid", "cancelled"},
    "paid": {"packed", "cancelled"},
    "packed": {"shipped", "cancelled"},
    "shipped": {"completed"},
    "completed": set(),
    "cancelled": set(),
}
TERMINAL = {"completed", "cancelled"}


async def create_order(db, *, user, items_in, address, shipping_id, payment, voucher_code=None, note=""):
    """Buat order (SSOT). Guest diperbolehkan (user=None). Semua angka dihitung server."""
    if not items_in:
        raise OrderError("Keranjang kosong")

    # 1) Metode kirim & bayar harus valid.
    ship = await db.shipping_methods.find_one({"id": shipping_id, "active": True})
    if not ship:
        raise OrderError("Metode pengiriman tidak valid")
    grp = (payment or {}).get("group")
    method_id = (payment or {}).get("method_id")
    pay = await db.payment_methods.find_one({"id": method_id, "group": grp, "active": True})
    if not pay:
        raise OrderError("Metode pembayaran tidak valid")

    # 2) Snapshot item + subtotal (server-authoritative).
    items = await _build_snapshot(db, items_in)
    subtotal = compute_subtotal(items)
    shipping_price = money(ship.get("price", 0))
    cod_fee = money(pay.get("fee", 0)) if grp == "cod" else 0

    # 3) Voucher (opsional) — evaluasi ulang server-side (scope-aware, SATU rumus E2).
    discount = 0
    v_code = None
    if voucher_code:
        ev = await evaluate_voucher(
            db, code=voucher_code, subtotal=subtotal, shipping=shipping_price,
            user_id=(user or {}).get("id"), items=items,
        )
        if not ev.get("valid"):
            raise OrderError(ev.get("reason") or "Voucher tidak berlaku")
        discount = money(ev.get("discount", 0))
        v_code = ev.get("code")

    total = max(0, subtotal - discount + shipping_price + cod_fee)

    # 4) Stok atomik (anti-oversell). Gagal → 409.
    ok, failed = await stock.decrement(db, items)
    if not ok:
        avail = await stock.available_stock(db, failed.get("product_id"), failed.get("sku"))
        raise StockConflict(failed, available=avail)

    # 5) Redemption voucher ATOMIK. Global usage_limit + per-user limit (race-safe).
    per_user_claimed = False
    if v_code:
        res = await db.vouchers.update_one(
            {"code": v_code, "$expr": {"$or": [
                {"$eq": [{"$ifNull": ["$usage_limit", 0]}, 0]},
                {"$lt": [{"$ifNull": ["$used_count", 0]}, {"$ifNull": ["$usage_limit", 0]}]},
            ]}},
            {"$inc": {"used_count": 1}},
        )
        if res.modified_count != 1:
            await stock.restore(db, items)
            raise OrderError("Kuota voucher telah habis")

        # 5b) Batas PER-USER (race-safe, RC-E2). Hanya untuk user login — guest tak terikat.
        uid = (user or {}).get("id")
        vdoc = await db.vouchers.find_one({"code": v_code}) or {}
        per_user_limit = int(vdoc.get("per_user_limit", 0) or 0)
        if uid and per_user_limit > 0:
            per_user_claimed = await _claim_per_user_voucher(db, v_code, uid, per_user_limit)
            if not per_user_claimed:
                # Kompensasi global usage_limit + stok, lalu tolak (400).
                await db.vouchers.update_one(
                    {"code": v_code, "used_count": {"$gt": 0}},
                    {"$inc": {"used_count": -1}},
                )
                await stock.restore(db, items)
                raise OrderError("Batas pemakaian voucher ini sudah tercapai")

    # 6) Kode unik + insert order. Bila gagal → kompensasi stok + voucher.
    try:
        code = await next_sequence(db, "orders", "CP", 8)
        order = {
            "id": new_id("ord"),
            "code": code,
            "user_id": (user or {}).get("id"),
            "items": items,
            "subtotal": subtotal,
            "discount": discount,
            "voucher_code": v_code,
            "shipping": {"method_id": ship["id"], "name": ship.get("name", ""),
                         "price": shipping_price, "eta": ship.get("eta", "")},
            "payment": {"group": grp, "method_id": method_id, "name": pay.get("name", "")},
            "cod_fee": cod_fee,
            "total": total,
            "paid_amount": 0,
            "address": _clean_address(address),
            "note": (note or "")[:500],
            "status": "pending",
            "payment_status": "belum_bayar",
            "created_at": now_iso(),
            "updated_at": now_iso(),
        }
        await db.orders.insert_one(order)
        if v_code:
            await db.voucher_redemptions.insert_one({
                "id": new_id("vrd"),
                "voucher_code": v_code,
                "user_id": (user or {}).get("id"),
                "order_code": code,
                "discount": discount,
                "created_at": now_iso(),
            })
    except Exception:
        await stock.restore(db, items)
        if v_code:
            await db.vouchers.update_one({"code": v_code, "used_count": {"$gt": 0}},
                                        {"$inc": {"used_count": -1}})
            if per_user_claimed:
                await _release_per_user_voucher(db, v_code, (user or {}).get("id"))
        raise
    return safe_doc(order)


async def transition_order(db, order, to_status):
    """SATU-SATUNYA mutator status. Menegakkan LEGAL_TRANSITIONS + efek samping.

    - Transisi di luar whitelist → InvalidTransition (RC-E7/E8).
    - to=cancelled → kembalikan stok (RC-E6).
    - payment_status SELALU diturunkan dari paid_amount (INV-5) — tak dipaksa lunas (RC-E4).
    """
    frm = order.get("status")
    if to_status not in LEGAL_TRANSITIONS.get(frm, set()):
        raise InvalidTransition(f"Transisi ilegal: {frm} -> {to_status}")

    if to_status == "cancelled":
        await stock.restore(db, order.get("items", []))

    paid = money(order.get("paid_amount", 0))
    total = money(order.get("total", 0))
    # COD: uang tunai DITERIMA saat barang sampai (completed) → lunasi (INV-5 tetap DERIVASI,
    #      bukan hand-set: paid_amount dinaikkan ke total lalu payment_status diturunkan).
    if to_status == "completed" and (order.get("payment") or {}).get("group") == "cod" and paid < total:
        paid = total

    payment_status = derive_payment_status(paid, total)
    updates = {"status": to_status, "paid_amount": paid,
               "payment_status": payment_status, "updated_at": now_iso()}
    await db.orders.update_one({"code": order["code"]}, {"$set": updates})
    order.update(updates)
    return safe_doc(order)


async def record_payment(db, order, amount, source="transfer"):
    """Catat pembayaran (SSOT uang). Menaikkan paid_amount (atomik $inc) lalu MENURUNKAN
    payment_status (INV-5 — tak pernah hand-set). Bila lunas & status masih `pending`,
    order maju ke `paid` LEWAT transition_order (state machine tetap otoritatif, anti RC-E7).

    - Terminal (cancelled/completed) → InvalidTransition (INV-P2 / RC-E8).
    - amount <= 0 → OrderError (RC-E11).
    - Idempotensi per-bukti dijamin pemanggil (status bukti pending→verified sekali; INV-P1).
    """
    if order.get("status") in TERMINAL:
        raise InvalidTransition("Tak bisa mencatat pembayaran pada order terminal")
    amt = money(amount)
    if amt <= 0:
        raise OrderError("Jumlah pembayaran harus > 0")
    await db.orders.update_one({"code": order["code"]},
                               {"$inc": {"paid_amount": amt}, "$set": {"updated_at": now_iso()}})
    fresh = await db.orders.find_one({"code": order["code"]})
    new_paid = money(fresh.get("paid_amount", 0))
    ps = derive_payment_status(new_paid, fresh.get("total", 0))
    if fresh.get("status") == "pending" and ps == "lunas":
        return await transition_order(db, fresh, "paid")
    await db.orders.update_one({"code": order["code"]}, {"$set": {"payment_status": ps}})
    fresh["payment_status"] = ps
    return safe_doc(fresh)


async def list_orders_for_user(db, user_id, limit=100):
    docs = await db.orders.find({"user_id": user_id}).sort([("created_at", -1)]).to_list(limit)
    return [safe_doc(d) for d in docs]


async def get_order_for_user(db, code, user):
    """Ambil order milik user (owner-scoped). Guest (user None) tak boleh baca list;
    detail by code hanya untuk pemilik (IDOR-safe, RC-E10)."""
    doc = await db.orders.find_one({"code": code})
    if not doc:
        return None
    uid = (user or {}).get("id")
    if doc.get("user_id") and doc.get("user_id") != uid:
        return None  # bukan pemilik → 404 (jangan bocorkan keberadaan)
    return safe_doc(doc)


__all__ = [
    "create_order", "transition_order", "record_payment",
    "list_orders_for_user", "get_order_for_user",
    "derive_payment_status", "LEGAL_TRANSITIONS", "TERMINAL",
    "OrderError", "StockConflict", "InvalidTransition",
]
