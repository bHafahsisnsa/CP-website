"""services/admin_config.py — konfigurasi toko, media library & users (Epic E5 BR-7/8/10).

Kurir & metode bayar (tarif/fee bounded >=0), settings singleton (id='store'), media_assets
(referensi URL — V1 tanpa upload nyata; upload nyata via integration agent), daftar users (read-only,
tanpa password_hash). Setiap mutasi diaudit (INV-M1).
"""
import re

from core_utils import money, new_id, now_iso, safe_doc
from services.audit import log_action

LIST_MAX = 500


def _slug_id(text: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", (text or "").lower().strip()).strip("-")
    return s or new_id("m")


# ---------------- Shipping methods ----------------
async def list_shipping(db):
    docs = await db.shipping_methods.find({}).sort([("price", 1)]).to_list(LIST_MAX)
    return [safe_doc(d) for d in docs]


async def create_shipping(db, actor_id, data):
    sid = _slug_id(data.get("name"))
    if await db.shipping_methods.find_one({"id": sid}, {"_id": 1}):
        sid = f"{sid}-{new_id('s')[-4:]}"
    doc = {"id": sid, "name": str(data.get("name", "")).strip()[:120],
           "eta": str(data.get("eta", ""))[:120], "price": money(data.get("price", 0)),
           "active": bool(data.get("active", True))}
    await db.shipping_methods.insert_one(doc)
    await log_action(actor_id, "create", "shipping_methods", sid)
    return safe_doc(doc)


async def update_shipping(db, actor_id, sid, data):
    existing = await db.shipping_methods.find_one({"id": sid})
    if not existing:
        return None
    updates = {"name": str(data.get("name", existing.get("name"))).strip()[:120],
               "eta": str(data.get("eta", existing.get("eta", "")))[:120],
               "price": money(data.get("price", existing.get("price", 0))),
               "active": bool(data.get("active", True))}
    await db.shipping_methods.update_one({"id": sid}, {"$set": updates})
    await log_action(actor_id, "update", "shipping_methods", sid)
    return safe_doc(await db.shipping_methods.find_one({"id": sid}))


async def delete_shipping(db, actor_id, sid):
    existing = await db.shipping_methods.find_one({"id": sid}, {"_id": 1})
    if not existing:
        return None
    await db.shipping_methods.delete_one({"id": sid})
    await log_action(actor_id, "delete", "shipping_methods", sid)
    return {"deleted": True, "id": sid}


# ---------------- Payment methods ----------------
async def list_payments(db):
    docs = await db.payment_methods.find({}).to_list(LIST_MAX)
    return [safe_doc(d) for d in docs]


async def create_payment(db, actor_id, data):
    pid = _slug_id(data.get("name"))
    if await db.payment_methods.find_one({"id": pid}, {"_id": 1}):
        pid = f"{pid}-{new_id('p')[-4:]}"
    doc = {"id": pid, "group": data.get("group"), "name": str(data.get("name", "")).strip()[:120],
           "extra": str(data.get("extra", ""))[:200], "fee": money(data.get("fee", 0)),
           "logo": (str(data.get("logo"))[:1000] if data.get("logo") else None),
           "qr_image": (str(data.get("qr_image"))[:1000] if data.get("qr_image") else None),
           "active": bool(data.get("active", True))}
    await db.payment_methods.insert_one(doc)
    await log_action(actor_id, "create", "payment_methods", pid)
    return safe_doc(doc)


async def update_payment(db, actor_id, pid, data):
    existing = await db.payment_methods.find_one({"id": pid})
    if not existing:
        return None
    updates = {"group": data.get("group", existing.get("group")),
               "name": str(data.get("name", existing.get("name"))).strip()[:120],
               "extra": str(data.get("extra", existing.get("extra", "")))[:200],
               "fee": money(data.get("fee", existing.get("fee", 0))),
               "logo": ((str(data["logo"])[:1000] or None) if data.get("logo") is not None
                        else existing.get("logo")),
               "qr_image": ((str(data["qr_image"])[:1000] or None) if data.get("qr_image") is not None
                            else existing.get("qr_image")),
               "active": bool(data.get("active", True))}
    await db.payment_methods.update_one({"id": pid}, {"$set": updates})
    await log_action(actor_id, "update", "payment_methods", pid)
    return safe_doc(await db.payment_methods.find_one({"id": pid}))


async def delete_payment(db, actor_id, pid):
    existing = await db.payment_methods.find_one({"id": pid}, {"_id": 1})
    if not existing:
        return None
    await db.payment_methods.delete_one({"id": pid})
    await log_action(actor_id, "delete", "payment_methods", pid)
    return {"deleted": True, "id": pid}


# ---------------- Settings (singleton) ----------------
async def get_settings(db):
    return safe_doc(await db.settings.find_one({"id": "store"}) or {"id": "store"})


async def update_settings(db, actor_id, data):
    updates = {}
    for k in ("store_name", "currency", "support_email", "support_phone",
              "whatsapp_number", "site_url", "seo_title", "seo_description", "og_image",
              "social_instagram", "social_tiktok", "social_facebook", "ga_measurement_id",
              "inspired_by_label"):
        if data.get(k) is not None:
            updates[k] = str(data[k])[:400]
    for k in ("cod_fee", "free_shipping_threshold", "low_stock_threshold"):
        if data.get(k) is not None:
            updates[k] = money(data[k])
    if data.get("inspired_by_enabled") is not None:
        updates["inspired_by_enabled"] = bool(data["inspired_by_enabled"])
    if data.get("house_brands") is not None:
        seen, brands = set(), []
        for b in (data["house_brands"] or [])[:50]:
            s = str(b or "").strip()[:120]
            if s and s.lower() not in seen:
                seen.add(s.lower())
                brands.append(s)
        updates["house_brands"] = brands
    updates["updated_at"] = now_iso()
    await db.settings.update_one({"id": "store"}, {"$set": updates}, upsert=True)
    await log_action(actor_id, "update", "settings", "store")
    return safe_doc(await db.settings.find_one({"id": "store"}))


# ---------------- Media library (references, V1) ----------------
async def list_media(db):
    docs = await db.media_assets.find({}).sort([("created_at", -1)]).to_list(LIST_MAX)
    return [safe_doc(d) for d in docs]


async def add_media(db, actor_id, data):
    doc = {"id": new_id("med"), "kind": data.get("kind", "image"),
           "url": str(data.get("url", "")).strip()[:1200],
           "alt": (str(data.get("alt"))[:300] if data.get("alt") else None),
           "width": (int(data["width"]) if data.get("width") else None),
           "height": (int(data["height"]) if data.get("height") else None),
           "owner_admin_id": actor_id, "created_at": now_iso()}
    await db.media_assets.insert_one(doc)
    await log_action(actor_id, "create", "media_assets", doc["id"])
    return safe_doc(doc)


async def delete_media(db, actor_id, mid):
    existing = await db.media_assets.find_one({"id": mid}, {"_id": 1})
    if not existing:
        return None
    await db.media_assets.delete_one({"id": mid})
    await log_action(actor_id, "delete", "media_assets", mid)
    return {"deleted": True, "id": mid}


# ---------------- Users (read-only) ----------------
async def list_users(db):
    docs = await db.users.find({}).sort([("created_at", 1)]).to_list(LIST_MAX)
    return [safe_doc(d) for d in docs]  # safe_doc membuang password_hash
