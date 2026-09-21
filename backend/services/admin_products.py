"""services/admin_products.py — CRUD produk admin (Epic E5 BR-2).

Reuse aturan katalog E1 (INV-C1 varian ml unik, INV-C2 compare_at_price>price, INV-4 stok>=0,
harga>0). TIDAK menghitung pricing (SSOT tetap services/pricing.py). Archive = soft-delete
(INV-M2: produk yang direferensikan order TAK PERNAH di-hard-delete). Setiap mutasi diaudit (INV-M1).
"""
import re

from core_utils import money, new_id, now_iso, safe_doc
from services.audit import log_action
from services.product_io import clean_variants
from services import variants as V

LIST_MAX = 500


def _slugify(text: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", (text or "").lower().strip()).strip("-")
    return s or "produk"


async def _unique_slug(db, base, exclude_id=None):
    slug, i = base, 2
    while True:
        q = {"slug": slug}
        if exclude_id:
            q["id"] = {"$ne": exclude_id}
        if not await db.products.find_one(q, {"_id": 1}):
            return slug
        slug, i = f"{base}-{i}", i + 1


async def _build_doc(db, data):
    """Validasi + normalisasi payload produk (create & update).

    Dua jalur input:
      - BARU: `variants[]` + `options[]` (N-dimensi ber-SKU) → SSOT.
      - LEGACY: hanya `volumes[]` (type × ml) → di-derive ke options/variants.
    `volumes[]` selalu diturunkan untuk kompat export/impor. Harga display = varian termurah.
    """
    name = str(data.get("name", "")).strip()[:200]
    base_name = name or data.get("slug") or ""
    variants_in = data.get("variants") or []
    concentration = data.get("concentration", "EDP")

    if variants_in:
        oin = [dict(o) for o in (data.get("options") or [])]
        vin = []
        for v in variants_in:
            v = dict(v)
            v["options"] = dict(v.get("options") or {})
            vin.append(v)
        options, variants = V.build_options_variants(base_name, oin, vin)
        conc_opt = next((o for o in options if o["name"] == V.CONCENTRATION_NAME), None)
        if conc_opt and conc_opt["values"]:
            concentration = conc_opt["values"][0]
    else:
        vols = clean_variants([dict(v) for v in data.get("volumes", [])], product_name=base_name)
        options, variants = V.derive_from_volumes(
            {"volumes": vols, "concentration": concentration, "name": base_name})

    volumes = V.derive_volumes(options, variants)
    rng = V.price_range(variants)
    price = rng["price"]

    prod_cap = rng["compare_at_price"]
    cap = data.get("compare_at_price")
    if cap not in (None, "", 0):
        if int(cap) <= price:
            raise ValueError("compare_at_price harus lebih besar dari harga varian termurah")
        prod_cap = int(cap)
    cat = await db.categories.find_one({"slug": data.get("category")}, {"_id": 1})
    if not cat:
        raise ValueError("Kategori tidak ditemukan")
    return {
        "name": name,
        "brand": str(data.get("brand", "Collector")).strip()[:120] or "Collector",
        "category": data.get("category"),
        "concentration": concentration,
        "gender": data.get("gender", "Unisex"),
        "price": price,
        "price_min": rng["price_min"],
        "price_max": rng["price_max"],
        "compare_at_price": (int(prod_cap) if prod_cap else None),
        "compare_at_min": rng["compare_at_min"],
        "compare_at_max": rng["compare_at_max"],
        "best_seller": bool(data.get("best_seller")),
        "is_new": bool(data.get("is_new")),
        "tags": [str(t).strip() for t in (data.get("tags") or []) if str(t).strip()][:20],
        "occasions": [str(x).strip() for x in (data.get("occasions") or []) if str(x).strip()][:20],
        "characters": [str(x).strip() for x in (data.get("characters") or []) if str(x).strip()][:20],
        "volumes": volumes,
        "options": options,
        "variants": variants,
        "notes": data.get("notes") or {"top": [], "heart": [], "base": []},
        "description": str(data.get("description", ""))[:8000],
        "ingredients": (data.get("ingredients") or None),
        "performance": data.get("performance") or {},
        "images": [str(u).strip() for u in (data.get("images") or []) if str(u).strip()][:12],
        "video_url": (data.get("video_url") or None),
        "seo": data.get("seo") or {},
        "status": data.get("status", "active"),
    }


def _list_filter(status=None, q=None) -> dict:
    """Filter Mongo untuk daftar produk admin. SSOT dipakai list_products & bulk_set_status
    supaya "pilih semua hasil filter" di UI PERSIS sama dengan yang tampil di daftar."""
    filt = {}
    if status in ("active", "archived"):
        filt["status"] = status
    if q and str(q).strip():
        rx = {"$regex": re.escape(str(q).strip()[:80]), "$options": "i"}
        filt["$or"] = [{"name": rx}, {"slug": rx}, {"brand": rx}]
    return filt


async def list_products(db, status=None, q=None, limit=LIST_MAX, skip=0):
    """Daftar produk admin (termasuk archived) + TOTAL untuk paginasi.

    Katalog bisa berisi ribuan produk (hasil impor massal), jadi endpoint ini WAJIB
    ter-paginasi: kembalikan (items, total) supaya UI bisa menampilkan halaman
    berikutnya dan tidak "kehilangan" produk di luar batas LIST_MAX.
    """
    filt = _list_filter(status, q)
    lim = max(1, min(int(limit or LIST_MAX), LIST_MAX))
    try:
        sk = max(0, int(skip or 0))
    except (TypeError, ValueError):
        sk = 0
    total = await db.products.count_documents(filt)
    docs = await db.products.find(filt).sort([("created_at", -1)]).skip(sk).to_list(lim)
    return [V.serialize_product(safe_doc(d)) for d in docs], total


async def get_product(db, pid):
    doc = await db.products.find_one({"id": pid})
    return V.serialize_product(safe_doc(doc)) if doc else None


async def create_product(db, actor_id, data):
    doc = await _build_doc(db, data)
    base = _slugify(data.get("slug") or doc["name"])
    doc.update({
        "id": new_id("prd"),
        "slug": await _unique_slug(db, base),
        "rating_avg": 0.0,
        "rating_count": 0,
        "created_at": now_iso(),
        "updated_at": now_iso(),
    })
    await db.products.insert_one(doc)
    await log_action(actor_id, "create", "products", doc["id"], {"slug": doc["slug"]})
    return V.serialize_product(safe_doc(doc))


# Field yang DIPERTAHANKAN saat update bila payload TIDAK mengirim key-nya sama sekali.
# Alasan: jalur impor massal (services/product_bulk._payload) hanya membawa kolom yang ada
# di CSV. Tanpa guard ini, `$set` doc hasil _build_doc akan MENGOSONGKAN field yang tidak
# dibawa file (mis. occasions/characters/notes/performance/seo) -> data-loss senyap saat
# admin melakukan export -> re-import (mode Upsert).
# Catatan: request HTTP PUT (AdminProductInput.model_dump()) SELALU mengirim semua key,
# jadi editor produk tetap bisa mengosongkan field secara eksplisit.
PRESERVE_IF_ABSENT = ("occasions", "characters", "notes", "performance", "seo",
                      "ingredients", "images", "video_url")


async def update_product(db, actor_id, pid, data):
    existing = await db.products.find_one({"id": pid})
    if not existing:
        return None
    doc = await _build_doc(db, data)
    for key in PRESERVE_IF_ABSENT:
        if key not in data and key in existing:
            doc[key] = existing[key]
    base = _slugify(data.get("slug") or doc["name"])
    doc["slug"] = await _unique_slug(db, base, exclude_id=pid)
    # INV-C3: rating adalah derivasi review — JANGAN diubah lewat editor produk.
    doc["rating_avg"] = float(existing.get("rating_avg", 0) or 0)
    doc["rating_count"] = int(existing.get("rating_count", 0) or 0)
    doc["updated_at"] = now_iso()
    await db.products.update_one({"id": pid}, {"$set": doc})
    await log_action(actor_id, "update", "products", pid, {"slug": doc["slug"]})
    return V.serialize_product(safe_doc(await db.products.find_one({"id": pid})))


async def archive_product(db, actor_id, pid):
    """Soft-delete: set status='archived'. INV-M2 — tak pernah hard-delete (FK order aman)."""
    existing = await db.products.find_one({"id": pid}, {"_id": 1})
    if not existing:
        return None
    await db.products.update_one({"id": pid}, {"$set": {"status": "archived", "updated_at": now_iso()}})
    await log_action(actor_id, "archive", "products", pid)
    return {"archived": True, "id": pid}


async def restore_product(db, actor_id, pid):
    existing = await db.products.find_one({"id": pid}, {"_id": 1})
    if not existing:
        return None
    await db.products.update_one({"id": pid}, {"$set": {"status": "active", "updated_at": now_iso()}})
    await log_action(actor_id, "restore", "products", pid)
    return {"archived": False, "id": pid}


# Batas satu aksi massal. Impor katalog klien bisa ribuan produk, tapi tetap dibatasi
# agar satu request tidak menyentuh seluruh koleksi tanpa sengaja.
BULK_MAX = 20000


async def bulk_set_status(db, actor_id, *, status, ids=None, filter_status=None,
                          q=None, confirm_count=None):
    """Ubah status BANYAK produk sekaligus (aktifkan / arsipkan).

    Dua cakupan (eksklusif): `ids` eksplisit, ATAU `filter_status` (+ q) yang PERSIS sama
    dengan filter daftar admin. `confirm_count` opsional: bila diisi dan tidak sama dengan
    jumlah yang cocok, aksi DIBATALKAN (mencegah admin mengubah lebih banyak dari yang
    dilihatnya karena data berubah di antara pemuatan halaman).
    Soft-delete tetap INV-M2: 'archived' hanya mengubah status, tak pernah hard-delete.
    """
    if status not in ("active", "archived"):
        raise ValueError("status harus 'active' atau 'archived'")
    clean_ids = [str(i).strip() for i in (ids or []) if str(i or "").strip()][:BULK_MAX]
    if clean_ids:
        filt = {"id": {"$in": clean_ids}}
        scope = f"ids({len(clean_ids)})"
    elif filter_status is not None:
        filt = _list_filter(None if filter_status == "all" else filter_status, q)
        scope = f"filter({filter_status}|{str(q or '').strip()[:40]})"
    else:
        raise ValueError("Tentukan daftar produk (ids) atau filter.")

    matched = await db.products.count_documents(filt)
    if matched > BULK_MAX:
        raise ValueError(f"Terlalu banyak produk ({matched}). Maksimal {BULK_MAX} "
                         f"per aksi \u2014 persempit filter.")
    if confirm_count is not None and int(confirm_count) != matched:
        return {"conflict": True, "matched": matched, "expected": int(confirm_count),
                "modified": 0, "status": status}
    if matched == 0:
        return {"matched": 0, "modified": 0, "status": status}

    res = await db.products.update_many(
        filt, {"$set": {"status": status, "updated_at": now_iso()}})
    await log_action(actor_id, "bulk_status", "products", scope,
                     {"status": status, "matched": matched, "modified": res.modified_count})
    return {"matched": matched, "modified": int(res.modified_count), "status": status}
