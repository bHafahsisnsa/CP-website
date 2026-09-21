# 🚀 DEPLOY COLLECTOR PARFUM KE VPS — SEKALI JADI

> Panduan deploy aplikasi **Collector Parfum** (React + FastAPI + MongoDB) ke VPS Ubuntu
> memakai satu skrip: **`deploy.sh`**.
> Skrip dirancang **berdampingan** dengan aplikasi lain di VPS yang sama (tidak menyentuh
> service, port, database, atau konfigurasi Nginx aplikasi lain).

---

## 1. Ringkasan

| Hal | Nilai |
|-----|-------|
| Nama aplikasi | `collector-parfum` |
| User Linux | `collector` |
| Folder aplikasi | `/home/collector/collector-parfum` |
| Port backend | **8003** (127.0.0.1 saja) |
| Database Mongo | **`collector_parfum`** |
| Frontend | build statis dilayani Nginx |
| Data persisten | `/var/lib/collector-parfum/media` & `/var/lib/collector-parfum/backups` |
| Domain | **collectorparfum.com** (DNS di fastcloud.id) → lihat §5. Sebelum DNS diarahkan: `http://148.230.102.29` |
| Repo sumber | `https://github.com/pandekomangyogaswastika-dot/cpweb.git` (branch `main`) |

**Peta port di VPS ini (agar tidak bentrok):**

| Port | Aplikasi |
|------|----------|
| 8001 | KBS8 |
| 8002 | Garment ERP (SOMMERVILLE) |
| **8003** | **Collector Parfum (aplikasi ini)** |

---

## 2. Prasyarat

1. VPS Ubuntu **22.04** atau **24.04**, akses `root` / `sudo`.
2. Perubahan terbaru sudah **di-push ke GitHub** (`main`) — skrip mengambil kode dari repo.
3. Port 80 (dan 443 bila nanti pakai domain) terbuka.
4. MongoDB sudah ada di VPS → dipakai bersama, **database terpisah**. Kalau belum ada, skrip
   memasangnya otomatis.

---

## 3. Cara deploy (1 perintah)

```bash
# di VPS, sebagai root
wget -O deploy.sh https://raw.githubusercontent.com/pandekomangyogaswastika-dot/cpweb/main/deploy.sh
sudo bash deploy.sh
```

Selesai. Skrip akan mencetak ringkasan:

```
Storefront   : http://148.230.102.29
Admin panel  : http://148.230.102.29/admin
API health   : http://148.230.102.29/api/health
Login admin  : admin@collectorparfum.id / Admin#2026
```

> ⚠️ **Ganti password admin** setelah login pertama (Admin → menu akun).

### Yang dikerjakan skrip (13 langkah)

1. Install dependency sistem (git, python3-venv, nginx, supervisor, ufw, openssl…).
2. Install Node.js 20 + Yarn (kalau belum ada).
3. Cek/install MongoDB (8.0, fallback 7.0) — **tidak** mengubah data aplikasi lain.
4. Buat user `collector` + `git clone`/`git pull` kode ke `/home/collector/collector-parfum`.
5. Siapkan folder data persisten (media & backup) di `/var/lib/collector-parfum`.
6. Buat virtualenv Python + install `backend/requirements-prod.txt` (14 paket, ±10 detik).
7. Tulis `backend/.env` (MONGO_URL, DB_NAME, CORS_ORIGINS, MEDIA_ROOT, BACKUP_ROOT).
8. Tulis `frontend/.env` + `yarn install` + **`yarn build`** (build produksi).
9. Daftarkan service Supervisor `collector-parfum-backend` di port 8003.
10. Seed data awal **hanya bila database masih kosong** (admin, kategori, voucher, konten
    storefront, 3 lokasi toko, 12 produk contoh).
11. Buat server block Nginx `collector-parfum` (root = folder build, `/api` → 127.0.0.1:8003).
12. SSL Let's Encrypt (webroot) — hanya bila `DOMAIN` diisi; lihat §5.
13. Firewall UFW + verifikasi `/api/health` lewat backend langsung maupun lewat Nginx.

---

## 4. Update aplikasi (setelah push perubahan baru)

Skrip **idempoten** — jalankan ulang kapan saja:

```bash
cd /home/collector/collector-parfum
sudo bash deploy.sh
```

Yang terjadi: `git fetch` + `reset --hard origin/main` → pip install → yarn build → restart
service. **Database, media, dan file backup TIDAK disentuh** (seed dilewati karena DB sudah berisi).

Update cepat tanpa rebuild frontend (hanya backend):

```bash
sudo SKIP_BUILD=yes bash deploy.sh
```

