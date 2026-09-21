"""services/media.py — Media Manager LOKAL (E20).

SSOT penyimpanan aset media untuk seluruh aplikasi (produk, CMS, kategori, toko,
metode bayar). Desain:

1. **Disk lokal = SSOT.** File asli ditulis ke
   `<MEDIA_ROOT>/originals/<YYYY>/<MM>/<uuid>.<ext>` dan turunan (thumbnail/medium)
   ke `<MEDIA_ROOT>/derived/<uuid>_<size>.webp`.
2. **Mirror GridFS (opsional, default AKTIF).** Biner yang sama dicadangkan ke
   MongoDB lokal (`media_files.*`). Bila file hilang dari disk (container di-rebuild,
   pod berpindah replika, volume belum ter-mount) route `GET /api/media/...`
   MEMULIHKANNYA otomatis dari mirror -> TIDAK ADA broken image lagi.
   Matikan di VPS dengan `MEDIA_DB_MIRROR=false` bila volume sudah persisten.
3. **URL stabil.** URL yang disimpan ke DB selalu RELATIF (`/api/media/...`) dan
   berbasis UUID; rename/ubah alt hanya metadata sehingga link tidak pernah rusak.
4. **Folder bertingkat.** Koleksi `media_folders` (id, name, parent_id, path, depth).
   Hapus folder = isi dipindahkan ke induk (tanpa orphan) atau cascade eksplisit.
5. **Optimasi otomatis.** Pillow: auto-orient EXIF, strip metadata, batas sisi
   terpanjang 2400px, re-encode teroptimasi, turunan WebP 400px & 1000px.
   HEIC/HEIF (foto iPhone) dikonversi ke JPEG. SVG & GIF animasi disimpan apa adanya.

ENV:
  MEDIA_ROOT       (default: <backend>/media)
  MEDIA_MAX_MB     (default: 15)
  MEDIA_DB_MIRROR  (default: true)
"""
import asyncio
import hashlib
import io
import os
import re
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from PIL import Image, ImageOps, ImageSequence  # noqa: F401
from motor.motor_asyncio import AsyncIOMotorGridFSBucket

from core_utils import new_id, now_iso, safe_doc
from services.audit import log_action

# ---- HEIC/HEIF (foto iPhone) -------------------------------------------------
try:  # pragma: no cover - tergantung wheel platform
    import pillow_heif

    pillow_heif.register_heif_opener()
    HEIF_OK = True
except Exception:  # pragma: no cover
    HEIF_OK = False

# Guard decompression bomb (gambar raksasa yang menghabiskan RAM).
Image.MAX_IMAGE_PIXELS = 120_000_000

BACKEND_ROOT = Path(__file__).resolve().parent.parent
MEDIA_ROOT = Path(os.environ.get("MEDIA_ROOT", str(BACKEND_ROOT / "media")))
ORIGINALS_DIR = MEDIA_ROOT / "originals"
DERIVED_DIR = MEDIA_ROOT / "derived"
for _d in (MEDIA_ROOT, ORIGINALS_DIR, DERIVED_DIR):
    _d.mkdir(parents=True, exist_ok=True)

MAX_MB = int(os.environ.get("MEDIA_MAX_MB", "15") or 15)
MAX_BYTES = MAX_MB * 1024 * 1024
DB_MIRROR = str(os.environ.get("MEDIA_DB_MIRROR", "true")).lower() in ("1", "true", "yes", "on")
MIRROR_MAX_BYTES = 24 * 1024 * 1024  # jangan mirror biner absurd

MAX_DIM = 2400          # sisi terpanjang file asli setelah optimasi
THUMB_DIM = 400         # turunan grid
MEDIUM_DIM = 1000       # turunan preview / kartu produk

# MIME yang diterima -> ekstensi kanonik.
EXT_MAP = {
    "image/jpeg": "jpg",
    "image/jpg": "jpg",
    "image/pjpeg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
    "image/gif": "gif",
    "image/svg+xml": "svg",
    "image/avif": "avif",
    "image/heic": "heic",
    "image/heif": "heif",
    "image/bmp": "bmp",
    "image/tiff": "tiff",
}
ALLOWED_MIME = set(EXT_MAP.keys())
# MIME yang TIDAK diproses Pillow (disimpan apa adanya).
PASSTHROUGH_MIME = {"image/svg+xml"}
# Format Pillow -> (format simpan, ekstensi, mime keluaran)
SAVE_AS = {
    "image/jpeg": ("JPEG", "jpg", "image/jpeg"),
    "image/jpg": ("JPEG", "jpg", "image/jpeg"),
    "image/pjpeg": ("JPEG", "jpg", "image/jpeg"),
    "image/png": ("PNG", "png", "image/png"),
    "image/webp": ("WEBP", "webp", "image/webp"),
    "image/avif": ("AVIF", "avif", "image/avif"),
    "image/bmp": ("PNG", "png", "image/png"),
    "image/tiff": ("JPEG", "jpg", "image/jpeg"),
    "image/heic": ("JPEG", "jpg", "image/jpeg"),
    "image/heif": ("JPEG", "jpg", "image/jpeg"),
}
EXT_TO_MIME = {
    "jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png",
    "webp": "image/webp", "gif": "image/gif", "svg": "image/svg+xml",
    "avif": "image/avif", "heic": "image/heic", "heif": "image/heif",
    "bmp": "image/bmp", "tiff": "image/tiff", "tif": "image/tiff",
    "ico": "image/x-icon",
}
LIST_MAX = 200
ROOT_FOLDER = {"id": None, "name": "Semua Media", "parent_id": None, "path": "/", "depth": 0}


class MediaError(ValueError):
    """Kesalahan yang aman ditampilkan ke pengguna (dipetakan ke HTTP 400)."""


# ============================== util ==============================
def _bucket(db):
    return AsyncIOMotorGridFSBucket(db, bucket_name="media_files")


