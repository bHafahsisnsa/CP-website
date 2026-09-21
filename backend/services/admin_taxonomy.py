"""services/admin_taxonomy.py — CRUD kategori & voucher admin (Epic E5 BR-3/BR-4).

- Kategori: FK-safe (tak bisa hard-delete bila dipakai produk — nonaktifkan saja, RC-E5).
- Voucher: reuse skema E2. `used_count` system-owned (read-only): create=0, update mempertahankan
  nilai lama, hapus diblok bila sudah ada redemption (CE1/INV-R FK-safe). Setiap mutasi diaudit (INV-M1).
"""
import re

from core_utils import money, new_id, now_iso, safe_doc
from services.audit import log_action

LIST_MAX = 500


def _slugify(text: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", (text or "").lower().strip()).strip("-")
    return s or "item"


# ---------------- Categories ----------------
async def list_categories(db):
    docs = await db.categories.find({}).sort([("name", 1)]).to_list(LIST_MAX)
    return [safe_doc(d) for d in docs]


async def _unique_cat_slug(db, base, exclude_id=None):
    slug, i = base, 2
    while True:
        q = {"slug": slug}
        if exclude_id:
            q["id"] = {"$ne": exclude_id}
        if not await db.categories.find_one(q, {"_id": 1}):
            return slug
        slug, i = f"{base}-{i}", i + 1


async def create_category(db, actor_id, data):
    base = _slugify(data.get("slug") or data.get("name"))
    doc = {
        "id": new_id("cat"),
        "slug": await _unique_cat_slug(db, base),
        "name": str(data.get("name", "")).strip()[:120],
        "desc": str(data.get("desc", ""))[:1000],
        "image": (data.get("image") or None),
        "seo": data.get("seo") or {},
        "active": bool(data.get("active", True)),
        "created_at": now_iso(),
    }
    await db.categories.insert_one(doc)
    await log_action(actor_id, "create", "categories", doc["id"], {"slug": doc["slug"]})
    return safe_doc(doc)


async def update_category(db, actor_id, cid, data):
    existing = await db.categories.find_one({"id": cid})
    if not existing:
        return None
    updates = {
        "name": str(data.get("name", existing.get("name"))).strip()[:120],
        "desc": str(data.get("desc", ""))[:1000],
        "image": (data.get("image") or None),
        "seo": data.get("seo") or {},
        "active": bool(data.get("active", True)),
        "updated_at": now_iso(),
    }
    # slug tak diubah bila dipakai produk (jaga FK products.category); boleh diubah bila belum dipakai
    used = await db.products.count_documents({"category": existing.get("slug")})
    if data.get("slug") and used == 0:
        updates["slug"] = await _unique_cat_slug(db, _slugify(data["slug"]), exclude_id=cid)
    await db.categories.update_one({"id": cid}, {"$set": updates})
    await log_action(actor_id, "update", "categories", cid)
    return safe_doc(await db.categories.find_one({"id": cid}))


async def delete_category(db, actor_id, cid):
    existing = await db.categories.find_one({"id": cid})
    if not existing:
        return None
    used = await db.products.count_documents({"category": existing.get("slug")})
    if used > 0:
        raise ValueError(f"Kategori dipakai {used} produk — nonaktifkan saja (jangan hapus)")
    await db.categories.delete_one({"id": cid})
    await log_action(actor_id, "delete", "categories", cid)
    return {"deleted": True, "id": cid}


# ---------------- Facets: Occasions / Characters (multi-facet taksonomi) ----------------
# Generic CRUD (dipakai occasions & characters). FK-safe: hapus diblok bila slug
# masih dipakai produk pada array `product_field` (occasions/characters).
async def list_facets(db, coll):
    docs = await db[coll].find({}).sort([("order", 1), ("name", 1)]).to_list(LIST_MAX)
    return [safe_doc(d) for d in docs]


async def _unique_facet_slug(db, coll, base, exclude_id=None):
    slug, i = base, 2
    while True:
        q = {"slug": slug}
        if exclude_id:
            q["id"] = {"$ne": exclude_id}
        if not await db[coll].find_one(q, {"_id": 1}):
            return slug
        slug, i = f"{base}-{i}", i + 1


async def create_facet(db, coll, id_prefix, actor_id, data):
    base = _slugify(data.get("slug") or data.get("name"))
    doc = {
        "id": new_id(id_prefix),
        "slug": await _unique_facet_slug(db, coll, base),
        "name": str(data.get("name", "")).strip()[:120],
        "icon": str(data.get("icon", "") or "").strip()[:60],
        "desc": str(data.get("desc", ""))[:600],
        "order": int(data.get("order", 0) or 0),
        "active": bool(data.get("active", True)),
        "created_at": now_iso(),
    }
    await db[coll].insert_one(doc)
    await log_action(actor_id, "create", coll, doc["id"], {"slug": doc["slug"]})
    return safe_doc(doc)


async def update_facet(db, coll, product_field, actor_id, fid, data):
    existing = await db[coll].find_one({"id": fid})
    if not existing:
        return None
    updates = {
        "name": str(data.get("name", existing.get("name"))).strip()[:120],
        "icon": str(data.get("icon", existing.get("icon", "")) or "").strip()[:60],
        "desc": str(data.get("desc", ""))[:600],
        "order": int(data.get("order", existing.get("order", 0)) or 0),
        "active": bool(data.get("active", True)),
        "updated_at": now_iso(),
    }
    # slug hanya boleh diubah bila belum dipakai produk (jaga FK products[product_field])
    used = await db.products.count_documents({product_field: existing.get("slug")})
    if data.get("slug") and used == 0:
        updates["slug"] = await _unique_facet_slug(db, coll, _slugify(data["slug"]), exclude_id=fid)
    await db[coll].update_one({"id": fid}, {"$set": updates})
    await log_action(actor_id, "update", coll, fid)
    return safe_doc(await db[coll].find_one({"id": fid}))


async def delete_facet(db, coll, product_field, actor_id, fid):
    existing = await db[coll].find_one({"id": fid})
    if not existing:
        return None
    used = await db.products.count_documents({product_field: existing.get("slug")})
    if used > 0:
        raise ValueError(f"Dipakai {used} produk — nonaktifkan saja (jangan hapus)")
    await db[coll].delete_one({"id": fid})
    await log_action(actor_id, "delete", coll, fid)
    return {"deleted": True, "id": fid}


# ---------------- Vouchers ----------------
def _validate_voucher(data):
    vtype = data.get("type")
    value = int(data.get("value", 0) or 0)
    if vtype not in ("percent", "flat", "free_shipping"):
        raise ValueError("Tipe voucher tidak sah")
    if vtype == "percent" and not (1 <= value <= 100):
        raise ValueError("Voucher percent: value harus 1..100")
    if value <= 0:
        raise ValueError("value voucher harus > 0")


async def list_vouchers(db):
    docs = await db.vouchers.find({}).sort([("min_spend", 1)]).to_list(LIST_MAX)
    return [safe_doc(d) for d in docs]


def _voucher_doc(data):
    return {
        "code": str(data.get("code", "")).strip().upper()[:40],
        "type": data.get("type"),
        "value": int(data.get("value", 0) or 0),
        "label": str(data.get("label", ""))[:200],
        "min_spend": money(data.get("min_spend", 0)),
        "usage_limit": int(data.get("usage_limit", 0) or 0),
        "per_user_limit": int(data.get("per_user_limit", 0) or 0),
        "scope": data.get("scope") or {"category": None, "product_ids": []},
        "starts_at": (data.get("starts_at") or None),
        "ends_at": (data.get("ends_at") or None),
        "campaign": (data.get("campaign") or None),
        "active": bool(data.get("active", True)),
    }


async def create_voucher(db, actor_id, data):
    _validate_voucher(data)
    doc = _voucher_doc(data)
    if await db.vouchers.find_one({"code": doc["code"]}, {"_id": 1}):
        raise ValueError("Kode voucher sudah ada")
    doc.update({"id": new_id("vcr"), "used_count": 0, "created_at": now_iso()})
    await db.vouchers.insert_one(doc)
    await log_action(actor_id, "create", "vouchers", doc["id"], {"code": doc["code"]})
    return safe_doc(doc)


async def update_voucher(db, actor_id, vid, data):
    existing = await db.vouchers.find_one({"id": vid})
    if not existing:
        return None
    _validate_voucher(data)
    doc = _voucher_doc(data)
    if doc["code"] != existing.get("code"):
        if await db.vouchers.find_one({"code": doc["code"], "id": {"$ne": vid}}, {"_id": 1}):
            raise ValueError("Kode voucher sudah dipakai voucher lain")
    # used_count system-owned: pertahankan nilai lama (anti-tamper CE1).
    doc["used_count"] = int(existing.get("used_count", 0) or 0)
    doc["updated_at"] = now_iso()
    await db.vouchers.update_one({"id": vid}, {"$set": doc})
    await log_action(actor_id, "update", "vouchers", vid, {"code": doc["code"]})
    return safe_doc(await db.vouchers.find_one({"id": vid}))


async def delete_voucher(db, actor_id, vid):
    existing = await db.vouchers.find_one({"id": vid})
    if not existing:
        return None
    used = await db.voucher_redemptions.count_documents({"voucher_code": existing.get("code")})
    if used > 0:
        raise ValueError("Voucher sudah dipakai pada pesanan — nonaktifkan saja (jangan hapus)")
    await db.vouchers.delete_one({"id": vid})
    await log_action(actor_id, "delete", "vouchers", vid)
    return {"deleted": True, "id": vid}
