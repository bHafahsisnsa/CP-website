# 08 — FRONTEND GUARDRAILS (React)
## Collector Parfum

> **Status:** WAJIB. Sejajar 07. **Prinsip emas:** *KODE MENANG atas DOKUMEN.* Design SSOT = `/app/design_guidelines.md`.

---

## 0. ARSITEKTUR FE (struktur NYATA proyek ini)
```
src/
  App.js                      # routing + provider (CartProvider, WishlistProvider)
  index.js / index.css        # index.css = token/tema (paper/ink/champagne/brass + market-blue)
  services/apiClient.js       # axios instance + const API + setAuthToken (WAJIB dipakai)
  pages/                      # HalamanXxxPage (default export)
  components/layout|home|shared # komponen shared
  components/ui/               # shadcn (PAKAI INI, bukan elemen native)
  store/                       # CartContext, WishlistContext (localStorage → sinkron API nanti)
  lib/ | data/ | constants/testIds/
```
Stack: React + react-router + axios + framer-motion + embla + Tailwind + shadcn + lucide-react + sonner.

---

## 1. KONTRAK API DI FRONTEND (WAJIB)
1. **Semua call lewat `services/apiClient.js`** → `import axios, { API } from '.../services/apiClient'`. `API = ${REACT_APP_BACKEND_URL}/api`. JANGAN hardcode URL. JANGAN `fetch()` mentah.
2. **Respons BE = ARRAY/OBJEK telanjang.** Guard: `const rows = Array.isArray(res.data) ? res.data : []`.
3. **Auth:** token field `token` (prefiks `sess_`), dipasang global via `setAuthToken` → `Authorization: Bearer sess_...`. Jangan simpan rahasia di FE.
4. **Path literal** di segmen akhir (lolos verify_api_contract CHECK C).
5. Tiap field yang DIBACA FE harus ADA di respons BE.

---

## 2. UI / UX (ditegakkan `ux_audit.py`, target 0 ERROR)
- **Komponen shadcn** dari `components/ui`. **Hindari `<select>` native** → pakai `Select`. Hindari `<button>/<input>` telanjang untuk aksi utama.
- **Ikon HANYA `lucide-react`.** Emoji bukan ikon UI.
- **Uang**: `formatIDR` (lib/format.js) + kelas `tabular-nums`. Jangan format manual tersebar.
- **State data wajib**: tiap view yang fetch HARUS punya **loading** (Skeleton), **empty state** (ikon+pesan+aksi), **error state** (pesan+retry).
- **JANGAN background transparan dengan teks gelap.** Kontras AA. Responsif. Hover/focus/disabled.
- **Tema**: pakai token index.css (paper/ink/champagne/brass + market-blue). Jangan warna mentah (`#FF0000`).

---

## 3. TESTABILITY (WAJIB)
- **`data-testid` di SETIAP** elemen interaktif (button/input/link/select/dialog) **dan** info kritis (total, status, pesan error).
- Penamaan kebab-case berbasis peran & unik: `checkout-place-order-button`, `product-card`, `admin-product-save-button`.
- Jangan hapus/duplikat testid yang dipakai test (lihat `constants/testIds/`).

---

## 4. ROOT CAUSE TAXONOMY (FE)
| Kode | Gejala | Akar | Cegah |
|------|--------|------|-------|
| RC-F1 | Layar putih | import komponen/ikon hilang | cek import; esbuild |
| RC-F2 | `.map is not a function` | asumsi array | `Array.isArray()` guard |
| RC-F3 | 401/403 beruntun | token tak ter-set / role | `setAuthToken`; cek RBAC |
| RC-F4 | FE↔BE drift | path/field FE ≠ BE | `verify_api_contract.py`; path literal |
| RC-F5 | `body stream already read` | double-fetch StrictMode | async IIFE + cleanup |
| RC-F6 | URL salah di prod | hardcode host | selalu `${API}` dari env |
| RC-F8 | UI "datar" | abaikan token & state data | ikuti §2; loading/empty/error |

---

## 5. EXPORT, UKURAN FILE, ENV
- **Halaman/Page** → default export; **komponen** → named export.
- **Batas baris**: page/komponen `.js` ≤ **500**; hooks ≤ **300**; `.css` ≤ **400** (`validate_compliance.py`). `data/` & `lib/` (art SVG) dikecualikan.
- **ENV**: hanya `REACT_APP_BACKEND_URL` (+ `/api`). Jangan ubah `.env`. **Paket**: `yarn add` — JANGAN `npm`.

---

## 6. ALUR KERJA SEBELUM "DONE" (FE)
1. Build/esbuild bersih (0 error import).
2. `python scripts/ux_audit.py --strict` → 0 ERROR (WARN ke backlog).
3. `python scripts/verify_api_contract.py` → FE↔BE OK.
4. Screenshot via **preview URL** (bukan localhost).
5. Verifikasi visual: loading/empty/error tampil, angka rapi (`tabular-nums`), tanpa console error.
