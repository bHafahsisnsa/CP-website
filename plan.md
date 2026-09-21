# Development Plan — Media Upload + Media Manager (Collector Parfum)

## 1) Objectives
- Enable **reliable image upload** (JPG/PNG/WebP/GIF/SVG/AVIF/HEIC) with **15MB limit**.
- Build a **premium admin Media Manager** with **nested folders**, search/filter/sort, grid+list, bulk ops.
- Provide a **unified Media Picker** usable across: Product Editor, CMS Konten, Kategori, Lokasi Toko, Pengaturan pembayaran.
- Fix broken images by making storage **local disk SSOT** (VPS) with optional **MongoDB GridFS mirror + self-heal** (toggle via env).
- Preserve backward compatibility for legacy endpoints/records and existing `/api/media/*` URLs.

## 2) Implementation Steps

### Phase 1 — Core POC (must pass before UI work)
**Goal:** Prove end-to-end core: folders + upload + derivatives + serve + self-heal + product attachment.
1. **Web research (best practices)**: confirm recommended Pillow pipeline (EXIF transpose, WebP derivatives, GIF/SVG handling), HEIC/AVIF decoding options, and FastAPI streaming FileResponse caching headers.
2. Backend minimal core additions (only what POC needs):
   - `media_folders` model + CRUD functions (nested tree).
   - Extend `media_assets` schema to include: `folder_id`, `checksum`, `width/height`, `alt/title`, `thumb_url`, `medium_url`, `stored_path`, timestamps.
   - Upload pipeline: 15MB cap; Pillow optimize; generate `_400.webp` + `_1000.webp` (skip SVG; GIF: keep original, no WebP); EXIF auto-orient.
   - Storage layout: `MEDIA_ROOT/originals/YYYY/MM/<uuid>.<ext>` and `MEDIA_ROOT/derived/<uuid>_{400|1000}.webp`.
   - GridFS mirror (AsyncIOMotorGridFSBucket) gated by `MEDIA_DB_MIRROR=true`.
   - Replace static mount with **GET `/api/media/{path:path}`** handler: serve from disk; if missing and mirror enabled → restore from GridFS → serve.
3. Unify API surface (POC subset):
   - `POST /api/admin/media/folders`, `GET /api/admin/media/folders/tree`, `PATCH /api/admin/media/folders/{id}`.
   - `POST /api/admin/media/upload` (multi-file), `POST /api/admin/media/from-url`.
   - `GET /api/admin/media/assets` (q/folder_id/sort/page/limit + `X-Total-Count`).
   - `PATCH /api/admin/media/assets/{id}` (rename, alt/title, move).
   - `POST /api/admin/media/assets/bulk-move`, `POST /api/admin/media/assets/bulk-delete`.
   - Keep aliases: `/api/admin/uploads` and legacy `/api/admin/media` working.
4. Write **one script**: `scripts/test_media_core.py` executing the 14 checks in the spec (upload multi-MB, thumbs, serve 200, self-heal after deleting disk, from-url ingest, move/rename/alt, search/sort/pagination, bulk ops, folder delete guard, attach to product + verify in public catalog, invalid mime & >15MB reject, legacy compatibility).
5. Iterate until **100% PASS** with no 5xx.

**Phase 1 user stories**
1. As an admin, I can create nested folders (Produk > Banner > 2026) and see them as a tree.
2. As an admin, I can upload multiple images up to 15MB and get stable `/api/media/...` URLs.
3. As an admin, I get thumbnails/medium images automatically for fast browsing.
4. As an admin, if the original file disappears from disk, the same URL still works (self-heal).
5. As an admin, I can ingest an external URL and it becomes a locally-served image.

