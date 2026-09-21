# E4 — Customer Account: Wishlist, Address Book, Order History (IDOR-Safe)

> Priority: **P1**. Depends on: Foundation auth + E3 (orders for history). Unlocks: richer E7 CRM.
> Read first: `docs/09_THREAT_MODEL.md` (RC-E10 IDOR, RC-E15 session), `backend/dependencies.py`, `backend/permissions_config.py`.

## 1. Epic Summary

Give logged-in customers a real account surface: profile, address book, wishlist synced to server,
and order history/detail. The dominant risk here is **IDOR/authorization** — every read and write
must be strictly scoped to the authenticated owner. This Epic activates the ownership guardrails
(`fa_write_idor.py`, `fa_idor_matrix.py`) fully and proves session hardening (`fa_session.py`).

**Aha moment:** a customer logs in, sees their real orders, manages saved addresses, and their
wishlist persists across devices — while attempts to touch another user's data return 403/404.

## 2. Business Requirements

- **BR-1 Profile:** `GET /api/auth/me` (exists) + `PUT /api/account/profile` (name, phone) — email
  immutable in V1; never return `password_hash`.
- **BR-2 Address book:** full CRUD `/api/addresses`; fields per `docs/03`; one `is_default` per user
  (setting a new default unsets others); addresses are owner-scoped.
- **BR-3 Wishlist:** `GET /api/wishlist` + `POST /api/wishlist/toggle {product_id}`; server-side per
  user; merges with guest localStorage wishlist on login.
- **BR-4 Order history:** `GET /api/orders` (own) + `GET /api/orders/{code}` (own) — reuses E3
  endpoints; account page lists status, total, date, items; detail shows full snapshot + payment info.
- **BR-5 Address in checkout:** checkout can pick a saved address or enter a new one (snapshotted into
  the order per E3).
- **BR-6 Ownership everywhere:** no endpoint returns or mutates another user's resource; admin bypass
  only via explicit `require_role('admin')`.

## 3. Scope & Non-Goals

**In scope:** profile update, address CRUD, wishlist sync, order history/detail wiring, guest→user
merge on login, `AccountPage`/`WishlistPage` API wiring.

**Non-goals (deferred):** password reset/email verification (needs email integration — backlog),
loyalty/points, saved payment methods, social login. Review submission is E5 moderation-linked.

## 4. Data Model

Extend `docs/03_DATA_MODEL.md` (`addresses` `adr_`, `wishlists` `wsh_`):

```
addresses:
  id (adr_), user_id (owner), name, phone, street, district?, city, province,
  postal?, label, is_default (bool)      # exactly one default per user

wishlists:
  id (wsh_), user_id (owner, unique), product_ids[] (FK -> products.id, deduped)
```

All queries filter by `user_id` from the session (never from the request body). Register/confirm both
collections in `verify_contract.py`/`verify_schema.py`; wishlist FK checked by `verify_schema.py`.

## 5. API Contract

```
PUT    /api/account/profile {name?, phone?}     -> User (no password_hash)
GET    /api/addresses                           -> [Address,...]  # own only
POST   /api/addresses {..}                       -> Address
PUT    /api/addresses/{id} {..}                  -> Address        # 404 if not owner
DELETE /api/addresses/{id}                       -> {ok:true}      # 404 if not owner
GET    /api/wishlist                             -> [Product,...] | [product_id,...]
POST   /api/wishlist/toggle {product_id}         -> {product_ids:[...]}
```

All require `Authorization: Bearer sess_...`. Define specific routes before parameterized ones. Sync
to `docs/04_API_CONTRACT.md`.

## 6. State Machine & Invariants

No order lifecycle changes (reads only). Account invariants (add to `verify_data_integrity.py`):

- **INV-A1:** at most one `addresses.is_default == true` per `user_id`.
- **INV-A2:** every `addresses.user_id` and `wishlists.user_id` references an existing user (FK).
- **INV-A3:** `wishlists.product_ids[]` are unique and reference existing products (RC-E5).
- **Ownership invariant (runtime):** any authenticated request returns only rows where
  `user_id == session.user_id` (enforced/probed by `fa_write_idor.py`, `fa_idor_matrix.py`).

## 7. Execution Steps

1. **Docs first:** confirm `addresses`/`wishlists` fields in `docs/03`; add account endpoints to `docs/04`.
2. **Service:** `backend/services/account.py` — address CRUD (owner-scoped, single-default logic),
   wishlist toggle (dedupe, FK-check), profile update.
3. **Router:** `backend/routers/account.py` (profile, addresses, wishlist); all use
   `dependencies.get_current_user`; register in `server.py`. Reuse E3 order endpoints for history.
4. **Guest merge:** on login, FE posts local wishlist/cart to merge endpoints (idempotent union).
5. **Gate wiring:** add INV-A1..A3 to `verify_data_integrity.py`; activate `fa_write_idor.py`
   (A-vs-B: user B cannot PUT/DELETE user A's address), `fa_idor_matrix.py` (customer cannot hit
   admin routes); `fa_session.py` remains GREEN (forged/expired/inactive → 401).
6. **Frontend:** wire `AccountPage` (profile form, address book CRUD, order history list+detail) and
   `WishlistPage` to APIs; loading/empty/error states; optimistic wishlist toggle with rollback.
   Add unique `data-testid` on every form field, save/delete buttons, default toggle, order rows.