def _slug_name(text: str, fallback: str = "file") -> str:
    """Nama tampilan yang aman (bukan path fisik) — dipakai folder & filename."""
    t = unicodedata.normalize("NFKD", str(text or "")).encode("ascii", "ignore").decode()
    t = re.sub(r"[^A-Za-z0-9._&+()' -]+", "", t).strip()
    t = re.sub(r"\s+", " ", t)
    return (t[:120] or fallback)


def _rel(path: Path) -> str:
    return str(path.relative_to(MEDIA_ROOT)).replace(os.sep, "/")


def _url_of(rel: str) -> str:
    return f"/api/media/{rel}"


def safe_rel_path(rel: str) -> Optional[Path]:
    """Cegah path traversal. Kembalikan Path absolut di dalam MEDIA_ROOT atau None."""
    raw = (rel or "").strip().lstrip("/")
    if not raw or "\x00" in raw:
        return None
    candidate = (MEDIA_ROOT / raw).resolve()
    try:
        candidate.relative_to(MEDIA_ROOT.resolve())
    except ValueError:
        return None
    return candidate


def guess_mime_from_name(name: str) -> str:
    ext = (name or "").rsplit(".", 1)[-1].lower()
    return EXT_TO_MIME.get(ext, "application/octet-stream")


def _norm_mime(mime: str, filename: str) -> str:
    m = (mime or "").split(";")[0].strip().lower()
    if m in ALLOWED_MIME:
        return m
    # Browser kadang kirim application/octet-stream -> tebak dari ekstensi.
    guessed = guess_mime_from_name(filename)
    return guessed


# ============================== mirror GridFS ==============================
async def _mirror_put(db, rel: str, data: bytes, mime: str) -> None:
    if not DB_MIRROR or len(data) > MIRROR_MAX_BYTES:
        return
    try:
        bucket = _bucket(db)
        async for old in bucket.find({"filename": rel}):
            try:
                await bucket.delete(old._id)
            except Exception:
                pass
        await bucket.upload_from_stream(rel, data, metadata={"mime": mime, "rel": rel})
    except Exception:
        # Mirror adalah jaring pengaman — kegagalannya tidak boleh menggagalkan upload.
        pass


async def _mirror_get(db, rel: str) -> Optional[bytes]:
    if not DB_MIRROR:
        return None
    try:
        bucket = _bucket(db)
        stream = await bucket.open_download_stream_by_name(rel)
        return await stream.read()
    except Exception:
        return None


async def _mirror_delete(db, rel: str) -> None:
    if not DB_MIRROR:
        return
    try:
        bucket = _bucket(db)
        async for old in bucket.find({"filename": rel}):
            try:
                await bucket.delete(old._id)
            except Exception:
                pass
    except Exception:
        pass


async def resolve_file(db, rel: str):
    """Kembalikan (Path, mime) untuk disajikan. Self-heal dari mirror bila perlu.

    Mengembalikan None bila benar-benar tidak ada.
    """
    fpath = safe_rel_path(rel)
    if fpath is None:
        return None
    mime = guess_mime_from_name(fpath.name)
    if fpath.exists() and fpath.is_file():
        return fpath, mime
    data = await _mirror_get(db, str(Path(rel)).replace(os.sep, "/").lstrip("/"))
    if data is None:
        return None
    try:
        fpath.parent.mkdir(parents=True, exist_ok=True)
        with open(fpath, "wb") as f:
            f.write(data)
    except Exception:
        return None
    return fpath, mime


# ============================== indexes ==============================
async def ensure_indexes(db) -> None:
    try:
        await db.media_folders.create_index("id", unique=True)
        await db.media_folders.create_index("parent_id")
        await db.media_folders.create_index("path")
        await db.media_assets.create_index("id", unique=True)
        await db.media_assets.create_index("folder_id")
        await db.media_assets.create_index("uploaded_at")
        await db.media_assets.create_index("checksum")
    except Exception:
        pass


# ============================== FOLDERS ==============================
def _folder_doc(d):
    return {
        "id": d.get("id"),
        "name": d.get("name"),
        "parent_id": d.get("parent_id"),
        "path": d.get("path"),
        "depth": int(d.get("depth") or 0),
        "created_at": d.get("created_at"),
        "updated_at": d.get("updated_at"),
    }


async def list_folders(db):
    docs = await db.media_folders.find({}, {"_id": 0}).sort(
        [("path", 1)]
    ).to_list(1000)
    counts = {}
    try:
        pipeline = [{"$group": {"_id": "$folder_id", "n": {"$sum": 1}}}]
        async for row in db.media_assets.aggregate(pipeline):
            counts[row["_id"]] = int(row["n"])
    except Exception:
        counts = {}
    out = []
    for d in docs:
        f = _folder_doc(d)
        f["asset_count"] = counts.get(f["id"], 0)
        out.append(f)
    root = dict(ROOT_FOLDER)
    root["asset_count"] = counts.get(None, 0)
    root["total_count"] = sum(counts.values())
    return {"root": root, "folders": out}


async def folder_tree(db):
    data = await list_folders(db)
    folders = data["folders"]
    by_parent = {}
    for f in folders:
        by_parent.setdefault(f["parent_id"], []).append(dict(f, children=[]))

    def build(parent_id):
        nodes = by_parent.get(parent_id, [])
        for n in nodes:
            n["children"] = build(n["id"])
            n["total_count"] = n["asset_count"] + sum(c["total_count"] for c in n["children"])
        return sorted(nodes, key=lambda x: (x["name"] or "").lower())

    return {"root": data["root"], "tree": build(None)}


async def _folder_or_error(db, fid):
    if fid in (None, "", "root"):
        return None
    doc = await db.media_folders.find_one({"id": fid}, {"_id": 0})
    if not doc:
        raise MediaError("Folder tidak ditemukan")
    return doc


