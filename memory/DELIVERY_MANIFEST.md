# 📦 DELIVERY MANIFEST — Collector Parfum

> Kontrak deliverable yang **bisa dihitung & ditagih** per fase (ditegakkan `scripts/verify_delivery.py`).
> Format baris: `- [P0|P1] <kind>: <ident>` dengan kind ∈ doc|script|page|endpoint|collection|invariant.
> `verify_delivery.py` membaca `ACTIVE_PHASE` lalu memverifikasi semua P0 fase itu BENAR-BENAR ada.
> Item P0 belum ada → DILARANG klaim selesai.

ACTIVE_PHASE: E13

---

## PHASE E13 — KONTEN RESMI COLLECTOR PARFUM + DEPLOY VPS SEKALI JADI
STATUS: ✅ SELESAI (2026-08-04)

Dua permintaan user: (1) memakai informasi asli dari situs lama `collectorparfum.com` sebagai
konten situs baru; (2) menyediakan **satu skrip deploy** untuk VPS (mengacu pola repo
`SOMMERVILLE-FINAL`), project baru di VPS yang sama, domain dikosongkan dulu sehingga dilayani
lewat IP VPS `148.230.102.29`.

Konten resmi yang dipindahkan (default CMS `content_registry.py`, jadi ikut ter-seed di instalasi
baru DAN bisa diedit admin di `/admin/konten`):
- Sejarah asli: didirikan **8 September 1970** di Jalan Kolektor Bandung → pindah Jl. Paledang
  No. 14 → menetap **Jl. Paledang No. 58** → cabang Pasirkaliki No. 148A & Gatot Subroto No. 271.
- Tagline resmi **“Refill Perfume Distributor Since 1970”**, announcement bar, hero, story strip,
  trust strip, dan section video disesuaikan (parfum refill, ukuran 30/50/60/100 ml).
- Kontak asli: WA +62 857-2000-0105 & +62 857-2013-7777, `cs@collectorparfum.com`,
  LINE @collectorparfum, IG @collectorparfum, toko pusat Jl. Paledang No. 58, jam
  Senin–Jumat 09.00–17.00 · Sabtu 09.00–14.00 WIB.
- FAQ asli (cara order via WA/LINE, proses 1×24 jam / partai besar 2–5 hari kerja, estimasi
  Jabodetabek 1–3 hari & luar Jabodetabek 2–7 hari, kirim ke Indonesia/Brunei/Malaysia,
  same-day Bandung bila bayar sebelum 10.00 WIB, penjelasan katalog “Inspired by”).
- Fallback frontend (ContactPage/AboutPage/bottleArt/MobileMenuDrawer) diselaraskan agar tidak
  ada lagi placeholder Jakarta / `hello@collectorparfum.id`.
- Harga & metode pembayaran TIDAK diubah (permintaan user), produk demo tetap 12.

Deliverable (ditagih verify_delivery):
- [P0] script: deploy.sh
- [P0] script: backend/requirements-prod.txt
- [P0] doc: DEPLOYMENT_VPS.md
- [P0] script: backend/content_registry.py
- [P1] script: scripts/seed_data.py

Bukti:
- `bash -n deploy.sh` lolos; 13 langkah idempoten (apt, node 20, MongoDB 8.0 fallback 7.0,
  user+clone, data persisten, venv, .env, yarn build, supervisor :8003, seed bila DB kosong,
  nginx server block terpisah, SSL opsional, UFW + health check).
- Simulasi jalur deploy di container: venv baru + `requirements-prod.txt` (14 paket) terpasang
  **8 detik**, `uvicorn server:app --workers 2` menyala, `/api/health` → `{"status":"ok","db":true}`,
  `/api/products` 200 (12 produk), `/api/admin/products` tanpa token 401, `openapi.json` memuat
  92 endpoint termasuk `io/session/*`, `io/tiers`, `bulk-status`, unduh template `.xlsx` 200
  (openpyxl OK), `scripts/seed_data.py` sukses pada database bersih, konten `about` berisi 1970.
