# E6 — Payments: Bank Transfer (Admin Verification) + COD

> Priority: **P1**. Depends on: E3 (orders/lifecycle), E5 (admin verification UI). No payment gateway in V1.
> Read first: `docs/06_STATE_MACHINE.md`, `docs/09_THREAT_MODEL.md` (RC-E4, RC-E8, RC-E9), `docs/01_PRD.md` §3.

## 1. Epic Summary

Implement V1 manual payments per the owner's decision: **bank transfer** (customer uploads/records
proof, admin verifies) and **COD** (cash on delivery with a fixed fee). Payment state must be derived
from money, never faked; verifying/receiving payment flows through the single `transition_order`
function so the state machine and cross-entity guardrails stay authoritative. No third-party gateway.

**Aha moment:** a customer places a transfer order, submits proof; the admin verifies it; the order
moves `pending → paid` with `payment_status=lunas` — and the money math (sum paid ≤ sum total) always
reconciles.

## 2. Business Requirements

- **BR-1 Payment methods:** seeded `payment_methods` (transfer banks, e-wallet manual, COD). COD adds
  `settings.cod_fee` (Rp 4.000) — only when `payment.group == 'cod'` (INV-10).
- **BR-2 Transfer proof:** `POST /api/orders/{code}/payment-proof {amount, ref?, image_url?}` by the
  order owner; records a pending proof; does NOT auto-mark paid.
- **BR-3 Admin verification:** admin verifies/rejects proof; on verify, `paid_amount` increases and
  `transition_order` moves status appropriately (pending→paid) with `payment_status` derived (INV-5).
- **BR-4 COD flow:** COD orders are `pending` until shipped/delivered; payment recorded on completion;
  `payment_status` stays honest (unpaid until money received).
- **BR-5 Payment instructions:** success page + account order detail show bank/e-wallet/COD
  instructions and current `payment_status`.
- **BR-6 Reconciliation:** aggregates never contradict — `sum(paid_amount) <= sum(total)`; no payment
  accepted on terminal (cancelled/completed) orders.

## 3. Scope & Non-Goals

**In scope:** payment-proof capture (URL/reference; image upload only if object storage integrated in
E5), admin verify/reject, `paid_amount` updates via `transition_order`, COD fee handling, payment
instruction UI, reconciliation invariants/cross-entity checks.

**Non-goals (deferred):** Midtrans/Xendit gateway, auto-reconciliation from bank API, partial refunds
automation, installment/DP plans beyond the `dp` payment_status. These need credentials/integration
(backlog in `docs/01_PRD.md`).

## 4. Data Model

Extend `orders` (payment sub-fields) + reuse `payment_methods`, `settings`:

```
orders.payment: { group in {transfer, ewallet, cod}, method_id }
orders.paid_amount (int >= 0)
orders.payment_status in {belum_bayar, dp, lunas}   # DERIVED (INV-5), never hand-set
orders.cod_fee (int >= 0)                           # > 0 only if group == cod (INV-10)

payment_proofs (new, pay_):
  id (pay_), order_code (FK -> orders.code), user_id (owner), amount (int > 0),
  ref?, image_url?, status in {pending, verified, rejected},
  verified_by?, created_at, verified_at?
```

`payment_methods` (existing): `{id, group, name, extra, fee (>=0), active}`. Register `payment_proofs`
in `verify_contract.py`/`verify_schema.py`; bounds in `schemas.py`.

## 5. API Contract

```
GET  /api/payment-methods                              -> [PaymentMethod,...]   # grouped by group in FE
POST /api/orders/{code}/payment-proof {amount, ref?, image_url?}  -> PaymentProof   # owner only
GET  /api/orders/{code}/payment-proofs                 -> [PaymentProof,...]    # owner or admin
# admin
GET  /api/admin/payments?status                        -> [PaymentProof,...]
PUT  /api/admin/payments/{id}/verify {approve:bool, note?}  -> Order   # -> transition_order on approve
```

