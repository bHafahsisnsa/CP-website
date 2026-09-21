# HANDOFF — Collector Parfum (FARM Stack)

> **Bahasa user: Indonesia.** Agen berikutnya WAJIB berkomunikasi dalam Bahasa Indonesia.
> Dokumen ini DITULIS ULANG 2026-08-03 (sesi penutupan E12). Catatan usang sudah DIBUANG —
> apa yang tertulis di sini = kondisi kode saat ini.

---

## 0. STATUS RINGKAS (baca ini dulu)

| Hal | Kondisi |
|-----|---------|
| Repo | `github.com/pandekomangyogaswastika-dot/cpweb` → di-restore ke `/app` (env `MONGO_URL` & `REACT_APP_BACKEND_URL` TIDAK diubah) |
| Epic selesai | E1 Catalog · E2 Pricing/Voucher · E3 Cart/Checkout/Orders · E4 Account · E5 Admin Backoffice · E6 Payments · E7 Growth/Analytics · E9 CMS Storefront · E10 Export/Import · **E11 Matriks Tier + Aksi Massal + Inspired by** · **E12 Sesi Impor (DITUTUP RESMI)** · **E13 Konten resmi collectorparfum.com + deploy.sh VPS** |
| Epic belum | **E8 Hardening** (forensics lanjutan, N+1, aksesibilitas, release readiness) — kandidat pekerjaan berikutnya |
| Gate | `bash scripts/gate.sh` → **HIJAU** (33 gate non-skip, receipt `memory/GATE_RECEIPT.md`) |
| Testing agent | Iterasi 36–40 semua LULUS, 0 bug tersisa (backend 70/70; frontend 4 batch) |
| Target user | **RILIS** — user ingin app dideploy; uji manual final dilakukan user sendiri |

### Bukti regresi terakhir (jalankan ulang bila ragu)
```bash
cd /app
python scripts/test_import_session_poc.py    # 69 PASS / 0 FAIL  (E12 sesi impor)
python scripts/test_tier_matrix_poc.py       # 63 PASS / 0 FAIL  (E11, file asli 6.426 baris)
python scripts/verify_user_import.py         # 46 PASS / 0 FAIL
python scripts/test_product_io_core.py       # 22 PASS / 0 FAIL
python scripts/test_shop_and_import_e2e.py   # 155 PASS / 0 FAIL (belanja + wizard impor)
bash   scripts/gate.sh                       # HIJAU total
```

---

## 1. Cara menyiapkan environment (setelah clone/restore)

```bash
cd /app/backend && pip install -r requirements.txt      # WAJIB: openpyxl + et_xmlfile
cd /app/frontend && yarn install                        # yarn, JANGAN npm
cd /app && python scripts/seed_data.py                  # idempoten: 12 produk, 6 kategori, 8 occasion,
                                                        # 12 karakter, 6 voucher, 20 section CMS, dll.
sudo supervisorctl restart backend frontend
```
Gejala khas bila `openpyxl` belum ada: backend crash-loop di `services/product_bulk.py:13`.

---

## 2. Kredensial uji
- Admin: `admin@collectorparfum.id` / `Admin#2026` (login di `/admin`)
- Customer: `customer@collectorparfum.id` / `Customer#2026` (login di `/akun`)
- Detail: `memory/test_credentials.md`

### testId login (SERING SALAH — perhatikan)
| Permukaan | testId |
|-----------|--------|
| Admin `/admin` | `admin-login-email`, `admin-login-password`, `admin-login-submit` |
| Storefront `/akun` | `login-email-input`, `login-password-input`, `login-submit-button` (panel `auth-panel`, tab `auth-tab-login`) |

Token sesi disimpan di `localStorage['cp:token:v1']` (prefiks `sess_`, TTL **30 hari**).
Respons `POST /api/auth/login` memakai field **`token`** (BUKAN `access_token`).

---

## 3. Arsitektur kode

```
backend/
  server.py            # include semua router + index/TTL startup
  routers/             # endpoint (semua ber-prefix /api)
  services/            # logika inti (SSOT). <=300 baris/berkas (compliance gate)
  schemas.py           # Pydantic (semua field numerik WAJIB ge=/gt= → INV-NUM-01)
frontend/src/
  pages/ pages/admin/  # halaman storefront & backoffice
  components/          # admin/, shop/, home/, layout/, shared/, ui(shadcn)
  services/            # apiClient (SSOT HTTP) + modul per domain
  store/               # AuthContext, CartContext, WishlistContext, SettingsContext, ThemeContext
scripts/               # seed, verifier, guardrail, POC, gate.sh
forensic/              # fa_* (IDOR, race, fuzz, 5xx, session, dark sweep, mutation)
docs/                  # SSOT dokumen (PRD, arsitektur, data model, API contract, threat model, roadmap)
memory/                # HANDOFF (ini), INVARIANTS, BUG_REGISTRY, DELIVERY_MANIFEST, GATE_RECEIPT
```

