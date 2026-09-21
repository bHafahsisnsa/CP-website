# E7 — Growth & Analytics: SEO, Visitor Analytics, Live Chat, WhatsApp, CRM, CTA

> Priority: **P2**. Depends on: storefront (E1) + orders (E3) live. Mostly additive/read-path.
> Read first: `docs/09_THREAT_MODEL.md` (RC-E11, RC-E13, RC-E16, RC-E10), `docs/05_NAVIGATION_MAP.md`.

## 1. Epic Summary

Turn the working store into a growth engine: smart SEO (per-product/category meta tags, sitemap,
structured data), first-party visitor analytics (page/product/funnel events), a live chat widget that
carries cart context, WhatsApp click-to-chat with prefilled order/cart context, lightweight CRM
(customer segments from order history), and conversion-focused CTAs. External integrations (chat/WA
providers, analytics vendors) are gated behind the integration agent + user-provided credentials.

**Aha moment:** a product page ships correct SEO meta + structured data, a visitor's journey is
captured as events, and a “Chat via WhatsApp” button opens a prefilled message including their cart.

## 2. Business Requirements

- **BR-1 SEO meta:** each product/category/page renders `<title>`, meta description, canonical, and
  Open Graph/Twitter tags from the `seo` fields (E1). Missing values fall back to sensible defaults.
- **BR-2 Structured data:** JSON-LD `Product` (name, image, price, availability, aggregateRating) and
  `BreadcrumbList`; `Organization`/`WebSite` on home.
- **BR-3 Sitemap & robots:** `GET /api/sitemap.xml` (or generated static) listing active products/
  categories/pages; `robots.txt` allows indexing.
- **BR-4 Visitor analytics:** first-party event capture `POST /api/analytics/event {type, path,
  product_id?, meta?}` for page_view, product_view, add_to_cart, begin_checkout, purchase; admin sees
  aggregates (top products, funnel, conversion rate).
- **BR-5 Live chat w/ cart context:** floating chat widget; opening it attaches current cart summary;
  provider integration (e.g., a chat SDK) via integration agent — fallback = WhatsApp deep link.
- **BR-6 WhatsApp integration:** click-to-chat (`https://wa.me/<number>?text=...`) prefilled with
  cart/order context; admin sets the support number in `settings`. (Business API only if requested + credentialed.)
- **BR-7 CRM (lightweight):** derive customer segments from order history (new, repeat, high-value,
  dormant); admin list + export; used for targeted CTAs/vouchers.
- **BR-8 CTA & conversion:** prominent, accessible CTAs (add-to-cart, checkout, voucher claim) with
  clear states; A/B-ready structure (not full experimentation yet).

## 3. Scope & Non-Goals

**In scope:** SEO meta rendering + JSON-LD + sitemap, first-party analytics events + admin aggregates,
WhatsApp click-to-chat, chat widget shell (provider via integration), CRM segmentation from existing
orders, CTA polish.

**Non-goals / integration gates:** third-party analytics (GA4/Segment), chat provider SDKs, WhatsApp
Business API, and email/SMS campaigns all **require the integration agent + user credentials** before
implementation. Full experimentation platform, recommendation ML, and marketing automation are backlog.

## 4. Data Model

Additive, read-mostly:

```
analytics_events (new, evt_):
  id (evt_), type in {page_view, product_view, add_to_cart, begin_checkout, purchase, ...},
  path, product_id?, order_code?, session_hint?, user_id?, meta?, created_at

seo lives on products/categories (E1): seo { title, description, keywords[], og_image? }
settings (existing): support_phone (WA number), support_email, social links, seo defaults
crm_segments derived at query time from orders (no dedicated collection required in V1)
```

Register `analytics_events` in `verify_contract.py`/`verify_schema.py`; bound any numeric meta; never
store PII beyond what's already in orders/users. Anonymize `session_hint` (no raw IP/email).

## 5. API Contract

```
POST /api/analytics/event {type, path, product_id?, order_code?, meta?}   -> {ok:true}   # public, rate-limited
GET  /api/sitemap.xml                                                     -> XML          # active entities
GET  /api/admin/analytics?range                                          -> {funnel, top_products, conversion, ...}
GET  /api/admin/crm/segments?type                                        -> [ {user, segment, ltv, last_order} ]
```

