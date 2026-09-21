# E2 — Centralized Pricing SSOT + Shopee-like Voucher Campaigns

> Priority: **P0**. Depends on: E1 (products/prices). Unlocks: E3 (checkout uses pricing SSOT).
> Read first: `memory/INVARIANTS.md` (INV-1..INV-3, INV-9, INV-10), `docs/09_THREAT_MODEL.md` (RC-E1, RC-E2, RC-E9).

## 1. Epic Summary

Create ONE authoritative pricing engine (`backend/services/pricing.py`) that computes subtotal,
discount, shipping, COD fee and total — used by BOTH checkout (E3) and the integrity verifier
(`verify_data_integrity.py`). Then build a Shopee-like voucher system: admin-created campaigns with
types (percent / flat / free-shipping), min-spend, usage limits (global + per-user), validity window,
and a public validation endpoint. The whole point is to eliminate “two places compute the discount”
drift (RC-E1/RC-E2) that plagued the mature repos.

**Aha moment:** entering a valid voucher on the cart instantly shows the exact discount the backend
will also apply at checkout — numbers always agree because there is one formula.

## 2. Business Requirements

- **BR-1 Pricing SSOT:** a pure function `compute_pricing(items, voucher?, shipping?, payment_group?)`
  returns `{subtotal, discount, shipping_price, cod_fee, total}` with `total = max(0, subtotal -
  discount + shipping_price + cod_fee)`.
- **BR-2 Voucher types:** `percent` (1..100, capped so discount ≤ subtotal), `flat` (≤ subtotal),
  `free_shipping` (discount = shipping_price, only if min-spend met).
- **BR-3 Eligibility:** `min_spend` enforced; `active` flag; validity window `starts_at`/`ends_at`;
  optional category/product scoping (campaign applies only to eligible line items).
- **BR-4 Usage limits:** global `usage_limit` (0 = unlimited) and optional `per_user_limit`; enforced
  atomically at redemption (E3), validated defensively on validate.
- **BR-5 Public validation:** `POST /api/vouchers/validate {code, subtotal}` →
  `{valid, code, type, value, discount, label, reason?}`. Invalid/expired/over-limit → `valid=false`
  with a human reason (never 5xx).
- **BR-6 Campaign concept:** a voucher may belong to a campaign (banner label, theme). Distribution
  (auto-claim vs code entry) is a display concern; redemption accounting is server-side truth.
- **BR-7 Display SSOT:** cart/checkout show discount from the API response, never recompute locally.

## 3. Scope & Non-Goals

**In scope:** `services/pricing.py`, voucher schema extensions (window, scope, per-user limit),
`POST /api/vouchers/validate`, admin voucher CRUD contract (implemented in E5, contract defined here),
and the invariants that keep discount math honest.

**Non-goals (deferred):** actual redemption `used_count` increment happens at order creation (E3);
tiered/stackable multi-voucher, points/loyalty, and gamified claim mechanics are future backlog.
Shipping price selection is defined here but the shipping method catalog is seeded already.

## 4. Data Model

Extend `vouchers` (`vcr_`) in `docs/03_DATA_MODEL.md` (additive-only):

```
vouchers:
  id (vcr_), code (unique, uppercase), type in {percent, flat, free_shipping},
  value (int > 0; percent 1..100; flat = rupiah; free_shipping ignored),
  label, min_spend (int >= 0), usage_limit (int >= 0; 0 = unlimited),
  per_user_limit (int >= 0; 0 = unlimited), used_count (int >= 0),
  scope: { category? (slug), product_ids? [] },      # null/empty = whole cart
  starts_at? (ISO), ends_at? (ISO), campaign? { id, name, theme }, active (bool)

voucher_redemptions (new, vrd_):   # for per-user accounting + audit (E3 writes)
  id (vrd_), voucher_code, user_id?, order_code, discount (int), created_at
```

**Bounds:** `value gt=0`, `min_spend ge=0`, `usage_limit ge=0`, `per_user_limit ge=0` in `schemas.py`
(anti RC-E12). Register `voucher_redemptions` in `verify_contract.py` + `verify_schema.py`.

