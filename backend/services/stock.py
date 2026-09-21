"""services/stock.py — STOK ATOMIK per-SKU (anti-oversell, RC-E3). Epic E3.

SATU-SATUNYA tempat stok varian dinaikkan/diturunkan. SSOT stok = `products.variants[].stock`
(identitas varian = `sku`). Model N-dimensi: tiap kombinasi opsi = satu `variant` ber-SKU unik.

Prinsip:
  - decrement(): per-SKU `$inc -qty` DENGAN filter `stock >= qty` (atomik, anti-TOCTOU) via
    `$elemMatch {sku, stock>=qty}` + operator posisional `$`. Bila SATU baris gagal → seluruh
    baris yang telanjur turun DIKEMBALIKAN (all-or-nothing).
  - restore(): kompensasi saat order dibatalkan (RC-E6) — stok TAK PERNAH negatif (INV-4).

Caller (services/orders.py) me-resolve setiap item ke `sku` (via services/variants.resolve_variant)
sehingga payload lama (variant_type+volume_ml) maupun baru (sku) sama-sama didukung.
"""
from core_utils import money


def _norm(items):
    """Normalisasi baris {product_id, sku, quantity} → int aman (qty>0)."""
    out = []
    for it in (items or []):
        pid = it.get("product_id")
        sku = str(it.get("sku") or "").strip()
        try:
            qty = int(it.get("quantity"))
        except (TypeError, ValueError):
            continue
        if pid and sku and qty > 0:
            out.append({"product_id": pid, "sku": sku, "quantity": qty})
    return out


async def _restore_one(db, pid, sku, qty):
    await db.products.update_one(
        {"id": pid, "variants.sku": sku},
        {"$inc": {"variants.$.stock": qty}},
    )


async def restore(db, items):
    """Kembalikan stok (kompensasi cancel). Idempotent-safe per baris."""
    for it in _norm(items):
        await _restore_one(db, it["product_id"], it["sku"], it["quantity"])


async def decrement(db, items):
    """Turunkan stok ATOMIK per SKU. Kembalikan (ok, failed_item).

    Untuk tiap baris: `$inc variants.$.stock -qty` ber-filter (sku, stock >= qty). Jika
    `modified_count != 1` → stok tak cukup / SKU tak ada → ROLLBACK semua baris yang sudah
    turun, lalu kembalikan (False, baris_gagal) → caller balas 409.
    """
    norm = _norm(items)
    applied = []
    for it in norm:
        pid, sku, qty = it["product_id"], it["sku"], it["quantity"]
        res = await db.products.update_one(
            {"id": pid, "variants": {"$elemMatch": {"sku": sku, "stock": {"$gte": qty}}}},
            {"$inc": {"variants.$.stock": -qty}},
        )
        if res.modified_count != 1:
            for done in applied:
                await _restore_one(db, done["product_id"], done["sku"], done["quantity"])
            return False, it
        applied.append(it)
    return True, None


async def available_stock(db, product_id, sku):
    """Stok tersedia untuk 1 SKU (untuk pesan error yang jujur). None bila tak ada."""
    if not sku:
        return None
    doc = await db.products.find_one(
        {"id": product_id, "variants.sku": sku}, {"variants": 1, "_id": 0})
    if not doc:
        return None
    for v in doc.get("variants", []):
        if v.get("sku") == sku:
            return max(0, int(v.get("stock", 0) or 0))
    return None


__all__ = ["decrement", "restore", "available_stock", "money"]
