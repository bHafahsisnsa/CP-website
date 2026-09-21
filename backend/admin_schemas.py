"""admin_schemas.py — Pydantic input models untuk Admin Backoffice (Epic E5).

Dipisah dari schemas.py agar file tetap dalam batas ukuran. Semua field uang/kuantitas
BER-BOUND (ge=/gt=) untuk mencegah negative-value (kelas RC-E12). Reuse tipe bersama
(Volume/NotesPyramid/Performance/SeoMeta/VoucherScope/Campaign) dari schemas.py.
"""
from typing import List, Optional, Literal

from pydantic import BaseModel, ConfigDict, Field

from schemas import (
    Campaign, NotesPyramid, OptionDef, Performance, SeoMeta, VariantDef, Volume, VoucherScope,
)

_cfg = ConfigDict(extra="ignore")


class AdminProductInput(BaseModel):
    """Buat/ubah produk. `price` display diturunkan dari varian utama (server-side)."""
    model_config = _cfg
    name: str = Field(min_length=1, max_length=200)
    slug: Optional[str] = Field(default=None, max_length=200)
    brand: str = Field(default="Collector", max_length=120)
    category: str = Field(min_length=1)  # FK -> categories.slug
    concentration: Literal["EDP", "EDT"] = "EDP"
    gender: Literal["Pria", "Wanita", "Unisex"] = "Unisex"
    compare_at_price: Optional[int] = Field(default=None, gt=0)  # INV-C2: > price / null
    best_seller: bool = False
    is_new: bool = False
    tags: List[str] = Field(default_factory=list)
    occasions: List[str] = Field(default_factory=list)   # facet MULTI (slug taksonomi occasion)
    characters: List[str] = Field(default_factory=list)  # facet MULTI (slug taksonomi character)
    volumes: List[Volume] = Field(default_factory=list)   # legacy path (opsional bila kirim variants)
    options: List[OptionDef] = Field(default_factory=list)    # N-dimensi (baru)
    variants: List[VariantDef] = Field(default_factory=list)  # kombinasi ber-SKU (baru)
    notes: NotesPyramid = Field(default_factory=NotesPyramid)
    description: str = Field(default="", max_length=8000)
    ingredients: Optional[str] = Field(default=None, max_length=8000)
    performance: Performance = Field(default_factory=Performance)
    images: List[str] = Field(default_factory=list)
    video_url: Optional[str] = Field(default=None, max_length=1000)
    seo: SeoMeta = Field(default_factory=SeoMeta)
    status: Literal["active", "archived"] = "active"


class AdminCategoryInput(BaseModel):
    model_config = _cfg
    name: str = Field(min_length=1, max_length=120)
    slug: Optional[str] = Field(default=None, max_length=120)
    desc: str = Field(default="", max_length=1000)
    image: Optional[str] = Field(default=None, max_length=1000)
    seo: SeoMeta = Field(default_factory=SeoMeta)
    active: bool = True


class AdminFacetInput(BaseModel):
    """Input taksonomi facet (Occasion / Character). `icon` = kunci ikon lucide."""
    model_config = _cfg
    name: str = Field(min_length=1, max_length=120)
    slug: Optional[str] = Field(default=None, max_length=120)
    icon: str = Field(default="", max_length=60)
    desc: str = Field(default="", max_length=600)
    order: int = Field(default=0, ge=0)
    active: bool = True


class AdminVoucherInput(BaseModel):
    model_config = _cfg
    code: str = Field(min_length=1, max_length=40)
    type: Literal["percent", "flat", "free_shipping"]
    value: int = Field(gt=0)  # percent 1..100 divalidasi di service
    label: str = Field(default="", max_length=200)
    min_spend: int = Field(default=0, ge=0)
    usage_limit: int = Field(default=0, ge=0)
    per_user_limit: int = Field(default=0, ge=0)
    scope: VoucherScope = Field(default_factory=VoucherScope)
    starts_at: Optional[str] = None
    ends_at: Optional[str] = None
    campaign: Optional[Campaign] = None
    active: bool = True


class AdminShippingInput(BaseModel):
    model_config = _cfg
    name: str = Field(min_length=1, max_length=120)
    eta: str = Field(default="", max_length=120)
    price: int = Field(ge=0)
    active: bool = True


class AdminPaymentInput(BaseModel):
    model_config = _cfg
    group: Literal["transfer", "ewallet", "cod"]
    name: str = Field(min_length=1, max_length=120)
    extra: str = Field(default="", max_length=200)
    fee: int = Field(default=0, ge=0)
    active: bool = True
    # Aset media (E20): logo bank/e-wallet & QR statis (QRIS) — URL relatif /api/media/...
    logo: Optional[str] = Field(default=None, max_length=1000)
    qr_image: Optional[str] = Field(default=None, max_length=1000)


