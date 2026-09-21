"""services/pricing.py — PRICING SSOT (Single Source of Truth) — Epic E2.

SATU-SATUNYA tempat diskon & total dihitung. Dipakai OLEH:
  - checkout (E3, create_order),
  - voucher validate endpoint (services/vouchers.py),
  - verifier integritas (scripts/verify_data_integrity.py) sebagai referensi.

Prinsip (anti RC-E1/E2/E14):
  - PURE function (tanpa I/O DB) → mudah di-unit-test & mutation-proof.
  - Uang = INTEGER rupiah (via core_utils.money) → tak ada drift float.
  - Diskon DI-CAP ke subtotal; total DI-FLOOR ke 0 (tak pernah negatif).
  - COD fee hanya bila payment_group == 'cod' (INV-10).

Formula kanonik (memory/INVARIANTS.md):
  subtotal = Σ(unit_price * quantity)
  discount = voucher ? (percent→round(subtotal*value/100) | flat→value | free_shipping→shipping_price)
             capped ke subtotal (untuk percent/flat), hanya bila subtotal >= min_spend
  cod_fee  = payment_group=='cod' ? cod_fee : 0
  total    = max(0, subtotal - discount + shipping_price + cod_fee)
"""
from core_utils import money

VOUCHER_TYPES = ("percent", "flat", "free_shipping")


def _int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def voucher_discount(voucher, subtotal, shipping_price=0):
    """SSOT perhitungan DISKON (pure, integer). Kembalikan diskon rupiah (>=0).

    - percent: round(subtotal * value / 100), di-cap ke subtotal (value 1..100).
    - flat: min(value, subtotal), tak pernah negatif.
    - free_shipping: sama dengan shipping_price (di-offset di total), hanya bila min_spend terpenuhi.
    - min_spend belum terpenuhi → diskon 0.
    - voucher None / tipe tak dikenal → 0.
    """
    if not voucher:
        return 0
    subtotal = money(subtotal)
    shipping_price = money(shipping_price)
    vtype = voucher.get("type")
    value = _int(voucher.get("value", 0), 0)
    min_spend = _int(voucher.get("min_spend", 0), 0)

    if subtotal < max(0, min_spend):
        return 0
    if vtype == "percent":
        if value <= 0:
            return 0
        return min(subtotal, int(round(subtotal * value / 100)))
    if vtype == "flat":
        return min(subtotal, max(0, value))
    if vtype == "free_shipping":
        return max(0, shipping_price)
    return 0


def compute_subtotal(items):
    """Σ(unit_price * quantity) sebagai integer rupiah. Bounded & defensif."""
    subtotal = 0
    for it in (items or []):
        subtotal += money(it.get("unit_price", 0)) * max(0, _int(it.get("quantity", 0), 0))
    return money(subtotal)


def compute_pricing(items, voucher=None, shipping=None, payment_group=None, cod_fee=0):
    """SSOT pricing. Kembalikan dict 5-tuple:
        {subtotal, discount, shipping_price, cod_fee, total}

    Argumen:
      items         : list of {unit_price, quantity} (product_id/category opsional untuk scope).
      voucher       : dict voucher (atau None). Diskon dihitung via voucher_discount().
      shipping      : dict {price} ATAU int harga ongkir.
      payment_group : 'transfer' | 'ewallet' | 'cod' (cod_fee hanya berlaku bila 'cod').
      cod_fee       : biaya COD (rupiah) — diterapkan hanya bila payment_group=='cod'.
    """
    subtotal = compute_subtotal(items)
    if isinstance(shipping, dict):
        shipping_price = money(shipping.get("price", 0))
    else:
        shipping_price = money(shipping or 0)

    discount = voucher_discount(voucher, subtotal, shipping_price)
    fee = money(cod_fee) if payment_group == "cod" else 0
    total = max(0, subtotal - discount + shipping_price + fee)
    return {
        "subtotal": subtotal,
        "discount": discount,
        "shipping_price": shipping_price,
        "cod_fee": fee,
        "total": total,
    }
