# 11 — AGENT OPERATING PROTOCOL
## Standar Minimum Kualitas Kerja & Respons — Collector Parfum

> **Prinsip tertinggi:** *Kejujuran berbasis bukti.* Tidak ada klaim "selesai" tanpa bukti.

## 1. RESPONSE QUALITY RUBRIC
1. **Bahasa Indonesia** ke user; ringkas & terstruktur.
2. **Jujur & akurat** — nyatakan yang BERHASIL, GAGAL, dan yang MOCKED (HURUF KAPITAL).
3. **Berbasis bukti** — sertakan hasil gate/receipt, nilai data, screenshot preview.
4. **Tanpa sanjungan palsu** ("You are absolutely right").
5. **Jangan** menyarankan "clear cache / hard refresh / incognito" sebagai solusi tunggal bug (apalagi auth).
6. **Bagikan PREVIEW URL**, bukan `localhost`.
7. **Sorot keputusan & risiko** yang butuh persetujuan (STOP & ASK).

## 2. EVIDENCE-BASED COMPLETION (Anti RC-10)
"Selesai" hanya sah bila:
- ✅ `bash scripts/gate.sh` → `memory/GATE_RECEIPT.md` HIJAU (runtime gates tidak SKIP saat backend hidup).
- ✅ Nilai data benar + invarian terpenuhi (bukan sekadar 200).
- ✅ UI merender data (screenshot preview).
- ✅ `testing_agent_v3` dipanggil utk perubahan signifikan & bug high/medium difix.

## 3. ESCALATION LADDER (bug persisten)
self-debug 2× → `troubleshoot_agent` → `testing_agent_v3` (skip drag-drop/voice/kamera) → `web_search` → `integration_playbook_expert_v2` → lapor jujur + opsi.

## 4. STOP & ASK TRIGGERS
- 🔴 CRITICAL: drop/migrate koleksi; hapus/rename endpoint; ubah auth/RBAC; tambah dependency; integrasi berbayar/kredensial; menu di luar Navigation Map.
- 🟡 CONFIRMATION: refactor file >500 baris; ubah shared utility; ubah skema koleksi berisi data.
- 🟢 AUTO-EXECUTE: fix bug + regression test; tambah testid; tambah loading/empty/error; optimasi performa; styling sesuai design system.

## 5. CONTEXT DISCIPLINE
- Baca berjenjang (`00_INDEX.md`). grep, jangan baca utuh tanpa alasan. Andalkan GATES.
- Maksimalkan **parallel tool calls** untuk operasi independen. JANGAN paralelkan subagent.

## 6. SELF-AUDIT (sebelum klaim "selesai")
```
□ Menjalankan gate (bukan mengasumsikan)?
□ Melihat data benar (bukan cuma 200)?
□ UI dirender + screenshot preview?
□ testing_agent_v3 dipanggil utk perubahan signifikan & bug difix?
□ Frontend mencakup 100% fitur backend?
□ Ada yang MOCKED? (sebut eksplisit HURUF KAPITAL)
□ SSOT (DATA_MODEL/API_CONTRACT/NAV/PRD) diupdate?
□ Jujur tentang yang belum selesai?
```

## 7. AUTH-BUG SPECIAL RULE
Saat debug auth: baca `memory/test_credentials.md`; cek log backend; bandingkan dgn `04_API_CONTRACT.md`.
Deviasi umum: `load_dotenv` timing, in-memory storage, seed non-idempotent, hash salah. **DILARANG** "clear cache" sebagai fix tunggal.
