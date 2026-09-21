# 04 — API CONTRACT
## Collector Parfum — kontrak endpoint (SSOT FE↔BE)

> Sinkron dengan `scripts/verify_api_contract.py` & `scripts/health_check.py`.
> **Aturan bentuk:** list → **ARRAY telanjang**; detail/objek → **OBJEK telanjang**. Tanpa envelope `{items,total}`.
> **Auth:** field token = `token` (prefiks `sess_`); header `Authorization: Bearer sess_...`.
> Semua path berprefiks **`/api`**. Uang = integer rupiah.

---

## SUDAH ADA (fondasi)
### Health
- `GET /api/` → `{service,status,message}`
- `GET /api/health` → `{status,db,time}`

### Auth
- `POST /api/auth/register` `{name,email,password,phone?}` → `{token, user}`
- `POST /api/auth/login` `{email,password}` → `{token, user}`  (salah → 401)
- `GET /api/auth/me` (Bearer) → `user` (tanpa `password_hash`)

`user` = `{id,name,email,role,phone,status}`.

### Katalog (publik) — Epic E1 ✅ IMPLEMENTASI
- `GET /api/products?category&gender&concentration&tag&q&min_price&max_price&best_seller&is_new&sort&limit&skip` → `[Product,...]`
  - Hanya `status=active`. `category/gender/concentration/tag` mendukung **CSV multi-nilai** (mis. `gender=Pria,Wanita`).
  - `sort` ∈ `{featured,newest,best,low,high}` (nilai lain → `featured`).
  - `limit` clamp `1..100` (default 24), `skip` ≥ 0. Total baris di header **`X-Total-Count`** (body tetap array telanjang).
  - Param numerik/sampah di-clamp/di-abaikan (tidak pernah 5xx).
- `GET /api/products/{slug}` → `Product` (404 bila tak ada / archived)
- `GET /api/categories` → `[Category,...]` (hanya `active`)
- `GET /api/reviews?product_id` → `[Review,...]` (hanya `published`; tanpa `product_id` → semua published)

`Product` = `{id(prd_),slug,name,brand,category,concentration,gender,price,compare_at_price,best_seller,is_new,tags[],volumes[{ml,price,stock}],notes{top,heart,base},description,ingredients,performance{longevity,sillage,season},images[],video_url,seo{title,description,keywords[],og_image},rating_avg,rating_count,status}`.
`Category` = `{id(cat_),slug,name,desc,image,seo,active}`.
`Review` = `{id(rev_),product_id?,name,city,rating,quote,status,created_at}`.
> Catatan FE: `images[]` boleh kosong → storefront menurunkan bottle-art SVG generatif (parity). Field snake_case dinormalisasi ke camelCase di `services/catalog.js`.

### Voucher (publik) — Epic E2 ✅ IMPLEMENTASI
- `POST /api/vouchers/validate` `{code, subtotal, shipping?, user_id?, items?}` →
  `{valid, code, type, value, discount, label, min_spend, reason?}`
  - `discount` dihitung **SATU-SATUNYA** oleh `services/pricing.py::voucher_discount` (SSOT). Checkout (E3) memakai formula yang sama → angka SELALU cocok.
  - Invalid/kedaluwarsa/min-spend kurang/over-limit → `valid=false` + `reason` (Bahasa Indonesia). **TIDAK PERNAH 5xx** (input aneh → 422 Pydantic).
  - `items[]` (opsional) = `[{product_id?, category?, unit_price, quantity}]` untuk evaluasi `scope` (voucher berkategori/produk tertentu).
  - `shipping` (opsional, int) → dipakai voucher `free_shipping` agar diskon = ongkir.
- `GET /api/vouchers` → `[Voucher,...]` (hanya `active` & belum kedaluwarsa; untuk **Voucher Center**)

`Voucher` = `{id(vcr_),code,type∈{percent,flat,free_shipping},value,label,min_spend,usage_limit,per_user_limit,used_count,scope{category?,product_ids[]},starts_at?,ends_at?,campaign{id,name,theme}?,active}`.
> Redemption (`used_count` +1 & tulis `voucher_redemptions`) terjadi ATOMIK saat order dibuat (E3), bukan saat validate (validate bersifat advisory & race-free).