### Phase 2 — V1 App Development (Media Manager + Picker)
1. Backend hardening & consolidation:
   - Move all media endpoints into `routers/admin_media.py` under `/api/admin/media/*` (registered before legacy routes).
   - Finalize indexes: folders (parent_id, path), assets (folder_id, uploaded_at, checksum, text index on filename/title/alt).
   - Ensure legacy seed images in `backend/media/*.png` still served.
   - Document env: `MEDIA_ROOT`, `MEDIA_MAX_MB=15`, `MEDIA_DB_MIRROR`.
2. Frontend: new `src/services/media.js` (SSOT client for media endpoints).
3. Build **AdminMediaPage** at `/admin/media`:
   - Nested folder tree (collapse), breadcrumb, counts.
   - Upload dropzone + file picker; per-file progress.
   - Grid/list toggle; search; type filter; sort; pagination.
   - Bulk select bar: delete/move.
   - Details drawer: preview, copy URL, rename, alt/title, move, replace, delete.
4. Build reusable **`<MediaPickerDialog>`**:
   - Tabs: Library (folders), Upload, From URL.
   - Single & multi select.
5. Integrate picker everywhere (replace raw URL-only flows):
   - Product Editor media tab: add upload + picker, drag reorder, set primary.
   - CMS ContentForm ImageField uses picker (keep upload).
   - Categories, Stores, Settings payment/logo images use picker.
6. Add `resolveMediaUrl()` + `<SmartImage>` to avoid broken-image icon and normalize relative URLs.
7. Add sidebar nav entry “Media” under group “Konten”.
8. Run 1 full E2E pass (testing agent) + fix regressions.

**Phase 2 user stories**
1. As an admin, I can manage media in one place (/admin/media) with folders, search, and bulk actions.
2. As an admin, I can upload from the Media Manager and see thumbnails immediately.
3. As an admin, I can pick images for a product from the Media Picker without leaving the editor.
4. As an admin, I can paste an external image URL and the system stores it locally.
5. As an admin, I can use the same picker for CMS sections, category image, store location image, and payment QR/logo.

### Phase 3 — Quality, Migration, and Guardrails
1. Data migration script (idempotent):
   - Normalize existing `media_assets` docs (uploaded_at vs created_at) into unified fields.
   - Default folders seeded (Produk/Banner/Konten/Logo) and assign unfiled assets.
2. Update docs: `docs/03_DATA_MODEL.md`, `docs/04_API_CONTRACT.md`, `DEPLOYMENT_VPS.md` (persistent volume for MEDIA_ROOT, nginx `client_max_body_size 20m`).
3. Update memory: `memory/BUG_REGISTRY.md` (BUG-MEDIA-01..05 fixed), `memory/HANDOFF.md`, `memory/test_credentials.md`.
4. Add/extend gate checks:
   - Backend: ensure no 5xx on adversarial upload, and self-heal path covered.
   - Minimal FE smoke checks for picker open/close and asset list render.
5. Run `scripts/gate.sh` + forensics; run testing agent again.

**Phase 3 user stories**
1. As an admin, my previously uploaded/seeded images still appear and are searchable after migration.
2. As an admin, deleting a folder with content is handled safely (blocked or controlled cascade).
3. As an admin, media URLs remain stable and backward compatible.
4. As an admin, I can see storage stats and quickly find assets by search.
5. As an admin, after restart/redeploy, images still work without manual re-upload.

## 3) Next Actions
1. Implement `scripts/test_media_core.py` scaffold (login + folder CRUD + upload + fetch + self-heal asserts).
2. Add minimal backend endpoints + folder collection + unified asset schema + Pillow derivative generation.
3. Implement `/api/media/{path:path}` self-healing route + GridFS mirror toggle.
4. Run POC script repeatedly until 100% pass; only then start UI.

## 4) Success Criteria
- `python scripts/test_media_core.py` passes **all checks** (including self-heal, from-url ingest, >5MB uploads, invalid payload rejects with 400).
- Admin can upload images from Product Editor and Media Manager; images never break after restart/redeploy.
- Nested folder manager supports create/rename/delete, move assets, bulk operations, search/filter/sort, grid/list.
- Same Media Picker works in Product Editor + CMS Konten + Kategori + Lokasi + Pengaturan pembayaran.
- Legacy `/api/admin/uploads` and existing `/api/media/...` links continue working.
---