All customer routes owner-scoped; admin routes `require_role('admin')`. Sync to `docs/04_API_CONTRACT.md`.

## 6. State Machine & Invariants

All status/payment changes go through `services/orders.py::transition_order` (SSOT, `docs/06`):

- **INV-5:** `payment_status` derived from `paid_amount` vs `total` — never set directly (RC-E4 / SM4).
- **INV-10:** `cod_fee > 0` only when `payment.group == 'cod'`.
- **INV-P1 (new):** verifying a proof increases `paid_amount` by the proof amount exactly once
  (idempotent per proof id); rejecting does not change `paid_amount`.
- **INV-P2 (new):** no payment/proof verification on terminal orders (cancelled/completed) → 400 (RC-E8/SM3).
- **CE (cross-entity):** `sum(orders.paid_amount) <= sum(orders.total)`; `paid_amount ==
  sum(verified payment_proofs.amount)` per order (RC-E9).

## 7. Execution Steps

1. **Docs first:** add `payment_proofs` to `docs/03`; add payment endpoints to `docs/04`; confirm
   payment rules in `docs/06_STATE_MACHINE.md` §3.
2. **Service:** extend `services/orders.py` with `record_payment(order, amount, source)` that updates
   `paid_amount` then calls `transition_order` (never sets `payment_status` directly). Idempotent per proof.
3. **Proof capture:** `backend/routers/payments.py` — owner submits proof; admin verify/reject.
   Image upload only if object storage integrated (E5); else store `image_url`/`ref`.
4. **COD:** ensure `cod_fee` applied by `compute_pricing` (E2) when group=cod; payment recorded at delivery.
5. **Gate wiring:** add INV-P1/P2 to `verify_data_integrity.py`; extend `verify_cross_entity.py`
   (paid == verified proofs; sum paid ≤ sum total); `verify_state_machine.py` SM3/SM4 cover terminal
   + honest payment; `fa_write_idor.py` (only owner submits proof; only admin verifies).
6. **Frontend:** success page + account order detail show instructions + `payment_status`; proof
   submission form (owner); admin verification screen (E5 surface). Unique `data-testid` on amount
   field, submit, verify/reject buttons, status badges.
7. **Verify:** `bash scripts/gate.sh` GREEN; `run_forensics.sh` clean; `testing_agent_v3`.

## 8. Best Practices

- **Derive payment_status; never hand-set** (INV-5). “completed” does not imply “lunas” (RC-E4).
- **Route money through `transition_order`** so lifecycle + reconciliation stay single-source.
- **Idempotent verification** — verifying the same proof twice must not double-count `paid_amount`.
- **Terminal guard** — reject payment on cancelled/completed orders (RC-E8).
- **Owner submits, admin verifies** — strict RBAC/ownership (RC-E10).
- **COD fee only for COD** (INV-10); integer rupiah throughout.

## 9. Bug Mitigation & Threat Mapping

| Threat | Risk in E6 | Mitigation |
|--------|-----------|------------|
| **RC-E4** payment drift | complete marked lunas without paid | INV-5 derivation; SM4; `verify_state_machine.py` |
| **RC-E8** action on terminal | pay a cancelled order | INV-P2 terminal guard; SM3 |
| **RC-E9** cross-entity | paid != verified proofs; sum paid > sum total | `verify_cross_entity.py`; INV-P1 |
| **RC-E10** IDOR | non-owner submits proof; customer verifies | owner-scope + `require_role('admin')`; `fa_write_idor.py` |
| **RC-E11** adversarial | negative/huge amount, bad image_url | `ge/gt` bounds; validation; `fa_fuzz.py` |
| **RC-E1** total drift | COD fee applied twice / not at all | `compute_pricing` single source; INV-10 |

## 10. Guardrail Wiring