---

## RENCANA (fase business-logic — belum diimplementasi)
> Ditulis sebagai KONTRAK acuan agar FE & BE tidak drift saat dibangun.

### Katalog (publik) — ✅ SELESAI di Epic E1 (lihat blok "SUDAH ADA" di atas)
### Voucher (publik) — ✅ SELESAI di Epic E2 (lihat blok "SUDAH ADA" di atas)

### Kurir / pembayaran (publik)
- `GET /api/shipping-methods` → `[ShippingMethod,...]`
- `GET /api/payment-methods` → `[PaymentMethod,...]` (dikelompokkan di FE by `group`)

### Pembayaran (Bearer) — ✅ Epic E6 IMPLEMENTASI
> Bukti bayar TIDAK auto-lunas — perlu verifikasi admin. Uang = SSOT `record_payment`.
- `POST /api/orders/{code}/payment-proof` `{amount>0, ref?, image_url?}` → `PaymentProof` (pemilik; non-pemilik→404; order terminal/COD→400)
- `GET /api/orders/{code}/payment-proofs` → `[PaymentProof,...]` (pemilik atau admin)
- `GET /api/admin/payments?status` → `[PaymentProof,...]` (role admin)
- `PUT /api/admin/payments/{id}/verify` `{approve:bool, note?}` → `Order` (approve→record_payment; idempoten; terminal→400)

`PaymentProof` = `{id(pay_),order_code,user_id?,amount,ref?,image_url?,status∈{pending,verified,rejected},note?,verified_by?,created_at,verified_at?}`.

### Admin voucher (Bearer + role admin) — kontrak E5
- `POST/PUT/DELETE /api/admin/vouchers[/{id}]` — CRUD kampanye voucher (reuse `services/vouchers`).

### Customer (Bearer)
- `PUT /api/account/profile` `{name?,phone?}` → `User` (tanpa password_hash; email immutable)
- `GET/POST/PUT/DELETE /api/addresses[/{id}]` → alamat milik user (owner-or-404); `POST /api/addresses/{id}/default` → set default tunggal
- `GET /api/wishlist` → `{product_ids:[...]}` ; `POST /api/wishlist/toggle` `{product_id}` ; `POST /api/wishlist/merge` `{product_ids:[...]}` (guest→user)
- `POST /api/orders` `{items,address,shipping_id,payment:{group,method_id},voucher_code?,note?}` → `Order`
- `GET /api/orders` → `[Order,...]` (milik user) ; `GET /api/orders/{code}` → `Order`

