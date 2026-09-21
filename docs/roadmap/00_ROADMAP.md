# 00 — MASTER ROADMAP (Epics E1–E8)
## Collector Parfum — Execution Blueprint (Foundation → V1 → Growth → Hardening)

> **Golden rule (inherited from `docs/00_INDEX.md`):** A guardrail is *code that can FAIL* (exit ≠ 0).
> Code wins over prose. This roadmap is a planning SSOT; whenever code and this document disagree,
> synchronise them — never leave the drift silent.
>
> **How to use this folder:** Each Epic (E1–E8) has its own exhaustive spec file. Read the relevant
> Epic file **before** writing a single line of code for that Epic. Every Epic file follows the same
> 13-section contract (incl. a per-Epic **UI/UX Blueprint**) enforced by `scripts/verify_roadmap_docs.py`
> (wired into `scripts/gate.sh`).
>
> **Design & UX SSOT:** `docs/roadmap/UX_BLUEPRINT.md` (exhaustive UI/UX for all surfaces) extends the
> approved visual system in `design_guidelines.md`. Read it alongside any UI-touching Epic.
>
> **Language:** English (technical). User-facing copy in the product stays Bahasa Indonesia.

---

## 1. Overview

Collector Parfum is a premium Indonesian perfume e-commerce store. The **foundation phase is DONE**
(modular FastAPI scaffold, auth infra, idempotent seed, 28+ guardrail/forensic gates, SSOT docs,
threat model RC-E1..E16). See `plan.md` Phase 1 and `memory/GATE_RECEIPT.md` (VERDICT: GREEN).

This roadmap turns the agreed feature vision into **eight sequenced Epics**. Each Epic is a
self-contained, testable increment that:

- extends the canonical data model (`docs/03_DATA_MODEL.md`) and API contract (`docs/04_API_CONTRACT.md`),
- activates the matching *grow-with-code* guardrails (state-machine, concurrency, IDOR, cross-entity),
- maps every feature to at least one threat class from `docs/09_THREAT_MODEL.md` (RC-E series),
- ships a real UI (no orphan endpoints — enforced by `verify_delivery.py` D2),
- ends GREEN on `bash scripts/gate.sh`.

**Non-negotiables for every Epic**

1. **DO NOT bypass gates.** Run `bash scripts/gate.sh` after every small milestone; it must be GREEN.
2. **Money = integer rupiah**, time = ISO-8601 UTC. IDs = UUID with domain prefix (`prd_`, `ord_`, ...).
3. **One SSOT per concept** — pricing lives only in `services/pricing.py`; status transitions only in
   `services/orders.py`; never duplicate business math in the UI.
4. **Read the threat model first.** Before designing any write-path, open `docs/09_THREAT_MODEL.md`
   and `memory/BUG_REGISTRY.md`, find the relevant RC-E class, and confirm its guardrail is wired.

---

## 2. Epic Index

| Epic | File | Title | Priority | Primary threats covered |
|------|------|-------|----------|-------------------------|
| E1 | `E1_CATALOG.md` | Catalog (read-path): products, categories, reviews, variants, media, SEO | P0 | RC-E5, RC-E11, RC-E13, RC-E14 |
| E2 | `E2_PRICING_VOUCHERS.md` | Centralized pricing SSOT + Shopee-like voucher campaigns | P0 | RC-E1, RC-E2, RC-E9, RC-E12, RC-E14 |
| E3 | `E3_CART_CHECKOUT_ORDERS.md` | Cart, checkout & orders (atomic stock, anti-oversell, state machine) | P0 | RC-E1, RC-E3, RC-E4, RC-E6, RC-E7, RC-E8, RC-E9 |
| E4 | `E4_CUSTOMER_ACCOUNT.md` | Customer account: wishlist, address book, order history (IDOR-safe) | P1 | RC-E10, RC-E15, RC-E5 |
| E5 | `E5_ADMIN_BACKOFFICE.md` | Admin backoffice CMS: media gallery, RBAC, live preview | P1 | RC-E10, RC-E5, RC-E11, RC-E16 |
| E6 | `E6_PAYMENTS.md` | Payments: bank transfer (admin verification) + COD | P1 | RC-E4, RC-E8, RC-E9, RC-E10 |
| E7 | `E7_GROWTH_ANALYTICS.md` | Growth: SEO, analytics, live chat w/ cart context, WhatsApp, CRM, CTA | P2 | RC-E11, RC-E13, RC-E16, RC-E10 |
| E8 | `E8_HARDENING.md` | Hardening: forensics, N+1, accessibility, release readiness | P2 | RC-E3, RC-E9, RC-E10, RC-E11, RC-E16 |

---

## 3. Sequencing & Dependencies

```
Foundation (DONE)
   └─> E1 Catalog (read) ─────────────┐
         └─> E2 Pricing & Vouchers ──┐ │
               └─> E3 Cart/Checkout/Orders  (needs E1 products + E2 pricing)
                     ├─> E4 Account (needs E3 orders for history)
                     ├─> E5 Admin CMS (needs E1/E2/E3 write-paths)
                     └─> E6 Payments (needs E3 orders + E5 admin verify UI)
                            └─> E7 Growth (needs storefront + orders for analytics)
                                   └─> E8 Hardening (needs all write-paths live)
```

