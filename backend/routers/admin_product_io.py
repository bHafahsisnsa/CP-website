"""routers/admin_product_io.py — Export & Smart Import produk (CSV/XLSX). Epic E10/E11/E12.

Prefix /admin/products/io (hindari tabrakan dgn /admin/products/{pid}). Admin-only.
  GET  /export?format=csv|xlsx              -> unduh semua produk (1 baris/varian)
  GET  /template?format=csv|xlsx            -> template + panduan
  POST /analyze  (multipart file)           -> {session_id, headers, suggested_mapping,
                                                total, preview_rows[, rows]}
  POST /validate {session_id|rows, mapping} -> {summary, reports|reports_head, error_reports,
                                                products|products_head}
  POST /tiers    {session_id|rows, ...}     -> {tiers, dimensions, combos, ...} (matriks harga)
  POST /commit   {session_id|rows, mode}    -> {created, updated, skipped, failed, errors}
  GET  /session/{sid}/rows?offset&limit&indexes  -> jendela baris untuk tabel pratinjau
  POST /session/{sid}/cells {cells:[...]}        -> patch kecil hasil edit pratinjau
  POST /session/{sid}/fill  {matrix_price, ...}  -> isi harga massal (dijalankan server)
  POST /session/{sid}/close                      -> buang sesi

SESI IMPOR (E12): baris file disimpan SEKALI oleh /analyze (services/product_io_session).
Tanpa ini wizard mengirim ulang 6.426 baris (~5,2 MB) + mengunduh ~6,4 MB pada SETIAP
validasi sehingga gagal (timeout) di koneksi normal — bug "Gagal memvalidasi baris.".
Jalur lama berbasis `rows` TETAP didukung agar skrip POC/gate tidak berubah.

Parsing/penulisan file & commit di services/product_bulk; mapping/validasi di
services/product_import (fungsi murni); isi massal di services/product_fill.
Router tetap TIPIS.
"""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel, Field

from db import get_db
from dependencies import get_current_user, require_role
from services import product_bulk as bulk
from services import product_fill as fill
from services import product_io_session as sessions
from services.product_import import suggest_mapping, validate_and_group
from services.product_tiers import analyze_tiers

router = APIRouter(prefix="/admin/products/io", tags=["admin"],
                   dependencies=[Depends(require_role("admin"))])

CSV_MIME = "text/csv"
XLSX_MIME = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
MAX_UPLOAD = 8 * 1024 * 1024  # 8 MB
MAX_INDEXES = 400


class ValidateBody(BaseModel):
    rows: List[Dict[str, Any]] = Field(default_factory=list)
    mapping: Dict[str, Optional[str]] = Field(default_factory=dict)
    session_id: Optional[str] = Field(default=None, max_length=64)
    # Batas respons (dipakai UI). Bila None -> respons LENGKAP (kompatibel skrip lama).
    report_limit: Optional[int] = Field(default=None, ge=1, le=2000)
    product_limit: Optional[int] = Field(default=None, ge=1, le=500)
    error_limit: int = Field(default=300, ge=1, le=2000)


class CommitBody(ValidateBody):
    mode: str = "upsert"  # "add-only" | "upsert"


class TiersBody(ValidateBody):
    """Analisis struktur tier harga + dimensi untuk fitur ISI HARGA MASSAL di wizard."""
    tier_column: Optional[str] = Field(default=None, max_length=200)


class CellsBody(BaseModel):
    cells: List[Dict[str, Any]] = Field(default_factory=list)


class FillBody(BaseModel):
    mapping: Dict[str, Optional[str]] = Field(default_factory=dict)
    tier_column: Optional[str] = Field(default=None, max_length=200)
    dim_order: List[str] = Field(default_factory=list)
    matrix_price: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    matrix_compare: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    overwrite_price: bool = False
    stock: Optional[str] = Field(default=None, max_length=20)
    status: str = Field(default="file", max_length=20)
    concentration: str = Field(default="file", max_length=20)


async def _category_slugs(db):
    return {c["slug"] async for c in db.categories.find({}, {"slug": 1, "_id": 0})}


async def _all_products(db):
    return [p async for p in db.products.find({}).sort("name", 1)]


def _fname(prefix, ext):
    return f"{prefix}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M')}.{ext}"


