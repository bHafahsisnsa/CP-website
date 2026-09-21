# E3 — Cart, Checkout & Orders (Atomic Stock, Anti-Oversell, State Machine)

> Priority: **P0**. Depends on: E1 (catalog) + E2 (pricing/voucher SSOT). Unlocks: E4 history, E6 payments.
> Read first: `docs/06_STATE_MACHINE.md`, `docs/09_THREAT_MODEL.md` (RC-E3/E4/E6/E7/E8/E9), `memory/INVARIANTS.md`.

## 1. Epic Summary

The write-path heart of the store. Build a Shopee-style checkout that creates orders with correct
pricing (E2 SSOT), snapshots line items (immune to later catalog edits), decrements variant stock
**atomically** (no oversell under concurrency), records voucher redemption, and manages the order
lifecycle through a single guarded transition function. This Epic activates the most dangerous
“green-but-broken” guardrails: state-machine (SM1..SM4), concurrency (anti-oversell), cross-entity.

**Aha moment:** placing an order decrements the exact variant stock, produces a correct total, and
cancelling restores stock — provable under parallel checkout without ever going negative.

## 2. Business Requirements

- **BR-1 Cart:** hybrid cart (localStorage for guests + optional server cart `carts` for logged-in);
  add/update/remove line items by `{product_id, volume_ml, quantity}`; a cart drawer mirrors state.
- **BR-2 Checkout summary:** totals come from E2 `compute_pricing`; shows subtotal, discount,
  shipping, COD fee, total — identical to what the order will store.
- **BR-3 Create order:** `POST /api/orders` validates stock, computes pricing server-side, snapshots
  items (price/name/image/concentration/volume at purchase time), decrements stock atomically,
  increments voucher `used_count` (guarded), writes `voucher_redemptions`, assigns `code = CP########`
  via `counters`.
- **BR-4 Anti-oversell:** stock decrement uses `$inc` filtered by `stock >= qty`; if it fails for any
  line item, the whole order is rejected/rolled back — stock never goes negative (INV-4).
- **BR-5 Order read (owner):** `GET /api/orders` (own orders) + `GET /api/orders/{code}` (own only).
- **BR-6 Lifecycle:** status transitions via one guarded function `transition_order` following
  `docs/06_STATE_MACHINE.md`; illegal transitions → 400; cancel restores stock.
- **BR-7 Payment status:** derived only via INV-5 (`paid==0→belum_bayar; 0<paid<total→dp; paid>=total→lunas`).
- **BR-8 Success page:** `/pesanan-sukses` shows order code, summary, payment instructions (E6 detail).

## 3. Scope & Non-Goals

**In scope:** cart model + endpoints (optional server cart), `POST /api/orders`, owner order reads,
admin status transition contract (UI in E5), atomic stock service, order lifecycle service, voucher
redemption accounting, order success page wiring.

**Non-goals (deferred):** payment gateway (manual only, E6), shipping rate API (static methods already
seeded), refunds automation, partial shipments, returns. Admin order dashboard UI is E5.

## 4. Data Model

Extend `docs/03_DATA_MODEL.md` (`carts` `crt_`, `orders` `ord_`, `counters`):

```
carts:
  id (crt_), user_id?, items[]: { product_id, volume_ml, quantity (int > 0) },
  voucher_code?, note, updated_at

orders:
  id (ord_), code (CP########, unique via counters.orders),
  user_id?, items[]: { product_id (FK), slug, name, image, concentration,
                       volume_ml, unit_price (int > 0), quantity (int > 0) },
  subtotal (int >= 0), discount (int >= 0), voucher_code?,
  shipping: { method_id, name, price (int >= 0), eta },
  payment: { group in {transfer, ewallet, cod}, method_id },
  cod_fee (int >= 0), total (int >= 0), paid_amount (int >= 0),
  address (snapshot), note,
  status in {pending, paid, packed, shipped, completed, cancelled},
  payment_status in {belum_bayar, dp, lunas},
  created_at, updated_at
```

**Bounds:** `quantity gt=0`, all money `ge=0` in `schemas.py`. `code` uniqueness via
`core_utils.next_sequence('orders')`.

## 5. API Contract

```
# customer (Bearer optional in V1 for guest checkout; owner-scoped reads require Bearer)
POST /api/orders {items, address, shipping_id, payment:{group,method_id}, voucher_code?, note?}
     -> Order        # 409 on stock conflict; 400 on invalid transition/inputs
GET  /api/orders            -> [Order,...]   # own orders only
GET  /api/orders/{code}     -> Order         # own only -> 404/403 otherwise (IDOR-safe)

# server cart (optional, logged-in)
GET/PUT /api/cart           -> Cart

# admin (contract; UI in E5)
PUT /api/admin/orders/{code}/status {status}  -> Order   # via transition_order only
```

Order response must contain everything the FE reads (items snapshot, all money fields, status).
Sync to `docs/04_API_CONTRACT.md`.

