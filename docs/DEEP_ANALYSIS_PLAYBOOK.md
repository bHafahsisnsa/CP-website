# 🔬 DEEP ANALYSIS PLAYBOOK
## Panduan analisis mendalam — Collector Parfum

> **Tujuan:** mengubah analisis dangkal ("global, menebak") menjadi analisis berbasis bukti, point-per-point, sadar batasan, dan siap eksekusi.

## A. KAPAN DIPAKAI
Sebelum membangun/merombak fitur besar (checkout, admin, payment, migrasi). Tidak perlu utk tugas trivial.

## B. DOKTRIN KEDALAMAN (10 prinsip)
1. **Bukti dulu, opini belakangan** — baca kode/dokumen/data NYATA & kutip lokasinya.
2. **Sumber primer** — codebase, skema DB, `products.js`, router, log. Bukan ingatan.
3. **Telusuri batasan sebelum solusi** — guardrail, kontrak API, `.env`, RBAC.
4. **Traceability** — tiap poin kebutuhan → solusi konkret → fase → file.
5. **Spesifik, bukan normatif** — "tambah `GET /api/products` + `ShopPage` fetch", bukan "buat UI modern".
6. **Sintesis komparatif** — bila ada referensi (Shopee-style/butik), ekstrak pola → strategi spesifik.
7. **Leverage aset existing** — storefront V1 sudah ada; hubungkan, jangan bangun ulang.
8. **Kuantifikasi & benchmark** — target perf (list < 300ms), konversi, dsb.
9. **Keputusan ber-trade-off** — tiap pilihan: alasan + alternatif ditolak.
10. **Artefak + checkpoint** — hasil = dokumen review + konfirmasi sebelum eksekusi.

> Mnemonik: **B-T-K-S-R-A** → Bukti → Traceability → Kendala → Sintesis → Rencana → Artefak.

## C. PIPELINE 6 TAHAP
0. **Intent & batasan** — baca permintaan mentah TANPA parafrase; tandai tujuan/ambiguitas/kata kunci; tanya bila kritis.
1. **Kumpul bukti** — eksplor codebase/skema/URL; ringkas "yang SUDAH ADA & cara kerjanya" + temuan; kutip path/endpoint.
2. **Traceability matrix** — pecah jadi poin atomik; tiap poin → kondisi kini → akar → solusi (file) → fase.
3. **Kendala & arsitektur** — guardrail/kontrak/hal-yang-tak-boleh-rusak + strategi kepatuhan.
4. **Sintesis & keputusan** — decision log (opsi+alasan+alternatif ditolak); benchmark; NOW vs LATER.
5. **Rencana berfase + risiko** — fase (tujuan, file BE/FE, dependensi, testing, maps ke poin) + tabel risiko.
6. **Artefak + checkpoint** — tulis `plan.md`/`design_guidelines.md`; ajukan pertanyaan berpilihan; tunggu GO.

## D. DEFINITION OF DONE ANALISIS (lulus ≥ 85/100)
Berbasis bukti (20) · traceability (20) · sadar kendala (15) · spesifik/eksekutabel (15) · trade-off (10) · kuantifikasi (5) · leverage existing (5) · NOW/LATER (5) · artefak+checkpoint (5).

## E. ANTI-PATTERN → PENANGKAL
- "Buat UI modern" → sebut komponen/file spesifik.
- Menebak isi kode → baca sumber primer.
- Lewatkan poin → traceability matrix lengkap.
- Abaikan yang bisa rusak → tahap kendala wajib.
- Pilih library tanpa alasan → decision log.
- Langsung koding → artefak + checkpoint dulu.

## F. TEMPLATE
**Traceability**: | # | Kebutuhan | Kondisi kini (bukti) | Akar | Solusi (file/komponen) | Fase |
**Decision log**: | Keputusan | Opsi | Dipilih | Alasan | Alternatif ditolak |
**Rencana fase**: Tujuan / Backend / Frontend / Dependensi / Testing / Maps ke poin.
**Risiko**: | Risiko | Dampak | Kemungkinan | Mitigasi |
**NOW vs LATER**: SEKARANG (dampak tinggi/biaya rendah) · DITUNDA (butuh kredensial/biaya) + kesiapan.

_Dokumen hidup — perbarui saat menemukan pola baru._
