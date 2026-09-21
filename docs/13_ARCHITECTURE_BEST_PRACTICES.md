# 13 — ARCHITECTURE & PERFORMANCE BEST PRACTICES
## Collector Parfum

> **Prinsip:** kode efisien, ringkas, jelas; performa & skalabilitas sejak awal; tech-debt minimal.
> Penegak: `scripts/verify_architecture.py` (statis) + review.

## 1. MINIMUM BEST-PRACTICE ARCHITECTURE
```
React (pages tipis + shared) → apiClient (axios) → /api/*
FastAPI: routers (THIN I/O) → services (logika) → Motor/MongoDB
```
- **Separation of concerns**: router tanpa logika bisnis → `services/`.
- **SRP**: 1 file = 1 tanggung jawab. Router ≤ 800, service/util ≤ 300, page/komponen ≤ 500.
- **DRY**: util dipakai-ulang (`core_utils.py`, `lib/format.js`). Perhitungan uang → satu SSOT (`services/pricing` di fase berikutnya).
- **Stateless API**; **idempotent seed & migration**.

## 2. PERFORMA (dicek `verify_architecture.py`)
| Aturan | Wajib | Anti-pattern |
|--------|-------|--------------|
| Pagination | list endpoint dukung `limit` (default 20–50) + `skip` | `.to_list(None)` / tanpa limit |
| Projection | ambil field seperlunya utk list | tarik dokumen penuh utk tabel ringkas |
| Index | field query panas: `slug`(unik), `category`, `status`, `email`(unik), `orders.code`(unik), `user_id` | scan tanpa index |
| No N+1 | batukan query (`$in`/aggregate) | `for x: await db...` per item |
| Hitung di DB | `count_documents`/aggregate utk KPI | tarik semua lalu `len()` |
| Payload | jangan kirim `password_hash` | bocor field sensitif |
| FE list besar | pagination + skeleton | render ribuan baris sekaligus |
| Debounce | search di-debounce (~300ms) | request tiap ketukan |

Target MVP: list endpoint < 300 ms pada seed; tidak ada query unbounded.

## 3. KUALITAS & KERINGKASAN
- Tulis sependek mungkin yang tetap jelas. Hapus kode mati & abstraksi prematur.
- Early-return; fungsi fokus; nama deskriptif.
- Tanpa `print`/`console.log` debug tertinggal (`validate_compliance.py`).
- Tanpa TODO/FIXME diam-diam → catat di `01_PRD.md` backlog.
- **Reuse sebelum tulis baru**: `preflight.py`.

## 4. INDEX YANG SUDAH DISET (server.py startup)
`users.email`(unik), `users.id`(unik), `sessions.token`(unik), `products.slug`(unik), `products.category`, `products.status`, `categories.slug`(unik), `vouchers.code`(unik), `orders.code`(unik), `orders.user_id`, `orders.status`, `addresses.user_id`, `counters.name`(unik).

## 5. TECH-DEBT & DEPENDENCY
- Fitur baru WAJIB daftar ke gate terkait (docs/07 §7).
- Refactor file yang lewat batas ukuran **segera**.
- Dependency baru = **STOP & ASK**. `yarn add` (bukan npm); backend via requirements.

## 6. TECH STACK MENDUKUNG TUJUAN
| Kebutuhan | Pilihan | Alasan |
|-----------|---------|--------|
| Async I/O DB | Motor | non-blocking |
| Validasi/kontrak | Pydantic | kurangi drift |
| UI konsisten | shadcn/ui + Tailwind | teruji, a11y, tokenized |
| Animasi | framer-motion | halus, sudah dipakai storefront |
| Hash password | bcrypt | standar aman (+fallback legacy) |
