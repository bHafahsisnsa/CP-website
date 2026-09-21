# 03 — DATA MODEL (Koleksi Kanonik)
## Collector Parfum — SSOT skema MongoDB

> Sinkron dengan `scripts/verify_contract.py` (CANONICAL_COLLECTIONS) & `scripts/verify_schema.py`.
> Menambah koleksi/field baru WAJIB diperbarui di sini + didaftarkan ke gate terkait (docs/07 §7).
> Uang = **integer rupiah**. Waktu = ISO-8601 UTC string.

## Ringkasan koleksi & id-prefix
| Koleksi | id-prefix | Keterangan |
|---------|-----------|------------|
| `users` | `usr_` | akun admin & customer |
| `sessions` | (token) | token `sess_` → user_id, expires_at |
| `products` | `prd_` | parfum + varian volume/stok |
| `categories` | `cat_` | keluarga aroma (slug unik) |
| `vouchers` | `vcr_` | kode diskon |
| `carts` | `crt_` | keranjang server-side (opsional, hybrid localStorage) |
| `orders` | `ord_` | pesanan; `code` = `CP########` (number-series) |
| `addresses` | `adr_` | buku alamat customer |
| `shipping_methods` | (id slug) | kurir + tarif statis |
| `payment_methods` | (id slug) | metode bayar transfer/ewallet/cod |
| `reviews` | `rev_` | ulasan/testimoni |
| `wishlists` | `wsh_` | wishlist per user |
| `counters` | (name) | number-series (orders.seq) |
| `settings` | `store` | konfigurasi toko (singleton) |
| `audit_logs` | `aud_` | jejak audit |
| `voucher_redemptions` | `vrd_` | catatan pemakaian voucher (per-user + audit; E2/E3) |
| `media_assets` | `med_` | pustaka media (referensi URL image/video; E5) |
| `payment_proofs` | `pay_` | bukti bayar transfer/e-wallet (verifikasi manual admin; E6) |
| `import_sessions` | `imp_` | sesi wizard impor produk: baris file diunggah SEKALI, TTL 6 jam (E12) |

---

## Field per koleksi

### users
`id(usr_)`, `name`, `email`(unik), `password_hash`(bcrypt, JANGAN dikembalikan), `role`∈{admin,customer}, `phone?`, `status`∈{active,inactive}, `created_at`.

### sessions
`token`(sess_, unik), `user_id`, `created_at`, `expires_at`(ISO).

### products
`id(prd_)`, `slug`(unik), `name`, `brand`, `category`(FK→categories.slug), `concentration`∈{EDP,EDT}, `gender`∈{Pria,Wanita,Unisex}, `price`(int = harga varian TERMURAH / "mulai dari"), `compare_at_price?`, `best_seller`(bool), `is_new`(bool), `tags[]`, `volumes[]`={`type`(dimensi tipe opsional; ""=tanpa tipe, mis. Standard/Premium),`ml`,`price`,`stock`,`compare_at_price?`,`sku`(unik per varian, auto-generate bila kosong)}, `notes`={`top[]`,`heart[]`,`base[]`}, `description`, `performance`={`longevity`,`sillage`,`season`}, `images[]`, `status`∈{active,archived}. **Varian = matriks (type × ml); identitas runtime = (type, ml) — kombinasi WAJIB unik. INV-C1.**

### categories
`id(cat_)`, `slug`(unik), `name`, `desc`, `image?`, `active`(bool).

### vouchers
`id(vcr_)`, `code`(unik, uppercase), `type`∈{percent,flat,free_shipping}, `value`(int>0; percent 1..100; flat=rupiah; free_shipping diabaikan/set 1), `label`, `min_spend`(int>=0), `usage_limit`(int>=0; 0=tak terbatas global), `per_user_limit`(int>=0; 0=tak terbatas per user), `used_count`(int>=0), `scope`={`category?`(slug),`product_ids?`[]} (kosong=seluruh keranjang), `starts_at?`(ISO), `ends_at?`(ISO), `campaign?`={`id`,`name`,`theme`}, `active`(bool). (Epic E2)

