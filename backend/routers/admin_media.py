"""routers/admin_media.py — Media Manager admin (E20). Router TIPIS, RBAC admin-only.

SSOT endpoint media. URUTAN route penting: path spesifik (`/folders`, `/assets`,
`/upload`, ...) DIDAFTARKAN LEBIH DULU daripada route legacy `/{mid}` agar tidak
saling menelan.

Folders
  GET    /api/admin/media/folders            -> {root, folders[]}
  GET    /api/admin/media/folders/tree       -> {root, tree[]} (bertingkat)
  POST   /api/admin/media/folders            -> buat folder
  PATCH  /api/admin/media/folders/{fid}      -> rename / pindah
  DELETE /api/admin/media/folders/{fid}?cascade=false

Assets
  GET    /api/admin/media/assets             -> list (folder_id,q,kind,sort,page,limit)
                                                header X-Total-Count
  POST   /api/admin/media/upload             -> multipart banyak berkas (files[])
  POST   /api/admin/media/from-url           -> unduh URL eksternal -> simpan lokal
  GET    /api/admin/media/assets/{aid}
  PATCH  /api/admin/media/assets/{aid}       -> alt/title/filename/tags/folder
  POST   /api/admin/media/assets/{aid}/replace  -> ganti berkas, URL tetap
  DELETE /api/admin/media/assets/{aid}
  POST   /api/admin/media/assets/bulk-delete
  POST   /api/admin/media/assets/bulk-move
  GET    /api/admin/media/stats
  POST   /api/admin/media/maintenance/migrate -> rapikan dokumen lama (idempotent)

Legacy (dipertahankan agar FE/skrip lama tetap jalan)
  GET    /api/admin/media                    -> list datar
  POST   /api/admin/media                    -> registrasi/unduh URL
  DELETE /api/admin/media/{mid}              -> hapus aset
  GET/POST /api/admin/uploads                -> alias list/upload satu berkas
"""
from typing import List, Optional

from fastapi import (APIRouter, Depends, File, Form, HTTPException, Query,
                     Response, UploadFile)

from db import get_db
from dependencies import get_current_user, require_role
from media_schemas import (AssetPatch, BulkIds, BulkMove, FolderIn, FolderPatch,
                           FromUrlIn, LegacyMediaIn)
from services import media as media_svc

router = APIRouter(prefix="/admin/media", tags=["admin-media"],
                   dependencies=[Depends(require_role("admin"))])


def _bad(e: Exception):
    return HTTPException(status_code=400, detail=str(e))


# ============================== FOLDERS ==============================
@router.get("/folders")
async def list_folders():
    return await media_svc.list_folders(get_db())


@router.get("/folders/tree")
async def folders_tree():
    return await media_svc.folder_tree(get_db())


@router.post("/folders", status_code=201)
async def create_folder(payload: FolderIn, admin=Depends(get_current_user)):
    try:
        return await media_svc.create_folder(get_db(), admin["id"], payload.name,
                                            payload.parent_id)
    except media_svc.MediaError as e:
        raise _bad(e)


@router.patch("/folders/{fid}")
async def update_folder(fid: str, payload: FolderPatch, admin=Depends(get_current_user)):
    try:
        res = await media_svc.update_folder(
            get_db(), admin["id"], fid, name=payload.name,
            parent_id=(payload.parent_id if payload.move else "__keep__"),
        )
    except media_svc.MediaError as e:
        raise _bad(e)
    if res is None:
        raise HTTPException(status_code=404, detail="Folder tidak ditemukan")
    return res


@router.delete("/folders/{fid}")
async def delete_folder(fid: str, cascade: bool = Query(default=False),
                        admin=Depends(get_current_user)):
    res = await media_svc.delete_folder(get_db(), admin["id"], fid, cascade=cascade)
    if res is None:
        raise HTTPException(status_code=404, detail="Folder tidak ditemukan")
    return res


