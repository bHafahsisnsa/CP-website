"""services/crm.py — segmentasi CRM ringan diturunkan dari orders (Epic E7).

SATU sumber kebenaran: orders (INV-G2 — tak ada store segmen terpisah yang bisa drift).
Segmen: prospek (0 order), new (1), repeat (>=2), high_value (LTV>=ambang), dormant
(order terakhir > DORMANT_DAYS lalu). READ-only, bounded, tanpa N+1 (grouping in-memory).
"""
from datetime import datetime, timezone

ORDERS_MAX = 50000
USERS_MAX = 50000
HIGH_VALUE_LTV = 1500000     # Rp — ambang pelanggan bernilai tinggi
DORMANT_DAYS = 90
PAID_STATES = {"paid", "packed", "shipped", "completed"}
ROWS_MAX = 1000


def _parse_dt(s):
    try:
        return datetime.fromisoformat(str(s).replace("Z", "+00:00"))
    except Exception:
        return None


def _segment(order_count, ltv, last_dt, now):
    if order_count == 0:
        return "prospek"
    if last_dt and (now - last_dt).days > DORMANT_DAYS:
        return "dormant"
    if ltv >= HIGH_VALUE_LTV:
        return "high_value"
    if order_count >= 2:
        return "repeat"
    return "new"


async def segments(db, seg_type=""):
    users = await db.users.find(
        {"role": "customer"}, {"_id": 0, "id": 1, "name": 1, "email": 1, "created_at": 1}
    ).to_list(USERS_MAX)
    orders = await db.orders.find(
        {}, {"_id": 0, "user_id": 1, "total": 1, "paid_amount": 1, "status": 1, "created_at": 1}
    ).to_list(ORDERS_MAX)
    now = datetime.now(timezone.utc)
    agg = {}
    for o in orders:                    # in-memory grouping (bukan N+1)
        uid = o.get("user_id")
        if not uid:
            continue
        a = agg.setdefault(uid, {"count": 0, "ltv": 0, "last": None})
        a["count"] += 1
        if o.get("status") in PAID_STATES:
            a["ltv"] += int(o.get("paid_amount", 0) or 0) or int(o.get("total", 0) or 0)
        dt = _parse_dt(o.get("created_at"))
        if dt and (a["last"] is None or dt > a["last"]):
            a["last"] = dt
    rows = []
    counts = {}
    for u in users:
        a = agg.get(u["id"], {"count": 0, "ltv": 0, "last": None})
        seg = _segment(a["count"], a["ltv"], a["last"], now)
        counts[seg] = counts.get(seg, 0) + 1
        rows.append({
            "user_id": u["id"], "name": u.get("name"), "email": u.get("email"),
            "orders": a["count"], "ltv": a["ltv"],
            "last_order": a["last"].isoformat() if a["last"] else None,
            "segment": seg,
        })
    if seg_type:
        rows = [r for r in rows if r["segment"] == seg_type]
    rows.sort(key=lambda r: r["ltv"], reverse=True)
    return {
        "segments": counts,
        "rows": rows[:ROWS_MAX],
        "thresholds": {"high_value_ltv": HIGH_VALUE_LTV, "dormant_days": DORMANT_DAYS},
    }