## 6. State Machine & Invariants

SSOT: `docs/06_STATE_MACHINE.md`. Implement `backend/services/orders.py::transition_order(order, to)`
with `LEGAL_TRANSITIONS` identical to the doc. Enforced by `scripts/verify_state_machine.py`:

- **SM1:** create order (stock ↓) → cancel → status=cancelled AND stock restored (RC-E6).
- **SM2:** `pending → shipped` (skipping paid) → 400 (RC-E7).
- **SM3:** pay/confirm a `cancelled` order → 400 (RC-E8).
- **SM4:** `complete` an unpaid order → `payment_status` stays honest (RC-E4, INV-5).

Invariants: INV-1/2/3 (pricing via E2), INV-4 (stock ≥ 0), INV-5 (payment derivation), INV-6 (status
enum), INV-7 (unique code), INV-8 (item FK), INV-10 (cod_fee only for cod). Cross-entity CE1..CE4:
used_count vs orders/redemptions, sum(paid) ≤ sum(total), stock sold == decrements.

## 7. Execution Steps

1. **Docs first:** finalize `orders`/`carts` fields in `docs/03`; endpoints in `docs/04`; confirm
   `docs/06` transitions; add INV updates to `memory/INVARIANTS.md`.
2. **Stock service:** `backend/services/stock.py::decrement(items)` — atomic per-variant `$inc` with
   filter `volumes.$.stock >= qty`; `restore(items)` for cancel; all-or-nothing across line items.
3. **Orders service:** `backend/services/orders.py` — `create_order(...)` (calls `compute_pricing` +
   `stock.decrement` + voucher redemption `$inc` guarded by `used_count < usage_limit`);
   `transition_order(order, to)` with `LEGAL_TRANSITIONS` + side-effects (cancel → `stock.restore`).
4. **Router:** `backend/routers/orders.py` (create/list/detail, owner-scoped) + admin status route;
   register in `server.py`. Define specific routes before parameterized ones.
5. **Concurrency proof:** ensure decrement is a single atomic update; write `verify_concurrency.py`
   scenario (N parallel checkouts on last unit) + `forensic/fa_race.py` active.
6. **Gate wiring:** activate `verify_state_machine.py` (SM1..SM4), `verify_concurrency.py`,
   `mutation_smoke.py` (write-path), `verify_cross_entity.py` (CE1..CE4), `fa_write_idor.py`
   (order ownership). Remove SKIPs — these must run.
7. **Frontend:** wire `CartContext`, `CartPage`, `CheckoutPage`, `OrderSuccessPage` to APIs; totals
   from server; on submit, POST order and route to success with the `code`. Handle 409 (stock) and
   400 (invalid) with clear UI. Add `data-testid` to qty steppers, checkout submit, totals, success code.
8. **Verify:** `bash scripts/gate.sh` GREEN (runtime ACTIVE); `run_forensics.sh` clean; `testing_agent_v3`.

## 8. Best Practices

- **Snapshot line items** at order time — later price/name edits must not mutate historical orders.
- **Compute totals server-side** with `compute_pricing`; ignore any client-sent totals.
- **Atomic decrement, all-or-nothing.** If any line fails the `stock >= qty` filter, roll back the
  ones already decremented (compensate) and return 409.
- **Single transition function.** Never set `order.status` directly anywhere else (anti split-brain RC-E7).
- **Cancel compensates stock** and voucher redemption; keep accounting consistent (CE1).
- **Owner-scoping everywhere:** order reads filter by `user_id`; `{code}` detail returns 404/403 for
  non-owners (anti write/read IDOR RC-E10).

## 9. Bug Mitigation & Threat Mapping

| Threat | Risk in E3 | Mitigation |
|--------|-----------|------------|
| **RC-E3** oversell (TOCTOU) | parallel checkout on last unit | atomic `$inc` filtered `stock>=qty`; `verify_concurrency.py`, `fa_race.py`; INV-4 |
| **RC-E6** cancel keeps stock | cancel doesn't restore | `transition_order` cancel → `stock.restore`; SM1 |
| **RC-E7** illegal transition | pending→shipped; two update paths | single guarded `transition_order` + `LEGAL_TRANSITIONS`; SM2 |
| **RC-E8** action on terminal | pay a cancelled order | terminal guard; SM3 |
| **RC-E4** payment drift | complete marked lunas without paid | INV-5 derivation only; SM4 |
| **RC-E1** total drift | client-sent total trusted | server recompute via `compute_pricing`; INV-1/2 |
| **RC-E9** cross-entity | used_count/paid/stock mismatch | `verify_cross_entity.py` CE1..CE4 |
| **RC-E10** IDOR | read/modify others' orders | owner-scoped queries; `fa_write_idor.py`, `fa_idor.py` |
| **RC-E11** adversarial | bad qty/ids | Pydantic bounds; 4xx not 5xx; `fa_fuzz.py` |

