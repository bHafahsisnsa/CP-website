# E8 — Hardening: Forensics, N+1 Optimization, Accessibility, Release Readiness

> Priority: **P2**. Depends on: all write-paths live (E1–E6) + growth (E7). Final Epic before release.
> Read first: `docs/09_THREAT_MODEL.md` (all RC-E), `docs/07_ENGINEERING_GUARDRAILS.md`, `scripts/run_forensics.sh`.

## 1. Epic Summary

Close the loop: run the full forensic battery against the now-complete app, eliminate performance
debt (N+1, unbounded queries, missing indexes), reach the target accessibility bar, and confirm the
whole system is release-grade. This Epic adds few features; it turns every WATCH in
`memory/BUG_REGISTRY.md` into PREVENTED with runtime proof, and makes `gate.sh` + `run_forensics.sh`
the definition of “done.”

**Aha moment:** the full gate + forensic suite runs ACTIVE (no SKIP), finds no HIGH/VULN, `fa_mutation`
stays 3/3 CAUGHT, and the app passes an accessibility + performance sweep — release confidence is earned.

## 2. Business Requirements

- **BR-1 Forensic clean:** `bash scripts/run_forensics.sh` produces zero HIGH/VULN findings across
  IDOR, race, session, fuzz, 5xx, dark-sweep, N+1.
- **BR-2 Concurrency proof:** anti-oversell holds under sustained parallel checkout; voucher/payment
  limits hold under races (`verify_concurrency.py`, `fa_race.py`).
- **BR-3 Performance:** no N+1 on list/detail endpoints; all hot queries bounded + indexed; payload
  sizes reasonable; FE bundle/build clean.
- **BR-4 Accessibility:** semantic HTML, color contrast, alt text, keyboard navigability, ARIA where
  needed across storefront + admin; focus-visible states everywhere.
- **BR-5 Regression safety:** meta-proof `fa_mutation.py` remains 3/3 CAUGHT; all invariants
  (INV-1..INV-11 + epic INVs) enforced on realistic data.
- **BR-6 Release readiness:** deployment readiness check (env usage, ports, CORS) passes; no
  hardcoded secrets/URLs; docs + manifest reconciled with code.

## 3. Scope & Non-Goals

**In scope:** full forensic + gate run with everything ACTIVE, N+1/index/performance fixes, a11y
remediation, index creation on startup, final SSOT reconciliation, deployment-readiness static check.

**Non-goals:** new features, new integrations (those are their own Epics), infra/k8s changes, SSL/CI
configuration (out of scope per platform boundaries). Load testing beyond the concurrency gate is
optional/backlog.

## 4. Data Model

No new collections. Focus on **indexes** (created at startup in `server.py`/`db.py`):

```
indexes (ensure):
  products.slug (unique), products.category, products.status
  orders.code (unique), orders.user_id, orders.status
  addresses.user_id, wishlists.user_id (unique)
  vouchers.code (unique), voucher_redemptions.voucher_code
  reviews.product_id, analytics_events.type + created_at
  sessions.token (unique), sessions.expires_at (TTL-friendly)
```

Confirm all canonical collections/fields in `docs/03_DATA_MODEL.md` still match code (no silent drift);
`verify_schema.py`/`verify_contract.py` must be GREEN.

## 5. API Contract

No new endpoints. This Epic verifies that **every** existing endpoint:

- is consumed by the UI (no orphan — `verify_delivery.py` D2),
- returns the exact shape in `docs/04_API_CONTRACT.md` (`health_check.py` + `verify_api_contract.py`),
- never 5xx on adversarial input (`audit_endpoint_sweep.py`, `verify_adversarial_5xx.py`),
- is bounded/indexed (no N+1 — `fa_nplus1.py`, `verify_architecture.py`).

## 6. State Machine & Invariants

All invariants enforced on realistic (non-empty, partially deviant) data:

- INV-1..INV-11 (`memory/INVARIANTS.md`) + epic INVs (C1..C3, A1..A3, M1..M3, P1..P2, G1..G4).
- SM1..SM4 ACTIVE with real orders (`verify_state_machine.py`).
- CE1..CE4 ACTIVE with real orders/vouchers/payments (`verify_cross_entity.py`).
- Meta: `fa_mutation.py` 3/3 CAUGHT (guardrails not decayed into no-ops).

## 7. Execution Steps

1. **Full sweep:** run `bash scripts/gate.sh` (everything ACTIVE) + `bash scripts/run_forensics.sh`;
   triage every finding by severity.
2. **Fix HIGH/VULN first:** IDOR/race/session/5xx findings — fix root cause, add/adjust the gate that
   reproduces it (test-first), then confirm CAUGHT.
3. **N+1 & indexes:** eliminate per-row queries in list endpoints (batch/aggregate); ensure startup
   creates all indexes in §4; re-run `fa_nplus1.py`/`verify_architecture.py`.
4. **Accessibility pass:** audit storefront + admin — semantic landmarks, contrast, alt text, keyboard
   order, focus-visible, ARIA on custom widgets; fix violations.
5. **Regression proof:** confirm `fa_mutation.py` 3/3 CAUGHT; all invariants GREEN on realistic data.
6. **Deployment readiness:** run `deployment_agent`; ensure env-var usage (no hardcoded URLs/secrets),
   correct ports, CORS; fix reported blockers.
7. **SSOT reconciliation:** `verify_delivery.py` all phases satisfied; `memory/BUG_REGISTRY.md` every
   WATCH → PREVENTED with a linked runtime gate; update `plan.md` + `GATE_RECEIPT.md`.
8. **Final verify:** one `testing_agent_v3` end-to-end (storefront + admin) + full forensic clean.

## 8. Best Practices

