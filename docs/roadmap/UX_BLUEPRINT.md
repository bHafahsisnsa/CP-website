# UX BLUEPRINT — Collector Parfum (All Surfaces)

> Exhaustive UI/UX system that **extends** `design_guidelines.md` (the approved storefront design
> SSOT: Maya-theme, ivory/charcoal/champagne, DM Serif Display + Manrope + Azeret Mono) to every
> surface introduced by Epics E1–E8. This document does **not** invent a new theme or palette — it
> reuses the approved design tokens and applies them to new screens (Account, Voucher Center,
> Payments, Admin backoffice, Growth widgets) and to the data-driven states created once the backend
> is wired.
>
> Sources of truth: `design_guidelines.md` (visual system), `docs/05_NAVIGATION_MAP.md` (IA),
> `docs/08_FRONTEND_GUARDRAILS.md` (FE contract & testids). Where this file and code disagree,
> synchronise — never leave drift silent (guardrail: `scripts/check_nav_map.py`, `scripts/ux_audit.py`).

---

## 1. Purpose & Scope

Turn the polished V1 storefront (currently fed by dummy data) into a fully data-driven, accessible,
consistent experience across storefront + customer account + admin backoffice + growth touchpoints.
This blueprint defines: global data-states, motion/a11y standards, testid conventions, deep per-surface
UX, a responsive matrix, and a per-Epic UX mapping so each Epic doc can point here instead of
duplicating the system.

**Golden UX rules (non-negotiable, from `design_guidelines.md`):**
- Reuse design tokens only; **never** raw colors, **never** `transition: all`, **never** emoji icons
  (use `lucide-react`), **never** global center alignment.
- Shadcn/UI components only for interactive primitives (no native `<select>`/dropdown/toast).
- Generous whitespace (2–3× comfortable); editorial grid; left-aligned reading flow.
- Every interactive/critical element carries a unique kebab-case `data-testid`.
- Respect `prefers-reduced-motion`; animate only `transform`/`opacity`, 120–320ms.

---

## 2. Design Tokens Recap (reuse, do not redefine)

| Token group | Value source | Usage |
|-------------|--------------|-------|
| Paper | ivory `#F7F3EA`, warm-white `#FFFCF6`, fog `#EEE7DC` | backgrounds/surfaces |
| Ink | charcoal `#141414`, near-black `#0B0B0C`, graphite `#2A2A2A` | text, primary buttons |
| Metal | champagne `#D6C3A3`, brass `#B89B6A` | accents, focus ring |
| Utility | success `#1F7A5A`, warning `#B7791F`, danger `#B42318`, info `#1E5AA8` | status/toasts/badges |
| Marketplace | market-blue `#1A73E8`, soft `#EAF2FF` | checkout/place-order CTA only |
| Radius | card `rounded-2xl`, button `rounded-xl`, chip `rounded-full` | consistency |
| Fonts | DM Serif Display (display), Manrope (UI/body), Azeret Mono (SKU/price/volume) | hierarchy |
| Motion | instant 120 / fast 180 / base 260 / drawer 320ms; easing `[0.22,1,0.36,1]` | micro-motion |

Semantic HSL tokens live in `frontend/src/index.css` for shadcn (light + dark). **All new surfaces
consume these tokens** — admin and account inherit the same look so the brand stays coherent.

---

## 3. Global Data States (mandatory for every data-driven view)

Once E1 wires APIs, every list/detail/form must implement four explicit states. This is a hard
requirement (`docs/08_FRONTEND_GUARDRAILS.md`) and prevents blank/broken screens.

- **Loading:** Shadcn `Skeleton` matching the final layout (card grids → skeleton cards; tables →
  skeleton rows; detail → skeleton blocks). Trigger for any fetch that may exceed ~300ms. No spinners
  as the sole indicator on full pages. `data-testid="<view>-loading"`.
