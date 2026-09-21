"""services/product_io_session.py — SESI IMPOR: baris file diunggah SEKALI.

MASALAH NYATA YANG DIPECAHKAN
Wizard impor dulu menahan seluruh baris di browser dan mengirimnya ULANG pada setiap
validasi (katalog klien 6.426 baris = ~5,2 MB request + ~6,4 MB response). Pada koneksi
normal (~1 Mbps unggah) satu validasi > 60 detik -> axios timeout -> admin melihat
"Gagal memvalidasi baris." walaupun file 100% sah. Sekarang `/analyze` menyimpan baris
SEKALI di koleksi `import_sessions`, dan langkah berikutnya (validate / tiers / isi harga
massal / commit) hanya mengirim `session_id` + perubahan kecil.

DESAIN
- Dokumen META: {id, kind:'meta', admin_id, filename, headers, total, chunks, ...}
- Dokumen CHUNK: {id:'<sid>#<seq>', kind:'chunk', session_id, seq, rows:[...]}
  Baris dipecah per CHUNK_SIZE agar aman dari batas dokumen BSON 16 MB.
- TTL: dokumen kedaluwarsa otomatis (`expires_at`) sehingga tak ada sampah permanen.
- OWNER-SCOPED: sesi hanya bisa dibaca/diubah admin yang membuatnya (anti-IDOR).
"""
import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple

COLLECTION = "import_sessions"
ID_PREFIX = "imp_"
CHUNK_SIZE = 1200          # ~1 MB/dokumen untuk katalog lebar (28 kolom)
TTL_HOURS = 6
MAX_ROWS = 30000
MAX_PREVIEW = 400
MAX_PER_ADMIN = 5          # sesi lama milik admin yang sama dipangkas otomatis


class SessionNotFound(Exception):
    """Sesi impor tidak ada / kedaluwarsa / bukan milik admin ini."""


def _now() -> datetime:
    return datetime.now(timezone.utc)


def new_id() -> str:
    return f"{ID_PREFIX}{uuid.uuid4().hex[:16]}"


async def ensure_indexes(db) -> None:
    """Index sesi impor: unik per id + TTL otomatis (dipanggil saat startup)."""
    coll = db[COLLECTION]
    await coll.create_index("id", unique=True)
    await coll.create_index("session_id")
    await coll.create_index("expires_at", expireAfterSeconds=0)


def _chunk(rows: List[dict], size: int = CHUNK_SIZE) -> List[List[dict]]:
    return [rows[i:i + size] for i in range(0, len(rows), size)] or [[]]


async def _write_chunks(db, sid: str, rows: List[dict], expires_at: datetime) -> int:
    coll = db[COLLECTION]
    await coll.delete_many({"kind": "chunk", "session_id": sid})
    parts = _chunk(rows)
    docs = [{
        "id": f"{sid}#{seq}", "kind": "chunk", "session_id": sid, "seq": seq,
        "rows": part, "expires_at": expires_at,
    } for seq, part in enumerate(parts)]
    if docs:
        await coll.insert_many(docs)
    return len(docs)


async def _prune(db, admin_id: str) -> int:
    """Sisakan MAX_PER_ADMIN sesi terbaru per admin.

    TTL sudah menjamin sesi tidak jadi sampah permanen, tetapi seorang admin yang
    mencoba beberapa file berturut-turut bisa menumpuk puluhan sesi dalam jendela TTL.
    Pemangkasan ini menjaga koleksi tetap kecil tanpa mengganggu sesi yang aktif dipakai.
    """
    if not admin_id:
        return 0
    cursor = db[COLLECTION].find(
        {"kind": "meta", "admin_id": str(admin_id)}, {"_id": 0, "id": 1},
    ).sort("created_at", -1).skip(MAX_PER_ADMIN)
    stale = [d["id"] async for d in cursor]
    if not stale:
        return 0
    await db[COLLECTION].delete_many(
        {"$or": [{"id": {"$in": stale}}, {"session_id": {"$in": stale}}]})
    return len(stale)