- Port aman: 8001 KBS8 · 8002 Garment ERP · **8003 Collector Parfum**; database `collector_parfum`;
  media/backup di `/var/lib/collector-parfum` supaya tahan rebuild.

---

## PHASE E12 — SESI IMPOR: MENGHILANGKAN KEGAGALAN "GAGAL MEMVALIDASI BARIS."
STATUS: ✅ SELESAI & DITUTUP RESMI (2026-08-03 — POC 69/0, bukti browser throttle 1,2 Mbps,
dan pass testing agent iterasi 36–40: backend 70/70 + frontend 4 batch tanpa bug)

Masalah nyata yang dipecahkan (dilaporkan user dengan file `tests/user_uploads/testimport.xlsx`,
6.426 baris / 1.071 produk, `variant_price = 1000`): wizard impor menahan SELURUH baris di
browser dan MENGIRIMNYA ULANG pada SETIAP validasi (validate live, debounce 450 ms). Satu
putaran memindahkan ±5,2 MB request + ±6,4 MB response = ±11,6 MB. Di jaringan cepat itu
lolos; pada koneksi normal (±1,2 Mbps unggah) melewati timeout axios 60 detik sehingga
muncul toast **"Gagal memvalidasi baris."** dan bilah ringkasan MACET di "0 valid" —
padahal file 100% sah (dibuktikan: lewat API langsung hasilnya 6426 ok / 0 error / 1071 produk).

Perbaikan: baris disimpan SEKALI di koleksi `import_sessions` (meta + chunk, TTL 6 jam,
owner-scoped). Validasi/tier/isi-massal/commit kini hanya mengirim `session_id` + perubahan
kecil; respons validate dibatasi (`reports_head` + `error_reports` + `products_head`).

Deliverable (ditagih verify_delivery):
- [P0] script: backend/services/product_io_session.py
- [P0] script: backend/services/product_fill.py
- [P0] script: scripts/test_import_session_poc.py
- [P0] endpoint: /api/admin/products/io/session/{sid}/rows
- [P0] endpoint: /api/admin/products/io/session/{sid}/cells
- [P0] endpoint: /api/admin/products/io/session/{sid}/fill
- [P0] endpoint: /api/admin/products/io/session/{sid}/close
- [P0] collection: import_sessions
- [P0] page: AdminProductImportPage
- [P1] page: ImportPreviewTable
- [P1] script: scripts/qa_cleanup.py
- [P1] script: scripts/guardrails/verify_auth_resilience.py

Bukti:
- `python scripts/test_import_session_poc.py` → **69 PASS / 0 FAIL**. Angka kunci:
  analyze 4,86 MB → **157 KB**; request validate 5,2 MB → **0,91 KB**; respons validate
  6,4 MB → **182 KB**; "Terapkan matriks" (24 angka) hanya **1,59 KB** payload dan mengisi
  6.426 harga di server; rows/cells/fill/close + RBAC & 15 probe adversarial tanpa 5xx.
- Bukti browser (Playwright + CDP `Network.emulateNetworkConditions`, 1,2 Mbps unggah):
  SEBELUM perbaikan → toast "Gagal memvalidasi baris." pada t+71s, ringkasan macet "0 valid".
  SESUDAH perbaikan → validasi selesai **13 detik** (6.426 valid / 0 error / 1.071 produk),
  isi matriks → valid dalam **5 detik**, tombol "Impor 1071 Produk" aktif, status pratinjau
  `archived`, 0 error/warning console.
- Kompatibilitas mundur (jalur `rows` lama tetap hidup): `test_tier_matrix_poc.py` 63/0,
  `verify_user_import.py` 46/0, `test_product_io_core.py` 22/0,
  `test_shop_and_import_e2e.py` 155/0.