- **Empty:** friendly editorial message + a primary action (e.g., "Belum ada produk di kategori ini.
  Jelajahi semua parfum" → button). Use `lucide-react` line icon, never emoji.
  `data-testid="<view>-empty"`.
- **Error:** user-friendly copy (Bahasa Indonesia) + a **Retry** button; log details to console only.
  Never surface stack traces. Use `danger` token sparingly (icon/border, not full-bleed red).
  `data-testid="<view>-error"` + `data-testid="<view>-retry"`.
- **Success/optimistic:** Sonner toast (theme-matched, not raw green/red) for writes; optimistic UI
  for wishlist toggle / cart qty with rollback on failure.

**Array guard (anti-drift RC-F4):** always `const rows = Array.isArray(res.data) ? res.data : []`.

---

## 4. Global Interaction & Motion Standards

- **Buttons:** hover `translateY(-1px)` + subtle shadow (180ms); press `scale(0.98)` (120ms);
  disabled `opacity-50 cursor-not-allowed`; loading → inline spinner + label "Memproses…", button
  disabled to prevent double-submit.
- **Links/nav:** left→right underline reveal (background-size trick from guidelines); active route has
  distinct weight/color; breadcrumb when depth > 2 (admin).
- **Drawers/Sheets:** cart = right, search = top, mobile menu = full-screen, filters = bottom (mobile);
  focus-trap + ESC close (Shadcn handles). Backdrop fade.
- **Reveals:** scroll-reveal opacity+`y:18`→0, stagger 0.06–0.1 (storefront marketing only; admin is
  utilitarian — minimal motion).
- **Reduced motion:** disable marquee/rotation/parallax; keep opacity fades only.

---

## 5. Accessibility Standards (release gate — E8)

- Semantic landmarks (`header`, `nav`, `main`, `footer`, `aside`); one `h1` per page; logical heading order.
- `focus-visible` ring using champagne (`--ring`) on ALL interactive elements; visible keyboard focus.
- Color contrast ≥ 4.5:1 for body text on paper; never light-grey text on ivory.
- All images have meaningful `alt`; decorative art `alt=""`.
- Custom widgets (volume selector, variant picker, live preview toggles) get proper ARIA roles/labels.
- Drawers/dialogs: `aria-modal`, labelled by title, ESC + trap focus.
- Forms: label ↔ input association, inline error text with `aria-describedby`, error summary on submit.
- Honour `prefers-reduced-motion`.

---

## 6. Testid Conventions

- Kebab-case, role-based (not appearance-based): `checkout-place-order-button`, `admin-product-save-button`.
- Pattern per surface: `<surface>-<entity>-<action|state>`. Examples: `account-address-add-button`,
  `voucher-center-claim-button`, `admin-orders-status-select`, `payment-proof-upload-input`.
- Centralize new ids under `frontend/src/constants/testIds/` (existing pattern: `auth.js`, `home.js`).
- Every list item exposes a stable id: `product-card` (storefront), `admin-products-row`, `order-history-row`.

---

## 7. Storefront Surfaces (E1–E3) — data-state elaboration

The visual blueprints already exist in `design_guidelines.md` (`page_blueprints`). This section adds
what changes when real data + writes arrive.

### 7.1 Home (E1)
- Best-sellers carousel + category grid now fetch from `/api/products?sort=best_seller` and
  `/api/categories`. Loading → skeleton carousel/cards; empty category → hide section gracefully.
- Keep hero headline tracking animation, marquee, testimonials (from `/api/reviews`), FAQ accordion.
- Testids retained: `home-hero`, `home-best-sellers`, `home-category-card`, `home-faq-accordion`.

### 7.2 Shop / PLP (E1)
- Desktop sidebar filters + mobile filter `Sheet` (bottom). Filters (`Kategori/Harga/Notes/Konsentrasi/
  Volume`) map to query params; sort via `Select`. Server-side filter/sort/paginate.
- **States:** skeleton product grid on load; empty state ("Tidak ada hasil untuk filter ini" + Reset
  filters button); error + retry. Pagination or "Muat lebih banyak" button.
- Product card: hover image-swap, quick-view (`Dialog`), wishlist heart (optimistic), chips
  (notes/EDP-EDT/ml), price + strike. Testids: `product-card`, `product-card-quick-view-button`,
  `plp-filter-open-button`, `plp-sort-select`, `shop-grid-empty`, `shop-grid-loading`.

### 7.3 PDP (E1 + E3)
- 2-col desktop (sticky gallery + info), mobile swipe gallery + sticky ATC bar. Add optional
  `video_url` player in gallery. Volume selector (`RadioGroup`/segmented) drives price via Azeret Mono
  microtext; changing volume updates price + stock/availability label.
- Out-of-stock variant → disabled option + "Stok habis" badge; ATC disabled with reason.
- Notes pyramid (Top/Heart/Base chips), accordion (Deskripsi/Ketahanan/Sillage/Ingredients/Pengiriman),
  reviews block with rating aggregate. Related products carousel.
- Testids: `pdp-gallery`, `pdp-quantity-input`, `pdp-add-to-cart-button`, `pdp-buy-now-button`,
  `pdp-variant-option`, `pdp-sticky-atc-button`.

### 7.4 Cart + Cart Drawer (E3)
- Drawer for quick access; full page for edit qty (stepper), remove, voucher entry, order note.
- Live subtotal from server pricing preview. Empty cart state → "Keranjang kosong" + Belanja CTA.
- Stock conflict inline ("Stok tersisa N") when qty exceeds availability. Testids: `cart-page`,
  `cart-item`, `cart-item-qty-input`, `cart-checkout-button`, `cart-empty`.

### 7.5 Checkout (Shopee-style) (E3 + E6)
- Card sections: Alamat (Dialog picker) → Kurir (`RadioGroup`) → Pembayaran (`Tabs`:
  Transfer/E-Wallet/COD) → Voucher (Input+apply) → Catatan (`Textarea`) → Ringkasan (sticky Card).
- **Summary rows** Subtotal/Diskon/Ongkir/COD fee/Total come from `/api/vouchers/validate` +
  `compute_pricing`; **never computed client-side**. Place-order CTA uses market-blue.
- States: validating voucher (inline spinner in apply button), invalid voucher (reason text under
  input), placing order (CTA disabled + "Memproses…"), 409 stock (banner + affected item), 400 (field
  errors). Testids: `checkout-address-card`, `checkout-shipping-option`, `checkout-payment-tab`,
  `checkout-voucher-input`, `checkout-voucher-apply-button`, `checkout-total-amount`,
  `checkout-place-order-button`.

### 7.6 Order Success (E3)
- Centered card, content left-aligned. Shows order `code`, summary, payment instructions (E6),
  CTAs (Lanjut Belanja / Lihat Detail). Testids: `order-success-page`, `order-success-code`,
  `order-success-continue-shopping`.

---

## 8. Customer Account Surface (E4)

`/akun` uses a **two-column layout** (desktop): left vertical nav (`Tabs` or nav list) — Profil,
Pesanan, Alamat, Wishlist; right content. Mobile: top `Tabs` or accordion sections.

- **Profil:** read-only email (locked), editable name/phone (Form + Input); Save button with
  optimistic + toast. Testids: `account-profile-form`, `account-profile-save-button`.
- **Pesanan (order history):** list of order cards/rows (code, date, total, status `Badge` with
  utility colors), click → detail (item snapshots, timeline, payment status). Empty → "Belum ada
  pesanan" + Belanja CTA. Testids: `order-history-row`, `order-history-status-badge`,
  `order-detail-view`.
- **Alamat (address book):** cards per address; add/edit via `Dialog` (Form: Nama, No. HP, Alamat,
  Kota, Provinsi, Kode Pos, Label); one **default** address with distinct badge + "Jadikan default"
  action; delete with `AlertDialog` confirm. Testids: `account-address-add-button`,
  `account-address-card`, `account-address-default-toggle`, `account-address-delete-button`.
- **Wishlist:** reuse product-card grid; heart toggle removes with optimistic + undo toast. Empty →
  "Wishlist kosong" + Jelajahi CTA. Testids: `wishlist-grid`, `wishlist-item-remove-button`.
- **Auth-gate:** visiting `/akun` while logged out → redirect to login/announcement; session expiry →
  toast + re-login (RC-E15).

---

## 9. Voucher Center (E2)

A Shopee-like **voucher center** surfaced in cart/checkout and (optionally) a `/voucher` page.

- **Voucher card:** label, discount value (percent/flat/free-ship), min-spend note, validity window,
  campaign theme accent (champagne), CTA "Pakai" or "Klaim". Disabled/greyed when ineligible with
  reason ("Min. belanja Rp X"). Countdown chip for expiring soon (Azeret Mono).
- **Apply flow (checkout):** Input + Apply → inline validating state → success (discount line appears
  in summary, voucher chip with remove) or error (reason under input). Discount shown = API value only.
- **States:** loading skeleton voucher list; empty ("Belum ada voucher"); error + retry.
- Testids: `voucher-center-list`, `voucher-card`, `voucher-card-apply-button`,
  `voucher-card-ineligible-reason`, `checkout-voucher-remove-button`.

---

## 10. Payments UX (E6)

- **Payment instructions** (success page + order detail): bank/e-wallet number with copy button,
  amount to transfer (Azeret Mono), deadline, COD note + fee. `data-testid="payment-instructions"`.
- **Payment proof submission (owner):** Form — amount, reference, image (upload if object storage
  integrated in E5, else URL/reference input); submit → pending state; shows "Menunggu verifikasi".
  Testids: `payment-proof-form`, `payment-proof-amount-input`, `payment-proof-upload-input`,
  `payment-proof-submit-button`.
- **Payment status timeline:** vertical stepper (belum_bayar → dp → lunas) + order status
  (pending→paid→packed→shipped→completed / cancelled) with utility-colored nodes; current node
  emphasized. `data-testid="order-status-timeline"`, `payment-status-badge`.
- **Admin verification** (in E5 admin): proof list with image preview, Approve/Reject buttons + note;
  Approve triggers guarded transition. Testids: `admin-payment-verify-button`,
  `admin-payment-reject-button`.

---

## 11. Admin Backoffice UX (E5)

The admin surface (`/admin/*`) is **utilitarian but on-brand**: same tokens/fonts, less marketing
motion, denser information. Depth ≤ 2 (per `docs/05_NAVIGATION_MAP.md`).

### 11.1 Shell & Navigation
- **Layout:** fixed left sidebar (collapsible on tablet, `Sheet` drawer on mobile) + top bar (page
  title, breadcrumb, admin avatar/menu, theme toggle). Content area on paper with card sections.
- **Sidebar groups (from `docs/05`):** Ringkasan (Dashboard) · Katalog (Produk, Kategori, Ulasan) ·
  Penjualan (Pesanan, Voucher, Pembayaran) · Pengaturan (Kurir & Tarif, Metode Pembayaran, Pengaturan
  Toko, Pengguna). Active item distinct (champagne accent + weight).
- **RBAC states:** non-admin hitting `/admin` → redirect + toast "Akses ditolak"; unguarded route is a
  gate failure (`verify_rbac_guards.py`). Testids: `admin-shell`, `admin-sidebar`, `admin-nav-item`,
  `admin-breadcrumb`, `admin-theme-toggle`.

### 11.2 Dashboard
- Metric cards (revenue, orders by status, active products, low-stock) using `Card` + Azeret Mono
  numbers; orders-by-status as a compact bar/`Progress`; recent orders `Table`; low-stock list with
  "Kelola" links. Loading skeleton cards; empty ("Belum ada data").
- Testids: `admin-dashboard`, `admin-metric-revenue`, `admin-metric-orders`, `admin-low-stock-list`.

### 11.3 Data Tables (products/orders/vouchers/reviews)
- Shadcn `Table` + toolbar (search `Input`, status filter `Select`, "Tambah" primary button),
  pagination, row actions (Edit/Archive/View) via `DropdownMenu`. Sticky header; zebra rows subtle.
- **States:** skeleton rows; empty ("Belum ada produk" + Tambah CTA); error + retry. Bulk actions
  optional (checkbox column). Testids: `admin-products-table`, `admin-products-row`,
  `admin-products-add-button`, `admin-table-search`, `admin-table-status-filter`.

### 11.4 Product Editor (multi-variant + media + live preview)
- **Two-pane editor:** left = form; right = **live preview** (renders the actual storefront PDP
  components with current form values — same components/tokens to avoid publish drift).
- **Form sections (Accordion/Tabs):** Info (name, brand, category `Select`, concentration, gender,
  tags), **Variants** (repeatable rows: ml / price / stock / sku with add/remove; numeric bounds,
  inline validation, no negatives), **Notes** (top/heart/base tag inputs), **Media Gallery**
  (image grid: add from media library `Dialog`, reorder drag, set primary, remove; optional video
  URL), **Description/Ingredients** (`Textarea`), **SEO** (title/description/keywords/og-image with
  live character counters + preview snippet), **Status** (active/archived).
- **Save/Publish:** validation summary on error; success toast + preview refresh; archive via
  `AlertDialog`. Autosave draft optional. Testids: `admin-product-editor`, `admin-product-save-button`,
  `admin-variant-row`, `admin-variant-add-button`, `admin-media-add-button`, `admin-media-set-primary`,
  `admin-seo-title-input`, `admin-product-preview-pane`.

### 11.5 Media Gallery / Library
- Grid of `media_assets` (thumbnail, kind badge image/video, alt, dimensions); upload tile (URL/
  reference in V1; real upload only after object-storage integration playbook). Select mode returns to
  editor. Testids: `admin-media-library`, `admin-media-tile`, `admin-media-upload-input`.

### 11.6 Order Processing
- Order detail: item snapshots, address, payment info + proofs, status timeline. Status change via
  `Select`/buttons that call the **guarded** transition (illegal option disabled/hidden; illegal
  attempt → toast 400). Cancel → `AlertDialog` (warns stock restore). Testids: `admin-order-detail`,
  `admin-orders-status-select`, `admin-order-cancel-button`, `admin-payment-verify-button`.

### 11.7 Config & Settings
- Shipping methods & rates, payment methods & fees (tables + inline edit), store settings singleton
  (Form: store name, currency, cod_fee, free-ship threshold, support phone/email, socials, SEO
  defaults). Numeric bounds enforced. Testids: `admin-settings-form`, `admin-shipping-table`,
  `admin-payment-methods-table`, `admin-settings-save-button`.

---

## 12. Growth UX (E7)

- **SEO (invisible UX):** correct `<head>` meta + JSON-LD from `seo` fields; sitemap. No visual UI, but
  accurate share previews (OG) and rich results.
- **WhatsApp button:** floating/inline "Chat via WhatsApp" (lucide `message-circle`) building a
  `wa.me` deep link prefilled with cart/order context; brand-neutral accent (not raw green).
  `data-testid="wa-chat-button"`.
- **Live chat widget:** floating launcher bottom-right (above mobile bottom-nav); panel shows a short
  intro + current cart summary chip; provider SDK only via integration playbook, fallback = WA link.
  Scoped so it never leaks into admin. `data-testid="chat-widget-launcher"`, `chat-widget-panel`.
- **Analytics dashboard (admin):** funnel (page_view→product_view→add_to_cart→begin_checkout→purchase)
  as a horizontal step chart; top products `Table`; conversion rate metric card. Read-only, admin-gated.
  Testids: `admin-analytics`, `admin-analytics-funnel`, `admin-analytics-conversion`.
- **CTA system:** consistent primary CTAs (add-to-cart, checkout, claim voucher) with full state
  coverage (hover/focus/active/disabled/loading); above-the-fold on PDP + sticky on mobile.

---

## 13. Responsive Matrix

| Surface | Mobile (<640) | Tablet (640–1024) | Desktop (≥1024) |
|---------|---------------|-------------------|-----------------|
| Home | 1-col stacked; bottom-nav; hero 92vh | 2-col media grid | 12-col editorial grid |
| Shop/PLP | filter `Sheet` (bottom); grid 2-col | 3-col grid | sidebar + 4-col grid |
| PDP | swipe gallery + sticky ATC bar | 2-col compact | sticky gallery + info |
| Cart/Checkout | single column; summary at bottom | 1–2 col | content + sticky summary |
| Account | top `Tabs`/accordion | 2-col | left nav + content |
| Admin | topbar + sidebar `Sheet` | collapsible sidebar | fixed sidebar + content |
| Chat/WA | above bottom-nav | corner | corner |

Touch targets ≥ 44×44px on mobile. Tables scroll horizontally with a hint on small screens.

---

## 14. Component Inventory (Shadcn mapping)

| Need | Shadcn component |
|------|------------------|
| Buttons/CTAs | `button` |
| Cards/metrics | `card` |
| Nav/tabs | `tabs`, `navigation-menu`, `breadcrumb` |
| Drawers/panels | `sheet`, `drawer`, `dialog`, `alert-dialog` |
| Forms | `form`, `input`, `textarea`, `select`, `checkbox`, `radio-group`, `switch`, `slider`, `label` |
| Tables/lists | `table`, `pagination`, `scroll-area` |
| Feedback | `sonner` (toasts), `alert`, `tooltip`, `popover`, `skeleton`, `progress`, `badge` |
| Catalog/gallery | `carousel` (Embla), `accordion`, `aspect-ratio`, `avatar` |
| Commands/search | `command`, `input` |

No native HTML dropdown/select/toast/calendar — always the Shadcn equivalent.

---

## 15. Per-Epic UX Mapping

| Epic | Primary screens | Key components | New testids (samples) |
|------|-----------------|----------------|-----------------------|
| E1 Catalog | Home, Shop/PLP, PDP | ProductCard, carousel, filters, gallery, accordion | `product-card`, `plp-sort-select`, `pdp-variant-option`, `shop-grid-empty` |
| E2 Vouchers | Voucher Center, Checkout voucher | voucher card, input+apply | `voucher-card`, `checkout-voucher-apply-button` |
| E3 Cart/Checkout | Cart, Cart Drawer, Checkout, Success | steppers, Tabs, RadioGroup, sticky summary | `cart-item-qty-input`, `checkout-place-order-button`, `order-success-code` |
| E4 Account | /akun (Profil/Pesanan/Alamat/Wishlist) | Tabs, Form, Dialog, AlertDialog, Badge | `account-address-add-button`, `order-history-row` |
| E5 Admin | /admin/* shell, dashboard, editors, tables | sidebar, Table, two-pane editor, live preview | `admin-product-editor`, `admin-orders-status-select` |
| E6 Payments | instructions, proof form, timeline, admin verify | stepper, Form, image preview | `payment-proof-submit-button`, `order-status-timeline` |
| E7 Growth | WA button, chat widget, analytics dashboard | launcher, funnel chart, metric cards | `wa-chat-button`, `admin-analytics-funnel` |
| E8 Hardening | all (a11y/perf pass) | — | audit only |

---

## 16. UX Definition of Done (per screen)

- [ ] Loading (skeleton), Empty (with action), Error (with retry), Success states implemented.
- [ ] All interactive/critical elements have unique kebab-case `data-testid`.
- [ ] Responsive at mobile/tablet/desktop per §13; touch targets ≥ 44px on mobile.
- [ ] Keyboard-navigable; `focus-visible` ring; ARIA on custom widgets; contrast ≥ 4.5:1.
- [ ] Motion respects `prefers-reduced-motion`; no `transition: all`; transform/opacity only.
- [ ] Uses Shadcn components + design tokens only; no raw colors, no emoji icons.
- [ ] `scripts/check_nav_map.py` (no dead links) + `scripts/ux_audit.py --strict` pass.
