"""routers/admin_backup.py — Backup & Restore data (admin-only). Router TIPIS.

  GET    /api/admin/backup/collections            -> daftar koleksi + jumlah dokumen
  POST   /api/admin/backup/export                 -> unduh file JSON (koleksi terpilih)
  POST   /api/admin/backup/server                 -> buat backup tersimpan di server
  GET    /api/admin/backup/server                 -> daftar backup di server
  GET    /api/admin/backup/server/{bid}/download  -> unduh file backup server
  POST   /api/admin/backup/server/{bid}/restore   -> restore dari backup server
  DELETE /api/admin/backup/server/{bid}           -> hapus backup server
  POST   /api/admin/backup/restore                -> restore dari file upload (multipart)

Mode restore: 'overwrite' (kosongkan+isi) atau 'combine' (upsert, data backup menang).
Dijaga require_role('admin') di tingkat router.
"""
import json

from fastapi import APIRouter, Depends, File, Form, HTTPException, Response, UploadFile

from admin_schemas import BackupExportInput, BackupServerCreateInput, RestoreServerInput
from core_utils import now_iso
from db import get_db
from dependencies import get_current_user, require_role
from services import audit
from services import backup as svc

router = APIRouter(prefix="/admin/backup", tags=["admin-backup"],
                   dependencies=[Depends(require_role("admin"))])


def _parse_collections(raw: str):
    """Terima JSON array string atau CSV; kosong -> None (semua koleksi di backup)."""
    if raw is None:
        return None
    raw = raw.strip()
    if not raw:
        return None
    try:
        val = json.loads(raw)
        if isinstance(val, list):
            return [str(x) for x in val]
    except Exception:
        # Sengaja diam: nilai form boleh berupa JSON list ATAU daftar dipisah koma.
        # Bila bukan JSON, jatuh ke parsing koma di bawah (bukan kondisi error).
        pass
    return [s.strip() for s in raw.split(",") if s.strip()]


@router.get("/collections")
async def list_collections():
    return await svc.list_collections_info(get_db())


@router.post("/export")
async def export_backup(payload: BackupExportInput, admin=Depends(get_current_user)):
    try:
        data, counts = await svc.build_backup(get_db(), payload.collections)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    content = svc.serialize_backup(data)
    ts = now_iso().replace(":", "").replace("-", "").split(".")[0]
    filename = f"backup_collector_{ts}.json"
    await audit.log_action(admin["id"], "backup.export", "backup", "",
                           {"collections": data["meta"]["collections"], "counts": counts})
    return Response(
        content=content,
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/server")
async def create_server_backup(payload: BackupServerCreateInput, admin=Depends(get_current_user)):
    try:
        doc = await svc.create_server_backup(
            get_db(), payload.collections, admin["id"], payload.note or ""
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    await audit.log_action(admin["id"], "backup.server_create", "backup", doc["id"],
                           {"collections": doc["collections"]})
    return doc


@router.get("/server")
async def list_server_backups():
    return await svc.list_server_backups(get_db())


@router.get("/server/{bid}/download")
async def download_server_backup(bid: str):
    meta = await svc.get_server_backup(get_db(), bid)
    if not meta:
        raise HTTPException(status_code=404, detail="Backup tidak ditemukan.")
    try:
        content = svc.read_server_file(meta)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return Response(
        content=content,
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="{meta["filename"]}"'},
    )


@router.post("/server/{bid}/restore")
async def restore_server_backup(bid: str, payload: RestoreServerInput, admin=Depends(get_current_user)):
    try:
        report = await svc.restore_from_server(get_db(), bid, payload.collections, payload.mode)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    await audit.log_action(admin["id"], "backup.restore_server", "backup", bid,
                           {"mode": payload.mode, "summary": report.get("summary")})
    return report


@router.delete("/server/{bid}")
async def delete_server_backup(bid: str, admin=Depends(get_current_user)):
    res = await svc.delete_server_backup(get_db(), bid)
    if res is None:
        raise HTTPException(status_code=404, detail="Backup tidak ditemukan.")
    await audit.log_action(admin["id"], "backup.server_delete", "backup", bid)
    return {"deleted": True, "id": bid}


@router.post("/restore")
async def restore_upload(
    file: UploadFile = File(...),
    mode: str = Form("combine"),
    collections: str = Form(""),
    admin=Depends(get_current_user),
):
    if not file:
        raise HTTPException(status_code=400, detail="File backup wajib diunggah.")
    raw = await file.read()
    try:
        payload = svc.parse_backup(raw)
        colls = _parse_collections(collections)
        report = await svc.restore(get_db(), payload, colls, mode)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    await audit.log_action(admin["id"], "backup.restore_upload", "backup",
                           (file.filename or "")[:120],
                           {"mode": mode, "summary": report.get("summary")})
    return report
