# 07 — ENGINEERING GUARDRAILS (Backend)
## Collector Parfum — E-commerce Parfum

> **Status:** WAJIB. **Prinsip emas:** *Guardrail = kode yang bisa GAGAL (exit ≠ 0). Kode menang atas dokumen.*

---

## 0. CARA PAKAI (TL;DR)
Sebelum menyatakan task "selesai", jalankan dari `/app`:
```bash
bash scripts/gate.sh                    # orkestrator → memory/GATE_RECEIPT.md (WAJIB hijau)
```
Granular:
```bash
bash scripts/seed_reset.sh              # seed + [GATE] contract + api_contract + integrity
python scripts/verify_schema.py         # id-prefix + enum + FK
python scripts/health_check.py          # ISI endpoint kritis (bukan cuma 200)
python scripts/audit_endpoint_sweep.py  # sweep SEMUA GET /api → 5xx
python scripts/validate_compliance.py   # file-size, debug, env, /api, router wiring
bash scripts/run_forensics.sh           # idor / fuzz / 5xx / race
```
Semua hijau → boleh `finish`. Ada FAIL → **perbaiki dulu** (atau catat eksplisit sebagai keputusan owner).

---

## 1. RANTAI DESYNC (akar semua bug data)
```
SEED ─tulis→ KOLEKSI MONGO ←baca─ SERVICE ← ROUTER ─JSON→ FRONTEND
  nama koleksi    nama field       signature   /api prefix   import & parsing
```
Satu lapis "geser" (drift) → seluruh rantai patah **tanpa error jelas** (200 tapi data kosong/angka salah/500). Gate menutup tiap titik geser.

---

## 2. TAKSONOMI ROOT CAUSE (domain e-commerce parfum)
| RC | Nama | Contoh | Gate penangkap |
|----|------|--------|----------------|
| **RC-1** | Collection name drift | seed tulis `products`, app baca `items` | `verify_contract.py` |
| **RC-2** | Field/schema drift | `compare_at_price` vs `compareAtPrice`; enum salah | `verify_schema.py` |
| **RC-3** | Response shape drift | FE harap ARRAY, BE bungkus `{items}` | `health_check.py`, sweep |
| **RC-4** | Import komponen hilang | layar putih | esbuild / runtime |
| **RC-5** | Number-series desync | `CP0001` tanpa naikkan counter → kode order duplikat | `verify_data_integrity` (INV-7) |
| **RC-6** | Snapshot putus | order item tanpa `name/unit_price` → render 500 | sweep 5xx |
| **RC-7** | Bug semantik | "best seller" dihitung salah; total ≠ rincian | invarian lintas-endpoint |
| **RC-8** | Hardcoded value | ongkir/cod_fee literal di UI ≠ sumber data | review + integrity |
| **RC-9** | RBAC dua sumber | izin FE ≠ `permissions_config.py` | review + `fa_idor` |
| **RC-10** | False-positive testing | "200 = selesai" | **ATURAN:** cek ISI & invarian |
| **RC-F4** | Drift FE↔BE | path/field FE ≠ route/respons BE | `verify_api_contract.py` |
| **RC-E1 (domain)** | **Order total drift** | `total ≠ subtotal−discount+ongkir+cod_fee` | INV-2 |
| **RC-E2 (domain)** | **Voucher salah hitung** | percent/flat tak sesuai / melebihi subtotal | INV-3/INV-9 |
| **RC-E3 (domain)** | **Oversell stok** | qty terjual > stok / stok negatif | INV-4 + `fa_race` |
| **RC-E4 (domain)** | **Payment status drift** | paid≥total tapi status ≠ lunas | INV-5 |
| **RC-E5 (domain)** | **FK menggantung** | order.item.product_id / product.category tak ada | INV-8/verify_schema |

---

## 3. KONTRAK KANONIK (ringkas — detail di 04_API_CONTRACT & 03_DATA_MODEL)
- **Auth:** `POST /api/auth/login {email,password}` → `{token,user}`; field `token` (prefiks `sess_`).
- **Bentuk respons:** list → ARRAY; detail → OBJEK. Tanpa envelope.
- **Serialisasi:** semua dokumen lewat `safe_doc()` (strip `_id`+`password_hash`, koersi ObjectId/datetime).
- **Invarian wajib** (di-enforce `verify_data_integrity.py`): lihat `memory/INVARIANTS.md` (INV-1..INV-11).

---

## 4. CHECKLIST 3-GATE
### Gate A — PRE-CODE
- [ ] Konsep/koleksi sudah ada? `python scripts/preflight.py "<kata>"` + `verify_contract.py --list-canonical`. **Jangan duplikat.**
- [ ] Bentuk respons ikut kontrak (array/objek telanjang, field `token`).
- [ ] Posisi fitur di `05_NAVIGATION_MAP.md` ditentukan.
- [ ] Integrasi pihak-3 → minta playbook + simpan kredensial di `.env`.

### Gate B — DURING-CODE
- [ ] Akses Mongo pakai nama kanonik (`db.products`, bukan `db.items`).
- [ ] Render/serialisasi defensif (`.get()` + `safe_doc()`), uang lewat `money()`.
- [ ] Endpoint `/api`-prefixed; ENV via `os.environ` (jangan ubah `.env`).
- [ ] List endpoint pakai `limit` (default 20–50); tidak ada N+1.
- [ ] Router ≤ 800 baris; logika berat → `services/`.

### Gate C — POST-CODE (sebelum "selesai")
- [ ] `bash scripts/gate.sh` → receipt HIJAU (tanpa SKIP saat backend hidup).
- [ ] `health_check` 0 FAIL; `audit_endpoint_sweep` 0 entri 5xx.
- [ ] Invarian valid pada seed bersih.
- [ ] `testing_agent_v3` untuk perubahan signifikan; semua bug difix.

---

## 5. DEFINITION OF DONE (backend)
1. Gate A–C hijau (atau FAIL didokumentasikan sebagai keputusan owner).
2. Tidak ada 5xx baru pada sweep.
3. Invarian valid pada seed bersih.
4. Frontend mencerminkan 100% fitur backend (tidak ada endpoint yatim).
5. Tidak ada koleksi/field/endpoint duplikat.
6. Bila belum beres → **dilaporkan jujur** ("BELUM SELESAI" + bukti), bukan diklaim hijau.

---

## 6. ESKALASI BUG PERSISTEN
Self-debug maks 2× → `troubleshoot_agent` (RCA) → `testing_agent_v3` → `web_search` (versi/SDK) →
`integration_playbook_expert_v2` (integrasi) → lapor jujur + opsi. **DILARANG** klaim selesai tanpa bukti.
**Anti-RC-10:** "HTTP 200"/"service running"/"no error log" BUKAN bukti. Bukti = nilai data benar + invarian + UI merender data.

---

## 7. KAPAN MENAMBAH GATE BARU (guardrail tumbuh bersama kode)
Tambah fitur/koleksi ⇒ WAJIB:
- Tambah koleksi ke `CANONICAL_COLLECTIONS` (`verify_contract.py`) **dan** `03_DATA_MODEL.md`.
- Tambah `Concept(...)` + invarian ke `verify_data_integrity.py` + `memory/INVARIANTS.md`.
- Tambah endpoint kritis ke `CRITICAL_ENDPOINTS` (`health_check.py`).
- Tambah id-prefix/enum ke `verify_schema.py`.
- Update DELIVERY_MANIFEST fase aktif.
> Guardrail yang tidak tumbuh bersama kode akan **membusuk** dan menutupi drift.