async def create_folder(db, actor_id: str, name: str, parent_id: Optional[str] = None):
    clean = _slug_name(name, "")
    if not clean:
        raise MediaError("Nama folder wajib diisi")
    parent = await _folder_or_error(db, parent_id)
    pid = parent["id"] if parent else None
    dup = await db.media_folders.find_one(
        {"parent_id": pid, "name": re.compile(f"^{re.escape(clean)}$", re.I)}, {"_id": 1}
    )
    if dup:
        raise MediaError(f"Folder '{clean}' sudah ada di lokasi ini")
    base = (parent["path"].rstrip("/") if parent else "")
    doc = {
        "id": new_id("mdf"),
        "name": clean,
        "parent_id": pid,
        "path": f"{base}/{clean}",
        "depth": (int(parent["depth"]) + 1) if parent else 1,
        "created_by": actor_id,
        "created_at": now_iso(),
        "updated_at": now_iso(),
    }
    await db.media_folders.insert_one(dict(doc))
    await log_action(actor_id, "create", "media_folders", doc["id"], {"name": clean})
    doc.pop("_id", None)
    return dict(_folder_doc(doc), asset_count=0)


async def _reindex_descendants(db, folder_id: str):
    """Hitung ulang path & depth seluruh keturunan (setelah rename/move)."""
    node = await db.media_folders.find_one({"id": folder_id}, {"_id": 0})
    if not node:
        return
    children = await db.media_folders.find({"parent_id": folder_id}, {"_id": 0}).to_list(1000)
    for c in children:
        new_path = f"{node['path'].rstrip('/')}/{c['name']}"
        await db.media_folders.update_one(
            {"id": c["id"]},
            {"$set": {"path": new_path, "depth": int(node["depth"]) + 1, "updated_at": now_iso()}},
        )
        await _reindex_descendants(db, c["id"])


async def update_folder(db, actor_id: str, fid: str, name=None, parent_id="__keep__"):
    node = await db.media_folders.find_one({"id": fid}, {"_id": 0})
    if not node:
        raise MediaError("Folder tidak ditemukan")
    new_name = _slug_name(name, "") if name is not None else node["name"]
    if not new_name:
        raise MediaError("Nama folder wajib diisi")
    new_parent_id = node["parent_id"] if parent_id == "__keep__" else (parent_id or None)
    if new_parent_id == fid:
        raise MediaError("Folder tidak bisa menjadi induk dirinya sendiri")
    parent = await _folder_or_error(db, new_parent_id)
    # Cegah siklus: induk baru tidak boleh keturunan dari fid.
    if parent and (parent["path"] == node["path"] or parent["path"].startswith(node["path"].rstrip("/") + "/")):
        raise MediaError("Tidak bisa memindahkan folder ke dalam turunannya sendiri")
    dup = await db.media_folders.find_one(
        {"parent_id": new_parent_id, "name": re.compile(f"^{re.escape(new_name)}$", re.I),
         "id": {"$ne": fid}},
        {"_id": 1},
    )
    if dup:
        raise MediaError(f"Folder '{new_name}' sudah ada di lokasi tujuan")
    base = (parent["path"].rstrip("/") if parent else "")
    patch = {
        "name": new_name,
        "parent_id": new_parent_id,
        "path": f"{base}/{new_name}",
        "depth": (int(parent["depth"]) + 1) if parent else 1,
        "updated_at": now_iso(),
    }
    await db.media_folders.update_one({"id": fid}, {"$set": patch})
    await _reindex_descendants(db, fid)
    await log_action(actor_id, "update", "media_folders", fid, {"name": new_name})
    fresh = await db.media_folders.find_one({"id": fid}, {"_id": 0})
    return _folder_doc(fresh)


async def delete_folder(db, actor_id: str, fid: str, cascade: bool = False):
    node = await db.media_folders.find_one({"id": fid}, {"_id": 0})
    if not node:
        return None
    subs = await db.media_folders.find({"parent_id": fid}, {"_id": 0}).to_list(1000)
    assets = await db.media_assets.find({"folder_id": fid}, {"_id": 0, "id": 1}).to_list(5000)
    if cascade:
        # Hapus seluruh keturunan + asetnya (rekursif).
        for s in subs:
            await delete_folder(db, actor_id, s["id"], cascade=True)
        for a in assets:
            await delete_asset(db, actor_id, a["id"])
        moved = 0
    else:
        # Aman: pindahkan isi ke induk (tanpa orphan).
        parent_id = node.get("parent_id")
        for s in subs:
            await update_folder(db, actor_id, s["id"], parent_id=parent_id)
        if assets:
            await db.media_assets.update_many(
                {"folder_id": fid}, {"$set": {"folder_id": parent_id, "updated_at": now_iso()}}
            )
        moved = len(assets)
    await db.media_folders.delete_one({"id": fid})
    await log_action(actor_id, "delete", "media_folders", fid,
                     {"cascade": cascade, "moved_assets": moved})
    return {"deleted": True, "id": fid, "moved_assets": moved,
            "moved_folders": 0 if cascade else len(subs), "cascade": cascade}


async def _descendant_ids(db, fid: str):
    node = await db.media_folders.find_one({"id": fid}, {"_id": 0, "path": 1})
    if not node:
        return [fid]
    prefix = node["path"].rstrip("/") + "/"
    kids = await db.media_folders.find(
        {"path": {"$regex": f"^{re.escape(prefix)}"}}, {"_id": 0, "id": 1}
    ).to_list(2000)
    return [fid] + [k["id"] for k in kids]


# ============================== IMAGE PIPELINE ==============================
def _flatten(im):
    if im.mode in ("RGBA", "LA", "P"):
        im = im.convert("RGBA")
        bg = Image.new("RGB", im.size, (255, 255, 255))
        bg.paste(im, mask=im.split()[-1])
        return bg
    return im.convert("RGB")


