# 🐞 BUG REGISTRY — Collector Parfum

> Registry hidup untuk melacak bug & kelas-ancaman + status mitigasinya. Terinspirasi
> `BUG_REGISTRY`/`BUG_BACKLOG` repo mature. Tiap fitur baru: tinjau kelas relevan & pastikan gate-nya aktif.
> Kolom Status: PREVENTED (gate aktif mencegah) · WATCH (gate SIAP-AKTIF, menunggu fitur) · OPEN (bug nyata) · FIXED.

## A. Kelas ancaman warisan (dari analisis kn & travel) — dipetakan ke gate
| ID | Kelas (RC-E) | Ringkas | Gate pencegah | Status |
|----|--------------|---------|---------------|--------|
| TR-01 | RC-E3 | Oversell stok (TOCTOU race) | atomik `$inc` ber-guard `stock>=qty` (services/stock.py) + verify_concurrency (10 paralel→1 sukses) + fa_race (12 paralel) | PREVENTED (E3) |
| TR-02 | RC-E6 | Cancel tak kembalikan stok | transition_order cancel→stock.restore + verify_state_machine SM1 (endpoint pemilik) | PREVENTED (E3) |
| TR-03 | RC-E7 | Transisi status ilegal / split-brain | LEGAL_TRANSITIONS SSOT (services/orders.py) + verify_state_machine SM2 + docs/06 | PREVENTED (E3) |
| TR-04 | RC-E8 | Aksi (bayar) pada order terminal | LEGAL_TRANSITIONS (terminal=∅) + record_payment guard terminal + verify_state_machine SM3/SM5 + INV-P2 (verify_data_integrity) | PREVENTED (E3+E6) |
| TR-05 | RC-E4 | Payment status drift (complete≠lunas / uang palsu) | derive_payment_status (INV-5, tak pernah hand-set) + record_payment ($inc paid_amount) + verify_state_machine SM4/SM6 + INV-P1 rekonsiliasi (verify_data_integrity + CE5) | PREVENTED (E3+E6) |
| TR-06 | RC-E1 | Order total drift | pricing SSOT `compute_pricing` (dipakai verifier INV-2/3 + create_order/checkout E3) + cross_entity CE4 | PREVENTED (SSOT E2+E3) |
| TR-07 | RC-E2 | Voucher salah hitung / limit abuse | pricing SSOT `voucher_discount` (cap/clamp/min-spend/window/scope) + INV-3/9/9b + CE1 + redemption atomik (create_order guarded usage_limit) | PREVENTED (E2 validate + E3 redemption) |
| TR-08 | RC-E9 | Cross-entity inconsistency | verify_cross_entity CE1..CE4 (used==orders==redemptions) | PREVENTED (E3) |
| TR-09 | RC-E10 | RBAC leakage / IDOR / priv-injection | verify_rbac_guards + fa_idor(_matrix) + fa_write_idor (order & alamat A vs B → 404) + get_current_user owner-scoped (orders/addresses/wishlist) + `/api/admin/*` require_role('admin') (no-token→401, customer→403; 11 route diuji fa_idor_matrix) | PREVENTED (E3+E4 owner-scoped, E5 admin RBAC + audit) |
| TR-10 | RC-E11 | Input adversarial → 5xx | verify_adversarial_5xx + fa_fuzz + fa_5xx | PREVENTED (auth teruji) |
| TR-11 | RC-E12 | Negative-value | verify_numeric_bounds (20 field) + INV-4/11 | PREVENTED |
| TR-12 | RC-E13 | FE cross-page pollution / dead menu | check_nav_map (42 link OK) + ux_audit | PREVENTED |
| TR-13 | RC-E15 | Session/token hardening | fa_session (S1/S2/S3) + verify_auth_resilience (INV-AUTH-01: token tak dibuang karena blip jaringan) | PREVENTED |
| TR-14 | RC-E16 | Under-delivery / orphan endpoint | verify_delivery + fa_dark_sweep + fa_mutation | PREVENTED |
| TR-15 | RC-E5 | FK menggantung | verify_schema + cross_entity CE3 | PREVENTED (nihil) / WATCH |
| CAT-01 | RC-E11 | Katalog: input query adversarial (limit/skip/q/price) → 5xx | services.catalog parse_int+clamp + re.escape(q); fa_5xx/fa_fuzz/adversarial_5xx (19 probe) | PREVENTED (E1) |
| CAT-02 | RC-E13 | Storefront konsumsi data lokal (drift) / orphan endpoint | verify_api_contract (4 call FE↔BE) + verify_delivery D2 + fa_dark_sweep | PREVENTED (E1) |
| CAT-03 | RC-E5/E9 | Review FK menggantung + rating drift UI vs DB | verify_data_integrity INV-8/INV-C3 (SSOT rating dari reviews) | PREVENTED (E1) |
| CAT-04 | RC-E12 | Volume/price/compare_at_price non-positif atau varian duplikat | INV-4a/4b + INV-C1/INV-C2 | PREVENTED (E1) |
| VCH-01 | RC-E1/E2/E14 | Diskon/total beda UI vs BE (drift), rounding float | `services/pricing.py` PURE integer SSOT; `verify_data_integrity` INV-2/3 impor `compute_pricing`; FE render diskon dari respons API saja | PREVENTED (E2) |
| VCH-02 | RC-E2 | discount>subtotal, min_spend dilewati, window/expired, over-limit | cap ke subtotal + total floor 0; window/min-spend/usage/per-user checks di `evaluate_voucher`; redemption used_count di-guard atomik saat create_order | PREVENTED (E2 validate + E3 redemption) |
| VCH-03 | RC-E11 | Validate payload adversarial → 5xx | Pydantic `VoucherValidateIn` (bounds ge=) + validate selalu `valid=false`+reason; `scripts/test_e2_core.py` 5 payload rusak → no 5xx | PREVENTED (E2) |
| VCH-04 | RC-E9/E12 | Phantom redemption / used_count drift; negative limit | `verify_cross_entity` CE1 (used==orders==redemptions) + INV-9b + INV-R1..R3; redemption tertulis atomik + kuota di-guard `$expr usage_limit` | PREVENTED (E3) |

