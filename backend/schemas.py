"""schemas.py — Pydantic models (kontrak data) untuk Collector Parfum.

Prinsip:
- Response = OBJEK/ARRAY telanjang (tanpa envelope {items,total}).
- Token field = 'token' (bukan 'access_token').
- Semua uang & kuantitas = integer rupiah BER-BOUND (ge=/gt=) — cegah nilai negatif
  (kelas bug 'negative-value'; ditegakkan scripts/guardrails/verify_numeric_bounds.py).
- extra='ignore' agar field internal Mongo (_id) tidak bocor / tidak error.

Model di sini menjadi acuan bagi fase business-logic berikutnya (products, orders, dst).
"""
from typing import List, Optional, Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field

_cfg = ConfigDict(extra="ignore")


# ---------------- Auth / Users ----------------
class RegisterRequest(BaseModel):
    model_config = _cfg
    name: str
    email: EmailStr
    password: str = Field(min_length=6)
    phone: Optional[str] = None


class LoginRequest(BaseModel):
    model_config = _cfg
    email: EmailStr
    password: str


class PublicUser(BaseModel):
    model_config = _cfg
    id: str
    name: str
    email: EmailStr
    role: Literal["admin", "customer"] = "customer"
    phone: Optional[str] = None
    status: Literal["active", "inactive"] = "active"


class AuthResponse(BaseModel):
    model_config = _cfg
    token: str
    user: PublicUser


# ---------------- Catalog: Products & Categories ----------------
class Volume(BaseModel):
    """Varian produk. Identitas runtime = (type, ml). `type` = dimensi opsional
    (mis. Standard/Premium); "" = produk tanpa tipe (satu dimensi ukuran saja).
    `sku` unik per varian (auto-generate bila kosong) = kunci upsert import."""
    model_config = _cfg
    type: str = Field(default="", max_length=60)  # dimensi tipe (opsional); "" = tanpa tipe
    ml: int = Field(gt=0)
    price: int = Field(gt=0)  # E1 INV: setiap varian harus punya harga > 0
    stock: int = Field(default=0, ge=0)
    compare_at_price: Optional[int] = Field(default=None, gt=0)  # harga coret per varian (null / > price)
    sku: Optional[str] = None


class OptionDef(BaseModel):
    """Definisi satu dimensi varian (mis. Konsentrasi, Tipe, Ukuran) + nilai-nilainya (terurut)."""
    model_config = _cfg
    name: str = Field(max_length=60)
    values: List[str] = Field(default_factory=list)


class VariantDef(BaseModel):
    """Satu kombinasi varian ber-identitas SKU — SSOT stok & harga (N-dimensi)."""
    model_config = _cfg
    sku: Optional[str] = None
    options: dict = Field(default_factory=dict)   # {DimName: value}
    price: int = Field(gt=0)
    stock: int = Field(default=0, ge=0)
    compare_at_price: Optional[int] = Field(default=None, gt=0)


class NotesPyramid(BaseModel):
    model_config = _cfg
    top: List[str] = []
    heart: List[str] = []
    base: List[str] = []


class Performance(BaseModel):
    model_config = _cfg
    longevity: Optional[str] = None
    sillage: Optional[str] = None
    season: Optional[str] = None


class SeoMeta(BaseModel):
    """SEO metadata (dipakai penuh oleh E7; di E1 hanya disimpan & dikembalikan)."""
    model_config = _cfg
    title: Optional[str] = None
    description: Optional[str] = None
    keywords: List[str] = []
    og_image: Optional[str] = None