async def create(db, admin_id: str, filename: str, headers: List[str],
                 rows: List[dict]) -> dict:
    """Simpan hasil analyze sebagai sesi baru. Kembalikan {id, total, expires_at}."""
    rows = [r for r in list(rows or [])[:MAX_ROWS] if isinstance(r, dict)]
    sid = new_id()
    expires_at = _now() + timedelta(hours=TTL_HOURS)
    chunks = await _write_chunks(db, sid, rows, expires_at)
    await db[COLLECTION].insert_one({
        "id": sid, "kind": "meta", "admin_id": str(admin_id or ""),
        "filename": str(filename or "")[:200], "headers": [str(h) for h in (headers or [])],
        "total": len(rows), "chunks": chunks,
        "created_at": _now(), "updated_at": _now(), "expires_at": expires_at,
    })
    await _prune(db, str(admin_id or ""))
    return {"id": sid, "total": len(rows), "expires_at": expires_at.isoformat()}


async def meta(db, sid: str, admin_id: str) -> dict:
    doc = await db[COLLECTION].find_one(
        {"id": str(sid or ""), "kind": "meta"}, {"_id": 0, "rows": 0})
    if not doc:
        raise SessionNotFound("Sesi impor tidak ditemukan atau sudah kedaluwarsa.")
    if doc.get("admin_id") and str(doc["admin_id"]) != str(admin_id):
        raise SessionNotFound("Sesi impor tidak ditemukan atau sudah kedaluwarsa.")
    return doc


async def load_rows(db, sid: str, admin_id: str) -> Tuple[List[dict], dict]:
    """Ambil SELURUH baris sesi (untuk validate / tiers / commit di server)."""
    info = await meta(db, sid, admin_id)
    rows: List[dict] = []
    cursor = db[COLLECTION].find(
        {"kind": "chunk", "session_id": info["id"]}, {"_id": 0, "rows": 1, "seq": 1},
    ).sort("seq", 1)
    async for chunk in cursor:
        rows.extend(chunk.get("rows") or [])
    return rows, info


async def save_rows(db, sid: str, admin_id: str, rows: List[dict]) -> dict:
    """Tulis ulang baris sesi setelah patch/isi massal."""
    info = await meta(db, sid, admin_id)
    expires_at = _now() + timedelta(hours=TTL_HOURS)
    chunks = await _write_chunks(db, info["id"], rows, expires_at)
    await db[COLLECTION].update_one(
        {"id": info["id"], "kind": "meta"},
        {"$set": {"total": len(rows), "chunks": chunks,
                  "updated_at": _now(), "expires_at": expires_at}},
    )
    return {"id": info["id"], "total": len(rows)}


def window(rows: List[dict], offset: int = 0, limit: int = 100,
           indexes: Optional[List[int]] = None) -> List[dict]:
    """Potongan baris untuk tabel pratinjau: berurutan (offset/limit) atau indeks tertentu."""
    total = len(rows or [])
    limit = max(1, min(int(limit or 100), MAX_PREVIEW))
    if indexes:
        picked = []
        for i in indexes[:limit]:
            if 0 <= i < total:
                picked.append({"index": i, "data": rows[i]})
        return picked
    start = max(0, int(offset or 0))
    return [{"index": start + n, "data": r}
            for n, r in enumerate((rows or [])[start:start + limit])]


async def close(db, sid: str, admin_id: str) -> dict:
    """Hapus sesi (dipanggil saat admin ganti file / selesai impor)."""
    info = await meta(db, sid, admin_id)
    await db[COLLECTION].delete_many(
        {"$or": [{"id": info["id"]}, {"session_id": info["id"]}]})
    return {"closed": True, "id": info["id"]}


async def purge_expired(db) -> int:
    """Jaring aman bila TTL monitor belum berjalan (Mongo menyapu tiap ~60 detik)."""
    res = await db[COLLECTION].delete_many({"expires_at": {"$lt": _now()}})
    return int(res.deleted_count or 0)


__all__ = [
    "COLLECTION", "ID_PREFIX", "TTL_HOURS", "MAX_ROWS", "MAX_PREVIEW",
    "SessionNotFound", "ensure_indexes", "create", "meta", "load_rows",
    "save_rows", "window", "close", "purge_expired",
]
