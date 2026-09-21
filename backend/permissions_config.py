"""permissions_config.py — SSOT matrix RBAC untuk Collector Parfum.

Role:
  - admin    : mengelola seluruh backoffice (produk, order, voucher, dst).
  - customer : akun pembeli (order sendiri, alamat, wishlist).

Section = modul/area akses. Dipakai dependencies.require_role / require_section.
Storefront publik (katalog, kategori, cek voucher) TIDAK butuh login -> tidak
didaftarkan sebagai section ber-guard (diakses via endpoint publik).
"""

ROLES = ("admin", "customer")

# Section -> himpunan role yang boleh akses.
SECTION_ACCESS = {
    # Area customer (akun sendiri)
    "account": {"admin", "customer"},
    "orders_self": {"admin", "customer"},
    "addresses": {"admin", "customer"},
    "wishlist": {"admin", "customer"},
    "reviews_self": {"admin", "customer"},
    # Area admin backoffice
    "admin_dashboard": {"admin"},
    "admin_products": {"admin"},
    "admin_categories": {"admin"},
    "admin_vouchers": {"admin"},
    "admin_orders": {"admin"},
    "admin_shipping": {"admin"},
    "admin_payments": {"admin"},
    "admin_reviews": {"admin"},
    "admin_users": {"admin"},
    "admin_settings": {"admin"},
    "audit": {"admin"},
}


def can_access(role: str, section: str) -> bool:
    return role in SECTION_ACCESS.get(section, set())


def allowed_sections(role: str):
    return [s for s, roles in SECTION_ACCESS.items() if role in roles]