class Product(BaseModel):
    model_config = _cfg
    id: str
    slug: str
    name: str
    brand: str = "Collector"
    category: str  # FK -> categories.slug
    concentration: Literal["EDP", "EDT"] = "EDP"
    gender: Literal["Pria", "Wanita", "Unisex"] = "Unisex"
    price: int = Field(gt=0)  # harga display = harga varian utama (> 0)
    compare_at_price: Optional[int] = Field(default=None, gt=0)  # INV-C2: null atau > price
    best_seller: bool = False
    is_new: bool = False
    tags: List[str] = []
    occasions: List[str] = []   # facet MULTI (mis. office, gym, date-night) — filter storefront
    characters: List[str] = []  # facet MULTI karakter aroma (mis. fresh, rose, woody)
    volumes: List[Volume] = Field(default_factory=list)  # legacy (derived) — kompat export/impor
    options: List[OptionDef] = Field(default_factory=list)    # N-dimensi (SSOT definisi dimensi)
    variants: List[VariantDef] = Field(default_factory=list)  # kombinasi ber-SKU (SSOT stok/harga)
    price_min: int = Field(default=0, ge=0)
    price_max: int = Field(default=0, ge=0)
    compare_at_min: Optional[int] = Field(default=None, gt=0)
    compare_at_max: Optional[int] = Field(default=None, gt=0)
    notes: NotesPyramid = Field(default_factory=NotesPyramid)
    description: str = ""
    ingredients: Optional[str] = None
    performance: Performance = Field(default_factory=Performance)
    images: List[str] = []           # kosong => FE derive bottle-art (parity SVG generatif)
    video_url: Optional[str] = None  # referensi URL saja (bukan upload) di E1
    seo: SeoMeta = Field(default_factory=SeoMeta)
    rating_avg: float = Field(default=0.0, ge=0, le=5)   # derivasi dari reviews (INV-C3)
    rating_count: int = Field(default=0, ge=0)
    status: Literal["active", "archived"] = "active"
    created_at: Optional[str] = None


class Category(BaseModel):
    model_config = _cfg
    id: str
    slug: str
    name: str
    desc: str = ""
    image: Optional[str] = None
    seo: SeoMeta = Field(default_factory=SeoMeta)
    active: bool = True


class Facet(BaseModel):
    """Taksonomi facet MULTI storefront (Occasion / Character). Dikelola admin.
    `icon` = kunci ikon lucide (mis. 'briefcase') yang dipetakan di FE."""
    model_config = _cfg
    id: str
    slug: str
    name: str
    icon: str = ""
    desc: str = ""
    order: int = Field(default=0, ge=0)
    active: bool = True


# ---------------- Vouchers (Epic E2 — Shopee-like campaigns) ----------------
class VoucherScope(BaseModel):
    """Pembatasan cakupan voucher. Kosong/None = berlaku seluruh keranjang."""
    model_config = _cfg
    category: Optional[str] = None       # FK -> categories.slug
    product_ids: List[str] = Field(default_factory=list)


class Campaign(BaseModel):
    """Metadata kampanye (banner/tema) — display concern (BR-6)."""
    model_config = _cfg
    id: Optional[str] = None
    name: Optional[str] = None
    theme: Optional[str] = None


class Voucher(BaseModel):
    model_config = _cfg
    id: str
    code: str
    type: Literal["percent", "flat", "free_shipping"]
    value: int = Field(gt=0)  # percent 1..100; flat=rupiah; free_shipping diabaikan (set 1)
    label: str = ""
    min_spend: int = Field(default=0, ge=0)
    usage_limit: int = Field(default=0, ge=0)      # 0 = tak terbatas (global)
    per_user_limit: int = Field(default=0, ge=0)   # 0 = tak terbatas (per user)
    used_count: int = Field(default=0, ge=0)
    scope: VoucherScope = Field(default_factory=VoucherScope)
    starts_at: Optional[str] = None                # ISO-8601; null = tanpa batas awal
    ends_at: Optional[str] = None                  # ISO-8601; null = tanpa batas akhir
    campaign: Optional[Campaign] = None
    active: bool = True


class VoucherRedemption(BaseModel):
    """Catatan pemakaian voucher (ditulis E3 saat order dibuat) — akun per-user + audit."""
    model_config = _cfg
    id: str
    voucher_code: str
    user_id: Optional[str] = None
    order_code: str
    discount: int = Field(default=0, ge=0)
    created_at: Optional[str] = None


class VoucherLineIn(BaseModel):
    """Baris item untuk evaluasi scope voucher (opsional)."""
    model_config = _cfg
    product_id: Optional[str] = None
    category: Optional[str] = None
    unit_price: int = Field(default=0, ge=0)
    quantity: int = Field(default=0, ge=0)


