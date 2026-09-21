# E1 — Catalog (Read-Path): Products, Categories, Reviews, Variants, Media, SEO

> Priority: **P0**. Depends on: Foundation (DONE). Unlocks: E2 (pricing needs products), E3 (checkout snapshots line items).
> Read first: `docs/03_DATA_MODEL.md`, `docs/04_API_CONTRACT.md`, `docs/09_THREAT_MODEL.md`, `memory/INVARIANTS.md`.

## 1. Epic Summary

Expose the perfume catalog to the storefront through real APIs and replace the frontend's local
`frontend/src/data/products.js` dummy source. This is the **read-path** only: no cart/checkout writes
yet. The catalog must support the store's editorial identity: multi-variant SKUs (volume 30/50/100 ml
with independent price + stock), rich media galleries (multiple images + optional video), notes
pyramid, rich descriptions/ingredients, and per-product SEO metadata. Correctness here is the
foundation for E2 pricing and E3 order snapshots, so the product shape must be stable and validated.

**Aha moment:** the live storefront (Home / Shop / PDP) renders from the backend with correct
variants, images, and filters — indistinguishable from the current polished dummy UI, but real.

## 2. Business Requirements

- **BR-1 Product listing:** `GET /api/products` returns active products with filtering by category,
  gender, concentration, price range, search `q`, plus sorting (newest, price asc/desc, best-seller)
  and pagination (`limit`/`skip`).
- **BR-2 Product detail:** `GET /api/products/{slug}` returns a full product incl. `volumes[]`,
  `notes` pyramid, `images[]`, optional `video_url`, `description`, `ingredients`, `performance`,
  `compare_at_price`, badges (`best_seller`, `is_new`), and `seo` meta.
- **BR-3 Categories:** `GET /api/categories` returns active categories (slug, name, desc, image) for
  Home + Shop filters.
- **BR-4 Reviews (read):** `GET /api/reviews?product_id=` returns published reviews (rating, quote,
  author, city) for PDP and testimonials. Rating aggregate (avg + count) available per product.
- **BR-5 Multi-variant integrity:** each product has ≥1 `volume`; every volume has `ml>0`, `price>0`,
  `stock>=0`. The PDP volume selector drives price; the default is the primary/first in-stock volume.
- **BR-6 Media:** gallery slider with ≥1 image; optional `video_url`. Missing media must degrade
  gracefully (placeholder), never 5xx.
- **BR-7 SEO metadata:** each product/category carries `seo = {title, description, keywords[],
  og_image?}`; used by E7 for meta tags. Sensible defaults derived from name/description if absent.
- **BR-8 Storefront wiring:** `HomePage`, `ShopPage`, `ProductDetailPage` fetch via
  `frontend/src/services/apiClient.js`; loading/empty/error states are explicit.

## 3. Scope & Non-Goals

**In scope:** read APIs for products/categories/reviews; product/category seeding from the existing
12 dummy products; storefront read wiring; SEO meta fields on documents; review read + aggregates.

**Non-goals (deferred):** writing reviews from customers (moderation UI is E5), admin CRUD (E5),
cart/checkout writes (E3), voucher math (E2), real image uploads to object storage (E5 media library),
render of SEO tags in `<head>` (E7). Video is a URL reference only (no transcoding/upload here).

## 4. Data Model

Extend `docs/03_DATA_MODEL.md` (additive-only). Collections: `products` (`prd_`), `categories`
(`cat_`), `reviews` (`rev_`).

```
products:
  id (prd_), slug (unique), name, brand, category (FK -> categories.slug),
  concentration in {EDP,EDT}, gender in {Pria,Wanita,Unisex},
  price (int > 0),                      # display/base price = primary volume price
  compare_at_price (int > 0 | null),    # strike-through; must be > price when set
  best_seller (bool), is_new (bool), tags[] (str),
  volumes[]: { ml (int > 0), price (int > 0), stock (int >= 0), sku? (str) },
  notes: { top[], heart[], base[] },
  description (str), ingredients (str | str[]),
  performance: { longevity, sillage, season },
  images[] (str url, >= 1), video_url? (str url),
  seo: { title, description, keywords[], og_image? },
  rating_avg (float 0..5, derived), rating_count (int >= 0, derived),
  status in {active, archived}, created_at (ISO UTC)

categories:
  id (cat_), slug (unique), name, desc, image?, seo?, active (bool)

reviews:
  id (rev_), product_id? (FK -> products.id), user_id?, name, city?,
  rating (int 1..5), quote, avatar?, status in {published, pending, hidden}, created_at
```

**Bounds (anti RC-E12):** every money/quantity field gets `ge/gt` in `backend/schemas.py`
(`price gt=0`, `stock ge=0`, `rating ge=1 le=5`). Register new collections in
`scripts/verify_contract.py` (CANONICAL) and `scripts/verify_schema.py` (id-prefix + enum + FK).

## 5. API Contract

