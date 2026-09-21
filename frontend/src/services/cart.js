// services/cart.js — server cart opsional untuk user login (Epic E3).
// Guest tetap pakai localStorage (CartContext). Ini sinkron lintas-perangkat saat login.
import apiClient, { API } from './apiClient';

// GET /api/cart -> {items:[{product_id,volume_ml,quantity}], voucher_code, note}
export const getServerCart = async () => {
  const res = await apiClient.get(`${API}/cart`);
  return res.data || { items: [], voucher_code: null, note: '' };
};

// PUT /api/cart {items, voucher_code?, note?} -> Cart
export const saveServerCart = async ({ items = [], voucherCode = null, note = '' }) => {
  const res = await apiClient.put(`${API}/cart`, {
    items: (items || []).map((i) => ({
      product_id: i.productId || i.product_id,
      // Pertahankan dimensi tipe varian agar server cart konsisten dgn PDP/keranjang lokal.
      variant_type: String(i.variantType ?? i.variant_type ?? ''),
      volume_ml: Number(i.volumeMl ?? i.volume_ml),
      quantity: Math.max(1, Math.round(Number(i.quantity) || 1)),
    })),
    voucher_code: voucherCode || null,
    note: note || '',
  });
  return res.data;
};