- **Hardening tambahan saat penutupan E12 (BUG-AUTH-01):** sesi klien tidak lagi terhapus oleh
  gangguan jaringan/502 (root cause `AuthContext` memanggil `apiLogout()` pada SETIAP kegagalan
  `/auth/me`). Deliverable: `scripts/guardrails/verify_auth_resilience.py` (INV-AUTH-01, di-wire ke
  `gate.sh`) + state pemulihan sesi `admin-session-offline` & `account-session-offline`.
  Bukti: intercept `/api/auth/me` → 502 ⇒ panel pemulihan tampil, token DIPERTAHANKAN, "Coba Lagi"
  memulihkan sesi tanpa login manual; token palsu (401) tetap memunculkan form login; logout manual
  tetap membuang token. Diverifikasi testing agent iterasi 39 (admin) & 40 (customer).
- Pemangkasan sesi per-admin `MAX_PER_ADMIN = 5` (`services/product_io_session.py::_prune`) —
  7 sesi berurutan ⇒ hanya 5 meta tersisa, sesi terbaru tetap dapat dipakai (verifikasi backend it.36).

---

---

## PHASE E11 — IMPOR KATALOG MASSAL: MATRIKS HARGA TIER + AKSI MASSAL + LABEL MEREK
STATUS: ✅ SELESAI (2026-08-03 — POC skala penuh 63/0 dengan file klien 6.426 baris / 1.071 produk)

Masalah nyata yang dipecahkan: file katalog klien
(`tests/user_uploads/IMPOR_PRODUK_COLLECTOR_PARFUM_1.xlsx`) datang dengan `variant_price = 0`
di SELURUH 6.426 baris, sehingga wizard impor hanya bisa melaporkan "6426 error / 0 produk"
tanpa jalan keluar di UI. Sekarang admin mengisi matriks kecil (TIER × KOMBINASI DIMENSI,
mis. 4 tier × 6 kombinasi = 24 sel) lalu seluruh baris terisi sekali klik; hasil impor masuk
sebagai draft (`archived`, stok 0) dan bisa diaktifkan MASSAL dari halaman Produk.

Deliverable (ditagih verify_delivery):
- [P0] script: backend/services/product_tiers.py
- [P0] script: scripts/test_tier_matrix_poc.py
- [P0] script: scripts/verify_user_import.py
- [P0] script: frontend/src/components/admin/import/importBulkFill.js
- [P0] endpoint: /api/admin/products/io/tiers
- [P0] endpoint: /api/admin/products/bulk-status
- [P0] page: ImportBulkFillPanel
- [P0] page: ImportTierMatrix
- [P0] page: ProductsBulkBar
- [P1] script: frontend/src/lib/brand.js
- [P1] script: frontend/src/store/SettingsContext.js

Bukti: `python scripts/test_tier_matrix_poc.py` → 63 PASS / 0 FAIL (tier CP01 532 / CP02 417 /
CP03 107 / EXCLUSIVE 15 produk; dimensi efektif Ukuran×Tipe; 24 sel → 6.426 harga terisi;
commit 1.071 produk `archived` stok 0 dengan harga PERSIS per sel matriks; storefront 404 saat
draft; bulk-status mengaktifkan 1.071 sekaligus; adversarial & RBAC tanpa 5xx; cleanup bersih)
+ `python scripts/verify_user_import.py` → 46 PASS / 0 FAIL
+ `bash scripts/gate.sh` HIJAU termasuk `validate_compliance` yang sebelumnya MERAH
(refactor AdminProductImportPage 520→315, AdminBackupPage 578→467, services/backup.py 350→282).

---

## PHASE E9 — STOREFRONT CMS (semua konten storefront dapat diedit dari admin)
STATUS: ✅ SELESAI (Epic E9 — content registry, schema-driven editor; diverifikasi ulang
2026-08-03: `scripts/test_e9_core.py` → 16 PASS / 0 FAIL)