# 📌 STATUS PENGERJAAN (E20 — Media Manager Lokal)

## Fase 1 — POC Inti ✅ SELESAI
`scripts/test_media_core.py` → **117/117 PASS** (0 gagal).
Cakupan: login RBAC · folder bertingkat 3 level (create/rename/move/guard siklus/duplikat) ·
upload multi-berkas (JPEG 8.8MB, PNG transparan, SVG, GIF animasi, HEIC iPhone, AVIF) ·
optimasi Pillow (EXIF auto-orient, batas 2400px, turunan WebP 400/1000) · de-dup sha256 ·
penyajian HTTP 200 + content-type + cache + ETag 304 · **SELF-HEAL** (berkas dihapus dari
disk → GET tetap 200 & berkas pulih dari mirror MongoDB) · from-url (unduh ke lokal) ·
patch metadata tanpa mengubah URL · replace berkas (URL tetap) · cari/filter/sort/paginasi
+ X-Total-Count · bulk move/delete (berkas fisik & mirror ikut) · hapus folder aman
(isi dipindah ke induk) + cascade · pasang media ke produk → tampil di katalog PUBLIK ·
penolakan mime/ukuran/traversal tanpa 5xx · RBAC 401/403 · kompatibilitas legacy
(`/admin/uploads`, `/admin/media`, berkas datar lama) · **lokalisasi URL eksternal +
penulisan ulang referensi** (produk, kategori, CMS, toko, pembayaran) & idempotensi.

## Fase 2 — Aplikasi ✅ SELESAI (menunggu verifikasi testing agent)

### Backend
- `backend/services/media.py` (baru, ±1.150 baris): SSOT penyimpanan lokal.
  Layout `media/originals/YYYY/MM/<uuid>.<ext>` + `media/derived/<uuid>_{400,1000}.webp`.
  Mirror GridFS `media_files` (env `MEDIA_DB_MIRROR`, default aktif) + self-heal.
  Batas `MEDIA_MAX_MB=15`. Format: JPG/PNG/WebP/GIF/SVG/AVIF/HEIC(→JPEG)/BMP/TIFF.
- `backend/routers/media_public.py` (baru): `GET|HEAD /api/media/{path}` — pengganti
  `StaticFiles`, self-healing + Cache-Control + ETag + anti path-traversal.
- `backend/routers/admin_media.py` (ditulis ulang): SSOT endpoint media.
  Folders (`/folders`, `/folders/tree`, PATCH, DELETE?cascade), Assets (`/assets`,
  `/upload`, `/from-url`, `/assets/{id}` GET/PATCH/DELETE, `/assets/{id}/replace`,
  `/assets/bulk-delete`, `/assets/bulk-move`), `/stats`,
  `/maintenance/migrate`, `/maintenance/localize`. Alias legacy dipertahankan.
- `backend/media_schemas.py` (baru): kontrak Pydantic media.
- `backend/routers/admin.py`: endpoint media DIPINDAH keluar (hindari tabrakan route).
- `backend/server.py`: mount StaticFiles dihapus, router media didaftarkan lebih dulu,
  indeks media, migrasi + folder standar idempotent saat startup.
- `backend/routers/payments.py`: `POST /api/orders/{code}/payment-proof/upload` —
  pelanggan bisa UNGGAH FOTO bukti bayar (bukan lagi tempel URL). Owner-scoped.
- Skema baru: `payment_methods.logo`, `payment_methods.qr_image`, `store_locations.photo`.

### Frontend
- `src/lib/mediaUrl.js` — resolveMediaUrl (RELATIF di DB → absolut saat render),
  formatBytes, badge tipe, checkerboard, `handleImageError`, placeholder SVG inline.