## B. Bug aktif (OPEN) — fase ini
_(tidak ada bug OPEN pada fondasi. Isi saat fase business-logic bila ditemukan.)_

### BUG-AUTH-01 — blip jaringan MENGHAPUS sesi (FIXED 2026-08-03, E12 hardening)
| Field | Isi |
|-------|-----|
| Kelas | RC-E15 (session hardening) + RC-E13 (FE state) |
| Gejala | User/admin tiba-tiba terlempar ke form login di tengah pekerjaan (paling terasa di wizard impor 6.426 baris). Terlihat berulang saat pod/ingress restart (502) dan pada koneksi lambat. |
| Root cause | `frontend/src/store/AuthContext.js` memanggil `apiLogout()` di **setiap** kegagalan `GET /api/auth/me` — termasuk timeout/offline/502 — sehingga token di `localStorage` DIHAPUS meski sesi server masih sah (TTL 30 hari). |
| Fix | Token hanya dihapus pada penolakan definitif 401/403; error transient dicoba ulang (backoff 0,9s/2,2s/4,5s) + auto-retry saat event `online`/tab aktif; UI baru `admin-session-offline` & `account-session-offline` ("Server belum terjangkau — sesi masih aktif") menggantikan form login. |
| Gate pencegah | `scripts/guardrails/verify_auth_resilience.py` (INV-AUTH-01) — di-wire ke `scripts/gate.sh`. Uji negatif: mengembalikan `apiLogout()` tanpa pagar status → gate MERAH (terbukti bukan no-op). |
| Bukti | Playwright: intercept `**/api/auth/me` → 502, reload → panel `admin-session-offline` tampil, `login_form=0`, token TETAP ada; setelah server pulih klik "Coba Lagi" → kembali ke `admin-shell` TANPA login manual. |
| Status | FIXED |

## C. Log verifikasi mitigasi (bukti gate bekerja)
- fa_mutation: MUT-1 (INV-9), MUT-2 (RC-1 contract), MUT-3 (INV-NUM-01) — **3/3 CAUGHT** (gate bukan no-op).
- fa_session: S1 token palsu, S2 kedaluwarsa, S3 user nonaktif — **semua ditolak 401**.
- Negative test manual: voucher value=0 → INV-9 FAIL; `db.items` → RC-1 FAIL; pulih setelah restore.
- **Epic E1 (2026-07-05):** `bash scripts/gate.sh` HIJAU (semua gate non-skip PASS) + `testing_agent_v3` iteration_3: backend 34/34 (100%), frontend 37/37 (empty-state & PDP reviews diverifikasi manual: `shop-grid-empty` aktif pada `?cat=nonexistent`; 3 `pdp-review-item` render, rating 4.7·3). fa_5xx 19 probe adversarial → 0×5xx. INV-C1/C2/C3 + INV-8 aktif (22 invarian PASS).
- **Epic E2 (2026-07-05):** Pricing SSOT (`services/pricing.py`) + Voucher (`services/vouchers.py`, `POST /api/vouchers/validate`, `GET /api/vouchers`). `scripts/test_e2_core.py` 36/36 PASS (unit cap/clamp/rounding/free_shipping/COD/floor + DB eligibility window/scope/min-spend + HTTP kontrak & 5 adversarial → no 5xx). `verify_data_integrity` INV-2/3 kini impor `compute_pricing` (SATU formula). CE1 diperluas: `used_count == #orders == #redemptions`.
- **Epic E3 (2026-07-05):** Cart/Checkout/Orders. `services/stock.py` (atomik `$inc` guarded), `services/orders.py` (create_order + LEGAL_TRANSITIONS + derive_payment_status), routers orders/cart/config. `scripts/test_e3_core.py` 19/19 PASS (happy + anti-oversell 8-paralel + cancel-restore + SM2/3/4 + IDOR + redemption atomik + adversarial no-5xx). Gate AKTIF tanpa SKIP: verify_state_machine (SM1-4), verify_concurrency (10→1), mutation_smoke (M2/M3), fa_race (12→1), fa_write_idor (A vs B→404). INV-3 kini scope-aware. FE: guest checkout + login/register, checkout dari `/api/shipping-methods|payment-methods`, OrderSuccess by code, riwayat + cancel. `bash scripts/gate.sh` HIJAU penuh.

## D. Cara pakai
1. Menambah fitur → cari kelas RC-E terkait (docs/09) → pastikan gate WATCH-nya aktif (buka skenario di verify_*).
2. Menemukan bug → tambah baris OPEN + tulis gate yang MEREPRODUKSI-nya dulu (test-first), baru fix → FIXED.
3. Jalankan `bash scripts/gate.sh` + `bash scripts/run_forensics.sh` sebelum klaim selesai.
