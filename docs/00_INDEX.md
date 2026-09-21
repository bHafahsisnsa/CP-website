# 00 — INDEX & PROTOKOL BACA BERJENJANG
## Collector Parfum — E-commerce Parfum Premium (Bahasa Indonesia)

> **Prinsip emas:** *Guardrail = kode yang bisa GAGAL (exit ≠ 0). Kode menang atas dokumen.*
> Dokumen ini SSOT (single source of truth). Bila kode & dokumen bentrok → sinkronkan, jangan diamkan.

---

## Cara baca (hemat konteks)
**Tier 0 (WAJIB, selalu):**
- `07_ENGINEERING_GUARDRAILS.md` — taksonomi bug + 3-gate + Definition of Done backend.
- `08_FRONTEND_GUARDRAILS.md` — kontrak FE, testid, state data.
- `11_AGENT_OPERATING_PROTOCOL.md` — standar respons & bukti.
- `14_ANTI_UNDERDELIVERY_PROTOCOL.md` — anti kerja setengah.

**Tier 1 (sesuai tugas):**
- `01_PRD.md`, `02_ARCHITECTURE.md`, `03_DATA_MODEL.md`, `04_API_CONTRACT.md`, `05_NAVIGATION_MAP.md`, `13_ARCHITECTURE_BEST_PRACTICES.md`.

**Tier 2 (jarang):**
- `DEEP_ANALYSIS_PLAYBOOK.md` — saat analisis besar / redesign.

---

## Alur kerja singkat
```bash
cd /app
bash scripts/load_context.sh            # snapshot awal sesi
python scripts/preflight.py "<fitur>"    # anti-duplikasi sebelum bangun
# ... koding ...
bash scripts/gate.sh                     # WAJIB hijau sebelum "selesai" (memory/GATE_RECEIPT.md)
```

## Status proyek
- **Frontend V1 (storefront)**: SUDAH matang (Maya-theme), data masih lokal/dummy.
- **Fondasi backend + guardrails**: SUDAH berdiri (fase ini).
- **Business logic (products/orders/checkout/admin)**: fase BERIKUTNYA (belum dimulai).

## Peta dokumen
| File | Isi |
|------|-----|
| 01_PRD | Tujuan produk, persona, ruang lingkup V1 |
| 02_ARCHITECTURE | Diagram lapisan, konvensi, folder |
| 03_DATA_MODEL | Koleksi kanonik + field + id-prefix + enum |
| 04_API_CONTRACT | Endpoint, bentuk respons, auth |
| 05_NAVIGATION_MAP | IA storefront + akun + admin |
| 07/08 | Guardrail backend & frontend |
| 11/13/14 | Protokol agent, best-practice arsitektur, anti-under-deliver |
| DEEP_ANALYSIS_PLAYBOOK | Cara analisis mendalam |
