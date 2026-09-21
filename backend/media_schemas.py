"""media_schemas.py — kontrak I/O Media Manager (E20). Pydantic v2, strict-ish."""
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

_cfg = ConfigDict(extra="ignore", str_strip_whitespace=True)


class FolderIn(BaseModel):
    model_config = _cfg
    name: str = Field(min_length=1, max_length=120)
    parent_id: Optional[str] = Field(default=None, max_length=64)


class FolderPatch(BaseModel):
    model_config = _cfg
    name: Optional[str] = Field(default=None, min_length=1, max_length=120)
    parent_id: Optional[str] = Field(default=None, max_length=64)
    move: bool = False  # True bila parent_id ikut diubah (termasuk ke root/None)


class AssetPatch(BaseModel):
    model_config = _cfg
    filename: Optional[str] = Field(default=None, max_length=160)
    alt: Optional[str] = Field(default=None, max_length=300)
    title: Optional[str] = Field(default=None, max_length=200)
    tags: Optional[List[str]] = None
    folder_id: Optional[str] = Field(default=None, max_length=64)
    move: bool = False  # True bila folder_id ikut diubah (termasuk ke root/None)


class FromUrlIn(BaseModel):
    model_config = _cfg
    url: str = Field(min_length=4, max_length=1500)
    folder_id: Optional[str] = Field(default=None, max_length=64)
    alt: Optional[str] = Field(default=None, max_length=300)
    title: Optional[str] = Field(default=None, max_length=200)
    download: bool = True  # False = catat URL eksternal apa adanya (legacy)


class BulkIds(BaseModel):
    model_config = _cfg
    ids: List[str] = Field(default_factory=list, max_length=500)


class BulkMove(BaseModel):
    model_config = _cfg
    ids: List[str] = Field(default_factory=list, max_length=500)
    folder_id: Optional[str] = Field(default=None, max_length=64)


class LegacyMediaIn(BaseModel):
    """Kompatibilitas POST /api/admin/media (V1): daftarkan URL.

    `download=True` (default baru) MENGUNDUH gambar ke penyimpanan lokal agar tidak
    pernah broken. Kirim `download=False` untuk perilaku lama (hotlink).
    """
    model_config = _cfg
    kind: Literal["image", "video"] = "image"
    url: str = Field(min_length=1, max_length=1500)
    alt: Optional[str] = Field(default=None, max_length=300)
    width: Optional[int] = Field(default=None, ge=0)
    height: Optional[int] = Field(default=None, ge=0)
    folder_id: Optional[str] = Field(default=None, max_length=64)
    download: bool = True