7. **Verify:** `bash scripts/gate.sh` GREEN; `run_forensics.sh` clean; `testing_agent_v3`.

## 8. Best Practices

- **Never trust `user_id` from the body.** Derive it from the session token only.
- **Owner-or-404:** for `{id}` resources, if the row isn't owned, return 404 (don't leak existence).
- **Single default address:** setting default is a transaction that unsets prior defaults.
- **Idempotent merges** for guest→user wishlist/cart (set union, no duplicates).
- **Session hygiene:** expired/inactive/forged tokens → 401 (handled by `dependencies.py`; proven by `fa_session.py`).

## 9. Bug Mitigation & Threat Mapping

| Threat | Risk in E4 | Mitigation |
|--------|-----------|------------|
| **RC-E10** IDOR / privilege | edit/read another user's address/order | owner-scoped queries; owner-or-404; `fa_write_idor.py`, `fa_idor_matrix.py`; `require_role` for admin |
| **RC-E15** session | expired/forged token accepted | `dependencies.py` expiry+status checks; `fa_session.py` |
| **RC-E5** FK dangling | wishlist points to deleted product | FK check in `verify_schema.py`; archive-not-delete products |
| **RC-E11** adversarial | bad address payloads | Pydantic validation; 4xx not 5xx; `fa_fuzz.py` |
| **RC-E13** dead menu | account tabs to missing routes | `check_nav_map.py`; SSOT nav (`docs/05`) |

## 10. Guardrail Wiring

- **Runtime/forensic (activate):** `forensic/fa_write_idor.py` (ownership A-vs-B),
  `forensic/fa_idor_matrix.py` (role×endpoint), `forensic/fa_session.py`, `forensic/fa_idor.py`.
- **Data:** INV-A1..A3 in `scripts/verify_data_integrity.py`; FK in `verify_schema.py`.
- **Static:** `scripts/guardrails/verify_rbac_guards.py` (every account route guarded).
- **Delivery:** address/wishlist/profile endpoints + `AccountPage`/`WishlistPage` as P1/P0 in manifest;
  update `BUG_REGISTRY.md` TR-09 (RC-E10) → PREVENTED for account routes.

## 11. Test Plan

**Backend (curl/pytest):** address CRUD owner-scoped; user B PUT/DELETE user A's address → 404;
setting default unsets others; wishlist toggle dedupes; profile update never leaks `password_hash`.

**Auth/session:** forged token → 401; expired → 401; inactive user → 401 (`fa_session.py`).

**Frontend (testing_agent_v3):** login → account shows real orders; add/edit/delete address; set
default; wishlist persists after reload; guest wishlist merges on login.

**Deviant-path (mandatory):** two defaults attempted, wishlist toggling a non-existent product,
accessing `/akun` while logged out (redirect), cross-user `{id}` access.

## 12. UI/UX Blueprint

> Full system: `docs/roadmap/UX_BLUEPRINT.md` §8 (Account).

**Screens & layout**
- `/akun` two-column desktop (left vertical nav: Profil / Pesanan / Alamat / Wishlist; right content);
  mobile top `Tabs` or accordion.
- **Profil:** locked email + editable name/phone (`Form`), Save with optimistic + toast.
- **Pesanan:** order rows (code, date, total, status `Badge` utility colors) → detail (item snapshots,
  timeline, payment status).
- **Alamat:** address cards; add/edit `Dialog` (`Form`), one default (distinct badge + "Jadikan default"),
  delete via `AlertDialog`.
- **Wishlist:** product-card grid; remove with optimistic + undo toast.

**Components (Shadcn):** `tabs`, `form`, `input`, `dialog`, `alert-dialog`, `badge`, `card`, `skeleton`, `sonner`.

**States:** loading skeletons; empty per tab ("Belum ada pesanan/alamat", "Wishlist kosong" + CTA);
error + retry; auth-gate (logged out → redirect + toast); session expiry → re-login toast (RC-E15).

**Micro-interactions:** default-address toggle → badge move animation; wishlist remove → fade + undo;
save → success toast.

**Responsive:** mobile stacked tabs; desktop persistent left nav; touch targets ≥44px.

**Accessibility:** form label associations + inline errors (`aria-describedby`); `AlertDialog` focus trap;
status badges have text (not color-only).

**Testids:** `account-profile-form`, `account-profile-save-button`, `order-history-row`,
`order-history-status-badge`, `order-detail-view`, `account-address-add-button`, `account-address-card`,
`account-address-default-toggle`, `account-address-delete-button`, `wishlist-grid`, `wishlist-item-remove-button`.

## 13. Definition of Done

- [ ] Address CRUD + wishlist + profile live, all owner-scoped; INV-A1..A3 enforced.
- [ ] `fa_write_idor.py`/`fa_idor_matrix.py`/`fa_session.py` GREEN (ownership + session proven).
- [ ] Guest→user wishlist/cart merge idempotent; order history reuses E3 endpoints.
- [ ] `AccountPage`/`WishlistPage` wired; unique `data-testid`; loading/empty/error states.
- [ ] `bash scripts/gate.sh` GREEN + `run_forensics.sh` clean + `testing_agent_v3` (happy + deviant).
- [ ] `BUG_REGISTRY.md` TR-09 → PREVENTED (account scope).