def _encode(im, fmt: str) -> bytes:
    buf = io.BytesIO()
    if fmt == "JPEG":
        _flatten(im).save(buf, "JPEG", quality=88, optimize=True, progressive=True)
    elif fmt == "PNG":
        (im if im.mode in ("RGBA", "RGB", "P", "L") else im.convert("RGBA")).save(
            buf, "PNG", optimize=True
        )
    elif fmt == "WEBP":
        (im if im.mode in ("RGBA", "RGB") else im.convert("RGBA")).save(
            buf, "WEBP", quality=86, method=5
        )
    elif fmt == "AVIF":
        try:
            (im if im.mode in ("RGBA", "RGB") else im.convert("RGB")).save(
                buf, "AVIF", quality=75
            )
        except Exception:
            buf = io.BytesIO()
            _flatten(im).save(buf, "JPEG", quality=88, optimize=True)
    else:  # pragma: no cover
        _flatten(im).save(buf, "JPEG", quality=88, optimize=True)
    return buf.getvalue()


def _thumb_bytes(im, dim: int) -> bytes:
    c = im.copy()
    c.thumbnail((dim, dim), Image.LANCZOS)
    buf = io.BytesIO()
    if c.mode not in ("RGB", "RGBA"):
        c = c.convert("RGBA" if "A" in c.getbands() else "RGB")
    c.save(buf, "WEBP", quality=82, method=5)
    return buf.getvalue()


def process_image(data: bytes, mime: str):
    """Optimasi + turunan. Kembalikan dict siap ditulis ke disk.

    keys: data, ext, mime, width, height, thumb, medium, animated
    """
    if mime in PASSTHROUGH_MIME:
        return {"data": data, "ext": "svg", "mime": mime, "width": None,
                "height": None, "thumb": None, "medium": None, "animated": False}
    try:
        im = Image.open(io.BytesIO(data))
        im.load()
    except Exception:
        raise MediaError("Berkas bukan gambar yang valid atau format tidak didukung")

    animated = bool(getattr(im, "is_animated", False) and getattr(im, "n_frames", 1) > 1)
    if animated:
        # GIF/WebP animasi: simpan apa adanya agar animasi tidak hilang.
        ext = EXT_MAP.get(mime, "gif")
        try:
            first = ImageSequence.Iterator(im)[0].convert("RGBA")
            thumb = _thumb_bytes(first, THUMB_DIM)
        except Exception:
            thumb = None
        return {"data": data, "ext": ext, "mime": mime, "width": im.size[0],
                "height": im.size[1], "thumb": thumb, "medium": None, "animated": True}

    try:
        im = ImageOps.exif_transpose(im) or im
    except Exception:
        pass
    fmt, ext, out_mime = SAVE_AS.get(mime, ("JPEG", "jpg", "image/jpeg"))
    work = im
    if max(work.size) > MAX_DIM:
        work = work.copy()
        work.thumbnail((MAX_DIM, MAX_DIM), Image.LANCZOS)
    out = _encode(work, fmt)
    # Bila optimasi malah membengkak (dan format sama), pakai biner asli.
    if mime == out_mime and len(out) > len(data) and max(im.size) <= MAX_DIM:
        out = data
    return {
        "data": out, "ext": ext, "mime": out_mime,
        "width": work.size[0], "height": work.size[1],
        "thumb": _thumb_bytes(work, THUMB_DIM),
        "medium": _thumb_bytes(work, MEDIUM_DIM) if max(work.size) > MEDIUM_DIM else None,
        "animated": False,
    }


# ============================== ASSETS ==============================
def public_asset(d: dict) -> dict:
    """Bentuk respons publik aset (kontrak FE)."""
    if not d:
        return None
    return {
        "id": d.get("id"),
        "folder_id": d.get("folder_id"),
        "filename": d.get("filename") or d.get("original_name") or "media",
        "url": d.get("url"),
        "thumb_url": d.get("thumb_url") or d.get("url"),
        "medium_url": d.get("medium_url") or d.get("url"),
        "kind": d.get("kind") or "image",
        "mime": d.get("mime"),
        "size": int(d.get("size") or 0),
        "width": d.get("width"),
        "height": d.get("height"),
        "alt": d.get("alt"),
        "title": d.get("title"),
        "tags": d.get("tags") or [],
        "source": d.get("source") or ("upload" if d.get("stored_path") else "url"),
        "external": bool(d.get("source") == "external"),
        "stored_path": d.get("stored_path"),
        "uploaded_by": d.get("uploaded_by") or d.get("owner_admin_id"),
        "uploaded_at": d.get("uploaded_at") or d.get("created_at"),
        "updated_at": d.get("updated_at") or d.get("uploaded_at") or d.get("created_at"),
    }


async def _write_files(db, base_uuid: str, proc: dict):
    """Tulis asli + turunan ke disk & mirror. Kembalikan (stored_rel, thumb_rel, medium_rel)."""
    now = datetime.now(timezone.utc)
    sub = ORIGINALS_DIR / f"{now.year:04d}" / f"{now.month:02d}"
    sub.mkdir(parents=True, exist_ok=True)
    orig_path = sub / f"{base_uuid}.{proc['ext']}"
    with open(orig_path, "wb") as f:
        f.write(proc["data"])
    stored_rel = _rel(orig_path)
    await _mirror_put(db, stored_rel, proc["data"], proc["mime"])

    thumb_rel = medium_rel = None
    if proc.get("thumb"):
        DERIVED_DIR.mkdir(parents=True, exist_ok=True)
        tp = DERIVED_DIR / f"{base_uuid}_{THUMB_DIM}.webp"
        with open(tp, "wb") as f:
            f.write(proc["thumb"])
        thumb_rel = _rel(tp)
        await _mirror_put(db, thumb_rel, proc["thumb"], "image/webp")
    if proc.get("medium"):
        mp = DERIVED_DIR / f"{base_uuid}_{MEDIUM_DIM}.webp"
        with open(mp, "wb") as f:
            f.write(proc["medium"])
        medium_rel = _rel(mp)
        await _mirror_put(db, medium_rel, proc["medium"], "image/webp")
    return stored_rel, thumb_rel, medium_rel