Deliverable (ditagih verify_delivery):
- [P0] script: backend/content_registry.py
- [P0] script: backend/services/content.py
- [P0] script: backend/routers/content.py
- [P0] script: backend/routers/admin_content.py
- [P0] script: scripts/test_e9_core.py
- [P0] endpoint: /api/content
- [P0] endpoint: /api/admin/content
- [P0] endpoint: /api/admin/content/schema
- [P0] collection: content
- [P0] page: AdminContentPage
- [P0] invariant: INV-C1 (setiap section punya dokumen default)
- [P0] invariant: INV-C2 (hanya field skema tersimpan — anti-injection)

Bukti (target): scripts/test_e9_core.py PASS + bash scripts/gate.sh HIJAU (verify_data_integrity L11 INV-C1/C2, verify_rbac_guards admin_content dijaga, verify_delivery no-orphan) + testing_agent_v3 (edit section → tampil di storefront, RBAC, default aman).

---

## PHASE E7 — GROWTH & ANALYTICS (SEO, first-party analytics, WhatsApp/chat shell, CRM segmen)
STATUS: ✅ SELESAI (Epic E7 — GATE HIJAU + test_e7_core 11/11 + testing_agent BE 27/27 · FE 100%, 2026-07-06)

Deliverable (ditagih verify_delivery):
- [P0] doc: docs/roadmap/E7_GROWTH_ANALYTICS.md
- [P0] script: backend/routers/analytics.py
- [P0] script: backend/routers/admin_analytics.py
- [P0] script: backend/services/analytics.py
- [P0] script: backend/services/crm.py
- [P0] script: scripts/test_e7_core.py
- [P0] endpoint: /api/analytics/event
- [P0] endpoint: /api/sitemap.xml
- [P0] endpoint: /api/admin/analytics
- [P0] endpoint: /api/admin/crm/segments
- [P0] collection: analytics_events
- [P0] page: AdminAnalyticsPage
- [P0] page: AdminCrmPage
- [P0] invariant: INV-G1 (purchase event → orders; tak ada revenue hantu)
- [P0] invariant: INV-G3 (analytics events bebas-PII)
- [P0] invariant: INV-G4 (SEO meta produk/kategori aktif tersedia/ter-default)

Bukti (target): scripts/test_e7_core.py PASS + bash scripts/gate.sh HIJAU (verify_cross_entity CE6, verify_data_integrity L10 INV-G1/G3/G4, verify_rbac_guards admin_analytics/crm dijaga, verify_adversarial_5xx event fuzz aman, verify_delivery D2 no-orphan) + testing_agent_v3 (event funnel, SEO meta/JSON-LD, WA click-to-chat, admin analytics & CRM, RBAC deviant).

---

## PHASE E6 — PAYMENTS (bukti bayar transfer/e-wallet + verifikasi admin, COD-on-delivery)
STATUS: ✅ SELESAI (GATE HIJAU 29/29 + test_e6_core 14/14, diverifikasi 2026-07-06)

Deliverable (ditagih verify_delivery):
- [P0] doc: docs/roadmap/E6_PAYMENTS.md
- [P0] script: backend/routers/payments.py
- [P0] script: backend/routers/admin_payments.py
- [P0] script: backend/services/payments.py
- [P0] script: scripts/test_e6_core.py
- [P0] endpoint: /api/orders/{code}/payment-proof
- [P0] endpoint: /api/orders/{code}/payment-proofs
- [P0] endpoint: /api/admin/payments
- [P0] collection: payment_proofs
- [P0] page: OrderSuccessPage
- [P0] page: AdminPaymentsPage
- [P0] invariant: INV-P1 (paid_amount == Σ bukti verified; idempoten)
- [P0] invariant: INV-P2 (tak ada verifikasi pada order terminal)

Bukti (target): scripts/test_e6_core.py PASS + bash scripts/gate.sh HIJAU (verify_state_machine SM1..SM6, verify_cross_entity CE5, fa_write_idor proof-IDOR, verify_data_integrity INV-P1/P2, verify_rbac_guards admin_payments) + testing_agent_v3 (submit bukti → verifikasi → paid+lunas, tolak, COD, jalur menyimpang).