SEO tags + JSON-LD are rendered client-side (React Helmet-style) or via SSR-friendly meta from the
`seo` fields. WhatsApp is a pure FE deep link using `settings.support_phone`. Sync to `docs/04`.

## 6. State Machine & Invariants

No order lifecycle changes. Analytics/CRM invariants:

- **INV-G1:** analytics `purchase` events reconcile with real orders (count/revenue within tolerance)
  — cross-checked by `verify_cross_entity.py` (no inflated purchase events).
- **INV-G2:** CRM segments are derived from orders only (no separate mutable truth to drift).
- **INV-G3:** analytics endpoint stores no raw PII (email/phone/IP); `session_hint` is opaque.
- **INV-G4:** SEO meta present (or safely defaulted) for every active product/category (no empty tags).

## 7. Execution Steps

1. **Docs first:** add `analytics_events` to `docs/03`; add analytics/sitemap/CRM endpoints to `docs/04`;
   note WA/chat/analytics integrations require playbooks.
2. **SEO:** render meta + JSON-LD from `seo` fields on Home/Shop/PDP/Category; add `GET /api/sitemap.xml`
   (active entities) + `robots.txt`; defaults from `settings`.
3. **Analytics:** `backend/routers/analytics.py` — `POST /api/analytics/event` (rate-limited, PII-free);
   `services/analytics.py` aggregates for admin; FE emits events at key funnel steps.
4. **WhatsApp:** FE “Chat via WhatsApp” button building `wa.me` deep link with cart/order context from
   `settings.support_phone`. (Business API → integration agent only if requested.)
5. **Live chat:** widget shell with cart-context payload; **integration agent** for the chat provider
   SDK + credentials before wiring a real provider; fallback = WA deep link.
6. **CRM:** `services/crm.py` derives segments from orders; admin list + CSV export.
7. **Gate wiring:** register `analytics_events`; add INV-G1..G4; `verify_cross_entity.py` reconciles
   purchase events vs orders; `verify_adversarial_5xx.py`/`fa_fuzz.py` fuzz the event endpoint;
   `check_nav_map.py` covers new CTAs/links; `verify_delivery.py` D2 (no orphan analytics endpoint).
8. **Verify:** `bash scripts/gate.sh` GREEN; `run_forensics.sh` clean; `testing_agent_v3`.

## 8. Best Practices

- **First-party analytics, privacy-first:** no raw PII; opaque session hints; rate-limit the public
  event endpoint (anti abuse / RC-E11).
- **Single truth for CRM:** derive from orders; don't maintain a divergent segment store (RC-E9).
- **SEO from data:** meta/JSON-LD generated from `seo` fields, never hardcoded per page.
- **Integrations gated:** chat/WA-Business/analytics vendors go through the integration agent with
  user credentials — never guess SDKs (policy).
- **Accessible CTAs:** clear hover/focus/active/disabled states; keyboard reachable (a11y).
- **Do not let marketing scripts break the app** (defensive loading; no blocking third-party JS).

## 9. Bug Mitigation & Threat Mapping

| Threat | Risk in E7 | Mitigation |
|--------|-----------|------------|
| **RC-E11** adversarial | spam/oversized analytics events | rate-limit + Pydantic bounds; `fa_fuzz.py`, `verify_adversarial_5xx.py` |
| **RC-E13** dead menu / pollution | new CTAs link to missing routes; widget leaks across pages | `check_nav_map.py`; SSOT nav (`docs/05`); scoped widget |
| **RC-E16** orphan/under-deliver | analytics endpoint w/o admin UI | `verify_delivery.py` D2; manifest P0 |
| **RC-E9** cross-entity | purchase events inflate revenue vs orders | INV-G1; `verify_cross_entity.py` |
| **RC-E10** privacy/authz | analytics/CRM leak PII or admin data | PII-free events; CRM behind `require_role('admin')` |

## 10. Guardrail Wiring

