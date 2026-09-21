"""services/admin_reviews.py — moderasi ulasan (Epic E5 BR-5).

Mengubah status ulasan (published/pending/hidden) lalu MERECOMPUTE agregat rating produk
sehingga INV-C3 (rating_avg/count == mean review published) tetap benar. Setiap mutasi diaudit (INV-M1).
"""
from core_utils import now_iso, safe_doc
from services.audit import log_action

LIST_MAX = 1000


async def list_reviews(db, status=None, product_id=None):
    filt = {}
    if status in ("published", "pending", "hidden"):
        filt["status"] = status
    if product_id:
        filt["product_id"] = product_id
    docs = await db.reviews.find(filt).sort([("created_at", -1)]).to_list(LIST_MAX)
    return [safe_doc(d) for d in docs]


async def recompute_rating(db, product_id):
    """Set products.rating_avg/count = mean/count ulasan `published` (INV-C3 SSOT)."""
    if not product_id:
        return None
    revs = await db.reviews.find(
        {"product_id": product_id, "status": "published"}, {"_id": 0, "rating": 1}
    ).to_list(20000)
    cnt = len(revs)
    avg = round(sum(int(r.get("rating", 0) or 0) for r in revs) / cnt, 1) if cnt else 0.0
    await db.products.update_one(
        {"id": product_id}, {"$set": {"rating_avg": avg, "rating_count": cnt}}
    )
    return {"rating_avg": avg, "rating_count": cnt}


async def set_status(db, actor_id, review_id, status):
    r = await db.reviews.find_one({"id": review_id})
    if not r:
        return None
    await db.reviews.update_one({"id": review_id}, {"$set": {"status": status, "updated_at": now_iso()}})
    if r.get("product_id"):
        await recompute_rating(db, r["product_id"])
    await log_action(actor_id, "moderate", "reviews", review_id, {"status": status})
    return safe_doc(await db.reviews.find_one({"id": review_id}))