All paths prefixed `/api`. Lists → bare arrays; detail → bare object (no `{items,total}` envelope).

```
GET /api/products?category&gender&concentration&min_price&max_price&q&sort&limit&skip
    -> [Product, ...]           # only status=active
GET /api/products/{slug}        -> Product        # 404 if not found/archived
GET /api/categories             -> [Category,...] # only active
GET /api/reviews?product_id     -> [Review,...]   # only status=published
```

`Product` response MUST include exactly the fields the FE reads (anti RC-F4 drift): `id, slug, name,
brand, category, concentration, gender, price, compare_at_price, best_seller, is_new, tags, volumes,
notes, description, ingredients, performance, images, video_url, seo, rating_avg, rating_count`.
Never return `password_hash` or internal-only fields. Sync this shape into `docs/04_API_CONTRACT.md`.

## 6. State Machine & Invariants

No order state machine in E1 (read-only). Catalog invariants (add to `memory/INVARIANTS.md` +
`scripts/verify_data_integrity.py`):

- **INV-4 (existing):** every `volume.stock >= 0` and product `price > 0`.
- **INV-C1 (new):** each product has `len(volumes) >= 1` and unique `ml` per product.
- **INV-C2 (new):** `compare_at_price` is null OR `> price` (no fake discounts — anti RC-E1).
- **INV-C3 (new):** `rating_avg` within 0..5 and equals mean of published reviews (cross-entity CE-R).
- **INV-8 (existing):** review `product_id` (when set) references an existing product (FK — RC-E5).

## 7. Execution Steps

1. **Docs first:** add `reviews` SEO/rating fields + product `video_url/ingredients/seo` to
   `docs/03_DATA_MODEL.md`; add the four endpoints to `docs/04_API_CONTRACT.md`.
2. **Schemas:** add/extend Pydantic models in `backend/schemas.py` with numeric bounds; add response
   models `ProductOut`, `CategoryOut`, `ReviewOut`.
3. **Seed:** extend `scripts/seed_data.py` to insert the 12 products (from `frontend/src/data/products.js`),
   6 categories, and a handful of published reviews — idempotent (upsert by slug/id).
4. **Service:** `backend/services/catalog.py` — query builders for filter/sort/paginate; rating
   aggregation helper; `safe_doc` projection.
5. **Router:** `backend/routers/catalog.py` — the four GET endpoints; register under `/api` in `server.py`.
6. **Gate wiring:** register `products/categories/reviews` in `verify_contract.py`, `verify_schema.py`,
   `verify_data_integrity.py` (INV-C1..C3), and add product/category checks to `health_check.py`.
7. **Frontend read wiring:** replace `data/products.js` reads in `HomePage`, `ShopPage`,
   `ProductDetailPage` with `apiClient` calls; keep component structure; add loading skeletons,
   empty states, and error retry. Guard arrays: `Array.isArray(res.data) ? res.data : []`.
8. **Testids:** ensure product cards, volume selector, gallery, filter/sort controls carry unique
   `data-testid`.
9. **Verify:** `bash scripts/gate.sh` GREEN; screenshot Home/Shop/PDP; then `testing_agent_v3`.

## 8. Best Practices

- Keep the current polished UI; only swap the data source. No visual regressions.
- Server-side filter/sort/paginate (never ship the whole catalog and filter in the browser).
- Bounded queries only — no unbounded `find()` (anti RC-E; `verify_architecture.py`/`fa_nplus1.py`).
- Compute `rating_avg`/`rating_count` from reviews (single source), don't store a hand-set number.
- Slugs are immutable public identifiers; archiving (soft-delete) instead of hard-delete keeps FKs valid.
- Money stays integer rupiah; formatting only in the FE (`lib/format.js`).

## 9. Bug Mitigation & Threat Mapping

| Threat | Risk in E1 | Mitigation |
|--------|-----------|------------|
| **RC-E5** FK dangling | review/product `category` points to missing entity | `verify_schema.py` FK + `verify_cross_entity.py` CE3; archive not delete |
| **RC-E11** adversarial → 5xx | weird `q`, huge `limit`, bad `sort` | Pydantic query validation; clamp `limit`; `verify_adversarial_5xx.py`, `fa_fuzz.py` |
| **RC-E13** FE dead menu / missing data | PDP reads a field BE doesn't return | contract parity in `docs/04`; `check_nav_map.py`; explicit empty/error states |
| **RC-E14** money as float | variant price drift | integer rupiah only; `verify_architecture.py` review |
| **RC-E1** fake discount drift | `compare_at_price <= price` | INV-C2 in `verify_data_integrity.py` |
| **RC-E16** orphan endpoint | catalog API without UI | `verify_delivery.py` D2; wire all endpoints into FE |

## 10. Guardrail Wiring

- **Static/data:** register collections in `scripts/verify_contract.py`, `scripts/verify_schema.py`;
  add INV-C1..C3 to `scripts/verify_data_integrity.py`.