async def _rows_of(body: ValidateBody, admin_id: str) -> List[Dict[str, Any]]:
    """Baris kerja: dari SESI bila `session_id` dikirim, kalau tidak dari body (kompat)."""
    if body.session_id:
        try:
            rows, _ = await sessions.load_rows(get_db(), body.session_id, admin_id)
        except sessions.SessionNotFound as e:
            raise HTTPException(status_code=404, detail=str(e))
        return rows
    return body.rows


async def _session_rows(sid: str, admin_id: str):
    try:
        return await sessions.load_rows(get_db(), sid, admin_id)
    except sessions.SessionNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))


def _shape_validate(products, reports, body: ValidateBody) -> dict:
    """Bentuk respons /validate. Dibatasi bila UI meminta (respons MB -> KB)."""
    n_ok = sum(1 for r in reports if r["status"] == "ok")
    out: Dict[str, Any] = {
        "summary": {"rows": len(reports), "ok": n_ok, "error": len(reports) - n_ok,
                    "products": len(products)},
    }
    if body.report_limit is None and body.product_limit is None:
        out["products"] = products
        out["reports"] = reports
        return out
    r_limit = body.report_limit or 0
    p_limit = body.product_limit or 0
    out["reports_head"] = reports[:r_limit] if r_limit else []
    out["error_reports"] = [r for r in reports if r["status"] == "error"][:body.error_limit]
    out["products_head"] = products[:p_limit] if p_limit else []
    out["reports_total"] = len(reports)
    out["products_total"] = len(products)
    return out


@router.get("/export")
async def export_products(format: str = Query(default="csv")):
    products = await _all_products(get_db())
    if format == "xlsx":
        data = bulk.to_xlsx_bytes(products, with_instructions=True)
        return Response(content=data, media_type=XLSX_MIME,
                        headers={"Content-Disposition": f'attachment; filename="{_fname("produk_export", "xlsx")}"'})
    data = bulk.to_csv_bytes(products)
    return Response(content=data, media_type=CSV_MIME,
                    headers={"Content-Disposition": f'attachment; filename="{_fname("produk_export", "csv")}"'})


@router.get("/template")
async def import_template(format: str = Query(default="csv")):
    if format == "xlsx":
        data = bulk.template_xlsx_bytes()
        return Response(content=data, media_type=XLSX_MIME,
                        headers={"Content-Disposition": 'attachment; filename="template_impor_produk.xlsx"'})
    data = bulk.template_csv_bytes()
    return Response(content=data, media_type=CSV_MIME,
                    headers={"Content-Disposition": 'attachment; filename="template_impor_produk.csv"'})