class VoucherValidateIn(BaseModel):
    model_config = _cfg
    code: str
    subtotal: int = Field(default=0, ge=0)
    shipping: int = Field(default=0, ge=0)
    user_id: Optional[str] = None
    items: Optional[List[VoucherLineIn]] = None


class VoucherValidateOut(BaseModel):
    model_config = _cfg
    valid: bool = False
    code: str = ""
    type: Optional[str] = None
    value: int = Field(default=0, ge=0)
    discount: int = Field(default=0, ge=0)
    label: str = ""
    min_spend: int = Field(default=0, ge=0)
    reason: Optional[str] = None


# ---------------- Addresses ----------------
class Address(BaseModel):
    model_config = _cfg
    id: str
    user_id: str
    name: str
    phone: str
    street: str
    district: Optional[str] = None
    city: str
    province: str
    postal: Optional[str] = None
    label: str = "Rumah"
    is_default: bool = False


# ---------------- Shipping & Payment methods ----------------
class ShippingMethod(BaseModel):
    model_config = _cfg
    id: str
    name: str
    eta: str = ""
    price: int = Field(default=0, ge=0)
    active: bool = True


class PaymentMethod(BaseModel):
    model_config = _cfg
    id: str
    group: Literal["transfer", "ewallet", "cod"]
    name: str
    extra: str = ""
    fee: int = Field(default=0, ge=0)
    active: bool = True


# ---------------- Orders ----------------
class OrderItem(BaseModel):
    model_config = _cfg
    product_id: str  # FK -> products.id
    slug: str = ""
    name: str
    image: Optional[str] = None
    concentration: Optional[str] = None
    variant_type: str = ""       # label dimensi non-ukuran saat beli (snapshot); "" = tanpa tipe
    sku: Optional[str] = None    # SKU varian saat beli (snapshot) — identitas utama
    options: dict = Field(default_factory=dict)  # {DimName: value} snapshot (N-dimensi)
    volume_ml: int = Field(gt=0)
    unit_price: int = Field(ge=0)
    quantity: int = Field(gt=0)


ORDER_STATUSES = ("pending", "paid", "packed", "shipped", "completed", "cancelled")
PAYMENT_STATUSES = ("belum_bayar", "dp", "lunas")


# ---- Request bodies (checkout & cart, Epic E3) ----
class CreateOrderItem(BaseModel):
    model_config = _cfg
    product_id: str
    sku: Optional[str] = Field(default=None, max_length=60)   # identitas varian utama (baru)
    variant_type: str = Field(default="", max_length=120)     # legacy/composite (fallback)
    volume_ml: Optional[int] = Field(default=None, gt=0)      # legacy (fallback) — resolve via sku
    quantity: int = Field(gt=0, le=999)


class CreateAddress(BaseModel):
    model_config = _cfg
    name: str = Field(min_length=1, max_length=120)
    phone: str = Field(min_length=1, max_length=40)
    street: str = Field(min_length=1, max_length=300)
    district: Optional[str] = None
    city: str = Field(min_length=1, max_length=120)
    province: str = Field(min_length=1, max_length=120)
    postal: Optional[str] = None
    label: str = "Rumah"


class PaymentSelection(BaseModel):
    model_config = _cfg
    group: Literal["transfer", "ewallet", "cod"]
    method_id: str


class CreateOrderRequest(BaseModel):
    model_config = _cfg
    items: List[CreateOrderItem] = Field(min_length=1)
    address: CreateAddress
    shipping_id: str
    payment: PaymentSelection
    voucher_code: Optional[str] = None
    note: str = ""


class CartItemIn(BaseModel):
    model_config = _cfg
    product_id: str
    sku: Optional[str] = Field(default=None, max_length=60)   # identitas varian utama (baru)
    variant_type: str = Field(default="", max_length=120)     # legacy/composite (fallback)
    volume_ml: Optional[int] = Field(default=None, gt=0)      # legacy (fallback)
    quantity: int = Field(gt=0, le=999)


