# 09 — THREAT MODEL (Peta Ancaman Bug) — Collector Parfum

> **Sumber:** analisis laporan bug-find repo mature `kn` (ERP tekstil) & `travel` (ERP travel):
> `FORENSIC_00_EXECUTIVE_SUMMARY`, `BUG_REGISTRY`, `BUG_BACKLOG`, `AUDIT_REPORT_SESSION_*`,
> `root_cause_matrix`. Dokumen ini menerjemahkan kelas-bug yang TERBUKTI berulang di sana ke
> domain e-commerce parfum, lalu MEMETAKAN tiap ancaman ke GATE yang mencegahnya.
>
> **Temuan inti dari laporan:** mayoritas bug SERIUS lolos justru KARENA gate lama hanya menguji
> **clean-seed + happy-path + single-thread + HTTP 200**. Bug "green-but-broken" muncul di:
> (1) STATE-MACHINE (transisi menyimpang), (2) CONCURRENCY/TOCTOU (balapan), (3) CROSS-ENTITY
> (konsistensi lintas koleksi), (4) RBAC/IDOR, (5) input adversarial → 5xx, (6) negative-value,
> (7) FRONTEND cross-page pollution / dead menu. Fondasi ini menambah gate khusus untuk SETIAP kelas.

---

## A. RINGKAS: kenapa "semua hijau" tapi tetap bug (pelajaran dari laporan)
| Sumbu uji lama | Yang TIDAK teruji | Bug lolos |
|---|---|---|
| clean-seed | data "kotor"/menyimpang | total salah, FK menggantung |
| happy-path | jalur cancel/refund/ilegal | cancel tak balikin stok; bayar order batal |
| single-thread | akses paralel | oversell, overpay (TOCTOU) |
| per-entitas | konsistensi lintas koleksi | used_count voucher != realita |
| status 200 | ISI & invarian | angka salah tapi "sukses" |
| happy input | input adversarial | 5xx crash |
| — | nilai negatif | harga/stok negatif diterima |
| kualitas kode | UX lintas-halaman | menu mati, konten bocor antar-halaman |

---

## B. KATALOG ANCAMAN (RC-E series) — e-commerce parfum

### RC-E1 — Order total drift  (asal: travel INV total; kn financial recompute)
- **Ancaman:** `total != subtotal - discount + ongkir + cod_fee`; pembulatan/urutan salah; diskon dihitung 2 tempat berbeda (UI vs BE).
- **Dampak:** pelanggan tertagih salah; laporan omzet keliru.
- **Mitigasi:** SSOT perhitungan `services/pricing.py` dipakai checkout **dan** verifier. Gate: `verify_data_integrity` INV-1/INV-2, `verify_cross_entity` CE4.