- `src/components/shared/SmartImage.js` — skeleton → fade-in → placeholder+retry.
  TIDAK PERNAH menampilkan ikon broken-image browser.
- `src/services/media.js` — klien SSOT + `mediaErrorMessage` jujur.
- `src/pages/admin/AdminMediaPage.js` — Media Manager 3 kolom (rail folder / kanvas /
  inspektur), statistik penyimpanan, peringatan + tombol perbaiki gambar hotlink,
  overlay drag&drop global, antrean upload berprogres, bilah aksi massal,
  Sheet untuk mobile.
- `src/components/admin/media/` — FolderTree (flat-render, aman untuk Babel dev),
  MediaToolbar, AssetGrid/AssetList/AssetTile, AssetDetailsPanel, Dropzone,
  UploadQueuePanel, useMediaUpload, MediaDialogs, **MediaPickerDialog**, **MediaField**.
- Integrasi picker: Editor Produk (tab Media: pilih/upload/URL + set utama + urutkan),
  CMS ContentForm (semua field gambar), Kategori (image), Lokasi Toko (photo),
  Pengaturan (OG image + logo & QR metode bayar).
- Ketahanan storefront: ProductCard, ProductDetailPage (carousel/mosaik/sticky),
  QuickViewModal, ImageLightbox, CategoryGrid, StoreLocationsPage, ProductPreview admin,
  PaymentPanel — semua resolve URL + fallback placeholder.
- `src/App.js` rute `/admin/media`, sidebar grup "Konten" → **Media**.
- `src/constants/testIds/admin.js` — ±90 testId media baru.

## Fase 3 — Verifikasi E2E & polish ✅ SELESAI (sesi lanjutan)
- App dipulihkan dari GitHub (kaananabana/cp) ke /app, deps di-install, DB di-seed ulang.
- **Frontend E2E media manager: 100%** (testing_agent_v3 iteration_42): upload, folder
  bertingkat, detail/rename/alt, bulk, cari/filter/sort, hotlink localize, picker di
  editor produk + kategori + lokasi + pembayaran + CMS, add-from-URL lokal.
- Audit gambar (scroll penuh): **HOME 0 broken, SHOP 0 broken**; "9 broken" laporan awal
  adalah FALSE POSITIVE dari lazy-load (belum ter-scroll). PDP hanya placeholder SVG
  prosedural (bukan broken).
- **Perbaikan UI (permintaan user, terverifikasi 100%):**
  1. Manifesto (BigScrollingWord): parallax dibuat non-negatif + font `clamp()` →
     tipografi TIDAK terpotong lagi di tepi kiri/kanan (1920 & 1440).
  2. Margin samping section beranda ditambah via `[data-testid="home-page"] .cp-container-wide`
     (scoped — Shop/PDP sengaja dibiarkan immersive sesuai permintaan).
- Bersih-bersih pasca-test: gambar uji di prd_greenbasillime dihapus (kembali placeholder
  bersih), "Test Folder E2E" + 7 aset uji dihapus → media manager pristine (4 folder default,
  0 aset, 0 hotlink).

### Sisa pekerjaan (opsional, jika user minta)
1. (done) Verifikasi end-to-end oleh `testing_agent_v3` (backend + frontend) & perbaiki temuan.
2. Perbarui `docs/03_DATA_MODEL.md`, `docs/04_API_CONTRACT.md`, `DEPLOYMENT_VPS.md`
   (volume persisten `MEDIA_ROOT`, `client_max_body_size 20m`, `MEDIA_DB_MIRROR`),
   `memory/BUG_REGISTRY.md` (BUG-MEDIA-01..05), `memory/HANDOFF.md`,
   `memory/test_credentials.md`.
3. Opsional lanjutan: crop/rotate di browser, tag & koleksi, laporan aset tak terpakai.
