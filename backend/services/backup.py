"""services/backup.py — Backup & Restore data (admin-only).

Fitur:
  - Ekspor koleksi terpilih menjadi file JSON (Extended JSON via bson.json_util agar
    ObjectId/datetime terjaga penuh — full fidelity).
  - Simpan backup di server (file di disk + metadata di koleksi `backups`).
  - Restore dari file upload / backup server dengan 2 mode:
      * overwrite : kosongkan koleksi lalu isi penuh dari backup.
      * combine   : upsert by natural-key (DATA BACKUP MENANG) + tambah dokumen baru.

Keamanan: koleksi `sessions` & `backups` TIDAK PERNAH di-backup/restore.
Uang tetap integer (tidak diubah); dokumen disalin apa adanya.
"""
from bson import json_util
from pymongo import InsertOne, ReplaceOne
from pymongo.errors import BulkWriteError

from core_utils import new_id, now_iso
from services.backup_config import (  # konstanta dipisah agar file tetap ramping
    BACKUP_ROOT, COLLECTION_LABELS, DB_NAME, EXCLUDED, FORMAT, KEY_FIELDS, VERSION,
)


# ------------------------- Introspeksi koleksi -------------------------
async def _valid_collection_set(db) -> set:
    names = await db.list_collection_names()
    return {n for n in names if n not in EXCLUDED and not n.startswith("system.")}


async def list_collections_info(db):
    """Daftar koleksi yang bisa di-backup + jumlah dokumen (estimasi)."""
    valid = await _valid_collection_set(db)
    out = []
    for name in sorted(valid):
        try:
            count = await db[name].estimated_document_count()
        except Exception:
            count = 0
        out.append({
            "name": name,
            "label": COLLECTION_LABELS.get(name, name),
            "count": int(count),
        })
    return out


# ------------------------- Build & Serialize -------------------------
async def build_backup(db, collections):
    """Kumpulkan dokumen dari koleksi terpilih (yang valid & ada)."""
    valid = await _valid_collection_set(db)
    chosen = [c for c in (collections or []) if c in valid]
    if not chosen:
        raise ValueError("Tidak ada koleksi valid yang dipilih untuk backup.")
    data = {}
    counts = {}
    for name in chosen:
        docs = await db[name].find({}).to_list(length=None)
        data[name] = docs
        counts[name] = len(docs)
    meta = {
        "app": "collector_parfum",
        "format": FORMAT,
        "version": VERSION,
        "created_at": now_iso(),
        "db_name": DB_NAME,
        "collections": chosen,
        "counts": counts,
    }
    return {"meta": meta, "data": data}, counts


def serialize_backup(payload) -> bytes:
    """Extended JSON (json_util) -> bytes. Menjaga ObjectId/datetime."""
    return json_util.dumps(payload, indent=2, ensure_ascii=False).encode("utf-8")


def parse_backup(raw: bytes) -> dict:
    """Parse file backup -> {'meta':..., 'data': {coll: [docs]}}. Toleran beberapa bentuk."""
    if isinstance(raw, (bytes, bytearray)):
        try:
            raw = raw.decode("utf-8")
        except Exception as e:
            raise ValueError(f"Encoding file tidak valid: {e}")
    raw = (raw or "").strip()
    if not raw:
        raise ValueError("File backup kosong.")
    try:
        obj = json_util.loads(raw)
    except Exception as e:
        raise ValueError(f"File backup bukan JSON yang valid: {e}")
    if not isinstance(obj, dict):
        raise ValueError("Struktur backup tidak dikenali (harus objek JSON).")

    if isinstance(obj.get("data"), dict):
        data = obj["data"]
        meta = obj.get("meta", {}) if isinstance(obj.get("meta"), dict) else {}
    else:
        # Bentuk sederhana: {coll: [docs], ...}
        data = {k: v for k, v in obj.items() if isinstance(v, list)}
        meta = {}
    # Normalisasi: hanya simpan value list, buang koleksi terlarang.
    data = {k: v for k, v in data.items() if isinstance(v, list) and k not in EXCLUDED}
    if not data:
        raise ValueError("Backup tidak berisi data koleksi yang bisa dipulihkan.")
    return {"meta": meta, "data": data}


# ------------------------- Restore -------------------------
def _infer_keys(doc):
    for k in ("id", "slug", "code", "name"):
        if k in doc:
            return [k]
    return None


def _build_filter(name, doc):
    key_fields = KEY_FIELDS.get(name) or _infer_keys(doc)
    if not key_fields:
        return None
    flt = {}
    for k in key_fields:
        if k not in doc:
            return None
        flt[k] = doc[k]
    return flt


