# PRD — Collector Parfum (FARM Stack)

> Bahasa user: **Indonesia**. Detail arsitektur & aturan kritis ada di `memory/HANDOFF.md`.

## Problem statement asli (sesi 2026-09-21)
Lanjutkan development repo `github.com/pandekomangyogaswastika-dot/cpweb`. Aplikasi sudah
di-deploy ke VPS Hostinger (Ubuntu 24.04, IP 148.230.102.29, folder
`/home/collector/collector-parfum`, backend port 8003) tanpa domain/SSL. Pasang domain
**collectorparfum.com** + HTTPS, dengan panduan memasukkan domain.

Pilihan user: hanya `collectorparfum.com` (www opsional), record email di DNS fastcloud.id
(mail/smtp/pop/MX/SPF → 123.253.29.4) DIBIARKAN, siapkan config Nginx + Certbot + CORS di repo.

## Arsitektur
FastAPI (`backend/server.py`, routers/, services/) + React CRA (frontend/) + MongoDB.
Deploy VPS: `deploy.sh` idempoten (Supervisor `collector-parfum-backend` :8003, Nginx server
block `collector-parfum`, Certbot webroot), dokumentasi `DEPLOYMENT_VPS.md`.

## Yang dikerjakan
- **s.d. 2026-08-04**: E1–E7, E9–E13 selesai (lihat HANDOFF.md). Deploy IP-only ke VPS.
- **2026-09-21 (sesi ini)** — domain + SSL:
  - `deploy.sh`: cek DNS sebelum Certbot (exit 1 bila A record belum ke IP VPS);
    `INCLUDE_WWW=auto|yes|no` (www ikut hanya bila DNS-nya sudah ke VPS); CORS otomatis
    (https/http domain, www bila ada, IP); Nginx ditulis via fungsi `write_nginx_conf`
    (HTTP + ACME webroot → setelah sertifikat: 443 TLS1.2/1.3 http2 HSTS, 80 → 301 ke
    https://domain); `certbot certonly --webroot` + `certbot.timer`; pilihan disimpan di
    `/etc/collector-parfum.deploy.conf` agar `sudo bash deploy.sh` berikutnya tetap HTTPS.
  - `scripts/vps_diag.sh` (diagnosa read-only VPS).
  - `DEPLOYMENT_VPS.md` §5 ditulis ulang: tabel DNS fastcloud.id, firewall Hostinger,
    perintah deploy, verifikasi, opsi, troubleshooting SSL. README diperbarui.
  - Testing agent iterasi 43: LULUS (logika deploy.sh skenario a–e, render nginx `nginx -t`,
    health, login admin, smoke frontend).
  - Belum diverifikasi di VPS asli (butuh user mengubah DNS lalu menjalankan skrip).

## Backlog
- P0: user ubah A record `@` di fastcloud.id → 148.230.102.29, lalu jalankan
  `sudo DOMAIN=collectorparfum.com SETUP_SSL=yes bash deploy.sh` di VPS; ganti password admin.
- P1: E8 Hardening (forensics, N+1, aksesibilitas, release readiness).
- P2: redirect www (bila DNS www diarahkan), backup harian otomatis (mongodump cron).
