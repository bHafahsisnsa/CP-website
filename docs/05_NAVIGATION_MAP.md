# 05 — NAVIGATION MAP (Information Architecture)
## Collector Parfum

> SSOT navigasi. Menu di luar peta ini = **STOP & ASK** (cegah "menu liar").
> Dua surface terpisah: **storefront** (publik/customer) & **admin** (backoffice).

## A. Storefront (publik + customer)
| Path | Halaman | Akses |
|------|---------|-------|
| `/` | Home | publik |
| `/shop` | Katalog + filter/sort | publik |
| `/parfum/:slug` | Product Detail (PDP) | publik |
| `/keranjang` | Cart | publik |
| `/checkout` | Checkout Shopee-style | publik (login opsional V1) |
| `/pesanan-sukses` | Order Success | publik |
| `/wishlist` | Wishlist | publik (sinkron akun bila login) |
| `/tentang` | About | publik |
| `/kontak` | Contact | publik |
| `/akun` | Account (profil, pesanan, alamat) | customer (login) |

Komponen global: AnnouncementBar, SiteHeader, SiteFooter, MobileBottomNav,
CartDrawer, SearchDrawer, MobileMenuDrawer, QuickViewModal.

## B. Admin backoffice (role: admin) — ✅ Epic E5 IMPLEMENTASI
Kedalaman maksimal 2 level. Surface terpisah `/admin/*` (shell sendiri, tema serasi design_guidelines.md).
| Grup | Item | Rute |
|------|------|------|
| Ringkasan | Dashboard | `/admin` |
| Katalog | Produk (+editor `/admin/produk/:id`), Kategori, Ulasan | `/admin/produk`, `/admin/kategori`, `/admin/ulasan` |
| Penjualan | Pesanan (+detail `/admin/pesanan/:code`), Voucher | `/admin/pesanan`, `/admin/voucher` |
| Pengaturan | Kurir & Tarif, Metode Pembayaran, Pengaturan Toko, Pengguna | `/admin/pengaturan` |

> Non-admin yang membuka `/admin/*` → form masuk admin (bila belum login) atau redirect + toast "Akses ditolak" (bila login sebagai customer).

## C. Aturan
- Tambah menu HANYA lewat konfigurasi navigasi + render shell; jangan tebar route liar.
- Active state jelas, breadcrumb bila > 2 level, empty state mengarahkan aksi.
- 1 konsep = 1 istilah (lihat glosarium koleksi kanonik di 03_DATA_MODEL.md).