async def save_upload(db, file_bytes: bytes, filename: str, mime: str, actor_id: str,
                      folder_id: Optional[str] = None, alt: Optional[str] = None,
                      title: Optional[str] = None, dedupe: bool = True):
    """Simpan satu berkas upload ke disk lokal (+ mirror) & catat metadata."""
    if not file_bytes:
        raise MediaError("Berkas kosong")
    if len(file_bytes) > MAX_BYTES:
        raise MediaError(f"Ukuran berkas melebihi batas {MAX_MB} MB")
    norm = _norm_mime(mime, filename)
    if norm not in ALLOWED_MIME:
        raise MediaError(
            f"Tipe berkas '{mime or norm}' tidak didukung. "
            "Gunakan JPG, PNG, WebP, GIF, SVG, AVIF, atau HEIC."
        )
    if norm in ("image/heic", "image/heif") and not HEIF_OK:
        raise MediaError("Dukungan HEIC belum aktif di server")
    await _folder_or_error(db, folder_id)

    checksum = hashlib.sha256(file_bytes).hexdigest()
    if dedupe:
        existing = await db.media_assets.find_one({"checksum": checksum}, {"_id": 0})
        if existing and existing.get("stored_path"):
            # Berkas identik sudah ada -> pakai ulang (hemat disk, cegah duplikat).
            patch = {"updated_at": now_iso()}
            if folder_id and existing.get("folder_id") != folder_id:
                patch["folder_id"] = folder_id
            # Alt/title yang DIKIRIM EKSPLISIT selalu menang (harapan pengguna).
            if alt:
                patch["alt"] = str(alt)[:300]
            if title:
                patch["title"] = str(title)[:200]
            await db.media_assets.update_one({"id": existing["id"]}, {"$set": patch})
            existing.update(patch)
            out = public_asset(existing)
            out["deduped"] = True
            return out

    proc = process_image(file_bytes, norm)
    base_uuid = new_id("f").replace("f_", "")
    stored_rel, thumb_rel, medium_rel = await _write_files(db, base_uuid, proc)

    display = _slug_name(filename or "", "") or f"gambar.{proc['ext']}"
    doc = {
        "id": new_id("med"),
        "folder_id": folder_id or None,
        "filename": display,
        "original_name": (filename or "")[:200],
        "stored_path": stored_rel,
        "url": _url_of(stored_rel),
        "thumb_url": _url_of(thumb_rel) if thumb_rel else _url_of(stored_rel),
        "medium_url": _url_of(medium_rel) if medium_rel else _url_of(stored_rel),
        "kind": "image",
        "mime": proc["mime"],
        "size": len(proc["data"]),
        "width": proc["width"],
        "height": proc["height"],
        "alt": (alt or "")[:300] or None,
        "title": (title or "")[:200] or None,
        "tags": [],
        "checksum": checksum,
        "source": "upload",
        "animated": proc["animated"],
        "uploaded_by": actor_id,
        "uploaded_at": now_iso(),
        "created_at": now_iso(),
        "updated_at": now_iso(),
    }
    await db.media_assets.insert_one(dict(doc))
    await log_action(actor_id, "create", "media_assets", doc["id"],
                     {"filename": display, "size": doc["size"]})
    doc.pop("_id", None)
    return public_asset(doc)


async def ingest_url(db, url: str, actor_id: str, folder_id: Optional[str] = None,
                     alt: Optional[str] = None, title: Optional[str] = None):
    """Unduh gambar dari URL eksternal lalu simpan LOKAL (anti broken image)."""
    import httpx

    raw = (url or "").strip()
    if not raw:
        raise MediaError("URL wajib diisi")
    if raw.startswith("/api/media/"):
        raise MediaError("URL ini sudah berasal dari media lokal")
    if not re.match(r"^https?://", raw, re.I):
        raise MediaError("URL harus dimulai dengan http:// atau https://")
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=25.0) as client:
            resp = await client.get(raw, headers={
                "User-Agent": "Mozilla/5.0 (compatible; CollectorParfumBot/1.0)",
                "Accept": "image/*,*/*;q=0.8",
            })
    except Exception as e:
        raise MediaError(f"Gagal mengunduh gambar: {type(e).__name__}")
    if resp.status_code >= 400:
        raise MediaError(f"Sumber menolak permintaan (HTTP {resp.status_code})")
    data = resp.content
    if not data:
        raise MediaError("Sumber tidak mengembalikan data gambar")
    if len(data) > MAX_BYTES:
        raise MediaError(f"Gambar dari URL melebihi batas {MAX_MB} MB")
    ctype = (resp.headers.get("content-type") or "").split(";")[0].strip().lower()
    name = raw.split("?")[0].rstrip("/").rsplit("/", 1)[-1] or "gambar"
    if ctype not in ALLOWED_MIME:
        ctype = guess_mime_from_name(name)
    if ctype not in ALLOWED_MIME:
        raise MediaError("URL bukan berkas gambar yang didukung")
    out = await save_upload(db, data, name, ctype, actor_id, folder_id=folder_id,
                            alt=alt, title=title)
    await db.media_assets.update_one({"id": out["id"]},
                                     {"$set": {"source": "url", "source_url": raw[:1200]}})
    out["source"] = "url"
    return out


async def register_external(db, actor_id: str, url: str, alt=None, kind="image",
                           width=None, height=None, folder_id=None):
    """Catat URL eksternal TANPA mengunduh (kompatibilitas legacy POST /admin/media)."""
    raw = (url or "").strip()[:1200]
    if not raw:
        raise MediaError("URL wajib diisi")
    doc = {
        "id": new_id("med"),
        "folder_id": folder_id or None,
        "filename": _slug_name(raw.split("?")[0].rsplit("/", 1)[-1], "gambar"),
        "url": raw,
        "thumb_url": raw,
        "medium_url": raw,
        "kind": kind or "image",
        "mime": guess_mime_from_name(raw),
        "size": 0,
        "width": int(width) if width else None,
        "height": int(height) if height else None,
        "alt": (str(alt)[:300] if alt else None),
        "title": None,
        "tags": [],
        "source": "external",
        "owner_admin_id": actor_id,
        "uploaded_by": actor_id,
        "uploaded_at": now_iso(),
        "created_at": now_iso(),
        "updated_at": now_iso(),
    }
    await db.media_assets.insert_one(dict(doc))
    await log_action(actor_id, "create", "media_assets", doc["id"], {"external": True})
    doc.pop("_id", None)
    return public_asset(doc)


