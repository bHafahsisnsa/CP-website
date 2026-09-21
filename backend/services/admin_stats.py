"""services/admin_stats.py — agregat dashboard admin (READ-only, Epic E5 BR-1).

Hanya membaca & meringkas (revenue, orders-by-status, produk aktif, low-stock, pesanan terbaru).
Tidak ada math bisnis baru (pricing tetap SSOT di services/pricing.py). Query bounded (anti N+1).
"""
from core_utils import safe_doc

LOW_STOCK_DEFAULT = 5
RECENT_MAX = 8
LOW_STOCK_MAX = 24
REVENUE_STATES = {"paid", "packed", "shipped", "completed"}


async def dashboard(db):
    """Ringkasan operasional toko. Revenue = Σ total order berstatus terbayar/diproses."""
    orders = await db.orders.find(
        {}, {"_id": 0, "total": 1, "status": 1, "paid_amount": 1}
    ).to_list(50000)
    revenue = sum(int(o.get("total", 0) or 0) for o in orders if o.get("status") in REVENUE_STATES)
    paid_revenue = sum(int(o.get("paid_amount", 0) or 0) for o in orders)
    orders_by_status = {}
    for o in orders:
        s = o.get("status", "pending")
        orders_by_status[s] = orders_by_status.get(s, 0) + 1

    active_products = await db.products.count_documents({"status": "active"})
    archived_products = await db.products.count_documents({"status": "archived"})

    settings = await db.settings.find_one({"id": "store"}) or {}
    threshold = int(settings.get("low_stock_threshold", LOW_STOCK_DEFAULT) or LOW_STOCK_DEFAULT)

    prods = await db.products.find(
        {"status": "active"}, {"_id": 0, "name": 1, "slug": 1, "variants": 1, "volumes": 1}
    ).to_list(10000)
    low_stock = []
    for p in prods:
        # SSOT stok = variants[]; fallback volumes[] untuk dokumen legacy belum termigrasi.
        rows = p.get("variants") or p.get("volumes") or []
        for v in rows:
            st = int(v.get("stock", 0) or 0)
            if st <= threshold:
                opts = v.get("options") or {}
                label = " / ".join(str(x) for x in opts.values()) if opts else (
                    f"{v.get('ml')}ml" if v.get("ml") else v.get("sku", ""))
                low_stock.append({"slug": p.get("slug"), "name": p.get("name"),
                                  "ml": label, "sku": v.get("sku"), "stock": st})
    low_stock = sorted(low_stock, key=lambda x: x["stock"])[:LOW_STOCK_MAX]

    recent = await db.orders.find({}, {"_id": 0}).sort([("created_at", -1)]).to_list(RECENT_MAX)
    pending_reviews = await db.reviews.count_documents({"status": "pending"})

    return {
        "revenue": revenue,
        "paid_revenue": paid_revenue,
        "total_orders": len(orders),
        "orders_by_status": orders_by_status,
        "active_products": active_products,
        "archived_products": archived_products,
        "low_stock_threshold": threshold,
        "low_stock": low_stock,
        "pending_reviews": pending_reviews,
        "recent": [safe_doc(o) for o in recent],
    }