### carts
Cart hybrid (guest=localStorage, user login=server). `id(crt_)`, `user_id`(unik, upsert), `items[]`={`product_id`,`variant_type`(""=tanpa tipe),`volume_ml`,`quantity`}, `voucher_code?`, `note`, `created_at`, `updated_at`.

### orders
`id(ord_)`, `code`(CP########, unik), `user_id?`, `items[]`={`product_id`(FK),`slug`,`name`,`image`,`concentration`,`variant_type`(snapshot; ""=tanpa tipe),`sku`(snapshot varian),`volume_ml`,`unit_price`,`quantity`}, `subtotal`(int), `discount`(int), `voucher_code?`, `shipping`={`method_id`,`name`,`price`,`eta`}, `payment`={`group`∈{transfer,ewallet,cod},`method_id`}, `cod_fee`(int), `total`(int), `paid_amount`(int), `address`(snapshot), `note`, `status`∈{pending,paid,packed,shipped,completed,cancelled}, `payment_status`∈{belum_bayar,dp,lunas}, `created_at`, `updated_at`.

### addresses
`id(adr_)`, `user_id`, `name`, `phone`, `street`, `district?`, `city`, `province`, `postal?`, `label`, `is_default`(bool).

### shipping_methods
`id`(slug: jne-reg,...), `name`, `eta`, `price`(int), `active`(bool).

### payment_methods
`id`(slug: bca,shopeepay,cod,...), `group`∈{transfer,ewallet,cod}, `name`, `extra`, `fee`(int), `active`(bool).

### reviews
`id(rev_)`, `product_id?`(FK), `user_id?`, `name`, `city?`, `rating`(1..5), `quote`, `avatar?`, `status`∈{published,pending,hidden}.

### wishlists
`id(wsh_)`, `user_id`, `product_ids[]`.

### counters
`name`(unik), `seq`(int).

### settings (singleton id="store")
`id`, `store_name`, `currency`, `cod_fee`, `free_shipping_threshold`, `support_email`, `support_phone`.
Growth (E7): `whatsapp_number`, `site_url`, `seo_title`, `seo_description`, `og_image`, `social_instagram`, `social_tiktok`, `social_facebook`, `ga_measurement_id`.
Label merek (E11): `inspired_by_enabled`(bool, default `true`), `inspired_by_label`(str, default `"Inspired by"`), `house_brands`(list[str], default `["Collector Parfum","Collector"]`).
Merek produk yang TIDAK ada di `house_brands` ditampilkan storefront sebagai `"{inspired_by_label} {brand}"`; JSON-LD tetap memakai merek rumah.

### audit_logs
`id(aud_)`, `actor_id`, `action`, `entity`, `entity_id`, `meta`, `created_at`.

### voucher_redemptions
`id(vrd_)`, `voucher_code`(FK→vouchers.code), `user_id?`, `order_code`(FK→orders.code), `discount`(int>=0), `created_at`. Ditulis ATOMIK saat order dibuat (E3) untuk akun per-user + audit (CE1: `used_count == #orders == #redemptions`).

### media_assets
`id(med_)`, `kind`∈{image,video}, `url`, `alt?`, `width?`, `height?`, `owner_admin_id?`, `created_at`. Pustaka media reusable untuk editor produk/kategori (Epic E5). V1 = referensi URL (tanpa upload nyata; upload nyata via integration agent). Field `images[]`/`video_url`/`image` boleh mereferensikan `media_assets.url`.

### payment_proofs
`id(pay_)`, `order_code`(FK→orders.code), `user_id?`, `amount`(int>0), `ref?`, `image_url?`, `status`∈{pending,verified,rejected}, `note?`, `verified_by?`(admin id), `created_at`, `verified_at?`. Bukti bayar transfer/e-wallet yang diunggah pemilik order (Epic E6). Verifikasi admin bersifat IDEMPOTEN (hanya `pending`→`verified/rejected` sekali; INV-P1). Approve → `services.orders.record_payment` (naikkan `orders.paid_amount` → derive `payment_status`; maju `pending`→`paid` bila lunas). **Invarian:** INV-P1 `orders.paid_amount == Σ bukti verified` (non-COD); INV-P2 tak ada verifikasi pada order terminal. COD: uang tunai diterima saat `completed` (tanpa bukti transfer).

### analytics_events
`id(evt_)`, `type`∈{page_view,product_view,add_to_cart,begin_checkout,purchase,search,view_cart,wa_click}, `path?`, `product_id?`(soft-ref products), `order_code?`(soft-ref orders.code), `session_hint?`(anonim), `meta?`(dict pendek, **bebas-PII**), `created_at`. Event analitik first-party (Epic E7) — publik, di-scrub PII di server (INV-G3), rate-limited & bounded. Read-mostly: dipakai admin untuk funnel/top-produk/konversi. **Invarian:** INV-G1 `purchase.order_code`→orders (tak ada revenue hantu); INV-G3 tak simpan email/telepon; INV-G4 SEO title produk/kategori aktif tersedia/ter-default. CRM (INV-G2) **diturunkan dari orders** — tak ada koleksi segmen terpisah.

### content
`id`(= section key, mis. `hero`/`footer`/`about`), `data`(dict konten sesuai skema section di `content_registry.py`), `created_at`, `updated_at`, `updated_by?`. Singleton per-section untuk **Storefront CMS** (Epic E9) — semua teks/tautan/gambar editorial storefront. Publik `GET /api/content` mengembalikan **default DI-MERGE override** (selalu lengkap → storefront tak pernah kosong). Admin edit per-key (audited, hanya field skema yang diterima). **Invarian:** INV-C1 setiap section kanonik punya dokumen (default ter-seed); INV-C2 hanya field skema tersimpan (anti-injection).

---

### import_sessions
Dua bentuk dokumen dalam satu koleksi (dibedakan `kind`), semuanya kedaluwarsa otomatis lewat **TTL index** pada `expires_at` (6 jam):
- **meta** — `id`(`imp_…`), `kind:'meta'`, `admin_id`(pemilik; owner-scoped anti-IDOR), `filename`, `headers[]`, `total`, `chunks`, `created_at`, `updated_at`, `expires_at`.
- **chunk** — `id`(`<sid>#<seq>`), `kind:'chunk'`, `session_id`, `seq`, `rows[]` (maks `CHUNK_SIZE` baris/dokumen agar aman dari batas BSON 16 MB), `expires_at`.

**Kenapa ada (E12):** wizard impor dulu menahan seluruh baris di browser dan MENGIRIM ULANG semuanya pada SETIAP validasi. Untuk katalog klien 6.426 baris itu ±5,2 MB request + ±6,4 MB response per validasi, sehingga pada koneksi normal (±1 Mbps unggah) axios timeout dan admin melihat **"Gagal memvalidasi baris."** walau filenya 100% sah. Sekarang `/analyze` menyimpan baris sekali di sini dan langkah berikutnya (`/validate`, `/tiers`, `/session/{id}/fill`, `/session/{id}/cells`, `/commit`) hanya mengirim `session_id` + perubahan kecil.

**Invarian:** sesi hanya dapat dibaca/diubah oleh `admin_id` pembuatnya (selain gate `require_role('admin')`); tidak ada data produk final di sini (murni buffer impor); dokumen tidak pernah menjadi sampah permanen karena TTL.

---

## Alias TERLARANG (drift RC-1)
`items/catalog/parfums → products` · `category → categories` · `voucher/promo/coupons → vouchers` ·
`cart → carts` · `order/pesanan/transactions → orders` · `address → addresses` ·
`shipping/kurir/ongkir → shipping_methods` · `payment/payments → payment_methods` ·
`testimonials/ulasan → reviews` · `customers/customer → users` · `config → settings` ·
`analytics/tracking/telemetry/events → analytics_events` · `segments/crm → (diturunkan dari orders, bukan koleksi)` ·
`cms/konten/pages/blocks/sections → content`.