SORTS = {
    "newest": [("uploaded_at", -1)],
    "oldest": [("uploaded_at", 1)],
    "name": [("filename", 1)],
    "name_desc": [("filename", -1)],
    "largest": [("size", -1)],
    "smallest": [("size", 1)],
}


def _int(v, default, lo=None, hi=None):
    try:
        n = int(v)
    except (TypeError, ValueError):
        return default
    if lo is not None:
        n = max(lo, n)
    if hi is not None:
        n = min(hi, n)
    return n


async def list_assets(db, folder_id="__all__", q=None, kind=None, sort="newest",
                      page=1, limit=48, recursive=False):
    query = {}
    if folder_id != "__all__":
        if folder_id in (None, "", "root"):
            query["folder_id"] = None
        elif recursive:
            ids = await _descendant_ids(db, folder_id)
            query["folder_id"] = {"$in": ids}
        else:
            query["folder_id"] = folder_id
    term = (q or "").strip()
    if term:
        rx = re.compile(re.escape(term), re.I)
        query["$or"] = [{"filename": rx}, {"alt": rx}, {"title": rx},
                        {"original_name": rx}, {"url": rx}]
    if kind in ("image", "video"):
        query["kind"] = kind
    elif kind == "external":
        query["source"] = "external"
    elif kind == "local":
        query["stored_path"] = {"$exists": True, "$ne": None}

    page = _int(page, 1, 1, 10000)
    limit = _int(limit, 48, 1, LIST_MAX)
    order = SORTS.get(sort or "newest", SORTS["newest"])
    total = await db.media_assets.count_documents(query)
    docs = await db.media_assets.find(query, {"_id": 0}).sort(order).skip(
        (page - 1) * limit
    ).limit(limit).to_list(limit)
    return [public_asset(d) for d in docs], total


async def get_asset(db, aid: str):
    doc = await db.media_assets.find_one({"id": aid}, {"_id": 0})
    return public_asset(doc) if doc else None


async def update_asset(db, actor_id: str, aid: str, patch: dict):
    doc = await db.media_assets.find_one({"id": aid}, {"_id": 0})
    if not doc:
        return None
    upd = {"updated_at": now_iso()}
    if "filename" in patch and patch["filename"] is not None:
        name = _slug_name(patch["filename"], "")
        if not name:
            raise MediaError("Nama berkas tidak boleh kosong")
        upd["filename"] = name
    if "alt" in patch:
        upd["alt"] = (str(patch["alt"])[:300] or None) if patch["alt"] is not None else None
    if "title" in patch:
        upd["title"] = (str(patch["title"])[:200] or None) if patch["title"] is not None else None
    if "tags" in patch and patch["tags"] is not None:
        upd["tags"] = [_slug_name(t, "")[:40] for t in list(patch["tags"])[:20] if str(t).strip()]
    if "folder_id" in patch:
        await _folder_or_error(db, patch["folder_id"])
        upd["folder_id"] = patch["folder_id"] or None
    await db.media_assets.update_one({"id": aid}, {"$set": upd})
    await log_action(actor_id, "update", "media_assets", aid, {"fields": list(upd.keys())})
    fresh = await db.media_assets.find_one({"id": aid}, {"_id": 0})
    return public_asset(fresh)


async def replace_asset(db, actor_id: str, aid: str, file_bytes: bytes, filename: str, mime: str):
    """Ganti biner berkas TANPA mengubah URL (link di produk/CMS tetap hidup)."""
    doc = await db.media_assets.find_one({"id": aid}, {"_id": 0})
    if not doc:
        return None
    stored = doc.get("stored_path")
    if not stored:
        raise MediaError("Aset ini bukan berkas lokal sehingga tidak bisa diganti")
    if len(file_bytes) > MAX_BYTES:
        raise MediaError(f"Ukuran berkas melebihi batas {MAX_MB} MB")
    norm = _norm_mime(mime, filename)
    if norm not in ALLOWED_MIME:
        raise MediaError("Tipe berkas tidak didukung")
    target_ext = stored.rsplit(".", 1)[-1].lower()
    target_mime = EXT_TO_MIME.get(target_ext, doc.get("mime") or "image/jpeg")
    if target_mime == "image/svg+xml" and norm != "image/svg+xml":
        raise MediaError("Aset SVG hanya bisa diganti dengan berkas SVG")
    if norm == "image/svg+xml" and target_mime != "image/svg+xml":
        raise MediaError("Berkas SVG tidak bisa mengganti aset raster")
    # Paksa keluaran ke format yang sama agar URL (ekstensi) tidak berubah.
    proc = process_image(file_bytes, norm)
    if proc["ext"] != target_ext and target_mime != "image/svg+xml":
        proc = process_image(file_bytes, target_mime)
        if proc["ext"] != target_ext:
            raise MediaError("Format tidak kompatibel untuk penggantian berkas")
    fpath = safe_rel_path(stored)
    if fpath is None:
        raise MediaError("Lokasi berkas tidak valid")
    fpath.parent.mkdir(parents=True, exist_ok=True)
    with open(fpath, "wb") as f:
        f.write(proc["data"])
    await _mirror_put(db, stored, proc["data"], proc["mime"])
    base_uuid = fpath.stem
    if proc.get("thumb"):
        tp = DERIVED_DIR / f"{base_uuid}_{THUMB_DIM}.webp"
        with open(tp, "wb") as f:
            f.write(proc["thumb"])
        await _mirror_put(db, _rel(tp), proc["thumb"], "image/webp")
    if proc.get("medium"):
        mp = DERIVED_DIR / f"{base_uuid}_{MEDIUM_DIM}.webp"
        with open(mp, "wb") as f:
            f.write(proc["medium"])
        await _mirror_put(db, _rel(mp), proc["medium"], "image/webp")
    upd = {
        "size": len(proc["data"]), "width": proc["width"], "height": proc["height"],
        "checksum": hashlib.sha256(file_bytes).hexdigest(),
        "original_name": (filename or "")[:200],
        "updated_at": now_iso(),
        "cache_bust": now_iso(),
    }
    await db.media_assets.update_one({"id": aid}, {"$set": upd})
    await log_action(actor_id, "update", "media_assets", aid, {"replaced": True})
    fresh = await db.media_assets.find_one({"id": aid}, {"_id": 0})
    return public_asset(fresh)