class CartPayload(BaseModel):
    model_config = _cfg
    items: List[CartItemIn] = Field(default_factory=list)
    voucher_code: Optional[str] = None
    note: str = ""


# ---- Account (profile, address, wishlist — Epic E4) ----
class ProfileUpdate(BaseModel):
    model_config = _cfg
    name: Optional[str] = Field(default=None, max_length=120)
    phone: Optional[str] = Field(default=None, max_length=40)


class AddressInput(BaseModel):
    model_config = _cfg
    name: str = Field(min_length=1, max_length=120)
    phone: str = Field(min_length=1, max_length=40)
    street: str = Field(min_length=1, max_length=300)
    district: Optional[str] = None
    city: str = Field(min_length=1, max_length=120)
    province: str = Field(min_length=1, max_length=120)
    postal: Optional[str] = None
    label: str = "Rumah"
    is_default: bool = False


class WishlistToggle(BaseModel):
    model_config = _cfg
    product_id: str = Field(min_length=1)


class WishlistMerge(BaseModel):
    model_config = _cfg
    product_ids: List[str] = Field(default_factory=list)


class Order(BaseModel):
    model_config = _cfg
    id: str
    code: str
    user_id: Optional[str] = None
    items: List[OrderItem] = []
    subtotal: int = Field(default=0, ge=0)
    discount: int = Field(default=0, ge=0)
    voucher_code: Optional[str] = None
    shipping: dict = {}
    payment: dict = {}
    cod_fee: int = Field(default=0, ge=0)
    total: int = Field(default=0, ge=0)
    paid_amount: int = Field(default=0, ge=0)
    address: dict = {}
    note: str = ""
    status: Literal[ORDER_STATUSES] = "pending"  # type: ignore
    payment_status: Literal[PAYMENT_STATUSES] = "belum_bayar"  # type: ignore
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


# ---------------- Payments (Epic E6) ----------------
class PaymentProofInput(BaseModel):
    """Owner mencatat bukti bayar (transfer/e-wallet). Tidak auto-lunas (perlu verifikasi admin)."""
    model_config = _cfg
    amount: int = Field(gt=0)  # rupiah > 0 (INV-P1); tak boleh negatif/0
    ref: Optional[str] = Field(default=None, max_length=120)
    image_url: Optional[str] = Field(default=None, max_length=1200)


class VerifyProofInput(BaseModel):
    model_config = _cfg
    approve: bool
    note: Optional[str] = Field(default=None, max_length=300)


class PaymentProof(BaseModel):
    model_config = _cfg
    id: str
    order_code: str            # FK -> orders.code
    user_id: Optional[str] = None
    amount: int = Field(gt=0)
    ref: Optional[str] = None
    image_url: Optional[str] = None
    status: Literal["pending", "verified", "rejected"] = "pending"
    note: Optional[str] = None
    verified_by: Optional[str] = None
    created_at: Optional[str] = None
    verified_at: Optional[str] = None


# ---------------- Analytics (Epic E7) ----------------
class AnalyticsEventIn(BaseModel):
    """Event first-party (publik). Tipe tak dikenal diabaikan; PII di-scrub di service (INV-G3)."""
    model_config = _cfg
    type: str = Field(max_length=40)
    path: Optional[str] = Field(default=None, max_length=300)
    product_id: Optional[str] = Field(default=None, max_length=60)
    order_code: Optional[str] = Field(default=None, max_length=40)
    session_hint: Optional[str] = Field(default=None, max_length=64)
    meta: Optional[dict] = None


# ---------------- Content CMS (Epic E9) ----------------
class ContentUpdateIn(BaseModel):
    """Update satu section konten storefront (data divalidasi/di-coerce per skema di service)."""
    model_config = _cfg
    data: dict = Field(default_factory=dict)


# ---------------- Reviews ----------------
class Review(BaseModel):
    model_config = _cfg
    id: str
    product_id: Optional[str] = None
    user_id: Optional[str] = None
    name: str
    city: Optional[str] = None
    rating: int = Field(default=5, ge=1, le=5)
    quote: str = ""
    avatar: Optional[str] = None
    status: Literal["published", "pending", "hidden"] = "published"
