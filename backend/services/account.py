"""services/account.py — Akun pelanggan: profil, alamat, wishlist (Epic E4).

PRINSIP KEAMANAN (RC-E10 IDOR): `user_id` SELALU berasal dari sesi (argumen fungsi),
TIDAK PERNAH dari body request. Resource ber-{id} → owner-or-None (router balas 404).
Invarian: INV-A1 (≤ 1 alamat default/user), INV-A3 (wishlist dedupe + FK produk).
"""
from core_utils import new_id, now_iso, safe_doc

ADDR_FIELDS = ("name", "phone", "street", "district", "city", "province", "postal", "label")
LIST_MAX = 200


def _clean_addr(data):
    out = {}
    for f in ADDR_FIELDS:
        v = data.get(f)
        out[f] = (str(v).strip()[:300] if v is not None else None)
    if not out.get("label"):
        out["label"] = "Rumah"
    return out


# ---------------- Profil (BR-1; email immutable) ----------------
async def update_profile(db, user_id, *, name=None, phone=None):
    updates = {}
    if name is not None and name.strip():
        updates["name"] = name.strip()[:120]
    if phone is not None:
        updates["phone"] = (phone.strip()[:40] or None)
    if updates:
        await db.users.update_one({"id": user_id}, {"$set": updates})
    return safe_doc(await db.users.find_one({"id": user_id}))  # safe_doc buang password_hash


# ---------------- Alamat (BR-2; single default) ----------------
async def list_addresses(db, user_id):
    docs = await db.addresses.find({"user_id": user_id}).sort(
        [("is_default", -1), ("created_at", 1)]).to_list(LIST_MAX)
    return [safe_doc(d) for d in docs]


async def create_address(db, user_id, data):
    want_default = bool(data.get("is_default"))
    if await db.addresses.count_documents({"user_id": user_id}) == 0:
        want_default = True  # alamat pertama otomatis default
    if want_default:
        await db.addresses.update_many({"user_id": user_id}, {"$set": {"is_default": False}})
    addr = {
        "id": new_id("adr"), "user_id": user_id, **_clean_addr(data),
        "is_default": want_default, "created_at": now_iso(), "updated_at": now_iso(),
    }
    await db.addresses.insert_one(addr)
    return safe_doc(addr)


async def update_address(db, user_id, addr_id, data):
    existing = await db.addresses.find_one({"id": addr_id, "user_id": user_id})
    if not existing:
        return None  # owner-or-404 (jangan bocorkan keberadaan)
    want_default = bool(data.get("is_default"))
    if want_default:
        await db.addresses.update_many({"user_id": user_id}, {"$set": {"is_default": False}})
    updates = {**_clean_addr(data), "is_default": want_default, "updated_at": now_iso()}
    await db.addresses.update_one({"id": addr_id, "user_id": user_id}, {"$set": updates})
    return safe_doc(await db.addresses.find_one({"id": addr_id, "user_id": user_id}))


async def set_default_address(db, user_id, addr_id):
    existing = await db.addresses.find_one({"id": addr_id, "user_id": user_id})
    if not existing:
        return None
    await db.addresses.update_many({"user_id": user_id}, {"$set": {"is_default": False}})
    await db.addresses.update_one({"id": addr_id, "user_id": user_id},
                                  {"$set": {"is_default": True, "updated_at": now_iso()}})
    return await list_addresses(db, user_id)


async def delete_address(db, user_id, addr_id):
    existing = await db.addresses.find_one({"id": addr_id, "user_id": user_id})
    if not existing:
        return False
    await db.addresses.delete_one({"id": addr_id, "user_id": user_id})
    # Bila yang dihapus adalah default & masih ada alamat lain → promosikan satu (jaga UX).
    if existing.get("is_default"):
        nxt = await db.addresses.find_one({"user_id": user_id})
        if nxt:
            await db.addresses.update_one({"id": nxt["id"]}, {"$set": {"is_default": True}})
    return True


# ---------------- Wishlist (BR-3; dedupe + FK) ----------------
async def _get_ids(db, user_id):
    doc = await db.wishlists.find_one({"user_id": user_id})
    if not doc:
        return []
    return list(dict.fromkeys(doc.get("product_ids", [])))  # dedupe, preserve order


async def _save_ids(db, user_id, ids):
    ids = list(dict.fromkeys([i for i in ids if i]))
    await db.wishlists.update_one(
        {"user_id": user_id},
        {"$set": {"product_ids": ids, "updated_at": now_iso()},
         "$setOnInsert": {"id": new_id("wsh"), "created_at": now_iso()}},
        upsert=True,
    )
    return ids


async def _existing_product_ids(db, ids):
    if not ids:
        return set()
    docs = await db.products.find({"id": {"$in": list(ids)}}, {"id": 1, "_id": 0}).to_list(LIST_MAX)
    return {d["id"] for d in docs}


async def get_wishlist(db, user_id):
    ids = await _get_ids(db, user_id)
    # buang FK menggantung (produk terhapus/arsip) agar INV-A3 tetap bersih
    valid = await _existing_product_ids(db, ids)
    return [i for i in ids if i in valid]


async def toggle_wishlist(db, user_id, product_id):
    ids = await _get_ids(db, user_id)
    if product_id in ids:
        ids = [i for i in ids if i != product_id]
    else:
        prod = await db.products.find_one({"id": product_id, "status": "active"})
        if not prod:
            raise ValueError("Produk tidak ditemukan")
        ids.append(product_id)
    return await _save_ids(db, user_id, ids)


async def merge_wishlist(db, user_id, product_ids):
    """Union idempotent wishlist guest -> user saat login (RC: tanpa duplikat, FK-valid)."""
    current = await _get_ids(db, user_id)
    incoming = [i for i in (product_ids or []) if i]
    valid = await _existing_product_ids(db, set(current) | set(incoming))
    union = [i for i in (current + incoming) if i in valid]
    return await _save_ids(db, user_id, union)