---

## 5. Pasang domain **collectorparfum.com** + HTTPS

> Kondisi saat ini: DNS domain dikelola di **fastcloud.id** (NS `ns1/ns2.fastcloud.id`), semua
> A record masih menunjuk ke hosting lama **123.253.29.4**. Email (`mail`, `smtp`, `pop`, MX,
> SPF) **tetap** di hosting lama — hanya website yang dipindah ke VPS **148.230.102.29**.

### 5.1 Ubah DNS di panel fastcloud.id (DNS Management)

Klik ikon ✏️ pada baris berikut, ubah **Value**, simpan:

| Name | Type | Value lama | **Value baru** | Keterangan |
|------|------|------------|----------------|------------|
| `collectorparfum.com.` | A | 123.253.29.4 | **148.230.102.29** | ✅ WAJIB — domain utama → VPS |
| `www` | A | 123.253.29.4 | **148.230.102.29** | Opsional. Bila diubah, skrip otomatis ikut melayani `www` → redirect ke domain utama. Bila tidak, `www` dilewati (tidak membuat Certbot gagal). |
| `mail`, `smtp`, `pop`, `ftp` | A | 123.253.29.4 | *(biarkan)* | Email & FTP tetap di hosting lama |
| `collectorparfum.com.` | MX / TXT (SPF) / NS | — | *(biarkan)* | Jangan disentuh |

TTL 3600 → propagasi biasanya **5–60 menit**. Cek dari VPS (atau laptop):

```bash
dig +short collectorparfum.com @1.1.1.1      # harus: 148.230.102.29
dig +short www.collectorparfum.com @1.1.1.1  # 148.230.102.29 bila www ikut diubah
```

Belum berubah? Tunggu; **jangan** jalankan langkah 5.3 dulu (skrip akan menolak otomatis).

### 5.2 Pastikan port 80 & 443 terbuka di VPS

UFW di dalam VPS sudah diizinkan oleh skrip (`Nginx Full`). **Firewall di panel Hostinger**
(VPS → Firewall rule) juga harus mengizinkan **TCP 80** dan **TCP 443** dari `0.0.0.0/0`.

### 5.3 Jalankan skrip deploy dengan domain

```bash
ssh root@148.230.102.29
cd /home/collector/collector-parfum
git pull                                   # ambil deploy.sh versi terbaru
sudo DOMAIN=collectorparfum.com SETUP_SSL=yes SSL_EMAIL=cs@collectorparfum.com bash deploy.sh
```

Yang dilakukan skrip:

1. **Cek DNS** — berhenti bila `collectorparfum.com` belum mengarah ke IP VPS (Certbot pasti gagal).
2. Deteksi `www` otomatis (`INCLUDE_WWW=auto`): ikut disertakan hanya bila DNS-nya sudah ke VPS.
3. Tulis `backend/.env` → `CORS_ORIGINS=https://collectorparfum.com,http://collectorparfum.com,http://148.230.102.29`.
4. Rebuild frontend dengan `REACT_APP_BACKEND_URL=https://collectorparfum.com`.
5. Nginx HTTP + lokasi ACME (`/.well-known/acme-challenge/` → `/var/www/letsencrypt`).
6. `certbot certonly --webroot` → sertifikat di `/etc/letsencrypt/live/collectorparfum.com/`.
7. Tulis ulang Nginx: **443 (TLS 1.2/1.3, HTTP/2, HSTS)** + **80 → 301 https://collectorparfum.com**
   (akses lewat IP atau `www` juga diarahkan ke domain utama).
8. Aktifkan `certbot.timer` (perpanjangan otomatis tiap 60 hari, reload Nginx via deploy-hook).
9. Simpan pilihan ke `/etc/collector-parfum.deploy.conf` → `sudo bash deploy.sh` berikutnya
   **otomatis tetap memakai domain + HTTPS** (tidak turun lagi ke mode IP).

Ringkasan akhir skrip menampilkan `Storefront : https://collectorparfum.com` dan hasil cek
`HTTPS OK`.

### 5.4 Verifikasi

```bash
curl -I https://collectorparfum.com                 # HTTP/2 200
curl -I http://collectorparfum.com                  # 301 -> https://collectorparfum.com/
curl -I http://148.230.102.29                       # 301 -> https://collectorparfum.com/
curl -s https://collectorparfum.com/api/health      # {"status":"ok","db":true,...}
sudo certbot certificates                           # Expiry Date ~90 hari
sudo systemctl status certbot.timer --no-pager      # active (waiting)
```

Di browser: `https://collectorparfum.com` (gembok hijau), `/admin` → login → ganti password.

