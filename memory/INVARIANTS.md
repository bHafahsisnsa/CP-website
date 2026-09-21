# 📏 INVARIANTS — Collector Parfum

> Aturan kebenaran data yang **di-enforce** `scripts/verify_data_integrity.py` di DB clean-seed.
> "HTTP 200" bukan bukti — invarian inilah buktinya. Tambah invarian saat menambah fitur (docs/07 §7).

| ID | Invarian | Ranah | Status enforce |
|----|----------|-------|----------------|
| INV-1 | `order.subtotal == Σ(item.unit_price * item.quantity)` | orders | aktif (bila ada order) |
| INV-2 | `order.total == subtotal - discount + shipping.price + cod_fee` dan `total >= 0` | orders | aktif |
| INV-3 | `order.discount` konsisten dgn voucher (scope-aware): percent → `round(eligible*value/100)` (capped); flat → `min(value, eligible)`; eligible = subtotal item yg cocok scope (category/product_ids) atau seluruh subtotal bila tanpa scope | orders/vouchers | aktif (E3 scope-aware) |
| INV-4 | Produk: setiap `volume.stock >= 0` (anti-oversell) dan `price > 0` | products | aktif (bila ada produk) |
| INV-5 | `payment_status`: `paid==0→belum_bayar`; `0<paid<total→dp`; `paid>=total→lunas` | orders | aktif |
| INV-6 | `order.status ∈ {pending,paid,packed,shipped,completed,cancelled}` | orders | aktif |
| INV-7 | `order.code` UNIK (number-series `counters.orders`) | orders/counters | aktif |
| INV-8 | `order.items[].product_id` → `products.id` (FK) | orders/products | aktif (verify_schema) |
| INV-9 | `voucher.type ∈ {percent,flat,free_shipping}` dan `value > 0` (percent 1..100) | vouchers | aktif (E2) |
| INV-10 | `cod_fee > 0` hanya bila `payment.group == 'cod'` | orders | aktif |
| INV-11 | `shipping_methods.price >= 0` dan `payment_methods.fee >= 0` | config | aktif |
| INV-C1 | Setiap `product` punya `>= 1` volume & `ml` unik per produk | products | aktif (E1) |
| INV-C2 | `product.compare_at_price` NULL atau `> price` | products | aktif (E1) |
| INV-C3 | `product.rating_avg`/`rating_count` == mean/count review `published` (product_id) | products/reviews | aktif (E1) |
| INV-9b | `voucher.usage_limit/per_user_limit/used_count/min_spend >= 0` | vouchers | aktif (E2) |
| INV-R1 | `voucher_redemptions.voucher_code` → `vouchers.code` (FK) | redemptions | aktif bila ada redemption (E3) |
| INV-R2 | `voucher_redemptions.order_code` → `orders.code` (FK) | redemptions/orders | aktif (E3) |
| INV-R3 | `voucher_redemptions.discount >= 0` | redemptions | aktif (E2) |
| CE1 | `voucher.used_count == #orders pakai voucher == #voucher_redemptions` | vouchers/orders/redemptions | aktif penuh (E3) |
| INV-AUTH-01 | Token sesi di klien HANYA dihapus bila server menolak definitif (401/403). Kegagalan transient (offline/timeout/5xx/502) WAJIB dicoba ulang dengan token dipertahankan + UI menampilkan status pemulihan (bukan form login) | frontend/auth | aktif (`scripts/guardrails/verify_auth_resilience.py`, statik) |

## Rekonsiliasi koleksi (L1)
- Wajib berisi data pada seed fondasi: `users, categories, vouchers, shipping_methods, payment_methods, settings, counters`.
- Opsional di fondasi (diisi fase business-logic): `products, orders, addresses, reviews, wishlists, carts`.
- Koleksi alias TERLARANG harus KOSONG (mis. `items, cart, order, testimonials, customers, config`).

## Catatan derivasi (PRICING SSOT — Epic E2 IMPLEMENTED)
SSOT perhitungan berada di `backend/services/pricing.py` (PURE, integer). Diskon: `voucher_discount()`.
```
subtotal = Σ(unit_price*qty)
discount = voucher & subtotal>=min_spend ?
             percent: round(subtotal*value/100) capped subtotal
             flat:    min(value, subtotal)
             free_shipping: shipping_price (di-offset di total)
           : 0
cod_fee  = payment.group=='cod' ? cod_fee : 0
total    = max(0, subtotal - discount + shipping.price + cod_fee)
```
Checkout (E3), `services/vouchers.py::evaluate_voucher`, dan `verify_data_integrity.py` (INV-2/3)
SEMUA memanggil `compute_pricing`/`voucher_discount` yang sama — satu sumber kebenaran (anti RC-E1/E2).
Voucher `scope` (category/product_ids) & `per_user_limit`/window dievaluasi di `services/vouchers.py`;
redemption (used_count + `voucher_redemptions`) ditulis ATOMIK saat order dibuat (E3), bukan saat validate.
