// services/vouchers.js — SSOT klien voucher (Epic E2).
// Diskon SELALU dari server (POST /api/vouchers/validate). FE TIDAK menghitung diskon lokal.
import apiClient, { API, asArray } from './apiClient';

// Map item keranjang (camelCase) -> payload backend (snake_case) untuk evaluasi scope.
const mapItems = (items) =>
  (items || []).map((i) => ({
    product_id: i.productId || i.product_id || null,
    category: i.category || null,
    unit_price: Math.max(0, Math.round(Number(i.unitPrice ?? i.unit_price ?? 0))),
    quantity: Math.max(0, Math.round(Number(i.quantity ?? 0))),
  }));

// POST /api/vouchers/validate -> {valid, code, type, value, discount, label, min_spend, reason?}
export const validateVoucher = async ({ code, subtotal = 0, shipping = 0, items = [], userId = null } = {}) => {
  const res = await apiClient.post(`${API}/vouchers/validate`, {
    code: String(code || '').trim(),
    subtotal: Math.max(0, Math.round(Number(subtotal) || 0)),
    shipping: Math.max(0, Math.round(Number(shipping) || 0)),
    user_id: userId,
    items: mapItems(items),
  });
  return res.data;
};

// GET /api/vouchers -> [Voucher,...] (aktif & belum kedaluwarsa) untuk Voucher Center.
export const fetchVouchers = async () => {
  const res = await apiClient.get(`${API}/vouchers`);
  return asArray(res.data);
};

// Label tampilan nilai voucher (metadata voucher — BUKAN diskon terhitung).
export const voucherValueLabel = (v) => {
  if (!v) return '';
  if (v.type === 'percent') return `${v.value}%`;
  if (v.type === 'free_shipping') return 'Gratis Ongkir';
  return 'Rp ' + (Number(v.value) || 0).toLocaleString('id-ID');
};
