# E5 — Admin Backoffice CMS: Media Gallery, RBAC, Live Preview

> Priority: **P1**. Depends on: E1–E3 (reuse services), E4 (auth patterns). Unlocks: E6 payment verification UI.
> Read first: `docs/05_NAVIGATION_MAP.md` (admin IA), `docs/09_THREAT_MODEL.md` (RC-E10, RC-E16), `backend/permissions_config.py`.

## 1. Epic Summary

Build the admin backoffice (`/admin/*`) so operators can run the store: dashboard, catalog CRUD
(products with multi-variant + media, categories, reviews moderation), voucher/campaign management,
order processing (status transitions via E3's `transition_order`), shipping/payment config, and store
settings. It includes a **media gallery** (image/video references + optional object-storage uploads)
and an **accurate live preview** so admins see exactly how a product/page renders on the storefront.
RBAC is central: only `admin` reaches these routes; all write-paths reuse existing services (no second
source of truth), so guardrails already covering checkout stay authoritative.

**Aha moment:** an admin creates a product with 3 volumes + a gallery, sees a faithful live preview,
saves, and it appears on the storefront instantly — with stock/pricing rules already enforced.

## 2. Business Requirements

- **BR-1 Dashboard:** `GET /api/admin/dashboard` — revenue, orders-by-status, active products, low-stock,
  recent orders; read aggregates only.
- **BR-2 Product CRUD:** create/update/archive products incl. `volumes[]` (ml/price/stock), media
  gallery, notes, description/ingredients, SEO, badges. Archive (soft-delete) instead of hard-delete
  when referenced by orders (RC-E5).
- **BR-3 Category CRUD:** manage categories (slug/name/desc/image/seo/active).
- **BR-4 Voucher/Campaign CRUD:** manage vouchers/campaigns from E2 (type/value/min-spend/window/
  scope/limits); redemption counters are read-only (system-owned).
- **BR-5 Review moderation:** list pending/published/hidden; set status; ratings recompute product aggregate.
- **BR-6 Order processing:** list/filter orders by status; change status ONLY via `transition_order`
  (illegal → 400); record payment verification (hook for E6).
- **BR-7 Config:** shipping methods & rates, payment methods & fees, store settings (singleton).
- **BR-8 Media gallery:** upload/select images (and video references); reorder; set primary; used by
  product/category editors. Uploads go to object storage (integration) — see §3 for V1 fallback.
- **BR-9 Live preview:** editor renders a storefront-accurate preview (same components/tokens) before save.
- **BR-10 RBAC:** all `/api/admin/*` require role `admin`; audit every mutation (`audit_logs`).

## 3. Scope & Non-Goals

**In scope:** admin routers reusing catalog/orders/pricing/voucher services; media library collection;
RBAC + audit; `/admin/*` React surface with dashboard, CRUD editors, order processing, config, live
preview.

**Non-goals / integration gate:** **real object-storage uploads require the integration agent** (do
not implement blind). V1 fallback = store media **URLs/references** (as the storefront already uses
generated art) and add true uploads once the object-storage playbook + credentials are provided.
Multi-admin roles/granular permissions beyond `admin` are backlog (structure allows extension via
`permissions_config.py`).

## 4. Data Model

Reuses `products`, `categories`, `vouchers`, `orders`, `reviews`, `shipping_methods`,
`payment_methods`, `settings`, `audit_logs`. New:

```
media_assets (new, med_):
  id (med_), kind in {image, video}, url, alt?, width?, height?,
  bytes?, owner_admin_id, created_at        # library of reusable media

audit_logs (existing, aud_):
  id (aud_), actor_id, action, entity, entity_id, meta, created_at   # write every admin mutation
```

Product/category `images[]`/`video_url`/`image` may reference `media_assets.url`. Register
`media_assets` in `verify_contract.py`/`verify_schema.py`. Numeric fields bounded in `schemas.py`.

## 5. API Contract

```
GET    /api/admin/dashboard                         -> {revenue, orders_by_status, active_products, low_stock, recent}
POST   /api/admin/products                          -> Product
PUT    /api/admin/products/{id}                      -> Product
DELETE /api/admin/products/{id}                      -> {archived:true}   # soft-delete
POST   /PUT /DELETE /api/admin/categories[/{id}]     -> Category
POST   /PUT /DELETE /api/admin/vouchers[/{id}]       -> Voucher
GET    /api/admin/orders?status                      -> [Order,...]
PUT    /api/admin/orders/{code}/status {status}      -> Order          # transition_order only
PUT    /api/admin/reviews/{id}/status {status}       -> Review
GET/PUT /api/admin/shipping-methods[/{id}]           -> [ShippingMethod]
GET/PUT /api/admin/payment-methods[/{id}]            -> [PaymentMethod]
GET/PUT /api/admin/settings                          -> Settings
GET    /api/admin/media                              -> [MediaAsset,...]
POST   /api/admin/media {kind,url,alt?}              -> MediaAsset      # + upload variant post-integration
```

All require `Bearer` + role `admin`. Sync to `docs/04_API_CONTRACT.md`.

## 6. State Machine & Invariants

- Order status changes go through E3 `transition_order` (SM1..SM4 still enforced by
  `verify_state_machine.py`) — admin is just another caller, not a second code path (anti RC-E7).
- **INV-M1:** every admin mutation writes an `audit_logs` entry (actor, action, entity, id).
- **INV-M2:** archiving a product referenced by any order does NOT hard-delete it (FK safety, RC-E5).
- **INV-M3:** editing product price/name does NOT retroactively change existing order snapshots (E3).
- Pricing/voucher edits keep INV-1/2/3/9 valid; low-stock threshold from `settings`.

## 7. Execution Steps

1. **Docs first:** add admin endpoints to `docs/04`; add `media_assets` to `docs/03`; confirm admin IA
   in `docs/05_NAVIGATION_MAP.md` (`/admin/*`, depth ≤ 2).
2. **RBAC:** confirm `permissions_config.py` sections; every admin route uses
   `dependencies.require_role('admin')`; wrap mutations with `services/audit.py`.
3. **Admin services/routers:** thin admin routers that call existing `services/catalog.py`,
   `services/orders.py` (`transition_order`), `services/vouchers.py`, `services/pricing.py` — NO new
   business math. `backend/routers/admin/*.py`; register under `/api/admin` in `server.py`.
4. **Media:** `media_assets` CRUD (URL/reference in V1). **If uploads requested → call integration
   agent for object storage first**, then add the upload endpoint per playbook (do not guess SDK).
5. **Gate wiring:** `verify_rbac_guards.py` must show ALL `/api/admin/*` guarded; `fa_idor_matrix.py`
   proves a customer token is rejected on every admin route; `verify_state_machine.py` stays ACTIVE;
   `verify_delivery.py` D2 ensures admin endpoints have UI (no orphan).
6. **Frontend `/admin/*`:** admin shell (nav per `docs/05`), dashboard, product editor (variants +
   media gallery + live preview), category/voucher editors, order processing (status dropdown →
   guarded transition), review moderation, config, settings. Use Shadcn components + design tokens;
   unique `data-testid` on every control. Live preview reuses storefront components.
7. **Verify:** `bash scripts/gate.sh` GREEN; `run_forensics.sh` clean; `testing_agent_v3` (admin CRUD + order processing).

## 8. Best Practices

- **Reuse services, never re-implement math** (single SSOT keeps guardrails authoritative).
- **Admin is a caller, not a bypass** — status changes still go through `transition_order`.
- **Soft-delete/archive** anything referenced by orders; keep historical snapshots immutable.
- **Audit everything** (`audit_logs`) — who changed what, when (INV-M1).
- **Live preview = same components/tokens** as storefront to avoid “looks different after publish” drift.
- **Media as references first**; add real uploads only with the object-storage integration playbook.
- **RBAC on every route** — default-deny; a missing guard is a gate failure (`verify_rbac_guards.py`).

## 9. Bug Mitigation & Threat Mapping

| Threat | Risk in E5 | Mitigation |
|--------|-----------|------------|
| **RC-E10** RBAC/IDOR | customer reaches admin route; privilege escalation | `require_role('admin')` on all; `verify_rbac_guards.py`; `fa_idor_matrix.py` |
| **RC-E16** under-deliver/orphan | admin endpoint with no UI, or UI with no endpoint | `verify_delivery.py` D1/D2; manifest P0 |
| **RC-E5** FK dangling | hard-deleting a referenced product | archive/soft-delete; INV-M2; `verify_schema.py` |
| **RC-E7** split-brain status | admin sets status directly | only via `transition_order`; `verify_state_machine.py` |
| **RC-E11** adversarial | huge/markup fields in editors | Pydantic validation + escape; `fa_fuzz.py`, `verify_adversarial_5xx.py` |
| **RC-E1** price drift | editor recomputes totals | pricing stays in `services/pricing.py` only |

## 10. Guardrail Wiring

- **Static:** `scripts/guardrails/verify_rbac_guards.py` (all `/api/admin/*` guarded + matrix),
  `verify_numeric_bounds.py`.
- **Runtime/forensic:** `forensic/fa_idor_matrix.py` (role×endpoint), `forensic/fa_write_idor.py`,
  `scripts/verify_state_machine.py`, `scripts/mutation_smoke.py` (admin write-path), `fa_fuzz.py`.
- **Delivery:** `verify_delivery.py` D1 (admin endpoints exist) + D2 (consumed by `/admin/*` UI);
  add admin endpoints + `AdminDashboardPage` etc. to `memory/DELIVERY_MANIFEST.md`.
- **Audit:** `services/audit.py` writes `audit_logs`; INV-M1 checked in `verify_data_integrity.py`.
- **Integration:** object-storage uploads → `integration_playbook_expert` first; then wire.

## 11. Test Plan

**Backend (curl/pytest):** admin CRUD products/categories/vouchers; archive keeps order FKs valid;
order status via `transition_order` (illegal → 400); review moderation recomputes aggregate; every
mutation writes `audit_logs`.

**RBAC:** customer token on every `/api/admin/*` → 401/403 (`fa_idor_matrix.py`); no unguarded admin
route (`verify_rbac_guards.py`).

**Frontend (testing_agent_v3):** admin creates product w/ variants + gallery + live preview → appears
on storefront; edits category; creates voucher; processes an order end-to-end; moderates a review.

**Deviant-path (mandatory):** archive a product in an existing order (snapshot unchanged), illegal
status jump from admin UI, oversized image alt / markup injection, customer trying `/admin`.

## 12. UI/UX Blueprint

> Full system: `docs/roadmap/UX_BLUEPRINT.md` §11 (Admin). Utilitarian but on-brand: same tokens/fonts,
> minimal marketing motion, denser info. Depth ≤ 2 (`docs/05_NAVIGATION_MAP.md`).

**Shell & navigation**
- Fixed left sidebar (collapsible tablet, `Sheet` on mobile) + top bar (title, breadcrumb, admin menu,
  theme toggle). Groups: Ringkasan · Katalog (Produk/Kategori/Ulasan) · Penjualan (Pesanan/Voucher/
  Pembayaran) · Pengaturan (Kurir/Metode Bayar/Toko/Pengguna). Active item = champagne accent + weight.
- **RBAC states:** non-admin → redirect + toast "Akses ditolak".

**Key screens**
- **Dashboard:** metric cards (revenue/orders-by-status/active products/low-stock, Azeret Mono numbers),
  recent orders `Table`, low-stock list.
- **Data tables** (products/orders/vouchers/reviews): `Table` + toolbar (search, status `Select`, "Tambah"),
  pagination, row actions (`DropdownMenu`).
- **Product Editor (two-pane):** left form (Info / **Variants** repeatable ml·price·stock·sku with numeric
  bounds / Notes / **Media Gallery** add-reorder-set-primary / Description·Ingredients / **SEO** with char
  counters + snippet preview / Status); right = **live preview** rendering the actual storefront PDP
  components (same tokens → no publish drift).
- **Order processing:** detail + status change via **guarded** transition (illegal options disabled;
  illegal attempt → toast 400); cancel via `AlertDialog` (warns stock restore).
- **Config/Settings:** shipping/payment tables + store settings `Form`.

**Components (Shadcn):** `table`, `card`, `form`, `input`, `select`, `textarea`, `tabs`, `accordion`,
`dialog`, `alert-dialog`, `dropdown-menu`, `badge`, `switch`, `skeleton`, `sonner`, `breadcrumb`, `sheet`.

**States:** skeleton rows/cards; empty ("Belum ada …" + Tambah CTA); error + retry; save validation
summary; archive confirm.

**Accessibility:** tables have header scope; editors keyboard-complete; live preview announced; forms
labelled with inline errors; theme toggle persists.

**Testids:** `admin-shell`, `admin-sidebar`, `admin-nav-item`, `admin-breadcrumb`, `admin-dashboard`,
`admin-metric-revenue`, `admin-products-table`, `admin-products-row`, `admin-products-add-button`,
`admin-product-editor`, `admin-product-save-button`, `admin-variant-row`, `admin-variant-add-button`,
`admin-media-add-button`, `admin-media-set-primary`, `admin-seo-title-input`, `admin-product-preview-pane`,
`admin-orders-status-select`, `admin-order-cancel-button`, `admin-settings-save-button`.

## 13. Definition of Done

- [ ] All `/api/admin/*` guarded by `require_role('admin')`; `verify_rbac_guards.py` + `fa_idor_matrix.py` GREEN.
- [ ] Admin routers reuse existing services (no duplicated pricing/transition logic).
- [ ] Media library (references V1); uploads only via integration playbook if requested.
- [ ] `/admin/*` UI: dashboard, catalog/voucher CRUD, order processing, review moderation, config, live preview; unique `data-testid`.
- [ ] Every mutation audited (INV-M1); archive-not-delete (INV-M2); snapshots immutable (INV-M3).
- [ ] No orphan endpoints (`verify_delivery.py` D2); manifest P0 satisfied.
- [ ] `bash scripts/gate.sh` GREEN + `run_forensics.sh` clean + `testing_agent_v3`.
- [ ] `BUG_REGISTRY.md` TR-09/TR-14 → PREVENTED (admin scope).