async def _remove_binaries(db, doc: dict):
    rels = []
    for key in ("stored_path",):
        if doc.get(key):
            rels.append(doc[key])
    for key in ("thumb_url", "medium_url"):
        u = doc.get(key) or ""
        if u.startswith("/api/media/"):
            rels.append(u[len("/api/media/"):])
    seen = set()
    for rel in rels:
        if rel in seen:
            continue
        seen.add(rel)
        p = safe_rel_path(rel)
        if p is not None and p.exists():
            try:
                p.unlink()
            except Exception:
                pass
        await _mirror_delete(db, rel)


async def delete_asset(db, actor_id: str, aid: str):
    doc = await db.media_assets.find_one({"id": aid}, {"_id": 0})
    if not doc:
        return None
    await _remove_binaries(db, doc)
    await db.media_assets.delete_one({"id": aid})
    await log_action(actor_id, "delete", "media_assets", aid,
                     {"filename": doc.get("filename")})
    return {"deleted": True, "id": aid}


async def bulk_delete(db, actor_id: str, ids):
    ok, fail = [], []
    for aid in list(ids or [])[:500]:
        res = await delete_asset(db, actor_id, aid)
        (ok if res else fail).append(aid)
    return {"deleted": ok, "not_found": fail, "count": len(ok)}


async def bulk_move(db, actor_id: str, ids, folder_id):
    await _folder_or_error(db, folder_id)
    ids = [i for i in list(ids or [])[:500] if i]
    if not ids:
        return {"moved": 0, "folder_id": folder_id or None}
    res = await db.media_assets.update_many(
        {"id": {"$in": ids}},
        {"$set": {"folder_id": folder_id or None, "updated_at": now_iso()}},
    )
    await log_action(actor_id, "update", "media_assets", ",".join(ids[:5]),
                     {"bulk_move": folder_id, "n": res.modified_count})
    return {"moved": int(res.modified_count), "folder_id": folder_id or None}


async def stats(db):
    total = await db.media_assets.count_documents({})
    local = await db.media_assets.count_documents({"stored_path": {"$exists": True, "$ne": None}})
    external = await db.media_assets.count_documents({"source": "external"})
    folders = await db.media_folders.count_documents({})
    size = 0
    try:
        cur = db.media_assets.aggregate([{"$group": {"_id": None, "s": {"$sum": "$size"}}}])
        async for row in cur:
            size = int(row.get("s") or 0)
    except Exception:
        size = 0
    disk = 0
    try:
        for p in MEDIA_ROOT.rglob("*"):
            if p.is_file():
                disk += p.stat().st_size
    except Exception:
        disk = 0
    return {
        "assets": total, "local_assets": local, "external_assets": external,
        "folders": folders, "bytes": size, "disk_bytes": disk,
        "max_mb": MAX_MB, "mirror": DB_MIRROR, "heif": HEIF_OK,
        "media_root": str(MEDIA_ROOT),
        "hotlinked": await count_external(db),
    }


# ============================== legacy compatibility ==============================
async def list_uploads(db, limit: int = 200):
    """Kompatibilitas GET /api/admin/uploads (list datar, terbaru dulu)."""
    docs, _ = await list_assets(db, folder_id="__all__", sort="newest", page=1,
                               limit=min(limit, LIST_MAX))
    return docs


async def migrate_legacy(db, actor_id: str = "system"):
    """Idempotent: rapikan dokumen media lama agar cocok kontrak baru.

    - `created_at` -> `uploaded_at` bila belum ada (sort konsisten).
    - `filename` diisi dari original_name / URL.
    - `stored_path` diisi untuk berkas datar lama `media/<uuid>.<ext>`.
    - `thumb_url`/`medium_url` fallback ke url.
    - `source` diberi label upload/external.
    """
    n = 0
    docs = await db.media_assets.find({}, {"_id": 0}).to_list(5000)
    for d in docs:
        patch = {}
        if not d.get("uploaded_at"):
            patch["uploaded_at"] = d.get("created_at") or now_iso()
        if not d.get("created_at"):
            patch["created_at"] = d.get("uploaded_at") or now_iso()
        if not d.get("updated_at"):
            patch["updated_at"] = patch.get("uploaded_at") or d.get("uploaded_at") or now_iso()
        url = d.get("url") or ""
        if not d.get("filename"):
            patch["filename"] = _slug_name(
                d.get("original_name") or url.split("?")[0].rsplit("/", 1)[-1], "gambar"
            )
        if "folder_id" not in d:
            patch["folder_id"] = None
        if not d.get("stored_path") and url.startswith("/api/media/"):
            rel = url[len("/api/media/"):]
            p = safe_rel_path(rel)
            if p is not None:
                patch["stored_path"] = rel
                if p.exists():
                    try:
                        patch["size"] = d.get("size") or p.stat().st_size
                    except Exception:
                        pass
                    # Mirror berkas lama agar ikut terlindungi self-heal.
                    try:
                        with open(p, "rb") as f:
                            await _mirror_put(db, rel, f.read(),
                                              guess_mime_from_name(p.name))
                    except Exception:
                        pass
        if not d.get("thumb_url"):
            patch["thumb_url"] = url
        if not d.get("medium_url"):
            patch["medium_url"] = url
        if not d.get("source"):
            patch["source"] = "upload" if url.startswith("/api/media/") else "external"
        if not d.get("kind"):
            patch["kind"] = "image"
        if patch:
            await db.media_assets.update_one({"id": d["id"]}, {"$set": patch})
            n += 1
    return {"migrated": n, "total": len(docs)}


