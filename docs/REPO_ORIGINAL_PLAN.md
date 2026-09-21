# plan.md — Collector Parfum (Phase 3)

## 1) Objectives
- Menyelesaikan **wizard Bulk Import/Export produk** agar sinkron dengan backend **variant N-dimensi (Shopify-style)**: `option1_name/value … option4_name/value` + `variant_*`.
- Memastikan **template download tidak rusak** (backend) dan bisa dipakai roundtrip import.
- Verifikasi end-to-end: **Admin upload → analyze → mapping → preview edit → validate → commit → produk terbuat/terupdate**, lalu export kembali.

## 2) Implementation Steps

### Phase 1 — CORE POC (Import/Template/Export Roundtrip)
**User stories (POC):**
1. Sebagai admin, saya bisa mengunduh template CSV/XLSX yang valid untuk N-dimensi.
2. Sebagai admin, saya bisa mengunggah file contoh dan sistem memetakan kolom dimensi dengan benar.
3. Sebagai admin, saya bisa melihat preview yang menunjukkan kombinasi dimensi per baris.
4. Sebagai admin, saya bisa commit impor dan produk muncul di katalog admin.
5. Sebagai admin, saya bisa export hasilnya dan formatnya konsisten (roundtrip).

**Langkah:**
- Backend: perbaiki `backend/services/product_bulk.py`:
  - Update `INSTRUCTIONS` agar menjelaskan **1 baris = 1 varian** dan kolom **option{i}_name/value**.
  - Update `template_rows()` agar mengisi kolom `option1_name/value..option4_name/value` + `variant_*` (tanpa `variant_type/variant_ml`).
- Tambah/upgrade test script kecil (atau perluas `scripts/test_product_io_core.py`) untuk:
  - Hit endpoint `/api/admin/products/io/template` (csv/xlsx) → parse → validate_import → commit_import (dry run minimal) → export.
- Pastikan backend restart via supervisorctl dan endpoint `/template` menghasilkan file yang bisa langsung diimpor tanpa error.

### Phase 2 — V1 App Development (Frontend Wizard N-Dimensi)
**User stories (V1 FE):**
1. Sebagai admin, saya bisa memetakan kolom dimensi `option1..4` (nama+nilai) tanpa kebingungan.
2. Sebagai admin, saya melihat preview tabel dengan **kolom dinamis** sesuai dimensi yang terdeteksi.
3. Sebagai admin, saya bisa mengedit sel preview dan validasi otomatis memperbarui status baris.
4. Sebagai admin, tombol “Impor” hanya aktif jika field penting terpetakan dan ada baris valid.
5. Sebagai admin, saya bisa mengekspor seluruh produk dari halaman yang sama (CSV/XLSX).

**Langkah:**
- Update `frontend/src/components/admin/import/importConstants.js`:
  - Tambah canonical field `option1_name/value … option4_name/value`.
  - Ubah `REQUIRED` (hapus `variant_ml`; gantikan dengan rule: harus ada **dimension size** via option columns atau legacy ml).
  - Sediakan helper list untuk kelompok field (Product fields, Dimensions, Variant fields) agar mapping UI rapi.
  - `PREVIEW_COLS` diganti menjadi builder dinamis (berdasarkan mapping + data headers yang tersedia).
- Update `frontend/src/pages/admin/AdminProductImportPage.js`:
  - Mapping editor: tampilkan field dimensi (option slots) dengan label jelas.
  - Preview table:
    - Bangun kolom dinamis: tampilkan `name, category`, lalu pasangan dimensi yang terdeteksi (`optionX_name/value`), lalu `variant_price/compare/stock/sku`.
    - Tetap dukung file legacy: jika user map `variant_ml/variant_type`, preview juga menampilkan kolom tersebut.
  - Validasi gating:
    - `canCommit` memerlukan `name`, `category`, `variant_price` terpetakan, dan **(size dimension hadir)** via opsi atau `variant_ml`.
  - Tambahkan tombol Export (CSV/XLSX) memanggil `exportProducts(format)`.
- Verifikasi FE compile: `esbuild src/ --loader:.js=jsx --bundle --outfile=/dev/null`.

### Phase 3 — Testing & Bug-Fix Loop
**User stories (QA):**
1. Sebagai admin, saya bisa mengimpor file dengan 1–4 dimensi tanpa UI pecah.
2. Sebagai admin, baris error ditandai jelas dan bisa difilter “Hanya error”.
3. Sebagai admin, mapping suggestion dari backend langsung usable untuk file template/export.
4. Sebagai admin, mode `add-only` tidak menimpa produk lama; `upsert` memperbarui.
5. Sebagai sistem, tidak ada 5xx pada analyze/validate/commit untuk input buruk (row-level error saja).

**Langkah:**
- Buat file uji CSV & XLSX N-dimensi:
  - Basis dari export/template endpoint, lalu modifikasi dimensi (2D, 3D, 4D) + SKU kosong/isi.
- Jalankan `testing_agent_v3` untuk skenario:
  - Admin login → buka halaman import → download template → upload → validate → commit.
  - Verifikasi produk & varian di Admin Products.
  - Export → pastikan kolom tetap konsisten.
- Fix bug sampai semua test bersih.

### Phase 4 — Regression + Closeout
**User stories (stabilitas):**
1. Sebagai shopper, PDP varian N-dimensi tetap berfungsi setelah perubahan import.
2. Sebagai admin, product editor varian tetap bisa generate dan simpan.
3. Sebagai admin, taxonomy (occasions/characters) tidak terpengaruh.
4. Sebagai sistem, seed_reset + gate tidak regress.
5. Sebagai tim, dokumentasi plan/handoff merefleksikan keadaan terbaru.

**Langkah:**
- Jalankan `bash scripts/gate.sh` (atau minimal subset relevan + verify_api_contract).
- Update `plan.md` menandai Phase 3 **COMPLETED**.
- Update `memory/HANDOFF.md` (status terbaru + catatan perubahan kolom + cara uji).

## 3) Next Actions
1. Fix backend template bug di `services/product_bulk.py` (template_rows + INSTRUCTIONS) lalu restart backend.
2. Buat POC script untuk roundtrip template → analyze/validate/commit → export.
3. Refactor FE import constants + dynamic preview columns (sesuai keputusan user).
4. Tambahkan tombol Export di halaman AdminProductImportPage.
5. Esbuild compile + 1 putaran testing_agent_v3 end-to-end; iterasi hingga bersih.

## 4) Success Criteria
- `/api/admin/products/io/template` menghasilkan CSV/XLSX yang **bisa langsung diimpor** (tanpa dimensi kosong).
- Wizard import FE mendukung **kolom dimensi dinamis** (1–4), termasuk fallback file legacy.
- Import commit berhasil membuat/mengupdate produk dengan `options[]` + `variants[]` (SKU sebagai SSOT).
- Export menghasilkan kolom Shopify-style konsisten.
- FE compile (esbuild) bersih, backend health ok, dan regression gate tidak merah.