### 5.5 Opsi

| Perintah | Efek |
|----------|------|
| `sudo bash deploy.sh` | Update kode; domain & HTTPS tetap (dibaca dari `/etc/collector-parfum.deploy.conf`) |
| `sudo INCLUDE_WWW=yes DOMAIN=collectorparfum.com bash deploy.sh` | Paksa `www` masuk sertifikat (DNS `www` harus sudah ke VPS) |
| `sudo DOMAIN=collectorparfum.com SETUP_SSL=no bash deploy.sh` | Domain tanpa HTTPS (sementara, mis. DNS belum propagasi) |
| `sudo DOMAIN= bash deploy.sh` | Kembali ke mode IP |
| `sudo CORS_ORIGINS=https://a.com,https://b.com bash deploy.sh` | Override daftar CORS manual |

### 5.6 Troubleshooting SSL

| Gejala | Solusi |
|--------|--------|
| Skrip berhenti: "DNS … BELUM mengarah" | DNS belum propagasi. `dig +short collectorparfum.com @1.1.1.1` sampai keluar `148.230.102.29`, ulangi. |
| Certbot: `Connection refused` / `Timeout during connect` | Port 80 tertutup di Firewall panel Hostinger → izinkan TCP 80 & 443. Cek `sudo ufw status`. |
| Certbot: `unauthorized` / `Invalid response` | Ada server block Nginx lain yang menangkap `collectorparfum.com` (mis. `default_server`). Cek `grep -rn server_name /etc/nginx/sites-enabled/`. |
| Certbot: `too many failed authorizations` | Rate limit Let's Encrypt (5 gagal/jam). Tunggu 1 jam, perbaiki penyebab dulu. |
| Browser "Not secure" padahal sertifikat ada | Cache browser / `REACT_APP_BACKEND_URL` masih http. Jalankan ulang `sudo bash deploy.sh` (rebuild). |
| Mixed content (gambar tidak muncul) | Gambar dipanggil via `http://IP/api/media/...` dari data lama. Rebuild + hard refresh; media URL bersifat relatif sehingga ikut domain aktif. |
| Perpanjangan otomatis | `sudo certbot renew --dry-run` harus sukses; lokasi ACME selalu ada di konfigurasi Nginx. |

### 5.7 Info VPS untuk diagnosa

Bila perlu mengirim kondisi VPS untuk dibantu, jalankan dan salin hasilnya:

```bash
bash /home/collector/collector-parfum/scripts/vps_diag.sh
```

---

## 6. Opsi konfigurasi (environment variable)

Semua bisa dioverride tanpa mengedit file:

```bash
sudo BACKEND_PORT=8005 DB_NAME=cp_staging APP_NAME=cp-staging APP_USER=cpstaging bash deploy.sh
```

| Variabel | Default | Keterangan |
|----------|---------|------------|
| `DOMAIN` | *(kosong)* | Kosong = pakai IP VPS |
| `SERVER_IP` | `148.230.102.29` | Kosongkan untuk auto-deteksi IP publik |
| `BACKEND_PORT` | `8003` | Port uvicorn (localhost saja) |
| `DB_NAME` | `collector_parfum` | Database MongoDB |
| `MONGO_URL` | `mongodb://localhost:27017` | Bisa diarahkan ke Mongo lain |
| `SEED_DATA` | `auto` | `auto` (seed bila DB kosong) · `yes` (paksa) · `no` |
| `SETUP_SSL` | `auto` | `auto`/`yes`/`no` (butuh `DOMAIN`) |
| `INCLUDE_WWW` | `auto` | `auto` (ikut bila DNS `www` → VPS) / `yes` / `no` |
| `SSL_EMAIL` | `cs@collectorparfum.com` | Email notifikasi Let's Encrypt |
| `CORS_ORIGINS` | *(otomatis)* | Override daftar origin CORS (dipisah koma) |
| `UVICORN_WORKERS` | `2` | Naikkan bila CPU banyak |
| `NODE_BUILD_MEMORY` | `2048` | Naikkan bila build “out of memory” |
| `SKIP_BUILD` | `no` | `yes` = lewati build frontend |
| `DATA_ROOT` | `/var/lib/collector-parfum` | Lokasi media & backup persisten |
| `REPO_URL` / `REPO_BRANCH` | repo `main` | Sumber kode |

---

## 7. Perintah operasional

