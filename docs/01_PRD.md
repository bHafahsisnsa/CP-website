# 01 — PRD (Product Requirements)
## Collector Parfum — E-commerce Parfum Premium

## 1. Visi
Toko parfum online premium berbahasa Indonesia dengan pengalaman belanja mirip marketplace
(Shopee-style checkout) namun bernuansa butik editorial (Maya-theme). Menjual parfum kurasi
merek "Collector" dengan varian volume (30/50/100 ml), notes pyramid, dan konten aroma.

## 2. Persona
- **Kolektor/Pembeli** (customer): menjelajah katalog, membaca notes, memilih volume, checkout,
  melacak pesanan, menyimpan wishlist & alamat.
- **Admin/Operator** (admin): mengelola produk (+varian/stok), kategori, voucher, pesanan
  (proses status), kurir & metode pembayaran, ulasan, dan melihat dashboard.

## 3. Ruang lingkup V1
### Storefront (publik + customer)
- Home (hero, marquee, best-seller, kategori, testimonial, FAQ).
- Shop (filter kategori/notes/gender/harga, sort).
- PDP (galeri, notes pyramid, volume selector, ATC/Buy Now, related).
- Cart + Cart Drawer, Wishlist.
- Checkout Shopee-style (alamat, kurir, pembayaran, voucher, catatan) + halaman sukses.
- Akun (profil, daftar pesanan, alamat, wishlist).

### Admin backoffice
- Dashboard ringkas (omzet, jumlah order per status, produk aktif, stok menipis).
- CRUD produk (varian volume + stok), kategori, voucher.
- Manajemen pesanan (ubah status: pending→paid→packed→shipped→completed / cancelled).
- Kelola kurir (tarif statis) & metode pembayaran (transfer/e-wallet/COD).
- Moderasi ulasan.

### Pembayaran (V1 — keputusan owner)
- **Manual**: transfer bank (konfirmasi manual) + COD (biaya tambahan Rp 4.000). Tanpa payment gateway.

### Pengiriman (V1)
- **Tarif statis** per kurir: JNE Reguler/YES, J&T Express, SiCepat, AnterAja.

## 4. Kriteria sukses
- Semua invarian (memory/INVARIANTS.md) lulus di DB bersih.
- Storefront mengambil data dari API (bukan dummy) tanpa 5xx.
- Checkout membuat order konsisten (total = subtotal − diskon + ongkir + cod_fee), stok berkurang, anti-oversell.
- Admin bisa mengubah katalog & status order; perubahan langsung terlihat di storefront.
- `bash scripts/gate.sh` → HIJAU.

## 5. Non-goals V1 (DITUNDA + alasan)
- Payment gateway (Midtrans/Xendit) — butuh kredensial & biaya; disepakati manual dulu.
- Ongkir real-time (RajaOngkir) — butuh API key; tarif statis dulu.
- Multi-kurir tracking real-time, retur otomatis, loyalty points — fase lanjutan.

## 6. Backlog (catat, jangan diam-diam)
- Upload bukti transfer + verifikasi admin.
- Notifikasi email/WhatsApp status order.
- Rekomendasi aroma berbasis notes.