- **Runtime:** extend `scripts/health_check.py` to assert `/api/products`, `/api/products/{slug}`,
  `/api/categories`, `/api/reviews` return correct shapes; `scripts/audit_endpoint_sweep.py` sweeps GETs.
- **Adversarial:** `scripts/guardrails/verify_adversarial_5xx.py`, `forensic/fa_fuzz.py`, `forensic/fa_5xx.py`
  cover the query params.
- **Cross-entity:** `scripts/verify_cross_entity.py` CE-R (rating aggregate vs reviews).
- **Delivery:** add products/categories/reviews endpoints + Shop/PDP pages as P0 in `memory/DELIVERY_MANIFEST.md`.
- **Meta:** `forensic/fa_mutation.py` stays 3/3 CAUGHT.

## 11. Test Plan

**Backend (curl / pytest):**
- list returns only active; filters (`category`, `gender`, `min/max_price`), sort variants, pagination.
- `GET /api/products/{slug}` 200 for active, 404 for archived/unknown.
- adversarial: `limit=999999`, `sort=DROP`, unicode/emoji `q` → 4xx/clamped, never 5xx.
- reviews list only `published`; `rating_avg` equals mean of published reviews.

**Frontend (screenshot + testing_agent_v3):** Home renders best-sellers/categories from API; Shop
filters/sorts/paginates; PDP shows gallery, volume selector switches price, notes pyramid, reviews;
loading skeletons + empty state + error retry all visible.

**Forensic:** `bash scripts/run_forensics.sh` — no HIGH/VULN; `fa_nplus1.py` flags no N+1 on list.

**Deviant-path (mandatory):** unknown slug, empty category, product with a zero-stock variant,
product with missing `video_url`/`compare_at_price`.

## 12. UI/UX Blueprint

> Full system: `docs/roadmap/UX_BLUEPRINT.md` §7 (storefront). Visual SSOT: `design_guidelines.md`.
> E1 keeps the current polished storefront visuals; only the **data source** changes to APIs, so every
> view must add explicit data-states.

**Screens & layout**
- **Home:** hero (headline tracking animation), category grid (`/api/categories`), best-sellers carousel
  (`/api/products?sort=best_seller`), testimonials (`/api/reviews`), FAQ accordion. Sections with no data
  hide gracefully (never blank frames).
- **Shop/PLP:** desktop sidebar filters + mobile filter `Sheet` (bottom); sort via `Select`; server-side
  filter/sort/paginate; "Muat lebih banyak" or pagination.
- **PDP:** sticky gallery (Embla, images + optional `video_url`) + info column; volume selector
  (`RadioGroup`/segmented) drives price (Azeret Mono); notes pyramid chips; accordion
  (Deskripsi/Ingredients/Ketahanan/Sillage/Pengiriman); reviews + rating aggregate; related carousel.

**Components (Shadcn):** `card`, `carousel`, `badge`, `accordion`, `dialog` (quick view), `select`,
`checkbox`, `slider`, `skeleton`, `aspect-ratio`. ProductCard = hover image-swap + quick view + wishlist heart.

**States (mandatory — UX_BLUEPRINT §3):** loading skeleton grid/cards; empty ("Tidak ada hasil / kategori
kosong" + reset/browse CTA); error + retry; out-of-stock variant disabled with "Stok habis" badge.

**Micro-interactions:** hover image-swap (crossfade 180ms), underline reveal on links/titles, scroll
reveals (stagger), reduced-motion disables marquee/rotation.

**Responsive:** grid 2/3/4-col (mobile/tablet/desktop); PDP swipe gallery on mobile; touch targets ≥44px.

**Accessibility:** one `h1` per page; `alt` on product images; volume selector ARIA; `focus-visible` ring;
contrast ≥4.5:1.

**Testids:** `product-card`, `product-card-quick-view-button`, `plp-filter-open-button`, `plp-sort-select`,
`shop-grid-loading`, `shop-grid-empty`, `pdp-gallery`, `pdp-variant-option`, `pdp-quantity-input`,
`pdp-add-to-cart-button`, `home-category-card`, `home-best-sellers`.

## 13. Definition of Done

- [x] Docs synced (`03`, `04`); INV-C1..C3 enforced by `verify_data_integrity.py`.
- [x] Four endpoints live, correct shapes, consumed by Home/Shop/PDP (no orphan — `verify_delivery.py` D2).
- [x] Seed idempotent with 12 products / 6 categories / sample reviews.
- [x] Adversarial query inputs never 5xx; N+1-free list.
- [x] `bash scripts/gate.sh` GREEN + `run_forensics.sh` clean + one `testing_agent_v3` pass (happy + deviant).
- [x] `memory/BUG_REGISTRY.md` updated (RC-E5/E11/E13/E14 → PREVENTED for catalog).
- [x] UI parity with current storefront; unique `data-testid` on catalog controls.
