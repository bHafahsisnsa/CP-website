"""services/cart.py — server cart (opsional, untuk user login). Epic E3.

Cart hybrid: guest memakai localStorage (FE); user login boleh sinkron ke koleksi `carts`
agar keranjang persist lintas perangkat. Cart menyimpan REFERENSI item
({product_id, variant_type, volume_ml, quantity}) — harga/nama TIDAK di-snapshot di sini
(itu saat order). Satu cart per user (upsert by user_id).
"""
from core_utils import new_id, now_iso, safe_doc

MAX_ITEMS = 100


def _norm_items(items):
    out = []
    for it in (items or [])[:MAX_ITEMS]:
        pid = it.get("product_id")
        sku = str(it.get("sku") or "").strip() or None
        vtype = str(it.get("variant_type", "") or "")
        try:
            qty = int(it.get("quantity"))
        except (TypeError, ValueError):
            continue
        ml_raw = it.get("volume_ml")
        try:
            ml = int(ml_raw) if ml_raw not in (None, "") else None
        except (TypeError, ValueError):
            ml = None
        # butuh identitas varian: sku (baru) ATAU volume_ml (legacy)
        if pid and qty > 0 and (sku or (ml and ml > 0)):
            out.append({
                "product_id": pid, "sku": sku, "variant_type": vtype,
                "volume_ml": ml, "quantity": min(qty, 999),
            })
    return out


async def get_cart(db, user_id):
    doc = await db.carts.find_one({"user_id": user_id})
    if not doc:
        return {"id": None, "user_id": user_id, "items": [], "voucher_code": None, "note": ""}
    return safe_doc(doc)


async def save_cart(db, user_id, *, items=None, voucher_code=None, note=""):
    payload = {
        "user_id": user_id,
        "items": _norm_items(items),
        "voucher_code": (voucher_code or None),
        "note": (note or "")[:500],
        "updated_at": now_iso(),
    }
    await db.carts.update_one(
        {"user_id": user_id},
        {"$set": payload, "$setOnInsert": {"id": new_id("crt"), "created_at": now_iso()}},
        upsert=True,
    )
    return await get_cart(db, user_id)


__all__ = ["get_cart", "save_cart"]