async def ensure_default_folders(db, actor_id: str = "system"):
    """Buat folder standar bila belum ada (idempotent)."""
    created = []
    for name in ("Produk", "Banner", "Konten", "Logo & Ikon"):
        exists = await db.media_folders.find_one(
            {"parent_id": None, "name": re.compile(f"^{re.escape(name)}$", re.I)}, {"_id": 1}
        )
        if not exists:
            try:
                f = await create_folder(db, actor_id, name, None)
                created.append(f["name"])
            except MediaError:
                pass
    return created


async def ensure_folder_by_name(db, name: str, actor_id: str = "system"):
    """Kembalikan id folder root ber-nama `name`; buat bila belum ada (idempotent)."""
    clean = _slug_name(name, "Folder")
    doc = await db.media_folders.find_one(
        {"parent_id": None, "name": re.compile(f"^{re.escape(clean)}$", re.I)}, {"_id": 0, "id": 1}
    )
    if doc:
        return doc["id"]
    try:
        created = await create_folder(db, actor_id, clean, None)
        return created["id"]
    except MediaError:
        return None


# ============================== LOKALISASI URL EKSTERNAL ==============================
def _deep_replace(value, old: str, new: str):
    """Ganti string `old` -> `new` secara rekursif di dict/list/str. Kembalikan (nilai, n)."""
    if isinstance(value, str):
        return (new, 1) if value == old else (value, 0)
    if isinstance(value, list):
        total = 0
        out = []
        for v in value:
            nv, n = _deep_replace(v, old, new)
            out.append(nv)
            total += n
        return out, total
    if isinstance(value, dict):
        total = 0
        out = {}
        for k, v in value.items():
            nv, n = _deep_replace(v, old, new)
            out[k] = nv
            total += n
        return out, total
    return value, 0


async def rewrite_references(db, old_url: str, new_url: str) -> int:
    """Perbarui SEMUA tempat yang memakai `old_url` menjadi `new_url`.

    Cakupan: galeri produk, gambar kategori, foto lokasi toko, logo/QR metode bayar,
    OG image di settings, dan seluruh section CMS (`content.data`, nested).
    """
    n = 0
    # Produk (array images)
    cur = db.products.find({"images": old_url}, {"_id": 0, "id": 1, "images": 1})
    async for p in cur:
        imgs = [new_url if u == old_url else u for u in (p.get("images") or [])]
        await db.products.update_one({"id": p["id"]},
                                     {"$set": {"images": imgs, "updated_at": now_iso()}})
        n += 1
    # Field tunggal
    for coll, field in (("categories", "image"), ("occasions", "image"),
                        ("characters", "image"), ("store_locations", "photo"),
                        ("payment_methods", "logo"), ("payment_methods", "qr_image")):
        res = await db[coll].update_many({field: old_url}, {"$set": {field: new_url}})
        n += int(res.modified_count or 0)
    # Settings singleton
    res = await db.settings.update_many({"og_image": old_url}, {"$set": {"og_image": new_url}})
    n += int(res.modified_count or 0)
    # CMS content (data nested bebas)
    cur = db.content.find({}, {"_id": 0, "id": 1, "key": 1, "data": 1})
    async for c in cur:
        data, cnt = _deep_replace(c.get("data"), old_url, new_url)
        if cnt:
            await db.content.update_one({"id": c["id"]},
                                        {"$set": {"data": data, "updated_at": now_iso()}})
            n += cnt
    return n


async def localize_external(db, actor_id: str, limit: int = 300):
    """Unduh SEMUA aset ber-URL eksternal ke disk lokal + perbarui referensinya.

    Ini pagar utama terhadap \"broken image\": gambar yang tadinya hanya di-hotlink ke
    situs luar (bisa mati / memblokir) menjadi berkas milik sendiri.
    """
    docs = await db.media_assets.find(
        {"$or": [{"source": "external"},
                 {"stored_path": {"$in": [None, ""]}},
                 {"stored_path": {"$exists": False}}]},
        {"_id": 0},
    ).to_list(limit)
    out = {"converted": 0, "failed": [], "refs_updated": 0, "details": []}
    for d in docs:
        old_url = (d.get("url") or "").strip()
        if not old_url.lower().startswith(("http://", "https://")):
            continue
        try:
            fresh = await ingest_url(db, old_url, actor_id, folder_id=d.get("folder_id"),
                                     alt=d.get("alt"), title=d.get("title"))
        except MediaError as e:
            out["failed"].append({"url": old_url[:120], "error": str(e)})
            continue
        except Exception as e:  # noqa: BLE001
            out["failed"].append({"url": old_url[:120], "error": f"{type(e).__name__}"})
            continue
        refs = await rewrite_references(db, old_url, fresh["url"])
        out["refs_updated"] += refs
        out["converted"] += 1
        out["details"].append({"from": old_url[:120], "to": fresh["url"], "refs": refs})
        if d.get("id") != fresh.get("id"):
            await db.media_assets.delete_one({"id": d["id"]})
    await log_action(actor_id, "update", "media_assets", "localize",
                     {"converted": out["converted"], "refs": out["refs_updated"]})
    return out


async def count_external(db) -> int:
    return await db.media_assets.count_documents({
        "$or": [{"source": "external"},
                {"stored_path": {"$in": [None, ""]}},
                {"stored_path": {"$exists": False}}],
        "url": {"$regex": "^https?://"},
    })
