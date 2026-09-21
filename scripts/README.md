# GUARDRAILS — Executable Gate Suite LENGKAP (Collector Parfum)

Guardrail **yang bisa GAGAL** (exit != 0) untuk mencegah bug data, drift FE<->BE, 5xx, utang UX,
**state-machine**, **concurrency/TOCTOU**, **cross-entity**, **RBAC/IDOR**, **negative-value**, dan
**under-delivery**. Diadaptasi dari repo mature `kn` & `travel` + laporan bug-find mereka. Baca dulu:
`docs/07_ENGINEERING_GUARDRAILS.md`, `docs/08_FRONTEND_GUARDRAILS.md`, **`docs/09_THREAT_MODEL.md`**.

## Orkestrator (WAJIB sebelum `finish`)
```bash
cd /app
bash scripts/gate.sh          # semua gate (statik+runtime+forensik+meta) -> memory/GATE_RECEIPT.md
bash scripts/run_forensics.sh # audit adversarial mendalam
python scripts/preflight.py "<kata>"   # anti-duplikasi sebelum bangun fitur
bash scripts/load_context.sh           # snapshot awal sesi
```

## Prinsip desain: GROW-WITH-CODE
Gate runtime (state-machine, concurrency, mutation_smoke, adversarial-5xx, fa_race, fa_write_idor,
fa_idor_matrix) **SKIP rapi** saat endpoint business-logic belum ada, lalu **AKTIF OTOMATIS** begitu
endpoint dibuat. Jadi mitigasi ancaman sudah "terpasang" sejak fondasi, bukan ditunda.

## Daftar gate
### A. Kontrak & data (statik/DB)
| Script | Fungsi | Kelas |
|--------|--------|-------|
| `seed_reset.sh` | seed bersih + [GATE] contract+api_contract+integrity | RC-1/RC-F4 |
| `seed_data.py` | seed data referensi (idempotent) | — |
| `verify_contract.py` | koleksi kanonik vs alias terlarang (`db.x` & `db["x"]`) | RC-1 |
| `verify_schema.py` | id-prefix + enum + FK referential | RC-2/RC-E5 |
| `verify_data_integrity.py` | invarian domain (INV-1..11) | RC-E1/2/4/9/12 |
| `verify_api_contract.py` | route duplikat + FE->route ada + path literal | RC-F4 |
| `verify_cross_entity.py` | konsistensi lintas koleksi (used_count/overpay/FK/total) | RC-E9 |
| `verify_architecture.py` | unbounded query, N+1, file-size, kebocoran field | perf/RC-E14 |
| `verify_delivery.py` | manifest P0 lengkap + orphan endpoint | RC-E16 |
| `check_nav_map.py` | dead link / orphan page (FE) | RC-E13 |
| `ux_audit.py` | baseline UX (select native/hardcode URL/testid) | RC-E13/F8 |
| `validate_compliance.py` | file-size, debug, hardcode, router wiring, env | RC-8/RC-6 |
### B. guardrails/ (invariant preventif)
| Script | Fungsi | Kelas |
|--------|--------|-------|
| `guardrails/verify_numeric_bounds.py` | field uang/qty wajib ge=/gt= (AST schemas) | RC-E12 |
| `guardrails/verify_rbac_guards.py` | router admin wajib require_role/section; matrix SSOT | RC-E10 |
| `guardrails/verify_stock_locks.py` | mutasi stok wajib atomik/stock_lock | RC-E3 |
| `guardrails/verify_adversarial_5xx.py` | input adversarial -> no 5xx (runtime) | RC-E11 |
### C. Runtime lifecycle
| Script | Fungsi | Kelas |
|--------|--------|-------|
| `verify_state_machine.py` | transisi order legal + cancel balikin stok + no-pay-terminal | RC-E4/6/7/8 |
| `verify_concurrency.py` | checkout paralel -> tak oversell | RC-E3 |
| `mutation_smoke.py` | audit alur TULIS (create/checkout) | write-path |
| `health_check.py` | ISI endpoint kritis (bukan cuma 200) | RC-3/RC-10 |
| `audit_endpoint_sweep.py` | hit SEMUA GET /api -> 5xx | RC-6 |
### D. forensic/ (adversarial + meta)
| Script | Fungsi | Kelas |
|--------|--------|-------|
| `fa_static.py` | statik: datetime naif, bare except, eval, unbounded | tech-debt |
| `fa_nplus1.py` | deteksi N+1 (heuristik) | perf |
| `fa_dark_sweep.py` | endpoint gelap (BE tanpa FE) | RC-E16 |
| `fa_mutation.py` | **META: suntik cacat -> gate HARUS gagal** | anti no-op |
| `fa_fuzz.py` | payload POST rusak -> 4xx/422 bukan 5xx | RC-E11 |
| `fa_5xx.py` | adversarial GET -> no 5xx | RC-E11 |
| `fa_session.py` | token palsu/kedaluwarsa/user-nonaktif -> 401 | RC-E15 |
| `fa_idor.py` | RBAC dasar (me tanpa token=401; register->customer) | RC-E10 |
| `fa_idor_matrix.py` | matriks role x endpoint admin | RC-E10 |
| `fa_write_idor.py` | write IDOR lintas-pemilik | RC-E10 |
| `fa_race.py` | anti-oversell konkurensi | RC-E3 |

## Aturan emas
1. Verifikasi di **DB bersih** (`seed_reset`) — DB kotor menutupi drift.
2. "200 / running" **bukan** bukti — cek **nilai** & **invarian**.
3. Uji **jalur menyimpang** (cancel/ilegal/terminal) & **paralel**, bukan hanya happy-path single-thread.
4. Fitur baru => tambah Concept/endpoint/invarian/skenario ke gate terkait (docs/07 §7) + entri `BUG_REGISTRY.md`. **Guardrail tumbuh bersama kode.**
5. Jalankan `fa_mutation` berkala — pastikan gate tidak jadi no-op (RC-10).

## Env
`MONGO_URL`, `DB_NAME` dari `backend/.env` (auto). `API_BASE`/`GUARD_BASE_URL` default `http://localhost:8001`; `ADMIN_EMAIL`/`ADMIN_PASS` bisa di-override.