class AdminSettingsInput(BaseModel):
    model_config = _cfg
    store_name: Optional[str] = Field(default=None, max_length=200)
    currency: Optional[str] = Field(default=None, max_length=10)
    cod_fee: Optional[int] = Field(default=None, ge=0)
    free_shipping_threshold: Optional[int] = Field(default=None, ge=0)
    low_stock_threshold: Optional[int] = Field(default=None, ge=0)
    support_email: Optional[str] = Field(default=None, max_length=200)
    support_phone: Optional[str] = Field(default=None, max_length=60)
    # --- Growth & Analytics (Epic E7) ---
    whatsapp_number: Optional[str] = Field(default=None, max_length=40)
    site_url: Optional[str] = Field(default=None, max_length=300)
    seo_title: Optional[str] = Field(default=None, max_length=200)
    seo_description: Optional[str] = Field(default=None, max_length=400)
    og_image: Optional[str] = Field(default=None, max_length=400)
    social_instagram: Optional[str] = Field(default=None, max_length=300)
    social_tiktok: Optional[str] = Field(default=None, max_length=300)
    social_facebook: Optional[str] = Field(default=None, max_length=300)
    ga_measurement_id: Optional[str] = Field(default=None, max_length=40)
    # --- Label merek storefront ---
    # Merek luar (mis. "Hugo Boss") ditampilkan sebagai "Inspired by Hugo Boss";
    # merek rumah (house_brands) ditampilkan apa adanya.
    inspired_by_enabled: Optional[bool] = None
    inspired_by_label: Optional[str] = Field(default=None, max_length=60)
    house_brands: Optional[List[str]] = Field(default=None, max_length=50)


class BulkProductStatusInput(BaseModel):
    """Aksi massal status produk (aktifkan / arsipkan) \u2014 hasil impor katalog bisa ribuan."""
    model_config = _cfg
    status: Literal["active", "archived"]
    ids: List[str] = Field(default_factory=list, max_length=20000)
    # Cakupan alternatif: seluruh hasil filter daftar admin ('all' = tanpa filter status).
    filter_status: Optional[Literal["active", "archived", "all"]] = None
    q: Optional[str] = Field(default=None, max_length=80)
    # Pengaman: jumlah yang dilihat admin. Bila tak cocok -> aksi dibatalkan (409).
    confirm_count: Optional[int] = Field(default=None, ge=0, le=1000000)


class MediaInput(BaseModel):
    model_config = _cfg
    kind: Literal["image", "video"] = "image"
    url: str = Field(min_length=1, max_length=1200)
    alt: Optional[str] = Field(default=None, max_length=300)
    width: Optional[int] = Field(default=None, ge=0)
    height: Optional[int] = Field(default=None, ge=0)


class AdminStoreLocationInput(BaseModel):
    """Cabang toko offline (peta embed tanpa API key)."""
    model_config = _cfg
    name: str = Field(min_length=1, max_length=160)
    address: str = Field(min_length=1, max_length=400)
    phone: str = Field(default="", max_length=60)
    whatsapp: str = Field(default="", max_length=60)
    hours: str = Field(default="", max_length=400)
    maps_query: str = Field(default="", max_length=400)   # alamat atau "lat,lng" utk embed
    map_url: str = Field(default="", max_length=1000)     # tautan Google Maps (petunjuk arah)
    embed_url: str = Field(default="", max_length=2000)   # override src embed (opsional)
    place_id: str = Field(default="", max_length=200)     # utk Google reviews per-cabang (opsional)
    lat: Optional[float] = Field(default=None, ge=-90, le=90)
    lng: Optional[float] = Field(default=None, ge=-180, le=180)
    photo: str = Field(default="", max_length=1000)        # foto cabang (E20, dari Media Manager)
    order: int = Field(default=0, ge=0)
    active: bool = True


class AdminStoreReviewInput(BaseModel):
    """Ulasan KURASI MANUAL (editable admin)."""
    model_config = _cfg
    author: str = Field(min_length=1, max_length=120)
    rating: int = Field(ge=1, le=5)
    text: str = Field(default="", max_length=2000)
    location: str = Field(default="", max_length=120)
    relative_time: str = Field(default="", max_length=80)
    avatar: str = Field(default="", max_length=1000)
    active: bool = True


class AdminStoreConfigInput(BaseModel):
    """Config maps & reviews. Kunci diisi belakangan oleh admin (default kosong / embed / manual)."""
    model_config = _cfg
    maps_mode: Optional[Literal["embed", "js"]] = None
    reviews_source: Optional[Literal["manual", "google"]] = None
    google_maps_api_key: Optional[str] = Field(default=None, max_length=200)     # client (JS maps)
    google_places_api_key: Optional[str] = Field(default=None, max_length=200)   # server (reviews)
    google_place_id: Optional[str] = Field(default=None, max_length=200)
    rating_avg: Optional[float] = Field(default=None, ge=0, le=5)
    rating_count: Optional[int] = Field(default=None, ge=0)
    intro: Optional[str] = Field(default=None, max_length=2000)


class BackupExportInput(BaseModel):
    """Ekspor: pilih koleksi yang akan di-backup (unduh file)."""
    model_config = _cfg
    collections: List[str] = Field(default_factory=list)


class BackupServerCreateInput(BaseModel):
    """Buat backup tersimpan di server (file + metadata)."""
    model_config = _cfg
    collections: List[str] = Field(default_factory=list)
    note: Optional[str] = Field(default=None, max_length=300)


class RestoreServerInput(BaseModel):
    """Restore dari backup server. `collections` kosong = semua koleksi di backup."""
    model_config = _cfg
    mode: Literal["overwrite", "combine"] = "combine"
    collections: Optional[List[str]] = None


class OrderStatusInput(BaseModel):
    model_config = _cfg
    status: Literal["pending", "paid", "packed", "shipped", "completed", "cancelled"]


class ReviewStatusInput(BaseModel):
    model_config = _cfg
    status: Literal["published", "pending", "hidden"]


class MediaAsset(BaseModel):
    model_config = _cfg
    id: str
    kind: Literal["image", "video"] = "image"
    url: str
    alt: Optional[str] = None
    width: Optional[int] = Field(default=None, ge=0)
    height: Optional[int] = Field(default=None, ge=0)
    owner_admin_id: Optional[str] = None
    created_at: Optional[str] = None
