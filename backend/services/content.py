"""services/content.py — CMS konten storefront (Epic E9).

SSOT default di content_registry. Publik: GET mengembalikan default DI-MERGE dgn override
tersimpan (selalu lengkap → storefront tak pernah kosong). Admin: update per-key (audited),
hanya field yang dikenal di skema yang diterima (abaikan sisanya — anti-injection).
"""
from core_utils import now_iso, new_id
from content_registry import SECTION_MAP, default_content, schema as _schema
from services.audit import log_action


REV_MAX = 20  # simpan maks 20 revisi terakhir per section


def _coerce(field, value):
    t = field["type"]
    if t in ("text", "textarea", "image"):
        return str(value)[:4000] if value is not None else ""
    if t == "list":
        if not isinstance(value, list):
            return []
        return [str(x)[:500] for x in value[:60]]
    if t == "repeater":
        if not isinstance(value, list):
            return []
        subs = {f["name"]: f for f in field["item"]}
        out = []
        for row in value[:60]:
            if not isinstance(row, dict):
                continue
            out.append({n: _coerce(subs[n], row.get(n)) for n in subs})
        return out
    return value


def _clean(section, data):
    """Terima hanya field yang ada di skema section; coerce tipe."""
    if not isinstance(data, dict):
        return {}
    out = {}
    for f in section["fields"]:
        if f["name"] in data:
            out[f["name"]] = _coerce(f, data[f["name"]])
    return out


async def _stored_map(db):
    docs = await db.content.find({}, {"_id": 0, "id": 1, "data": 1}).to_list(200)
    return {d["id"]: (d.get("data") or {}) for d in docs}


async def public_content(db):
    """{key: {default..., stored...}} — selalu lengkap utk semua section."""
    stored = await _stored_map(db)
    merged = {}
    for key, dflt in default_content().items():
        merged[key] = {**dflt, **(stored.get(key) or {})}
    return merged


async def admin_content(db):
    return await public_content(db)


def content_schema():
    return _schema()


async def update_section(db, key, data, actor_id):
    section = SECTION_MAP.get(key)
    if not section:
        return None
    clean = _clean(section, data)
    existing = await db.content.find_one({"id": key}, {"_id": 0, "data": 1})
    prev_data = existing.get("data") if existing else {}
    new_data = {**prev_data, **clean}
    # Simpan revisi HANYA jika benar-benar berubah (hindari noise revert dgn payload sama).
    if prev_data != new_data:
        await db.content_revisions.insert_one({
            "id": new_id("rev"),
            "section": key,
            "data": prev_data,  # revisi = snapshot SEBELUM update
            "created_at": now_iso(),
            "created_by": actor_id,
        })
        # Trim revisi lama supaya tak menumpuk (best-effort).
        try:
            docs = await db.content_revisions.find(
                {"section": key}, {"_id": 1, "created_at": 1}
            ).sort([("created_at", -1)]).to_list(REV_MAX + 50)
            if len(docs) > REV_MAX:
                stale_ids = [d["_id"] for d in docs[REV_MAX:]]
                await db.content_revisions.delete_many({"_id": {"$in": stale_ids}})
        except Exception:
            # Sengaja diam: pemangkasan revisi lama adalah housekeeping best-effort —
            # kegagalannya TIDAK boleh menggagalkan penyimpanan konten oleh admin.
            pass
    await db.content.update_one(
        {"id": key},
        {"$set": {"data": new_data, "updated_at": now_iso(), "updated_by": actor_id},
         "$setOnInsert": {"id": key, "created_at": now_iso()}},
        upsert=True,
    )
    await log_action(actor_id, "update", "content", key)
    return {**section["default"], **new_data}


async def list_revisions(db, key, limit=REV_MAX):
    section = SECTION_MAP.get(key)
    if not section:
        return None
    docs = await db.content_revisions.find(
        {"section": key}, {"_id": 0}
    ).sort([("created_at", -1)]).to_list(limit)
    return docs


async def revert_to_default(db, key, actor_id):
    section = SECTION_MAP.get(key)
    if not section:
        return None
    return await update_section(db, key, section["default"], actor_id)


async def seed_defaults(db):
    """Idempotent: pastikan tiap section punya dokumen (data awal = default)."""
    for key, dflt in default_content().items():
        await db.content.update_one(
            {"id": key},
            {"$setOnInsert": {"id": key, "data": dflt, "created_at": now_iso(), "updated_at": now_iso()}},
            upsert=True,
        )