### Admin Backoffice (Bearer + role `admin`) — Epic E5 ✅ IMPLEMENTASI
> Semua `/api/admin/*` dijaga `require_role('admin')` (tanpa token → 401; token customer → 403).
> Setiap mutasi ditulis ke `audit_logs` (INV-M1). Status order HANYA via `transition_order` (SM1..SM4).
- `GET /api/admin/dashboard` → `{revenue,paid_revenue,total_orders,orders_by_status,active_products,archived_products,low_stock[],low_stock_threshold,pending_reviews,recent[]}`
- `GET /api/admin/products?status&q` → `[Product,...]` (termasuk `archived`)
- `GET /api/admin/products/{id}` → `Product`
- `POST /api/admin/products` `{AdminProductInput}` → `Product`
- `PUT /api/admin/products/{id}` `{AdminProductInput}` → `Product`
- `DELETE /api/admin/products/{id}` → `{archived:true,id}` (soft-delete, INV-M2)
- `POST /api/admin/products/{id}/restore` → `{archived:false,id}`
- `POST /api/admin/products/bulk-status` `{status:'active'|'archived', ids?[], filter_status?:'active'|'archived'|'all', q?, confirm_count?}` → `{matched,modified,status}` — aksi massal (Epic E11). Cakupan `ids` ATAU `filter_status`(+`q`) yang PERSIS sama dengan filter daftar admin. Tanpa cakupan → 400; `confirm_count` tidak cocok → 409 (pengaman anti-mengubah-lebih-banyak); > `BULK_MAX` (20.000) → 400. Diaudit (INV-M1); tetap soft-delete (INV-M2).
- `GET/POST /api/admin/categories` ; `PUT/DELETE /api/admin/categories/{id}` (hapus diblok bila dipakai produk → 400)
- `GET/POST /api/admin/vouchers` ; `PUT/DELETE /api/admin/vouchers/{id}` (`used_count` read-only; hapus diblok bila ada redemption → 400)
- `GET /api/admin/orders?status` → `[Order,...]` ; `GET /api/admin/orders/{code}` → `Order`
- `PUT /api/admin/orders/{code}/status` `{status}` → `Order` (transisi ilegal → 400)
- `GET /api/admin/reviews?status&product_id` → `[Review,...]` ; `PUT /api/admin/reviews/{id}/status` `{status}` → `Review` (recompute rating, INV-C3)
- `GET/POST /api/admin/shipping-methods` ; `PUT/DELETE /api/admin/shipping-methods/{id}`
- `GET/POST /api/admin/payment-methods` ; `PUT/DELETE /api/admin/payment-methods/{id}`
- `GET/PUT /api/admin/settings` → `Settings`
- `GET /api/admin/media` → `[MediaAsset,...]` ; `POST /api/admin/media` `{kind,url,alt?,width?,height?}` → `MediaAsset` ; `DELETE /api/admin/media/{id}`
- `GET /api/admin/users` → `[User,...]` (tanpa `password_hash`)

### Export / Smart Import Produk (Epic E10 + E11) — admin-only, prefix `/api/admin/products/io`
- `GET /api/admin/products/io/export?format=csv|xlsx` → file (1 baris per varian; kolom `option1..4_name/value` + `occasions`/`characters` agar round-trip LOSSLESS)
- `GET /api/admin/products/io/template?format=csv|xlsx` → template + sheet panduan
- `POST /api/admin/products/io/analyze` (multipart `file`; query `include_rows=true|false`, `preview=0..400`) → `{session_id,expires_at,headers,suggested_mapping,total,preview_rows?[{index,data}],rows?}` (maks 8 MB; ekstensi/format salah → 400). **E12:** setiap analyze MEMBUAT SESI IMPOR; UI memakai `include_rows=false&preview=200` sehingga tidak menarik 6.426 baris ke browser (`rows` tetap dikirim bila `include_rows=true` demi kompatibilitas skrip/gate).
- `POST /api/admin/products/io/validate` `{session_id?|rows,mapping,report_limit?,product_limit?,error_limit?}` → `{summary{rows,ok,error,products}}` + **tanpa limit**: `products[],reports[]` (kompatibel lama) / **dengan limit**: `reports_head[],error_reports[],products_head[],reports_total,products_total` (row-level; baris error TIDAK menghentikan proses). **E12:** limit menurunkan respons dari ±6,4 MB → ±180 KB.
- `POST /api/admin/products/io/tiers` `{session_id?|rows,mapping,tier_column?}` → `{tier_column,tier_column_candidates[],tiers[{label,rows,products}],dimensions[{name,values[]}],combos[{key,label,values,rows}],cell_rows{tier:{comboKey:{rows,zero}}},summary{rows,products,rows_without_tier,rows_without_price,cells}}` — **E11**: struktur matriks ISI HARGA MASSAL. READ-ONLY (tak menulis DB). Deteksi tier deterministik (pola `Tier CP01` / `CP [01]`), dimensi EFEKTIF (hanya pasangan yang benar-benar berisi nilai), kombinasi hanya yang muncul di data. `cell_rows` (**E12**) memberi jumlah baris per sel agar UI bisa memperkirakan dampak matriks tanpa memindai baris di browser. Input rusak → 400, tidak pernah 5xx.
- `POST /api/admin/products/io/commit` `{session_id?|rows,mapping,mode:'add-only'|'upsert',report_limit?}` → `{created,updated,skipped,failed,errors[],skipped_details[],skipped_archived,row_errors,reports[]|error_reports[]+reports_total}` (mode lain → 400)