@router.post("/analyze")
async def analyze_import(file: UploadFile = File(...), admin=Depends(get_current_user),
                         include_rows: bool = Query(default=True),
                         preview: int = Query(default=0, ge=0, le=sessions.MAX_PREVIEW)):
    """Baca file -> simpan baris di SESI + kembalikan pemetaan cerdas.

    `include_rows=false` (dipakai UI) menahan array baris raksasa di server: UI hanya
    menerima `preview_rows` + `session_id`, lalu bekerja lewat sesi.
    """
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="File kosong")
    if len(data) > MAX_UPLOAD:
        raise HTTPException(status_code=400, detail="File terlalu besar (maks 8 MB)")
    name = (file.filename or "").lower()
    if not (name.endswith(".csv") or name.endswith(".xlsx") or name.endswith(".xlsm")):
        raise HTTPException(status_code=400, detail="Format tidak didukung. Gunakan .csv atau .xlsx")
    try:
        headers, rows = bulk.read_table(file.filename, data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Gagal membaca file: {e}")
    if not headers:
        raise HTTPException(status_code=400, detail="Tidak ada kolom header terdeteksi")

    created = await sessions.create(get_db(), admin["id"], file.filename, headers, rows)
    out: Dict[str, Any] = {
        "session_id": created["id"],
        "expires_at": created["expires_at"],
        "headers": headers,
        "suggested_mapping": suggest_mapping(headers),
        "total": len(rows),
    }
    if preview:
        out["preview_rows"] = sessions.window(rows, 0, preview)
    if include_rows:
        out["rows"] = rows
    return out


@router.post("/validate")
async def validate_import(body: ValidateBody, admin=Depends(get_current_user)):
    rows = await _rows_of(body, admin["id"])
    cats = await _category_slugs(get_db())
    products, reports = validate_and_group(rows, body.mapping, cats)
    return _shape_validate(products, reports, body)


@router.post("/tiers")
async def detect_tiers(body: TiersBody, admin=Depends(get_current_user)):
    """Struktur matriks harga massal: tier terdeteksi x kombinasi dimensi yang benar-benar ada.

    Tidak menulis apa pun ke DB. Dipakai wizard impor untuk merender grid harga massal
    ketika file klien datang tanpa harga (variant_price = 0).
    """
    rows = await _rows_of(body, admin["id"])
    try:
        return analyze_tiers(rows, body.mapping, body.tier_column)
    except Exception as e:  # noqa: BLE001 — input file bebas; jangan pernah 5xx
        raise HTTPException(status_code=400, detail=f"Gagal menganalisis tier: {e}")


@router.post("/commit")
async def commit_import(body: CommitBody, admin=Depends(get_current_user)):
    if body.mode not in ("add-only", "upsert"):
        raise HTTPException(status_code=400, detail="mode harus 'add-only' atau 'upsert'")
    rows = await _rows_of(body, admin["id"])
    db = get_db()
    cats = await _category_slugs(db)
    products, reports = validate_and_group(rows, body.mapping, cats)
    n_err = sum(1 for r in reports if r["status"] == "error")
    result = await bulk.commit(db, admin["id"], products, mode=body.mode)
    result["row_errors"] = n_err
    if body.report_limit is None:
        result["reports"] = reports        # kompatibel skrip lama
    else:
        result["error_reports"] = [r for r in reports if r["status"] == "error"][:body.error_limit]
        result["reports_total"] = len(reports)
    return result


@router.get("/session/{sid}/rows")
async def session_rows(sid: str, admin=Depends(get_current_user),
                       offset: int = Query(default=0, ge=0),
                       limit: int = Query(default=100, ge=1, le=sessions.MAX_PREVIEW),
                       indexes: Optional[str] = Query(default=None, max_length=4000)):
    """Jendela baris sesi untuk tabel pratinjau (berurutan atau indeks tertentu)."""
    rows, info = await _session_rows(sid, admin["id"])
    picked = None
    if indexes:
        picked = []
        for part in indexes.split(",")[:MAX_INDEXES]:
            part = part.strip()
            if part.lstrip("-").isdigit():
                picked.append(int(part))
    return {
        "session_id": info["id"], "total": len(rows),
        "headers": info.get("headers") or [],
        "rows": sessions.window(rows, offset, limit, picked),
    }


@router.post("/session/{sid}/cells")
async def session_cells(sid: str, body: CellsBody, admin=Depends(get_current_user)):
    """Simpan hasil edit sel di tabel pratinjau (payload kecil, bukan seluruh baris)."""
    rows, info = await _session_rows(sid, admin["id"])
    next_rows, updated = fill.apply_cells(rows, body.cells)
    if updated:
        await sessions.save_rows(get_db(), info["id"], admin["id"], next_rows)
    return {"session_id": info["id"], "updated": updated, "total": len(next_rows)}


@router.post("/session/{sid}/fill")
async def session_fill(sid: str, body: FillBody, admin=Depends(get_current_user)):
    """Terapkan matriks harga massal DI SERVER: UI cukup mengirim angka matriksnya."""
    rows, info = await _session_rows(sid, admin["id"])
    try:
        next_rows, stats = fill.apply_fill_spec(
            rows, body.mapping,
            {
                "tier_column": body.tier_column, "matrix_price": body.matrix_price,
                "matrix_compare": body.matrix_compare,
                "overwrite_price": body.overwrite_price, "stock": body.stock,
                "status": body.status, "concentration": body.concentration,
            },
            dim_order=body.dim_order or None,
        )
    except Exception as e:  # noqa: BLE001 — matriks datang dari input bebas
        raise HTTPException(status_code=400, detail=f"Gagal menerapkan matriks: {e}")
    await sessions.save_rows(get_db(), info["id"], admin["id"], next_rows)
    return {"session_id": info["id"], "stats": stats, "total": len(next_rows)}


@router.post("/session/{sid}/close")
async def session_close(sid: str, admin=Depends(get_current_user)):
    try:
        return await sessions.close(get_db(), sid, admin["id"])
    except sessions.SessionNotFound:
        return {"closed": True, "id": sid}
