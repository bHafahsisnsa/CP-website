# 14 — ANTI-UNDER-DELIVERY & EFFORT PROTOCOL
## Collector Parfum

> **Status:** TIER 0. **Prinsip:** *Effort itu wajib & terukur. "Selesai" = deliverable lengkap + bukti, bukan klaim.*

## 1. ⛔ ANTI-EXCUSE CLAUSE
DALIL berikut DILARANG untuk berhenti/menurunkan kualitas:
- ❌ "Konteks/instruksi kurang" → kerja seadanya/berhenti.
- ❌ "Mungkin maksud user begini" lalu ambil yang paling mudah.
- ❌ "HTTP 200 / tidak ada error" dianggap bukti selesai (RC-10).

**WAJIB saat info terasa kurang:**
1. **Gali dulu** sumber yang ADA (docs/, codebase, `preflight.py`, grep). Mayoritas "kurang konteks" = "belum dibaca".
2. Bila ada celah keputusan → tulis **ASSUMPTION LEDGER** lalu tetap maju dengan asumsi paling masuk akal (ditandai).
3. **STOP & ASK** hanya untuk hal kritis tak bisa diasumsikan (kredensial, biaya, breaking change) — pertanyaan bernomor + opsi.

## 2. 📏 DEPTH STANDARD per jenis tugas
- **ANALISIS**: pembedahan per-bagian; ≥ 8 temuan konkret + implikasi; kontradiksi/risiko/celah; referensi silang; rekomendasi actionable. (Bukan ringkasan 3 kalimat.)
- **BUILD**: Backend + Frontend + seed + states (loading/empty/error) + `data-testid` sebagai satu kesatuan. Tidak ada orphan endpoint / ghost page.
- **DEBUG**: RCA sampai akar (petakan ke RC), bukan tambal gejala. Kuatkan gate agar tak terulang.
- **DESIGN/UI**: ikuti `design_guidelines.md` sepenuhnya (bukan UI "datar").

## 3. 🧾 ASSUMPTION LEDGER (template)
```
ASUMSI (agar tetap maju):
1. [Asumsi] — alasan — risiko bila salah — mudah diubah? [ya/tidak]
BUTUH KONFIRMASI (kritis saja):
1. [pertanyaan + opsi a/b/c]
RENCANA: lanjut membangun X; bila (1) beda, dampak terbatas pada [file/area].
```

## 4. 📦 DELIVERY MANIFEST
Tiap fase punya kontrak deliverable **bisa dihitung** di `memory/DELIVERY_MANIFEST.md`
(endpoint apa saja, halaman apa saja, min testid, seed count, invarian yang lulus, screenshot wajib).
Item P0 belum ada → **dilarang klaim selesai**.

## 5. ✅ EVIDENCE-BASED COMPLETION
"Selesai" sah bila SEMUA ada:
- `memory/GATE_RECEIPT.md` HIJAU.
- Deliverable P0 manifest 100% + 0 orphan endpoint.
- Nilai data benar + invarian lulus.
- Screenshot preview URL.
- `testing_agent_v3` untuk perubahan signifikan; bug high/medium difix.
- Laporan jujur: sebut yang MOCKED/limitasi (HURUF KAPITAL).

## 6. 🧮 SELF-AUDIT EFFORT
```
□ Sudah MENGGALI semua sumber ADA sebelum bilang "kurang konteks"?
□ Kedalaman memenuhi DEPTH STANDARD (§2)?
□ Ada deliverable yang diam-diam dilewati? (cek DELIVERY_MANIFEST)
□ gate.sh hijau (bukan asumsi)?
□ Menulis Assumption Ledger alih-alih berhenti?
□ Jujur soal yang belum selesai / MOCKED?
```
Ada □ tak terpenuhi → JANGAN klaim selesai.

## 7. ESKALASI (bukan menyerah)
Buntu ≠ berhenti: self-debug 2× → troubleshoot_agent → testing_agent_v3 → web_search → integration_playbook_expert_v2 → lapor jujur + opsi + bukti.