**Hard dependencies**

- **E3 requires E1 + E2.** Checkout cannot compute totals without the pricing SSOT (E2) and cannot
  snapshot line items without the catalog (E1).
- **E4 order history requires E3.** Wishlist/address CRUD can start in parallel but ownership tests
  (IDOR) depend on the auth infra already present.
- **E5 admin write-paths reuse the same services** built in E1–E3 (no second source of truth).
- **E6 payment verification** flips order/payment status through `services/orders.py` only.
- **E7 analytics** is additive/read-mostly; **E8 hardening** is last and assumes everything is live.

**Rule:** Do not start an Epic until its upstream dependency is GREEN on `scripts/gate.sh` and its
P0 deliverables are checked by `verify_delivery.py`.

---

## 4. Global Guardrail Policy

Every Epic MUST follow the *grow-with-code* growth rule from `docs/07_ENGINEERING_GUARDRAILS.md`:

1. **Declare before you build.** New collection/field/endpoint → update `docs/03_DATA_MODEL.md` and
   `docs/04_API_CONTRACT.md`, then register it in: `scripts/verify_contract.py`,
   `scripts/verify_schema.py`, `scripts/verify_data_integrity.py`, `scripts/health_check.py`.
2. **Activate the matching runtime gate (no SKIP once the endpoint exists):**
   - order lifecycle → `scripts/verify_state_machine.py` (SM1..SM4)
   - limited resources (stock, voucher limit) → `scripts/verify_concurrency.py` + `forensic/fa_race.py`
   - cross-collection aggregates → `scripts/verify_cross_entity.py` (CE1..CE4)
   - ownership/authz → `forensic/fa_idor.py`, `fa_idor_matrix.py`, `fa_write_idor.py`
   - adversarial input → `scripts/guardrails/verify_adversarial_5xx.py`, `forensic/fa_fuzz.py`, `fa_5xx.py`
3. **Meta-proof stays honest.** `forensic/fa_mutation.py` must remain 3/3 CAUGHT (guardrails are not no-ops).
4. **Anti under-delivery.** Add each Epic's P0 items to `memory/DELIVERY_MANIFEST.md`; no orphan
   endpoints (`verify_delivery.py` D2). Update `memory/BUG_REGISTRY.md` status (WATCH → PREVENTED).
5. **Run the gate every milestone.** `bash scripts/gate.sh` → `memory/GATE_RECEIPT.md` must be GREEN.

---

## 5. Cross-Epic Data Model Evolution

The canonical collections already declared in `docs/03_DATA_MODEL.md` are introduced/populated by Epic:

| Collection | Introduced/populated in | Notes |
|------------|-------------------------|-------|
| `products`, `categories`, `reviews` | E1 | multi-variant `volumes[]`, media gallery, SEO meta |
| `vouchers` (+ campaign fields), `pricing` rules | E2 | Shopee-like campaigns; pricing math centralized |
| `carts`, `orders`, `counters` | E3 | server cart (hybrid), atomic stock, order code series |
| `addresses`, `wishlists` | E4 | strictly owner-scoped |
| `settings`, `audit_logs`, media assets | E5 | CMS singletons, media library, audit trail |
| payment fields on `orders`, `payment_methods` | E6 | transfer proof + admin verification, COD fee |
| analytics events, SEO metadata | E7 | additive read-mostly collections |
| — | E8 | no new collections; integrity/perf hardening |

**Additive-only rule:** New fields must have safe defaults and numeric bounds (`ge/gt`) in
`backend/schemas.py` (anti RC-E12). Renames are forbidden without updating the alias blacklist in
`docs/03_DATA_MODEL.md` and `scripts/verify_contract.py` (anti RC-E1 drift).

---

## 6. Definition of Done (Global)

An Epic is DONE only when ALL of the following hold:

- [ ] SSOT docs updated: `03_DATA_MODEL.md`, `04_API_CONTRACT.md` (+ `06_STATE_MACHINE.md` if lifecycle touched).
- [ ] New endpoints registered in `health_check.py` and consumed by a real UI (no orphan — `verify_delivery.py` D2).
- [ ] All relevant runtime gates ACTIVE (no SKIP): state-machine / concurrency / cross-entity / IDOR as applicable.
- [ ] `memory/DELIVERY_MANIFEST.md` P0 items present; `memory/BUG_REGISTRY.md` updated (WATCH → PREVENTED).
- [ ] `bash scripts/gate.sh` → `memory/GATE_RECEIPT.md` **VERDICT: GREEN** (runtime gates run, not skipped).
- [ ] `bash scripts/run_forensics.sh` → no HIGH/VULN findings.
- [ ] One `testing_agent_v3` pass on the Epic's happy-path **and** at least one deviant-path scenario.
- [ ] UI matches `design_guidelines.md`; every interactive/critical element has a unique `data-testid`.
- [ ] No `.env` / `MONGO_URL` / `REACT_APP_BACKEND_URL` changes.
