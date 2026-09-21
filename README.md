# Collector Parfum — Toko Parfum Refill (FARM Stack)

E-commerce **Collector Parfum**: distributor parfum refill di Bandung sejak **1970**
(Paledang · Pasir Kaliki · Gatot Subroto). Dibangun dengan **FastAPI + React + MongoDB**.

---

## Fitur utama

**Storefront**
- Katalog dengan filter keluarga aroma, occasion, karakter, gender, harga, pencarian.
- Varian N-dimensi (Ukuran × Tipe × Konsentrasi, sampai 4 dimensi) + stok per SKU.
- Label **“Inspired by <merek>”** otomatis untuk merek non-house (bisa dimatikan dari admin).
- Keranjang, checkout tamu/login, voucher, ongkir & metode pembayaran, unggah bukti bayar.
- Akun pelanggan: profil, alamat (single-default), riwayat pesanan, wishlist.
- Halaman Tentang (sejarah 1970), Lokasi 3 cabang + peta, Kontak, FAQ, Voucher Center.
- Sesi login tahan gangguan jaringan (token tidak dibuang saat 502/timeout).

**Admin backoffice** (`/admin`)
- Dashboard, produk & editor varian, kategori/occasion/karakter, ulasan, pesanan, pembayaran.
- **Impor / Ekspor katalog** CSV/XLSX ala Shopify (kolom `option1..4_name/value`):
  - sesi impor server-side → file 6.400+ baris tidak lagi menyebabkan timeout validasi,
  - **matriks harga tier** (Tier × Ukuran/Tipe) untuk mengisi ribuan harga sekali klik,
  - hasil impor masuk sebagai draft `archived` + stok 0, lalu **aktivasi massal**.
- CMS storefront: hampir semua teks halaman dapat diedit dari `/admin/konten`.
- Analitik, CRM segmen, media, pengaturan toko, Backup & Restore.

---

## Deploy ke VPS (sekali jadi)

```bash
wget -O deploy.sh https://raw.githubusercontent.com/pandekomangyogaswastika-dot/cpweb/main/deploy.sh
sudo bash deploy.sh
```

- Berdampingan dengan aplikasi lain di VPS yang sama (backend **port 8003**, database
  `collector_parfum`, server block Nginx sendiri).
- Tanpa domain → otomatis dilayani lewat IP VPS. Pasang domain + HTTPS (setelah A record
  `collectorparfum.com` → `148.230.102.29` di DNS fastcloud.id):
  `sudo DOMAIN=collectorparfum.com SETUP_SSL=yes bash deploy.sh`
  — skrip mengecek DNS dulu, `www` ikut otomatis hanya bila DNS-nya sudah ke VPS, dan pilihan
  domain diingat di `/etc/collector-parfum.deploy.conf`. Panduan: `DEPLOYMENT_VPS.md` §5.
- Update: jalankan ulang `sudo bash deploy.sh` (idempoten; data & domain/HTTPS tidak disentuh).
- Diagnosa VPS: `bash scripts/vps_diag.sh`.

Panduan lengkap + troubleshooting: **[`DEPLOYMENT_VPS.md`](DEPLOYMENT_VPS.md)**

---

## Pengembangan lokal

```bash
cd backend && pip install -r requirements.txt      # produksi: requirements-prod.txt
cd ../frontend && yarn install
cd .. && python scripts/seed_data.py               # data awal (idempoten)
sudo supervisorctl restart backend frontend
```

Login awal: `admin@collectorparfum.id` / `Admin#2026` — **segera ganti password.**

## Verifikasi (wajib hijau sebelum klaim selesai)

```bash
bash scripts/gate.sh                        # 31 gate: statik + runtime + forensik
python scripts/test_shop_and_import_e2e.py  # regresi belanja + wizard impor
python scripts/test_import_session_poc.py   # sesi impor (E12)
python scripts/test_tier_matrix_poc.py      # matriks harga tier (E11)
```

## Dokumentasi

| Berkas | Isi |
|--------|-----|
| `DEPLOYMENT_VPS.md` | Panduan deploy VPS + operasional + troubleshooting |
| `memory/HANDOFF.md` | Status proyek, aturan kritis, titik lanjut |
| `memory/DELIVERY_MANIFEST.md` | Deliverable per fase (ditagih `verify_delivery.py`) |
| `memory/BUG_REGISTRY.md` · `memory/INVARIANTS.md` | Kelas bug + invariant yang dijaga gate |
| `docs/` | PRD, arsitektur, data model, kontrak API, threat model, roadmap E1–E8 |
| `plan.md` | Rencana & status fase pengerjaan |