### SSOT yang tidak boleh diduplikasi
- Harga/diskon/total → `backend/services/pricing.py` (integer rupiah).
- Transisi status order → `backend/services/orders.py` (`LEGAL_TRANSITIONS`, `derive_payment_status`).
- Stok → `backend/services/stock.py` (atomik `$inc` ber-guard, anti-oversell).
- Parsing/isian impor → `backend/services/product_import.py`, `product_fill.py`, `product_tiers.py`.
- HTTP klien → `frontend/src/services/apiClient.js` (jangan `fetch` mentah / hardcode host).

---

## 4. Skema DB kunci (BENAR — pakai ini)

```js
// products
{
  id: "prd_…", slug, name, brand, category, status: "active"|"archived",
  options: [{ name: "Ukuran", values: ["35ml","60ml"] }, { name: "Tipe", values: ["Standard"] }],
  variants: [{ sku: "NOIROUD-STANDARD-30ML",
               options: { Konsentrasi: "EDP", Tipe: "Standard", Ukuran: "30ml" },  // KUNCI = options (BUKAN combination)
               price: 385000, compare_at_price: null, stock: 12 }],
  occasions: [slug], characters: [slug], price_min, price_max
}

// orders — ongkir NESTED di shipping.price
{ code: "CP00000015", subtotal, discount, shipping: { method, price }, cod_fee, total,
  status, payment_status, items: [{ product_id, sku, unit_price, quantity }] }
// total = subtotal - discount + shipping.price + cod_fee

// import_sessions (E12) — meta + chunk, TTL 6 jam, owner-scoped
{ id: "imp_…", kind: "meta", admin_id, filename, headers[], total, chunks, expires_at }
{ id: "imp_…#0", kind: "chunk", session_id, seq, rows[], expires_at }
```

Kolom impor/ekspor = **Shopify-style N-dimensi**: `option1_name`,`option1_value` … `option4_*`
(kolom lama `variant_type`/`variant_ml` tidak dipakai lagi; parser tetap toleran terhadap file legacy).

---

## 5. PERBAIKAN PENTING — JANGAN DI-REVERT

1. **Data-loss facet saat export → re-import.** `occasions`/`characters` masuk `EXPORT_COLUMNS` +
   parser; `services/admin_products.py::PRESERVE_IF_ABSENT` menjaga field yang TIDAK ada di payload
   (`occasions, characters, notes, performance, seo, ingredients, images, video_url`).
   Regresi: B47/B48 di `scripts/test_shop_and_import_e2e.py`.
2. **`styles/theme-glass.css`** — `position: relative` HARUS berada di `:where(...)` (spesifisitas 0)
   agar utility posisi Tailwind (`absolute`/`fixed`) tidak tertimpa. Jangan kembalikan ke selector kelas.
3. **`components/shop/ShopFilters.js`** panel filter TERPISAH dari `ShopPage` (kalau digabung, tipe
   komponen baru tiap render → Checkbox/Slider remount).
4. **E12 sesi impor** — wizard TIDAK BOLEH mengirim ulang seluruh baris. Semua aksi memakai
   `session_id` (`/validate`, `/tiers`, `/session/{sid}/rows|cells|fill|close`, `/commit`).
   Pemangkasan `MAX_PER_ADMIN = 5` di `services/product_io_session.py::_prune` + TTL 6 jam.
5. **BUG-AUTH-01** — `store/AuthContext.js` hanya boleh menghapus token pada **401/403**. Kegagalan
   transient (offline/timeout/502) WAJIB di-retry dan token dipertahankan; UI menampilkan
   `admin-session-offline` / `account-session-offline`. Dijaga gate
   `scripts/guardrails/verify_auth_resilience.py` (INV-AUTH-01).
6. **Impor default** = mode add-only, hasil `archived` + stok 0. `DELETE /api/admin/products/{id}`
   adalah **soft-delete** (INV-M2). Aktivasi massal via `POST /api/admin/products/bulk-status`.

---

