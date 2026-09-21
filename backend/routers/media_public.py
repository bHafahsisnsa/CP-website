"""routers/media_public.py — penyaji berkas media lokal (E20).

  GET/HEAD /api/media/{path}   -> berkas dari <MEDIA_ROOT>/{path}

Mengganti `StaticFiles` lama karena route ini SELF-HEALING: bila berkas hilang dari
disk (container di-rebuild / pod pindah replika) berkas dipulihkan otomatis dari
mirror MongoDB lokal sebelum disajikan. Inilah pagar anti "broken image".

Route PUBLIK (tanpa auth) — gambar produk & konten harus bisa dibaca storefront.
Path di-sanitasi (anti traversal) di `services.media.safe_rel_path`.
"""
import hashlib

from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import FileResponse

from db import get_db
from services import media as media_svc

router = APIRouter(prefix="/media", tags=["media"])

CACHE_CONTROL = "public, max-age=31536000, stale-while-revalidate=86400"


@router.api_route("/{path:path}", methods=["GET", "HEAD"])
async def serve_media(path: str, request: Request):
    resolved = await media_svc.resolve_file(get_db(), path)
    if not resolved:
        raise HTTPException(status_code=404, detail="Berkas media tidak ditemukan")
    fpath, mime = resolved
    try:
        st = fpath.stat()
        etag = 'W/"' + hashlib.md5(
            f"{fpath.name}-{st.st_mtime_ns}-{st.st_size}".encode()
        ).hexdigest() + '"'
    except Exception:
        etag = None
    headers = {"Cache-Control": CACHE_CONTROL, "X-Media-Source": "local-disk"}
    if etag:
        headers["ETag"] = etag
        if request.headers.get("if-none-match") == etag:
            return Response(status_code=304, headers=headers)
    return FileResponse(str(fpath), media_type=mime, headers=headers)