---

---

## PHASE E5 — ADMIN BACKOFFICE (CMS: dashboard, CRUD katalog/voucher, proses pesanan, moderasi ulasan, config, media, live preview)
STATUS: ✅ SELESAI (GATE HIJAU + test_e5_core 24/24 + testing_agent_v3 35/35, 2026-07-06)

Deliverable (ditagih verify_delivery):
- [P0] doc: docs/roadmap/E5_ADMIN_BACKOFFICE.md
- [P0] script: backend/routers/admin.py
- [P0] script: backend/routers/admin_products.py
- [P0] script: backend/routers/admin_orders.py
- [P0] script: backend/services/admin_products.py
- [P0] script: backend/services/admin_stats.py
- [P0] script: scripts/test_e5_core.py
- [P0] endpoint: /api/admin/dashboard
- [P0] endpoint: /api/admin/products
- [P0] endpoint: /api/admin/products/{id}
- [P0] endpoint: /api/admin/categories
- [P0] endpoint: /api/admin/vouchers
- [P0] endpoint: /api/admin/orders
- [P0] endpoint: /api/admin/orders/{code}/status
- [P0] endpoint: /api/admin/reviews
- [P0] endpoint: /api/admin/media
- [P0] endpoint: /api/admin/settings
- [P0] collection: media_assets
- [P0] collection: audit_logs
- [P0] page: AdminDashboardPage
- [P0] page: AdminProductsPage
- [P0] page: AdminProductEditorPage
- [P0] page: AdminOrdersPage
- [P0] page: AdminSettingsPage
- [P0] invariant: INV-M1 (setiap mutasi admin ditulis audit_logs)
- [P0] invariant: INV-M2 (archive-not-delete produk direferensikan order)
- [P0] invariant: INV-M3 (snapshot order imutabel saat produk diedit)

