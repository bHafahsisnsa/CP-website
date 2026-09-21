# 02 — ARCHITECTURE
## Collector Parfum

## 1. Lapisan
```
React (pages tipis + shared components)
   → services/apiClient.js (axios + REACT_APP_BACKEND_URL + /api)
   → FastAPI routers (THIN: I/O + validasi)
   → services/ (logika bisnis)
   → Motor / MongoDB (koleksi kanonik)
```
- **Router TIDAK berisi logika bisnis** — pindah ke `services/`.
- **Stateless API**: state di DB/`sessions`, bukan memori proses.
- **Idempotent seed & migration**: aman dijalankan berulang.

## 2. Folder backend
```
backend/
  server.py            # app factory + registry router (ROUTERS[]) + index startup
  db.py                # Motor client (MONGO_URL, DB_NAME dari env)
  core_utils.py        # safe_doc, hash_password, money, new_id, new_token, next_sequence
  dependencies.py      # get_current_user / get_optional_user / require_role / require_section
  permissions_config.py# SSOT RBAC (admin, customer)
  schemas.py           # Pydantic kontrak data
  routers/             # health, auth (+ products/orders/... di fase berikutnya)
  services/            # audit (+ pricing/orders/... di fase berikutnya)
```

## 3. Folder frontend
```
frontend/src/
  App.js               # routing + provider (Cart, Wishlist)
  services/apiClient.js# axios instance + const API + setAuthToken
  pages/               # HalamanXxxPage (default export)
  components/          # shared (layout/, home/, shared/) + ui/ (shadcn)
  store/               # CartContext, WishlistContext (localStorage; nanti sinkron API)
  lib/                 # format.js, bottleArt.js, moodArt.js
  data/                # products.js (dummy — akan diganti fetch API)
  constants/testIds/   # katalog data-testid
```

## 4. Konvensi
- Semua endpoint di bawah **`/api`** (Kubernetes ingress).
- Respons list = **ARRAY telanjang**; detail = **OBJEK telanjang** (tanpa envelope).
- Token field = **`token`** (prefiks `sess_`), header `Authorization: Bearer sess_...`.
- Uang = **integer rupiah** (`core_utils.money`).
- `.env` (`MONGO_URL`, `DB_NAME`, `REACT_APP_BACKEND_URL`) **tidak diubah**.

## 5. Adapter/ekstensi masa depan
- Payment gateway & ongkir real-time dirancang sebagai adapter (ganti implementasi tanpa rewrite UI).
- `services/pricing` akan menjadi SSOT perhitungan (subtotal/diskon/ongkir/total) dipakai checkout & verifier.