- **Fix root cause, not symptom;** write the failing gate first, then fix (test-first).
- **Bounded queries + indexes** on every hot path; never unbounded `find()` in a loop.
- **Accessibility is not optional** — semantic HTML + keyboard + contrast are release gates.
- **Keep guardrails honest** — `fa_mutation` must stay CAUGHT; a green suite that can't fail is worthless.
- **No hardcoded secrets/URLs** — env vars only; `deployment_agent` must pass.
- **Reconcile docs ↔ code** — drift between SSOT docs and implementation is itself a defect.

## 9. Bug Mitigation & Threat Mapping

| Threat | Focus in E8 | Mitigation |
|--------|-------------|------------|
| **RC-E3** oversell | sustained parallel load | `verify_concurrency.py`, `fa_race.py` ACTIVE + PASS; INV-4 |
| **RC-E9** cross-entity | realistic multi-entity data | `verify_cross_entity.py` CE1..CE4 GREEN |
| **RC-E10** IDOR | full role×endpoint matrix | `fa_idor.py`, `fa_idor_matrix.py`, `fa_write_idor.py` clean |
| **RC-E11** adversarial 5xx | every endpoint | `audit_endpoint_sweep.py`, `verify_adversarial_5xx.py`, `fa_5xx.py` |
| **RC-E15** session | token lifecycle | `fa_session.py` clean |
| **RC-E16** under-deliver | orphan endpoints / silent skips | `verify_delivery.py` D1/D2; `fa_dark_sweep.py`; `fa_mutation.py` 3/3 |
| **perf/N+1** | list/detail hot paths | `fa_nplus1.py`, `verify_architecture.py`; indexes |

## 10. Guardrail Wiring

- **Everything ACTIVE, no SKIP:** entire `scripts/gate.sh` runtime section + `scripts/run_forensics.sh`.
- **Performance:** `forensic/fa_nplus1.py`, `scripts/verify_architecture.py`; startup index creation.
- **Meta:** `forensic/fa_mutation.py` 3/3 CAUGHT; `forensic/fa_dark_sweep.py` no dark endpoints.
- **Delivery/SSOT:** `verify_delivery.py` all phases; `BUG_REGISTRY.md` WATCH → PREVENTED.
- **Deployment:** `deployment_agent` (env/ports/CORS/secrets) passes.

## 11. Test Plan

**Forensic:** `bash scripts/run_forensics.sh` — zero HIGH/VULN; each probe (IDOR/race/session/fuzz/
5xx/dark/N+1) explicitly clean.

**Gate:** `bash scripts/gate.sh` — GREEN with runtime + state-machine + concurrency + cross-entity ACTIVE.

**Performance:** list/detail endpoints show no N+1; indexes present; bounded queries; FE `esbuild`/build clean.

**Accessibility:** keyboard-only navigation of storefront + admin; contrast + alt-text audit; focus-visible everywhere.

**Regression (testing_agent_v3):** full end-to-end (Home→Shop→PDP→Cart→Checkout→Success + account +
admin CRUD + order processing + payment verify) with deviant paths.

**Deviant-path (mandatory):** parallel checkout on last unit, cross-user resource access, illegal
status jumps, payment on terminal order, adversarial inputs across all endpoints.

## 12. UI/UX Blueprint

> Full system: `docs/roadmap/UX_BLUEPRINT.md` §5 (Accessibility) + §16 (UX DoD). E8 adds **no new screens**;
> it is a UX quality + accessibility + performance pass across every surface built in E1–E7.

**Accessibility sweep (storefront + admin)**
- Semantic landmarks + logical heading order; single `h1` per page.
- `focus-visible` champagne ring on ALL interactive elements; full keyboard navigation (drawers/dialogs
  ESC + trap focus); no keyboard traps.
- Contrast ≥ 4.5:1 on paper; status conveyed by text + color (never color-only badges).
- `alt` text audit; ARIA on custom widgets (variant selector, live preview, timeline, funnel chart).
- `prefers-reduced-motion` disables marquee/rotation/parallax everywhere.

**Perceived-performance UX**
- Confirm skeleton loaders on all data fetches > ~300ms; no layout shift (reserve space with `aspect-ratio`).
- Verify empty/error/retry states exist for every data-driven view (no blank frames).
- Bundle/build clean (`esbuild`); images lazy-loaded; no N+1-driven UI stalls.

**Consistency audit**
- All surfaces use design tokens (no raw colors), Shadcn components (no native dropdown/toast), no
  `transition: all`, no emoji icons — verified by `scripts/ux_audit.py --strict` + `scripts/check_nav_map.py`.

**States/components:** no new components; re-audit existing per `UX_BLUEPRINT.md` §14 inventory.

**Testids:** ensure every interactive/critical element across E1–E7 has a unique kebab-case `data-testid`
(no missing/duplicate) — this is a release gate.

## 13. Definition of Done

- [ ] `bash scripts/gate.sh` GREEN (all runtime ACTIVE) + `run_forensics.sh` zero HIGH/VULN.
- [ ] `fa_mutation.py` 3/3 CAUGHT; every WATCH in `BUG_REGISTRY.md` → PREVENTED with a linked gate.
- [ ] No N+1; indexes created at startup; queries bounded (`fa_nplus1.py`, `verify_architecture.py` clean).
- [ ] Accessibility bar met (semantic/keyboard/contrast/ARIA/focus-visible) on storefront + admin.
- [ ] `deployment_agent` passes (env vars only, correct ports, CORS, no hardcoded secrets/URLs).
- [ ] SSOT reconciled (`03`/`04`/`06` match code; `verify_delivery.py` all phases satisfied).
- [ ] Final `testing_agent_v3` end-to-end (happy + deviant) PASS; `plan.md` + `GATE_RECEIPT.md` updated.