```bash
# status & log service
sudo supervisorctl status collector-parfum-backend
sudo supervisorctl restart collector-parfum-backend
sudo tail -f /var/log/collector-parfum-backend.err.log

# nginx
sudo nginx -t && sudo systemctl reload nginx
sudo tail -f /var/log/nginx/error.log

# health
curl -s http://127.0.0.1:8003/api/health
curl -s http://148.230.102.29/api/health

# database
mongosh collector_parfum --eval 'db.products.countDocuments({})'

# backup database (cepat)
mongodump --db collector_parfum --out /var/backups/cp-$(date +%F)
```

---

## 8. Impor katalog asli (6.000+ baris)

1. Login admin → **Produk → Impor / Ekspor**.
2. Unggah `.xlsx`/`.csv` (maks 8 MB; Nginx sudah disetel `client_max_body_size 64M`).
3. Bila kolom harga masih 0: pakai panel **Isi Harga Massal** (matriks Tier × Ukuran/Tipe),
   isi harga → **Terapkan** → **Impor**.
4. Hasil impor masuk sebagai **draft (`archived`) + stok 0** → aktifkan lewat
   **Produk → pilih semua → Aktifkan** (aksi massal).

Catatan performa: baris disimpan di sesi server (`import_sessions`, TTL 6 jam) sehingga validasi
tidak mengirim ulang seluruh baris; `proxy_read_timeout 600s` sudah disetel untuk commit besar.

---

## 9. Troubleshooting

| Gejala | Penyebab & solusi |
|--------|-------------------|
| `502 Bad Gateway` | Backend mati → `sudo supervisorctl status collector-parfum-backend`, lihat `/var/log/collector-parfum-backend.err.log`. Sering karena dependency belum lengkap → jalankan ulang `sudo bash deploy.sh`. |
| Build frontend “out of memory” | `sudo NODE_BUILD_MEMORY=4096 bash deploy.sh`, atau tambah swap 2 GB. |
| Halaman putih / aset 404 | Folder build tidak terbaca Nginx → `sudo chmod 755 /home/collector && sudo chmod -R 755 /home/collector/collector-parfum/frontend/build`. |
| API 404 di browser tapi 200 di `127.0.0.1:8003` | Server block Nginx tidak match → cek `server_name` di `/etc/nginx/sites-available/collector-parfum` sesuai IP/domain yang diakses. |
| `nginx -t` gagal setelah deploy | Ada server block lain memakai `default_server` untuk port 80 dengan `server_name` sama. Hapus duplikasi, lalu `sudo systemctl reload nginx`. |
| Gambar upload hilang setelah update | Pastikan `MEDIA_ROOT` di `backend/.env` menunjuk `/var/lib/collector-parfum/media` (skrip melakukannya otomatis). |
| MongoDB gagal dipasang | Cek codename Ubuntu: `lsb_release -cs`. Skrip mencoba repo 8.0 lalu fallback 7.0/jammy. Bisa juga pasang manual lalu jalankan ulang skrip. |
| Ingin reset data demo | `sudo -u collector bash -lc "cd /home/collector/collector-parfum && backend/venv/bin/python scripts/seed_data.py"` (mengembalikan konten CMS ke default). |

---

## 10. Checklist smoke test setelah deploy

- [ ] `http://148.230.102.29` → beranda tampil (announcement “Refill Perfume Distributor Since 1970”).
- [ ] `/tentang` → sejarah 1970 (Jalan Kolektor → Paledang 14 → Paledang 58).
- [ ] `/kontak` → WhatsApp `+62 857-2000-0105`, email `cs@collectorparfum.com`.
- [ ] `/lokasi` → 3 cabang (Paledang, Pasir Kaliki, Gatot Subroto).
- [ ] `/shop` → 12 produk contoh tampil, filter kategori bekerja.
- [ ] PDP → pilih varian → **Tambah ke Keranjang** → `/checkout` → **Buat Pesanan** → halaman sukses.
- [ ] `/admin` → login admin → Dashboard, Produk, Impor/Ekspor, Pengaturan terbuka.
- [ ] Impor file kecil (`tests/import_samples/qa_tier_small.csv`) berhasil.
- [ ] `curl http://148.230.102.29/api/health` → `{"status":"ok","db":true}`.

---

## 11. Keamanan minimum sebelum dipakai publik

1. **Ganti password admin** (`Admin#2026` hanya untuk instalasi awal).
2. Hapus/ganti akun demo `customer@collectorparfum.id` bila tidak diperlukan.
3. Setelah punya domain, pasang **HTTPS** (langkah §5) — jangan biarkan login lewat HTTP.
4. Batasi akses SSH (key-only), UFW sudah dinyalakan skrip (SSH + HTTP/HTTPS).
5. Jadwalkan `mongodump` harian (lihat §7) atau pakai menu **Admin → Backup & Restore**.