### RC-E2 — Voucher salah hitung / abuse
- **Ancaman:** percent/flat salah; diskon > subtotal; `min_spend` tak dicek; voucher dipakai melebihi `usage_limit`; `used_count` tak sinkron.
- **Mitigasi:** aturan diskon tunggal (INV-3); `verify_data_integrity` INV-9; `verify_cross_entity` CE1 (used_count == #order). Validasi `min_spend` & `usage_limit` di service.

### RC-E3 — Oversell stok (TOCTOU/race)  (asal: travel RC-01 race overpayment)
- **Ancaman:** 2 checkout paralel membeli unit terakhir → stok negatif / terjual > tersedia (cek-lalu-tulis tanpa kunci).
- **Dampak:** jual barang yang tak ada → refund/komplain.
- **Mitigasi:** dekremen stok ATOMIK (`$inc` ber-filter `stock >= qty`) atau `stock_lock`. Gate STATIK: `guardrails/verify_stock_locks`. Gate RUNTIME: `verify_concurrency` (N checkout paralel), `forensic/fa_race`. Invarian INV-4 (stok >= 0).

### RC-E4 — Payment status drift  (asal: travel RC-02 complete tanpa lunas)
- **Ancaman:** `paid >= total` tapi status != lunas; atau order di-"complete" tapi diam-diam ditandai lunas (sinyal keuangan kontradiktif).
- **Mitigasi:** derivasi `payment_status` tunggal (INV-5); `verify_state_machine` SM4 (complete tanpa lunas tetap jujur).

### RC-E5 — FK menggantung (referential)
- **Ancaman:** `order.items[].product_id` / `product.category` menunjuk entitas yang tak ada (produk dihapus, kategori di-rename).
- **Mitigasi:** `verify_schema` (FK), `verify_cross_entity` CE3. Hapus produk = arsip (soft-delete), bukan hard-delete bila terpakai order.

### RC-E6 — Cancel tak melepas sumber daya  (asal: travel RC-04 cancel tak bebaskan armada)
- **Ancaman:** batalkan order tapi stok yang sudah "dikurangi/di-reserve" TIDAK dikembalikan → stok hantu.
- **Mitigasi:** transisi `cancel` WAJIB mengembalikan stok (kompensasi). Gate: `verify_state_machine` SM1.

### RC-E7 — Transisi status ilegal / split-brain  (asal: travel RC-03 status via dua jalur beda)
- **Ancaman:** `pending -> shipped` tanpa `paid`; dua jalur update status (admin vs sistem) memberi hasil beda.
- **Mitigasi:** state-machine SSOT (docs/06); satu fungsi transisi ber-guard. Gate: `verify_state_machine` SM2.

### RC-E8 — Aksi pada order terminal  (asal: travel RC-05 bayar booking cancelled)
- **Ancaman:** menerima pembayaran/mutasi pada order `cancelled`/`completed`.
- **Mitigasi:** guard status terminal; Gate: `verify_state_machine` SM3.

### RC-E9 — Cross-entity inconsistency  (asal: travel RC-06 payroll overlap dobel-hitung)
- **Ancaman:** agregat lintas koleksi tak konsisten (Sum paid > Sum total; used_count salah; stok terjual != pengurangan).
- **Mitigasi:** `verify_cross_entity` (CE1..CE4).

### RC-E10 — RBAC / IDOR  (asal: kn/travel O-1 RBAC leakage)
- **Ancaman:** customer akses endpoint/route admin via URL; write-IDOR (ubah alamat/pesanan milik orang lain); privilege injection saat register (`role: admin`).
- **Mitigasi:** `dependencies.require_role/require_section` + SSOT `permissions_config`. Gate STATIK: `guardrails/verify_rbac_guards`. Gate RUNTIME: `forensic/fa_idor`, `fa_idor_matrix`, `fa_write_idor`. (register PAKSA role='customer'.)

### RC-E11 — Input adversarial -> 5xx  (asal: travel EXPORT-1/R6-4/R6-5)
- **Ancaman:** string super panjang / unicode/null / tipe salah / markup → crash 500.
- **Mitigasi:** validasi Pydantic + escape; input buruk = 4xx/422. Gate: `guardrails/verify_adversarial_5xx`, `forensic/fa_fuzz`, `fa_5xx`, `audit_endpoint_sweep`.

### RC-E12 — Negative-value  (asal: travel Putaran 11: 57/63 field terima negatif)
- **Ancaman:** harga/stok/qty/amount negatif → total kacau, stok negatif, abuse refund.
- **Mitigasi:** SEMUA field uang/kuantitas ber-bound `ge=/gt=` di `schemas.py`. Gate STATIK: `guardrails/verify_numeric_bounds`. Invarian INV-4/INV-11.

### RC-E13 — Frontend cross-page pollution / dead menu  (asal: kn BUG_BACKLOG)
- **Ancaman:** komponen halaman-spesifik (mis. kartu dashboard/onboarding) bocor ke semua halaman; menu mengarah ke rute yang tak ada; navigasi redundan.
- **Mitigasi:** SSOT navigasi (docs/05); Gate: `check_nav_map` (dead link/orphan); `ux_audit`; `verify_delivery` D2 (orphan endpoint = fitur yatim).

### RC-E14 — Money as float
- **Ancaman:** drift akumulasi float pada perhitungan uang.
- **Mitigasi:** uang = INTEGER rupiah (`core_utils.money`). Review + INV numeric.

### RC-E15 — Session/token hardening
- **Ancaman:** token palsu diterima; sesi kedaluwarsa masih valid; akun nonaktif tetap akses.
- **Mitigasi:** `dependencies` cek expiry + status aktif + hapus sesi kedaluwarsa. Gate: `forensic/fa_session`.
- **Ancaman (varian klien, BUG-AUTH-01 — nyata & sudah terjadi):** klien MEMBUANG token sendiri saat
  panggilan `GET /api/auth/me` gagal karena sebab TRANSIENT (offline, timeout, 502 ingress/pod restart).
  Dampak: admin di tengah pekerjaan panjang (wizard impor 6.426 baris) terlempar ke form login dan
  kehilangan konteks — padahal sesi server masih sah (TTL 30 hari).
- **Mitigasi:** `store/AuthContext.js` hanya menghapus token pada penolakan DEFINITIF (401/403);
  kegagalan transient di-retry (backoff 900/2200/4500 ms) + auto-retry pada event `online` /
  tab kembali terlihat; UI menampilkan status pemulihan (`admin-session-offline`,
  `account-session-offline`) bukan form login. Gate: `scripts/guardrails/verify_auth_resilience.py`
  (INV-AUTH-01, statik, sudah dibuktikan bisa MERAH lewat uji mutasi manual).

### RC-E16 — Under-delivery / orphan (asal: anti-under-deliver protocol)
- **Ancaman:** endpoint dibuat tanpa UI; deliverable P0 diam-diam dilewati; "green palsu".
- **Mitigasi:** `verify_delivery` (manifest P0 + orphan), `fa_dark_sweep`, `fa_mutation` (buktikan gate tak no-op).

---

## C. MATRIKS ANCAMAN -> GATE (checklist mitigasi)
| RC-E | Kelas | Gate STATIK | Gate RUNTIME/FORENSIK | Invarian |
|------|-------|-------------|----------------------|----------|
| E1 | total drift | — | verify_data_integrity, cross_entity | INV-1/2 |
| E2 | voucher | — | data_integrity, cross_entity | INV-3/9 |
| E3 | oversell race | verify_stock_locks | verify_concurrency, fa_race | INV-4 |
| E4 | payment status | — | verify_state_machine (SM4) | INV-5 |
| E5 | FK menggantung | — | verify_schema, cross_entity | INV-8 |
| E6 | cancel tak lepas stok | — | verify_state_machine (SM1) | INV-4 |
| E7 | transisi ilegal | — | verify_state_machine (SM2) | INV-6 |
| E8 | aksi order terminal | — | verify_state_machine (SM3) | INV-6 |
| E9 | cross-entity | — | verify_cross_entity | INV-1/2/7 |
| E10 | RBAC/IDOR | verify_rbac_guards | fa_idor, fa_idor_matrix, fa_write_idor | — |
| E11 | adversarial 5xx | — | verify_adversarial_5xx, fa_fuzz, fa_5xx, sweep | — |
| E12 | negative-value | verify_numeric_bounds | data_integrity | INV-4/11 |
| E13 | FE cross-page/dead menu | check_nav_map, ux_audit | verify_delivery (D2) | — |
| E14 | money float | verify_architecture/review | data_integrity | INV-1/2 |
| E15 | session | — | fa_session | — |
| E16 | under-deliver | verify_delivery | fa_dark_sweep, fa_mutation | — |

---

## D. ATURAN OPERASI (turunan langsung dari laporan)
1. **Uji jalur menyimpang, bukan hanya happy-path** — tiap fitur tulis WAJIB punya skenario cancel/ilegal/terminal di `verify_state_machine`.
2. **Uji paralel untuk setiap sumber daya terbatas** (stok, voucher limit, pembayaran) via `verify_concurrency`/`fa_race`.
3. **Konsistensi lintas koleksi** dicek `verify_cross_entity` tiap menambah relasi.
4. **HTTP 200 != bukti** — selalu cek nilai + invarian (anti RC-10).
5. **Guardrail tumbuh bersama kode** — fitur baru => daftarkan ke gate (docs/07 §7) & tambah entri `BUG_REGISTRY.md`.
6. **fa_mutation** dijalankan berkala — memastikan gate tidak berubah jadi no-op.