#### Sesi impor (E12) — admin-only, owner-scoped
> Alasan keberadaannya: wizard lama mengirim ULANG seluruh baris tiap validasi (±11,6 MB per putaran untuk 6.426 baris) sehingga pada koneksi normal muncul toast **"Gagal memvalidasi baris."** (timeout axios) meski file sah. Baris kini disimpan sekali di koleksi `import_sessions` (TTL 6 jam).
- `GET /api/admin/products/io/session/{sid}/rows?offset&limit(1..400)&indexes=1,2,3` → `{session_id,total,headers[],rows[{index,data}]}` — jendela baris untuk tabel pratinjau / mode "Hanya error". Sesi tidak ada/kedaluwarsa/bukan milik admin ini → 404.
- `POST /api/admin/products/io/session/{sid}/cells` `{cells:[{row,header,value}]}` → `{session_id,updated,total}` — patch hasil edit sel (indeks di luar batas diabaikan, bukan error).
- `POST /api/admin/products/io/session/{sid}/fill` `{mapping,tier_column?,dim_order[],matrix_price{},matrix_compare{},overwrite_price,stock?,status:'file'|'active'|'archived',concentration:'file'|'EDP'|'EDT'}` → `{session_id,stats{price_filled,compare_filled,rows_skipped_no_tier,rows_skipped_no_combo,rows_skipped_no_cell,filled_if_empty,forced,dim_order,rows},total}` — menerapkan matriks harga massal DI SERVER (UI hanya mengirim ±1,6 KB). Matriks rusak → 400, tanpa 5xx.
- `POST /api/admin/products/io/session/{sid}/close` → `{closed:true,id}` — idempoten (sesi tak ada tetap 200).

### Growth & Analytics (Epic E7)
- `POST /api/analytics/event` `{type,path?,product_id?,order_code?,session_hint?,meta?}` → `{ok,stored}` (PUBLIK, PII-scrubbed, rate-limited; tipe tak dikenal diabaikan → 200, tak pernah 5xx)
- `GET /api/sitemap.xml` → `application/xml` (URL entitas aktif; base URL diturunkan dari request/`settings.site_url`)
- `GET /api/admin/analytics?range` → `{range_days,funnel[],totals,conversion_rate,top_products[]}` (admin-only, READ)
- `GET /api/admin/crm/segments?type` → `{segments{},rows[],thresholds}` (admin-only, READ; segmen diturunkan dari orders)
- Public `GET /api/settings` diperluas: `whatsapp_number, seo_title, seo_description, og_image, social_instagram, social_tiktok, social_facebook, ga_measurement_id, site_url` (dipakai FE utk WA/SEO/sosial/GA4).

### Storefront CMS (Epic E9)
- `GET /api/content` → `{key: data}` (PUBLIK; default DI-MERGE override, selalu lengkap; storefront konsumsi)
- `GET /api/admin/content` → `{key: data}` (admin-only)
- `GET /api/admin/content/schema` → `[{key,label,group,fields[]}]` (admin-only; skema form generik)
- `PUT /api/admin/content/{key}` `{data}` → `{key,data}` (admin-only, audited; hanya field skema diterima)

`AdminProductInput` = `{name,slug?,brand,category,concentration,gender,compare_at_price?,best_seller,is_new,tags[],volumes[{ml,price,stock,sku?}],notes{top,heart,base},description,ingredients?,performance{},images[],video_url?,seo{},status}` (harga display diturunkan dari varian utama server-side).
`MediaAsset` = `{id(med_),kind∈{image,video},url,alt?,width?,height?,owner_admin_id?,created_at}`.

---

## Aturan FE (anti-drift RC-F4)
- Semua call lewat `services/apiClient.js` (`import axios, { API } from '.../services/apiClient'`).
- Guard array: `const rows = Array.isArray(res.data) ? res.data : []`.
- Segmen akhir path **literal** (✅ `${API}/orders/${code}/status` — ❌ `${API}/orders/${code}/${action}`).
- Field yang DIBACA FE harus ADA di respons BE.