- **Data:** INV-P1/P2 + INV-5/INV-10 in `scripts/verify_data_integrity.py`; register `payment_proofs`.
- **Cross-entity:** `scripts/verify_cross_entity.py` (paid==verified proofs, sum paid ≤ sum total).
- **State machine:** `scripts/verify_state_machine.py` SM3/SM4 (terminal + honest payment).
- **Forensic:** `forensic/fa_write_idor.py` (proof ownership), `forensic/fa_fuzz.py` (amount fuzz).
- **Delivery:** payment endpoints + proof/verify UI as P1 in `memory/DELIVERY_MANIFEST.md`;
  update `BUG_REGISTRY.md` TR-04/TR-05 (RC-E4/E8) → PREVENTED.

## 11. Test Plan

**Backend (curl/pytest):** submit proof (owner) → pending; admin verify → `paid_amount` up, status
`paid`, `payment_status=lunas`; reject → no change; verify same proof twice → idempotent; pay a
cancelled order → 400; COD fee only on COD.

**Cross-entity:** `verify_cross_entity.py` — per-order `paid_amount == sum(verified proofs)`; global
`sum(paid) <= sum(total)`.

**Frontend (testing_agent_v3):** transfer order → submit proof → admin verifies → status/payment
badges update; COD order shows COD fee + instructions.

**Deviant-path (mandatory):** proof amount 0/negative, proof on someone else's order, verify on
completed/cancelled, partial payment (`dp`), double verification.

## 12. UI/UX Blueprint

> Full system: `docs/roadmap/UX_BLUEPRINT.md` §10 (Payments).

**Screens & layout**
- **Payment instructions** (success page + order detail): bank/e-wallet number with copy button, amount
  (Azeret Mono), deadline, COD note + fee.
- **Payment proof form (owner):** `Form` — amount, reference, image (upload if object storage integrated
  in E5, else URL/reference input) → submit → "Menunggu verifikasi".
- **Payment status timeline:** vertical stepper (belum_bayar → dp → lunas) alongside order status
  (pending→paid→packed→shipped→completed/cancelled), utility-colored nodes, current node emphasized.
- **Admin verification** (in `/admin/*`): proof list with image preview + Approve/Reject + note; Approve
  triggers guarded transition.

**Components (Shadcn):** `card`, `form`, `input`, `button`, `badge`, `alert-dialog`, `dialog` (image
preview), `separator`, `skeleton`, `sonner`, `tooltip`.

**States:** proof submitting/pending; verified/rejected badges; loading skeleton; error + retry; disabled
actions on terminal orders (with reason); COD shows fee line + instructions.

**Micro-interactions:** copy-to-clipboard toast; status node advance animation (opacity/scale); approve →
success toast + timeline update.

**Responsive:** instructions card full-width mobile; timeline vertical on mobile, can be horizontal on
desktop order detail.

**Accessibility:** copy buttons labelled; timeline nodes have text labels (not color-only); amounts in
`aria-live` on update; image preview dialog focus-trapped.

**Testids:** `payment-instructions`, `payment-proof-form`, `payment-proof-amount-input`,
`payment-proof-upload-input`, `payment-proof-submit-button`, `order-status-timeline`, `payment-status-badge`,
`admin-payment-verify-button`, `admin-payment-reject-button`.

## 13. Definition of Done

- [ ] `payment_proofs` live; owner submit / admin verify (RBAC-scoped).
- [ ] `payment_status` derived only (INV-5); COD fee only for COD (INV-10); verification idempotent (INV-P1).
- [ ] No payment on terminal orders (INV-P2 / SM3); `verify_state_machine.py` SM3/SM4 GREEN.
- [ ] `verify_cross_entity.py` reconciliation GREEN (paid == verified proofs; sum paid ≤ sum total).
- [ ] UI: instructions + proof form + admin verify; unique `data-testid`; payment status badges.
- [ ] `bash scripts/gate.sh` GREEN + `run_forensics.sh` clean + `testing_agent_v3` (happy + deviant).
- [ ] `BUG_REGISTRY.md` TR-04/TR-05 → PREVENTED.