## 6. Aturan kerja (guardrail proses)
- `bash scripts/gate.sh` HARUS hijau sebelum klaim selesai. SKIP ≠ PASS.
- Menemukan bug → tulis dulu gate/verifier yang MEREPRODUKSI, baru fix, lalu catat di
  `memory/BUG_REGISTRY.md`.
- Batas ukuran berkas (compliance): FE pages/components ≤500 baris, hooks ≤300, css ≤400;
  BE routers ≤800, services ≤300.
- ID = UUID berprefiks (`prd_`, `ord_`, `imp_`, `usr_`…), uang = INTEGER rupiah, waktu = ISO-8601 UTC.
- **JANGAN** ubah `frontend/.env` (`REACT_APP_BACKEND_URL`) & `backend/.env` (`MONGO_URL`).
- Pakai **yarn** (bukan npm) dan **supervisorctl** (jangan jalankan uvicorn manual).
- Data uji: bersihkan dengan `python scripts/qa_cleanup.py` (hapus produk slug `qa-` / `uji-`).

---

## 7. Titik lanjut berikutnya (rekomendasi)
1. **Rilis/deploy ke VPS** — SUDAH DISIAPKAN: `deploy.sh` (skrip sekali jadi) + panduan
   `DEPLOYMENT_VPS.md`. Ringkas:
   - VPS Ubuntu, jalankan `sudo bash deploy.sh` → app `collector-parfum`, user `collector`,
     backend **port 8003** (8001 KBS8 / 8002 Garment ERP), database `collector_parfum`,
     nginx server block sendiri, seed otomatis bila DB kosong.
   - Domain belum dipakai → dilayani lewat IP `http://148.230.102.29`. Pasang domain nanti:
     `sudo DOMAIN=namadomain.com SETUP_SSL=yes bash deploy.sh`.
   - Media & backup persisten di `/var/lib/collector-parfum/{media,backups}`
     (env `MEDIA_ROOT`/`BACKUP_ROOT`) agar tidak hilang saat rebuild.
   - Dependency produksi dipisah: `backend/requirements-prod.txt` (14 paket, install ±10 detik)
     — kalau menambah library backend, TAMBAHKAN di file ini juga.
2. **Epic E8 Hardening** (`docs/roadmap/E8_HARDENING.md`): forensik lanjutan, audit N+1,
   aksesibilitas (a11y), release readiness checklist.
3. Opsional produk: object storage untuk media, notifikasi WhatsApp status pesanan,
   laporan penjualan, riwayat impor.

## 7b. Konten storefront = data ASLI Collector Parfum (E13)
Default CMS di `backend/content_registry.py` sudah memakai informasi resmi dari situs lama
`collectorparfum.com` (ikut ter-seed di instalasi baru, tetap bisa diedit di `/admin/konten`):
- Sejarah: berdiri **8 September 1970** di Jalan Kolektor Bandung → Jl. Paledang No. 14 →
  menetap **Jl. Paledang No. 58**; cabang Pasirkaliki No. 148A & Gatot Subroto No. 271.
- Tagline **“Refill Perfume Distributor Since 1970”**; ukuran botol 30/50/60/100 ml.
- Kontak: WA +62 857-2000-0105 & +62 857-2013-7777, `cs@collectorparfum.com`,
  LINE/IG `@collectorparfum`; jam Senin–Jumat 09.00–17.00 · Sabtu 09.00–14.00 WIB.
- FAQ & pengiriman asli (proses 1×24 jam / partai besar 2–5 hari, Jabodetabek 1–3 hari,
  luar Jabodetabek 2–7 hari, kirim ke Indonesia/Brunei/Malaysia, same-day Bandung < 10.00 WIB).
- Harga, metode pembayaran, dan 12 produk demo TIDAK diubah (permintaan user).
- Fallback frontend (`ContactPage.js`, `AboutPage.js`, `lib/bottleArt.js`, `MobileMenuDrawer.js`)
  ikut diselaraskan — jangan kembalikan placeholder Jakarta / `hello@collectorparfum.id`.

---

## 8. Riwayat testing
- Laporan: `/app/test_reports/iteration_*.json` (terbaru: 36 backend 70/70, 37 E11 file besar,
  38 commit + Harga Coret, 39 BUG-AUTH-01 admin + aksi massal + smoke 26 halaman,
  40 BUG-AUTH-01 customer + Inspired by + alur belanja).
- Protokol & catatan antar-agen: `/app/test_result.md` (JANGAN hapus blok protokol di atasnya).