## 10. Guardrail Wiring

- **Runtime (activate, no SKIP):** `scripts/verify_state_machine.py` (SM1..SM4),
  `scripts/verify_concurrency.py`, `scripts/mutation_smoke.py`, `scripts/verify_cross_entity.py`.
- **Forensic:** `forensic/fa_race.py`, `forensic/fa_write_idor.py`, `forensic/fa_idor.py`,
  `forensic/fa_fuzz.py`, `forensic/fa_5xx.py`.
- **Static:** `scripts/guardrails/verify_stock_locks.py` (atomic decrement present),
  `scripts/guardrails/verify_numeric_bounds.py`.
- **Data:** register `orders`/`carts`/`counters` in contract/schema/integrity; add order INVs.
- **Delivery:** `POST /api/orders`, `/api/orders/{code}`, Checkout/Success pages as P0 in manifest;
  update `BUG_REGISTRY.md` TR-01..TR-08 WATCH → PREVENTED.

## 11. Test Plan

**Backend (curl/pytest):** happy order (totals match `compute_pricing`, stock ↓, code assigned,
redemption ↑); cancel restores stock; illegal transition → 400; pay cancelled → 400; complete unpaid
→ payment_status honest.

**Concurrency:** `verify_concurrency.py` — N parallel checkouts on a 1-stock variant → exactly one
succeeds, stock ends at 0 (never negative); `fa_race.py` GREEN.

**IDOR:** user B cannot GET/modify user A's order (`fa_write_idor.py`).

**Frontend (testing_agent_v3):** Cart → Checkout → place order → Success shows code; 409 stock error
surfaces cleanly; totals identical to summary.

**Deviant-path (mandatory):** empty cart, qty > stock, expired voucher at submit, guest vs logged-in
checkout, double-submit (idempotency guard).

## 12. UI/UX Blueprint

> Full system: `docs/roadmap/UX_BLUEPRINT.md` §7.4–7.6 (Cart, Checkout, Success). Visual SSOT:
> `design_guidelines.md` (`checkout_shopee_style`).

**Screens & layout**
- **Cart Drawer** (`Sheet` right) for quick access; **Cart page** for qty stepper, remove, voucher, note.
- **Checkout (Shopee-style):** stacked `Card` sections — Alamat (`Dialog` picker) → Kurir (`RadioGroup`)
  → Pembayaran (`Tabs`: Transfer/E-Wallet/COD) → Voucher → Catatan (`Textarea`) → **Ringkasan** (sticky
  `Card` desktop). Summary rows (Subtotal/Diskon/Ongkir/COD/Total) from server `compute_pricing`; CTA
  market-blue "Buat Pesanan".
- **Order Success:** centered card, left-aligned content; order `code`, summary, payment instructions, CTAs.

**Components (Shadcn):** `sheet`, `card`, `tabs`, `radio-group`, `input`, `textarea`, `dialog`,
`separator`, `button`, `sonner`, `skeleton`, `alert`.

**States (critical):** empty cart ("Keranjang kosong" + Belanja CTA); qty > stock inline ("Stok tersisa
N"); placing order → CTA disabled + "Memproses…" (anti double-submit); **409 stock conflict** → banner +
highlight affected item; **400** → inline field errors; voucher validating/invalid inline.

**Micro-interactions:** qty stepper press scale; summary total updates with subtle count-up (respect
reduced-motion); toast "Ditambahkan ke keranjang".

**Responsive:** mobile single-column, summary at bottom + sticky place-order bar; desktop content +
sticky summary.

**Accessibility:** payment `Tabs` keyboard-navigable; RadioGroup roving focus; totals in an `aria-live`
region so screen readers hear updates; error summary on submit.

**Testids:** `cart-page`, `cart-item`, `cart-item-qty-input`, `cart-checkout-button`, `cart-empty`,
`checkout-address-card`, `checkout-shipping-option`, `checkout-payment-tab`, `checkout-total-amount`,
`checkout-place-order-button`, `checkout-stock-error`, `order-success-code`.

## 13. Definition of Done

- [ ] `services/pricing.py` (E2) used by checkout; totals server-authoritative.
- [ ] Atomic stock decrement + restore; INV-4 holds under `verify_concurrency.py` + `fa_race.py`.
- [ ] `transition_order` is the ONLY status mutator; SM1..SM4 GREEN (no SKIP).
- [ ] Owner-scoped order reads; `fa_write_idor.py`/`fa_idor.py` GREEN.
- [ ] CE1..CE4 GREEN with real orders; voucher `used_count` == orders == redemptions.
- [ ] Cart/Checkout/Success wired; 409/400 handled; unique `data-testid` on flow controls.
- [ ] `bash scripts/gate.sh` GREEN (runtime ACTIVE) + `run_forensics.sh` clean + `testing_agent_v3` (happy + deviant).
- [ ] `BUG_REGISTRY.md` TR-01..TR-08 → PREVENTED.