## 5. API Contract

```
POST /api/vouchers/validate  {code, subtotal, user_id?, items?}
     -> { valid: bool, code, type, value, discount: int, label, reason?: str }
```

Admin CRUD (contract only; built in E5): `POST/PUT/DELETE /api/admin/vouchers[/{id}]`. Discount in the
response MUST equal what E3 checkout computes for the same inputs (single formula). Sync to
`docs/04_API_CONTRACT.md`.

## 6. State Machine & Invariants

No lifecycle in E2 itself, but it locks the pricing invariants enforced by `verify_data_integrity.py`
and `verify_cross_entity.py`:

- **INV-1:** `order.subtotal == Σ(unit_price * quantity)`.
- **INV-2:** `order.total == subtotal - discount + shipping.price + cod_fee` and `total >= 0`.
- **INV-3:** discount consistent with voucher: percent → `round(subtotal*value/100)` capped to subtotal;
  flat → `min(value, subtotal)`; free_shipping → `min(shipping_price, ...)`.
- **INV-9:** `voucher.type in {percent,flat,free_shipping}` and `value > 0` (percent 1..100).
- **INV-10:** `cod_fee > 0` only when `payment.group == 'cod'`.
- **CE1 (cross-entity):** `voucher.used_count == count(orders using that voucher)` and
  `== count(voucher_redemptions)` — no phantom redemptions.

## 7. Execution Steps

1. **Docs first:** extend voucher fields + add `voucher_redemptions` in `docs/03`; add validate
   endpoint + admin voucher contract in `docs/04`; confirm formulas in `memory/INVARIANTS.md`.
2. **Pricing SSOT:** implement `backend/services/pricing.py::compute_pricing(...)` — pure, no DB writes,
   integer math, returns the 5-tuple dict. This is the ONLY place discount/total is computed.
3. **Voucher service:** `backend/services/vouchers.py` — `evaluate_voucher(code, subtotal, user_id?,
   items?)` returns eligibility + discount using `compute_pricing`; checks window, min-spend,
   scope, active, and (defensively) usage/per-user counts.
4. **Router:** `backend/routers/vouchers.py` → `POST /api/vouchers/validate`; register in `server.py`.
5. **Schemas:** add bounds; add `VoucherValidateIn/Out`.
6. **Gate wiring:** make `verify_data_integrity.py` import and call `services.pricing.compute_pricing`
   as the reference (so checkout and verifier can never diverge); add CE1 to `verify_cross_entity.py`;
   register redemptions collection; add validate to `health_check.py`.
7. **Frontend:** cart/checkout call `POST /api/vouchers/validate`; render discount from the response;
   show `reason` on invalid; never compute discount client-side. Add `data-testid` to voucher input,
   apply button, discount line.
8. **Verify:** `bash scripts/gate.sh` GREEN; unit-test `compute_pricing` edge cases.

## 8. Best Practices

- **One formula, two callers.** Checkout (E3) and `verify_data_integrity.py` both call `compute_pricing`.
- Cap discount at subtotal; total floored at 0 (no negative totals — RC-E1/E12).
- Uppercase/normalize codes; treat codes as opaque, rate-limit brute force at E7/E8.
- Redemption counting is **atomic at order creation** (E3, `$inc` guarded by `used_count < usage_limit`),
  not at validate-time (validate is advisory and race-free by design).
- Keep pricing pure (no I/O) so it's trivially unit-testable and mutation-provable.

## 9. Bug Mitigation & Threat Mapping

| Threat | Risk in E2 | Mitigation |
|--------|-----------|------------|
| **RC-E1** total drift | UI computes discount differently than BE | single `compute_pricing`; INV-1/2 call it as reference |
| **RC-E2** voucher miscalc/abuse | discount>subtotal; min_spend skipped; over-limit | cap logic; window/min-spend checks; atomic redemption in E3; INV-9 |
| **RC-E9** cross-entity | `used_count` != real redemptions | `verify_cross_entity.py` CE1 (used_count == orders == redemptions) |
| **RC-E12** negative value | negative `value`/`min_spend` | `ge/gt` bounds in `schemas.py`; `verify_numeric_bounds.py` |
| **RC-E14** money float | percent rounding drift | integer `round(subtotal*value/100)`; unit tests on boundaries |
| **RC-E11** adversarial validate | bad `code`/`subtotal` types | Pydantic validation; validate never 5xx, returns `valid=false` |