# ============================== ASSETS ==============================
@router.get("/assets")
async def list_assets(
    response: Response,
    folder_id: Optional[str] = Query(default=None,
                                     description="kosong=semua, 'root'=tanpa folder"),
    q: Optional[str] = None,
    kind: Optional[str] = None,
    sort: str = "newest",
    page: int = 1,
    limit: int = 48,
    recursive: bool = False,
):
    fid = "__all__" if folder_id in (None, "", "all") else folder_id
    items, total = await media_svc.list_assets(
        get_db(), folder_id=fid, q=q, kind=kind, sort=sort, page=page,
        limit=limit, recursive=recursive,
    )
    response.headers["X-Total-Count"] = str(total)
    return {"items": items, "total": total, "page": page, "limit": limit}


@router.post("/upload", status_code=201)
async def upload_assets(
    files: List[UploadFile] = File(default=[]),
    file: Optional[UploadFile] = File(default=None),
    folder_id: Optional[str] = Form(default=None),
    alt: Optional[str] = Form(default=None),
    title: Optional[str] = Form(default=None),
    admin=Depends(get_current_user),
):
    incoming = [f for f in (files or []) if f is not None]
    if file is not None:
        incoming.append(file)
    if not incoming:
        raise HTTPException(status_code=400, detail="Tidak ada berkas yang dikirim")
    db = get_db()
    fid = folder_id or None
    if fid in ("", "root", "null"):
        fid = None
    ok, failed = [], []
    for f in incoming[:40]:
        try:
            data = await f.read()
            doc = await media_svc.save_upload(
                db, data, f.filename or "", f.content_type or "", admin["id"],
                folder_id=fid, alt=alt, title=title,
            )
            ok.append(doc)
        except media_svc.MediaError as e:
            failed.append({"filename": f.filename or "", "error": str(e)})
        except Exception as e:  # jangan pernah 5xx karena satu berkas rusak
            failed.append({"filename": f.filename or "",
                           "error": f"Gagal memproses berkas ({type(e).__name__})"})
    if not ok and failed:
        raise HTTPException(status_code=400,
                            detail=failed[0]["error"] if len(failed) == 1 else
                            "; ".join(f"{x['filename']}: {x['error']}" for x in failed[:3]))
    return {"uploaded": ok, "failed": failed, "count": len(ok)}


@router.post("/from-url", status_code=201)
async def from_url(payload: FromUrlIn, admin=Depends(get_current_user)):
    db = get_db()
    try:
        if payload.download:
            return await media_svc.ingest_url(db, payload.url, admin["id"],
                                              folder_id=payload.folder_id,
                                              alt=payload.alt, title=payload.title)
        return await media_svc.register_external(db, admin["id"], payload.url,
                                                alt=payload.alt,
                                                folder_id=payload.folder_id)
    except media_svc.MediaError as e:
        raise _bad(e)


@router.post("/assets/bulk-delete")
async def bulk_delete(payload: BulkIds, admin=Depends(get_current_user)):
    return await media_svc.bulk_delete(get_db(), admin["id"], payload.ids)


@router.post("/assets/bulk-move")
async def bulk_move(payload: BulkMove, admin=Depends(get_current_user)):
    try:
        return await media_svc.bulk_move(get_db(), admin["id"], payload.ids,
                                        payload.folder_id)
    except media_svc.MediaError as e:
        raise _bad(e)


@router.post("/assets/{aid}/replace")
async def replace_asset(aid: str, file: UploadFile = File(...),
                        admin=Depends(get_current_user)):
    try:
        data = await file.read()
        res = await media_svc.replace_asset(get_db(), admin["id"], aid, data,
                                           file.filename or "", file.content_type or "")
    except media_svc.MediaError as e:
        raise _bad(e)
    if res is None:
        raise HTTPException(status_code=404, detail="Media tidak ditemukan")
    return res


@router.get("/assets/{aid}")
async def get_asset(aid: str):
    res = await media_svc.get_asset(get_db(), aid)
    if res is None:
        raise HTTPException(status_code=404, detail="Media tidak ditemukan")
    return res