Bukti (target): scripts/test_e5_core.py PASS + bash scripts/gate.sh HIJAU (verify_rbac_guards semua /api/admin/* dijaga, fa_idor_matrix customer→403, verify_state_machine tetap AKTIF, verify_delivery D2 no-orphan) + testing_agent_v3 (admin CRUD, proses pesanan, moderasi ulasan, RBAC deviant).

---

---

## PHASE E4 — CUSTOMER ACCOUNT (profil, alamat single-default, wishlist hybrid)
STATUS: ✅ SELESAI (Epic E4 — diverifikasi ulang 2026-08-03: `scripts/test_e4_core.py`
→ 12 PASS / 0 FAIL; owner-scoped + IDOR 404 ditegakkan fa_write_idor)

Deliverable (ditagih verify_delivery):
- [P0] doc: docs/roadmap/E4_CUSTOMER_ACCOUNT.md
- [P0] script: backend/services/account.py
- [P0] script: backend/routers/account.py
- [P0] script: scripts/test_e4_core.py
- [P0] endpoint: /api/account/profile
- [P0] endpoint: /api/addresses
- [P0] endpoint: /api/wishlist
- [P0] collection: addresses
- [P0] collection: wishlists
- [P0] page: AccountPage
- [P0] page: WishlistPage
- [P0] invariant: INV-A1 (<=1 alamat default/user)
- [P0] invariant: INV-A2 (address/wishlist.user_id -> users FK)
- [P0] invariant: INV-A3 (wishlist.product_ids dedupe + FK products)

Bukti: scripts/test_e4_core.py 12/12 PASS + bash scripts/gate.sh HIJAU (verify_data_integrity L7 INV-A1..A3, verify_schema wishlist FK, fa_write_idor address A-vs-B) + testing_agent_v3 (profil, alamat single-default, wishlist sync/merge, IDOR).

---

## PHASE E3 — CART, CHECKOUT & ORDERS (atomic stock, anti-oversell, state machine)
STATUS: ✅ SELESAI (Epic E3 — GATE HIJAU + test_e3_core 19/19 + testing_agent BE 99%/FE 100%)

Deliverable (ditagih verify_delivery):
- [P0] doc: docs/roadmap/E3_CART_CHECKOUT_ORDERS.md
- [P0] script: backend/services/stock.py
- [P0] script: backend/services/orders.py
- [P0] script: backend/services/cart.py
- [P0] script: backend/routers/orders.py
- [P0] script: backend/routers/config.py
- [P0] script: backend/routers/cart.py
- [P0] script: scripts/test_e3_core.py
- [P0] endpoint: /api/orders
- [P0] endpoint: /api/orders/{code}
- [P0] endpoint: /api/orders/{code}/cancel
- [P0] endpoint: /api/shipping-methods
- [P0] endpoint: /api/payment-methods
- [P0] endpoint: /api/settings
- [P0] endpoint: /api/cart
- [P0] collection: orders
- [P0] collection: carts
- [P0] collection: counters
- [P0] page: CartPage
- [P0] page: CheckoutPage
- [P0] page: OrderSuccessPage
- [P0] page: AccountPage
- [P0] invariant: INV-4 (stock >= 0 anti-oversell)
- [P0] invariant: INV-7 (order.code UNIK)
- [P0] invariant: CE1 (used_count == #orders == #redemptions)

Bukti (target): scripts/test_e3_core.py PASS + bash scripts/gate.sh HIJAU (state-machine/concurrency/mutation_smoke/fa_race/fa_write_idor AKTIF) + testing_agent_v3 (happy + deviant: 409 stok, cancel restore, IDOR) + screenshot Cart→Checkout→Success.

---

## PHASE E2 — PRICING SSOT + VOUCHERS (Shopee-like campaigns)
STATUS: ✅ SELESAI (Epic E2 — lihat docs/roadmap/E2_PRICING_VOUCHERS.md)

Deliverable (ditagih verify_delivery):
- [P0] doc: docs/roadmap/E2_PRICING_VOUCHERS.md
- [P0] script: backend/services/pricing.py
- [P0] script: backend/services/vouchers.py
- [P0] script: backend/routers/vouchers.py
- [P0] script: scripts/test_e2_core.py
- [P0] endpoint: /api/vouchers/validate
- [P0] endpoint: /api/vouchers
- [P0] collection: vouchers
- [P0] collection: voucher_redemptions
- [P0] page: CartPage
- [P0] page: CheckoutPage
- [P0] page: VoucherPage
- [P0] invariant: INV-3 (discount == compute_pricing SSOT)
- [P0] invariant: INV-9 (voucher.type/value sah + free_shipping)
- [P0] invariant: CE1 (used_count == #orders == #redemptions)

Bukti (target): bash scripts/gate.sh HIJAU + scripts/test_e2_core.py PASS + testing_agent_v3 (happy + deviant) + screenshot Voucher Center / apply di cart-checkout.

---

## PHASE E1 — CATALOG (read-path: products/categories/reviews + storefront wiring)
STATUS: ✅ SELESAI (Epic E1 — lihat docs/roadmap/E1_CATALOG.md)

Deliverable (ditagih verify_delivery):
- [P0] doc: docs/roadmap/E1_CATALOG.md
- [P0] script: scripts/seed_data.py
- [P0] script: scripts/verify_data_integrity.py
- [P0] script: scripts/health_check.py
- [P0] endpoint: /api/products
- [P0] endpoint: /api/products/{slug}
- [P0] endpoint: /api/categories
- [P0] endpoint: /api/reviews
- [P0] collection: products
- [P0] collection: categories
- [P0] collection: reviews
- [P0] page: HomePage
- [P0] page: ShopPage
- [P0] page: ProductDetailPage
- [P0] invariant: INV-C1 (>=1 volume & ml unik)
- [P0] invariant: INV-C2 (compare_at_price null atau > price)
- [P0] invariant: INV-C3 (rating_avg/count == mean published reviews)

Bukti (target): bash scripts/gate.sh HIJAU (runtime aktif untuk katalog) + testing_agent_v3 (happy + deviant) + screenshot Home/Shop/PDP.

---

## PHASE 1 — FONDASI (guardrails + auth infra + seed)
STATUS: ✅ SELESAI & TERVERIFIKASI HIJAU

Deliverable (ditagih verify_delivery):
- [P0] doc: docs/07_ENGINEERING_GUARDRAILS.md
- [P0] doc: docs/08_FRONTEND_GUARDRAILS.md
- [P0] doc: docs/09_THREAT_MODEL.md
- [P0] doc: docs/03_DATA_MODEL.md
- [P0] doc: docs/04_API_CONTRACT.md
- [P0] doc: docs/06_STATE_MACHINE.md
- [P0] doc: memory/INVARIANTS.md
- [P0] doc: memory/BUG_REGISTRY.md
- [P0] doc: docs/roadmap/00_ROADMAP.md
- [P0] doc: docs/roadmap/UX_BLUEPRINT.md
- [P0] doc: docs/roadmap/E1_CATALOG.md
- [P0] doc: docs/roadmap/E2_PRICING_VOUCHERS.md
- [P0] doc: docs/roadmap/E3_CART_CHECKOUT_ORDERS.md
- [P0] doc: docs/roadmap/E4_CUSTOMER_ACCOUNT.md
- [P0] doc: docs/roadmap/E5_ADMIN_BACKOFFICE.md
- [P0] doc: docs/roadmap/E6_PAYMENTS.md
- [P0] doc: docs/roadmap/E7_GROWTH_ANALYTICS.md
- [P0] doc: docs/roadmap/E8_HARDENING.md
- [P0] script: scripts/gate.sh
- [P0] script: scripts/seed_data.py
- [P0] script: scripts/verify_contract.py
- [P0] script: scripts/verify_schema.py
- [P0] script: scripts/verify_data_integrity.py
- [P0] script: scripts/verify_api_contract.py
- [P0] script: scripts/verify_architecture.py
- [P0] script: scripts/verify_state_machine.py
- [P0] script: scripts/verify_concurrency.py
- [P0] script: scripts/verify_cross_entity.py
- [P0] script: scripts/verify_delivery.py
- [P0] script: scripts/verify_roadmap_docs.py
- [P0] script: scripts/mutation_smoke.py
- [P0] script: scripts/check_nav_map.py
- [P0] script: scripts/health_check.py
- [P0] script: scripts/audit_endpoint_sweep.py
- [P0] script: scripts/ux_audit.py
- [P0] script: scripts/validate_compliance.py
- [P0] script: scripts/preflight.py
- [P0] script: scripts/guardrails/verify_rbac_guards.py
- [P0] script: scripts/guardrails/verify_numeric_bounds.py
- [P0] script: scripts/guardrails/verify_adversarial_5xx.py
- [P0] script: scripts/guardrails/verify_stock_locks.py
- [P0] script: forensic/fa_idor.py
- [P0] script: forensic/fa_idor_matrix.py
- [P0] script: forensic/fa_write_idor.py
- [P0] script: forensic/fa_race.py
- [P0] script: forensic/fa_fuzz.py
- [P0] script: forensic/fa_5xx.py
- [P0] script: forensic/fa_static.py
- [P0] script: forensic/fa_session.py
- [P0] script: forensic/fa_nplus1.py
- [P0] script: forensic/fa_mutation.py
- [P0] script: forensic/fa_dark_sweep.py
- [P0] endpoint: /api/auth/login
- [P0] endpoint: /api/auth/register
- [P0] endpoint: /api/auth/me
- [P0] endpoint: /api/health
- [P0] collection: users
- [P0] collection: categories
- [P0] collection: vouchers
- [P0] collection: shipping_methods
- [P0] collection: payment_methods

Bukti Phase 1:
- memory/GATE_RECEIPT.md = VERDICT HIJAU (semua gate non-skip PASS; runtime + forensic dijalankan).
- fa_mutation: 3/3 mutan tertangkap (guardrail terbukti efektif, bukan no-op).
- fa_session: token palsu/kedaluwarsa/user-nonaktif ditolak 401.

---

## PHASE 2 — BUSINESS LOGIC + WIRING + ADMIN
STATUS: ⏳ BELUM DIMULAI (aktifkan dgn ubah ACTIVE_PHASE: 2 saat fase ini dikerjakan)

Deliverable (rencana — ditagih saat fase aktif):
- [P0] endpoint: /api/products
- [P0] endpoint: /api/products/{slug}
- [P0] endpoint: /api/categories
- [P0] endpoint: /api/shipping-methods
- [P0] endpoint: /api/payment-methods
- [P0] endpoint: /api/vouchers/validate
- [P0] endpoint: /api/orders
- [P0] endpoint: /api/orders/{code}
- [P0] endpoint: /api/admin/dashboard
- [P0] page: ShopPage
- [P0] page: ProductDetailPage
- [P0] page: CheckoutPage
- [P0] page: AccountPage
- [P0] collection: products
- [P0] collection: orders
- [P0] invariant: INV-1..INV-11 lulus dgn data order nyata
- [P1] page: AdminDashboardPage

Bukti (nanti): gate.sh hijau (runtime state-machine/concurrency AKTIF), testing_agent_v3, screenshot preview.

---

## PHASE 3 — HARDENING
STATUS: ⏳ BELUM DIMULAI
- [P0] invariant: fa_race anti-oversell AKTIF (stok tak pernah negatif di bawah balapan)
- [P0] script: forensic/fa_write_idor.py (skenario A-vs-B aktif)
th/login
- [P0] endpoint: /api/auth/register
- [P0] endpoint: /api/auth/me
- [P0] endpoint: /api/health
- [P0] collection: users
- [P0] collection: categories
- [P0] collection: vouchers
- [P0] collection: shipping_methods
- [P0] collection: payment_methods

Bukti Phase 1:
- memory/GATE_RECEIPT.md = VERDICT HIJAU (semua gate non-skip PASS; runtime + forensic dijalankan).
- fa_mutation: 3/3 mutan tertangkap (guardrail terbukti efektif, bukan no-op).
- fa_session: token palsu/kedaluwarsa/user-nonaktif ditolak 401.

---

## PHASE 2 — BUSINESS LOGIC + WIRING + ADMIN
STATUS: ⏳ BELUM DIMULAI (aktifkan dgn ubah ACTIVE_PHASE: 2 saat fase ini dikerjakan)

Deliverable (rencana — ditagih saat fase aktif):
- [P0] endpoint: /api/products
- [P0] endpoint: /api/products/{slug}
- [P0] endpoint: /api/categories
- [P0] endpoint: /api/shipping-methods
- [P0] endpoint: /api/payment-methods
- [P0] endpoint: /api/vouchers/validate
- [P0] endpoint: /api/orders
- [P0] endpoint: /api/orders/{code}
- [P0] endpoint: /api/admin/dashboard
- [P0] page: ShopPage
- [P0] page: ProductDetailPage
- [P0] page: CheckoutPage
- [P0] page: AccountPage
- [P0] collection: products
- [P0] collection: orders
- [P0] invariant: INV-1..INV-11 lulus dgn data order nyata
- [P1] page: AdminDashboardPage

Bukti (nanti): gate.sh hijau (runtime state-machine/concurrency AKTIF), testing_agent_v3, screenshot preview.

---

## PHASE 3 — HARDENING
STATUS: ⏳ BELUM DIMULAI
- [P0] invariant: fa_race anti-oversell AKTIF (stok tak pernah negatif di bawah balapan)
- [P0] script: forensic/fa_write_idor.py (skenario A-vs-B aktif)