async def _restore_collection(db, name, docs, mode):
    coll = db[name]
    report = {
        "collection": name,
        "label": COLLECTION_LABELS.get(name, name),
        "mode": mode,
        "in_backup": len(docs),
        "deleted": 0,
        "inserted": 0,
        "updated": 0,
        "errors": 0,
        "error_detail": "",
    }

    if mode == "overwrite":
        try:
            res = await coll.delete_many({})
            report["deleted"] = res.deleted_count
        except Exception as e:
            report["errors"] += 1
            report["error_detail"] = str(e)[:300]
        if docs:
            try:
                r = await coll.insert_many([dict(d) for d in docs], ordered=False)
                report["inserted"] = len(r.inserted_ids)
            except BulkWriteError as bwe:
                det = bwe.details or {}
                report["inserted"] = int(det.get("nInserted", 0))
                report["errors"] += len(det.get("writeErrors", []))
                report["error_detail"] = str(det.get("writeErrors", [{}])[0].get("errmsg", ""))[:300]
            except Exception as e:
                report["errors"] += 1
                report["error_detail"] = str(e)[:300]
        return report

    # mode == 'combine' -> upsert by natural key (DATA BACKUP MENANG)
    ops = []
    for d in docs:
        d = dict(d)
        flt = _build_filter(name, d)
        if flt is None:
            d.pop("_id", None)
            ops.append(InsertOne(d))
        else:
            repl = {k: v for k, v in d.items() if k != "_id"}
            ops.append(ReplaceOne(flt, repl, upsert=True))
    if ops:
        try:
            r = await coll.bulk_write(ops, ordered=False)
            report["inserted"] = int((r.upserted_count or 0) + (r.inserted_count or 0))
            report["updated"] = int(r.matched_count or 0)
        except BulkWriteError as bwe:
            det = bwe.details or {}
            report["inserted"] = int(det.get("nUpserted", 0) + det.get("nInserted", 0))
            report["updated"] = int(det.get("nMatched", 0))
            report["errors"] += len(det.get("writeErrors", []))
            errs = det.get("writeErrors", [])
            if errs:
                report["error_detail"] = str(errs[0].get("errmsg", ""))[:300]
        except Exception as e:
            report["errors"] += 1
            report["error_detail"] = str(e)[:300]
    return report


async def restore(db, payload, collections, mode):
    if mode not in ("overwrite", "combine"):
        raise ValueError("mode harus 'overwrite' atau 'combine'.")
    data = payload.get("data") or {}
    names = collections if collections else list(data.keys())
    reports = []
    skipped = []
    for name in names:
        if name in EXCLUDED:
            skipped.append(name)
            continue
        if name not in data:
            skipped.append(name)
            continue
        rep = await _restore_collection(db, name, data.get(name) or [], mode)
        reports.append(rep)
    total_docs = sum(r["inserted"] + r["updated"] for r in reports)
    total_err = sum(r["errors"] for r in reports)
    return {
        "mode": mode,
        "restored": reports,
        "skipped": skipped,
        "meta": payload.get("meta", {}),
        "summary": {
            "collections": len(reports),
            "written": total_docs,
            "errors": total_err,
        },
    }


# ------------------------- Server-side backup store -------------------------
async def create_server_backup(db, collections, actor_id, note=""):
    payload, counts = await build_backup(db, collections)
    content = serialize_backup(payload)
    bid = new_id("bkp")
    fname = f"{bid}.json"
    fpath = BACKUP_ROOT / fname
    with open(fpath, "wb") as f:
        f.write(content)
    doc = {
        "id": bid,
        "filename": fname,
        "note": (note or "")[:300],
        "collections": payload["meta"]["collections"],
        "counts": counts,
        "size": len(content),
        "created_by": actor_id or "system",
        "created_at": now_iso(),
    }
    await db.backups.insert_one(dict(doc))
    doc.pop("_id", None)
    return doc


async def list_server_backups(db, limit=200):
    return await db.backups.find({}, {"_id": 0}).sort([("created_at", -1)]).to_list(limit)


async def get_server_backup(db, bid):
    return await db.backups.find_one({"id": bid}, {"_id": 0})


def read_server_file(meta) -> bytes:
    fpath = BACKUP_ROOT / meta["filename"]
    if not fpath.exists():
        raise FileNotFoundError("File backup tidak ditemukan di server.")
    with open(fpath, "rb") as f:
        return f.read()


async def delete_server_backup(db, bid):
    meta = await db.backups.find_one({"id": bid})
    if not meta:
        return None
    try:
        (BACKUP_ROOT / meta["filename"]).unlink(missing_ok=True)
    except Exception:
        # Sengaja diam: file fisik mungkin sudah hilang/dipindah. Metadata TETAP dihapus
        # supaya daftar backup tidak menyimpan entri hantu.
        pass
    await db.backups.delete_one({"id": bid})
    return True


async def restore_from_server(db, bid, collections, mode):
    meta = await db.backups.find_one({"id": bid}, {"_id": 0})
    if not meta:
        raise FileNotFoundError("Backup server tidak ditemukan.")
    raw = read_server_file(meta)
    payload = parse_backup(raw)
    return await restore(db, payload, collections, mode)