- **Data:** register `analytics_events`; INV-G1..G4 in `verify_data_integrity.py`.
- **Cross-entity:** `verify_cross_entity.py` (purchase events vs orders reconciliation).
- **Adversarial:** `scripts/guardrails/verify_adversarial_5xx.py`, `forensic/fa_fuzz.py` on the event endpoint.
- **FE nav:** `scripts/check_nav_map.py`, `scripts/ux_audit.py` for CTAs/links.
- **Delivery:** analytics/sitemap/CRM endpoints + admin analytics UI as P2 in manifest; no orphan (D2).
- **Integration:** chat/WA-Business/analytics vendors → `integration_playbook_expert` first.

## 11. Test Plan

**Backend (curl/pytest):** analytics event accepts valid types (PII-free), rejects/clamps oversized
payloads (never 5xx); sitemap lists only active entities; admin analytics aggregates match seeded
orders; CRM segments derive correctly; CRM behind admin auth.

**SEO:** PDP renders title/description/canonical/OG + JSON-LD `Product`; category breadcrumbs;
defaults when `seo` empty (INV-G4).

**Frontend (testing_agent_v3):** WhatsApp button opens prefilled `wa.me` with cart context; chat
widget shows cart summary; CTA states (hover/focus/disabled) correct; events fire on funnel steps.

**Deviant-path (mandatory):** spammed analytics endpoint (rate-limited), product with no `seo`
(defaults), empty cart WA link, CRM with zero orders.

## 12. UI/UX Blueprint

> Full system: `docs/roadmap/UX_BLUEPRINT.md` §12 (Growth).

**Screens & elements**
- **SEO (invisible UX):** correct `<head>` meta + JSON-LD from `seo` fields → accurate share previews +
  rich results; no visible UI.
- **WhatsApp button:** floating/inline "Chat via WhatsApp" (lucide `message-circle`) → `wa.me` deep link
  prefilled with cart/order context; brand-neutral accent (NOT raw green).
- **Live chat widget:** floating launcher bottom-right (above mobile bottom-nav); panel with short intro +
  current cart summary chip; provider SDK via integration playbook, fallback = WA link; scoped out of `/admin`.
- **Analytics dashboard (admin):** funnel step chart (page_view→product_view→add_to_cart→begin_checkout→
  purchase), top-products `Table`, conversion metric card. Read-only, admin-gated.
- **CTA system:** consistent primary CTAs with full state coverage (hover/focus/active/disabled/loading);
  sticky on mobile PDP.

**Components (Shadcn):** `button`, `card`, `table`, `badge`, `tooltip`, `sheet`/`popover` (chat panel),
`progress` (funnel bars), `skeleton`.

**States:** chat launcher idle/open; widget loading provider; analytics loading skeleton; empty ("Belum ada
data") ; rate-limited event fails silently (no UI break).

**Micro-interactions:** launcher hover lift; funnel bars animate width on view (reduced-motion → static);
CTA press scale.

**Responsive:** WA/chat above bottom-nav on mobile; analytics dashboard tables scroll horizontally on mobile.

**Accessibility:** chat launcher labelled + keyboard-openable + ESC close; funnel chart has text/table
fallback; WA button descriptive label; CTAs meet contrast + focus-visible.

**Testids:** `wa-chat-button`, `chat-widget-launcher`, `chat-widget-panel`, `admin-analytics`,
`admin-analytics-funnel`, `admin-analytics-conversion`.

## 13. Definition of Done

- [ ] SEO meta + JSON-LD + sitemap/robots live; INV-G4 (no empty meta) holds.
- [ ] First-party analytics events (PII-free, rate-limited); admin aggregates match orders (INV-G1).
- [ ] WhatsApp click-to-chat w/ cart context; chat widget shell (provider via integration if requested).
- [ ] CRM segments derived from orders (INV-G2), behind admin RBAC.
- [ ] No orphan endpoints; new CTAs pass `check_nav_map.py`; a11y-correct CTA states.
- [ ] `bash scripts/gate.sh` GREEN + `run_forensics.sh` clean + `testing_agent_v3` (happy + deviant).
- [ ] External integrations (if any) implemented per integration playbook with user credentials.