@router.patch("/assets/{aid}")
async def update_asset(aid: str, payload: AssetPatch, admin=Depends(get_current_user)):
    patch = payload.model_dump(exclude_unset=True)
    patch.pop("move", None)
    if not payload.move:
        patch.pop("folder_id", None)
    try:
        res = await media_svc.update_asset(get_db(), admin["id"], aid, patch)
    except media_svc.MediaError as e:
        raise _bad(e)
    if res is None:
        raise HTTPException(status_code=404, detail="Media tidak ditemukan")
    return res


@router.delete("/assets/{aid}")
async def delete_asset(aid: str, admin=Depends(get_current_user)):
    res = await media_svc.delete_asset(get_db(), admin["id"], aid)
    if res is None:
        raise HTTPException(status_code=404, detail="Media tidak ditemukan")
    return res


@router.get("/stats")
async def media_stats():
    return await media_svc.stats(get_db())


@router.post("/maintenance/migrate")
async def maintenance_migrate(admin=Depends(get_current_user)):
    db = get_db()
    res = await media_svc.migrate_legacy(db, admin["id"])
    res["default_folders"] = await media_svc.ensure_default_folders(db, admin["id"])
    return res


@router.post("/maintenance/localize")
async def maintenance_localize(limit: int = Query(default=300, ge=1, le=1000),
                               admin=Depends(get_current_user)):
    """Unduh semua gambar ber-URL eksternal ke disk lokal + perbarui referensinya.

    Pagar utama anti \"broken image\": setelah ini tidak ada lagi gambar yang
    bergantung pada situs pihak ketiga.
    """
    return await media_svc.localize_external(get_db(), admin["id"], limit=limit)


# ============================== LEGACY ==============================
@router.get("")
async def legacy_list():
    """Legacy GET /api/admin/media — list datar (dipakai FE lama / skrip)."""
    return await media_svc.list_uploads(get_db(), limit=200)


@router.post("", status_code=201)
async def legacy_add(payload: LegacyMediaIn, admin=Depends(get_current_user)):
    """Legacy POST /api/admin/media — sekarang MENGUNDUH ke lokal (anti broken)."""
    db = get_db()
    try:
        if payload.download and payload.kind == "image" and \
                str(payload.url).lower().startswith(("http://", "https://")):
            return await media_svc.ingest_url(db, payload.url, admin["id"],
                                              folder_id=payload.folder_id,
                                              alt=payload.alt)
        return await media_svc.register_external(
            db, admin["id"], payload.url, alt=payload.alt, kind=payload.kind,
            width=payload.width, height=payload.height, folder_id=payload.folder_id,
        )
    except media_svc.MediaError as e:
        raise _bad(e)


@router.delete("/{mid}")
async def legacy_delete(mid: str, admin=Depends(get_current_user)):
    res = await media_svc.delete_asset(get_db(), admin["id"], mid)
    if res is None:
        raise HTTPException(status_code=404, detail="Media tidak ditemukan")
    return res


# ---------- alias /api/admin/uploads (kompatibilitas ContentForm & skrip lama) ----------
uploads_router = APIRouter(prefix="/admin/uploads", tags=["admin-uploads"],
                           dependencies=[Depends(require_role("admin"))])


@uploads_router.post("")
async def upload_single(file: UploadFile = File(...),
                       folder_id: Optional[str] = Form(default=None),
                       alt: Optional[str] = Form(default=None),
                       admin=Depends(get_current_user)):
    if not file:
        raise HTTPException(status_code=400, detail="File wajib")
    try:
        data = await file.read()
        fid = folder_id or None
        if fid in ("", "root", "null"):
            fid = None
        return await media_svc.save_upload(
            get_db(), data, file.filename or "", file.content_type or "",
            admin["id"], folder_id=fid, alt=alt,
        )
    except media_svc.MediaError as e:
        raise _bad(e)


@uploads_router.get("")
async def uploads_list():
    return await media_svc.list_uploads(get_db(), limit=200)
