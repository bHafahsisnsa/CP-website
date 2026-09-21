"""services/vouchers.py — logika voucher (Epic E2), Shopee-like campaigns.

- evaluate_voucher(): eligibility (aktif/window/min-spend/scope/usage/per-user) + diskon.
  Diskon SELALU dari services.pricing.voucher_discount (SATU rumus, lihat RC-E1/E2).
- list_active_vouchers(): voucher publik untuk Voucher Center (display).

Catatan penting:
  - validate bersifat ADVISORY & RACE-FREE (tak menulis apa pun). Penghitungan pemakaian
    (used_count) dilakukan ATOMIK saat order dibuat (E3). Di sini pengecekan usage/per-user
    bersifat defensif agar UI memberi alasan yang jujur.
  - Tak pernah melempar 5xx: input aneh → {valid:false, reason}.
"""
from datetime import datetime, timezone

from core_utils import safe_doc
from services.pricing import voucher_discount

LIST_MAX = 100


def _now():
    return datetime.now(timezone.utc)


def _parse_iso(value):
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(str(value))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except (TypeError, ValueError):
        return None


def _fmt_rp(n):
    try:
        return "Rp " + f"{int(n):,}".replace(",", ".")
    except (TypeError, ValueError):
        return "Rp 0"


def _int(v, default=0):
    try:
        return int(v)
    except (TypeError, ValueError):
        return default


def _has_scope(voucher):
    scope = voucher.get("scope") or {}
    return bool(scope.get("category") or scope.get("product_ids"))


def _eligible_subtotal(voucher, subtotal, items):
    """Subtotal item yang MEMENUHI scope voucher.

    - Tanpa scope → seluruh subtotal.
    - Ada scope tapi items tak dikirim → fallback ke subtotal penuh (advisory).
    - Ada scope & items → jumlahkan hanya item yang cocok (category / product_ids).
    """
    scope = voucher.get("scope") or {}
    cat = scope.get("category")
    pids = set(scope.get("product_ids") or [])
    if not (cat or pids):
        return subtotal
    if not items:
        return subtotal
    total = 0
    for it in items:
        it_cat = it.get("category")
        it_pid = it.get("product_id")
        match = (cat and it_cat == cat) or (it_pid in pids)
        if match:
            price = _int(it.get("unit_price", 0), 0)
            qty = max(0, _int(it.get("quantity", 0), 0))
            total += price * qty
    return max(0, total)


async def evaluate_voucher(db, code, subtotal, shipping=0, user_id=None, items=None):
    """Evaluasi voucher → dict kontrak validate:
        {valid, code, type, value, discount, label, min_spend, reason?}
    """
    code = (code or "").strip().upper()
    subtotal = max(0, _int(subtotal, 0))
    shipping = max(0, _int(shipping, 0))
    out = {
        "valid": False, "code": code, "type": None, "value": 0,
        "discount": 0, "label": "", "min_spend": 0, "reason": None,
    }
    if not code:
        out["reason"] = "Masukkan kode voucher"
        return out

    v = await db.vouchers.find_one({"code": code})
    if not v:
        out["reason"] = "Kode voucher tidak ditemukan"
        return out

    out["type"] = v.get("type")
    out["value"] = _int(v.get("value", 0), 0)
    out["label"] = v.get("label", "")
    out["min_spend"] = _int(v.get("min_spend", 0), 0)

    if not v.get("active", True):
        out["reason"] = "Voucher tidak aktif"
        return out

    now = _now()
    starts = _parse_iso(v.get("starts_at"))
    ends = _parse_iso(v.get("ends_at"))
    if starts and now < starts:
        out["reason"] = "Voucher belum berlaku"
        return out
    if ends and now > ends:
        out["reason"] = "Voucher sudah kedaluwarsa"
        return out

    if subtotal < out["min_spend"]:
        out["reason"] = f"Min. belanja {_fmt_rp(out['min_spend'])}"
        return out

    usage_limit = _int(v.get("usage_limit", 0), 0)
    used_count = _int(v.get("used_count", 0), 0)
    if usage_limit > 0 and used_count >= usage_limit:
        out["reason"] = "Kuota voucher telah habis"
        return out

    per_user_limit = _int(v.get("per_user_limit", 0), 0)
    if per_user_limit > 0 and user_id:
        used_by_user = await db.voucher_redemptions.count_documents(
            {"voucher_code": code, "user_id": user_id}
        )
        if used_by_user >= per_user_limit:
            out["reason"] = "Batas pemakaian voucher ini sudah tercapai"
            return out

    scoped = _has_scope(v)
    base = _eligible_subtotal(v, subtotal, items) if scoped else subtotal
    if scoped and items is not None and base <= 0:
        out["reason"] = "Voucher tidak berlaku untuk item di keranjang"
        return out

    discount = voucher_discount(v, base, shipping)
    out["valid"] = True
    out["discount"] = discount
    out["reason"] = None
    return out


async def list_active_vouchers(db, now=None):
    """Voucher publik untuk Voucher Center. Aktif & belum kedaluwarsa (bounded)."""
    now = now or _now()
    docs = await db.vouchers.find({"active": True}).sort([("min_spend", 1)]).to_list(LIST_MAX)
    out = []
    for v in docs:
        ends = _parse_iso(v.get("ends_at"))
        if ends and now > ends:
            continue
        out.append(safe_doc(v))
    return out