## 10. Guardrail Wiring

- **Static/data:** register `voucher_redemptions` in `verify_contract.py`/`verify_schema.py`;
  numeric bounds via `guardrails/verify_numeric_bounds.py`.
- **Integrity:** `verify_data_integrity.py` imports `services.pricing.compute_pricing` (reference impl).
- **Cross-entity:** `verify_cross_entity.py` CE1 (used_count == #orders == #redemptions).
- **Runtime:** `health_check.py` asserts `/api/vouchers/validate` behavior; `verify_adversarial_5xx.py`
  fuzzes the payload.
- **Delivery:** add validate endpoint (P0) to `memory/DELIVERY_MANIFEST.md`; update `BUG_REGISTRY.md`
  TR-07 (RC-E2) toward PREVENTED once redemption is wired (E3).

## 11. Test Plan

**Unit (`compute_pricing`):** percent capped at subtotal; flat > subtotal → clamped; free_shipping
with/without min-spend; COD fee only when group=cod; total never negative; rounding at 33%/varied subtotals.

**API (curl):** valid code → correct discount; below min-spend → `valid=false, reason`; expired window
→ invalid; unknown code → invalid (not 5xx); adversarial types → 422.

**Cross-entity (after E3):** create orders using a voucher; `verify_cross_entity.py` CE1 stays GREEN.

**Deviant-path (mandatory):** discount equal to subtotal (total shipping-only), voucher exactly at
usage_limit, per-user limit exceeded, free_shipping with zero shipping.

## 12. UI/UX Blueprint

> Full system: `docs/roadmap/UX_BLUEPRINT.md` §9 (Voucher Center) + §7.5 (checkout voucher).

**Screens & layout**
- **Voucher Center** (surfaced in cart/checkout and optional `/voucher`): grid of voucher cards —
  label, discount value (percent/flat/free-ship), min-spend note, validity window, campaign accent
  (champagne), countdown chip (Azeret Mono) for expiring soon. CTA "Pakai" / "Klaim".
- **Checkout voucher field:** `Input` + Apply button → inline validating state → success (discount line
  appears in summary + voucher chip with remove) or error (reason under input). Discount shown = API only.

**Components (Shadcn):** `card`, `input`, `button`, `badge`, `tooltip`, `skeleton`, `sonner`.

**States:** ineligible voucher greyed with reason ("Min. belanja Rp X"); validating (spinner in Apply);
invalid/expired (reason text); loading skeleton list; empty ("Belum ada voucher"); error + retry.

**Micro-interactions:** apply success → summary discount row animates in (opacity/height); remove chip →
fade; toast "Voucher diterapkan".

**Responsive:** voucher cards 1-col mobile / 2-col desktop; checkout field full-width on mobile.

**Accessibility:** voucher code input labelled; error via `aria-describedby`; disabled cards not focusable
but reason announced; contrast on accent chips.

**Testids:** `voucher-center-list`, `voucher-card`, `voucher-card-apply-button`,
`voucher-card-ineligible-reason`, `checkout-voucher-input`, `checkout-voucher-apply-button`,
`checkout-voucher-remove-button`, `checkout-total-amount`.

## 13. Definition of Done

- [ ] `services/pricing.py` is the single pricing SSOT; `verify_data_integrity.py` calls it as reference.
- [ ] Voucher schema extended (window/scope/per-user); `voucher_redemptions` registered.
- [ ] `POST /api/vouchers/validate` live, consumed by cart/checkout UI (discount from API only).
- [ ] INV-1/2/3/9/10 enforced; CE1 wired (activates fully with E3 orders).
- [ ] Adversarial validate never 5xx; unit tests cover rounding/cap/clamp edges.
- [ ] `bash scripts/gate.sh` GREEN; `BUG_REGISTRY.md` updated (RC-E2 toward PREVENTED).
