// services/orders.js — SSOT klien Checkout & Orders (Epic E3).
// Diskon & total dihitung SERVER (compute_pricing). FE tidak menghitung total final.
import apiClient, { API, asArray } from './apiClient';
import { bottleImage } from '../lib/bottleArt';

// Map item keranjang (camelCase) -> payload backend (snake_case). SKU = identitas utama.
const mapItems = (items) =>
  (items || []).map((i) => ({
    product_id: i.productId || i.product_id,
    sku: i.sku ?? null,
    variant_type: i.variantType ?? i.variant_type ?? '',
    volume_ml: i.volumeMl != null ? Number(i.volumeMl) : (i.volume_ml != null ? Number(i.volume_ml) : null),
    quantity: Math.max(1, Math.round(Number(i.quantity) || 1)),
  }));

// Derive gambar botol bila snapshot item tak punya image (parity storefront).
export const orderItemImage = (it) => {
  if (it.image) return it.image;
  return bottleImage({
    name: it.name,
    concentration: it.concentration,
    category: it.category,
    variant: 0,
  });
};

export const normalizeOrder = (o) => {
  if (!o) return null;
  return {
    ...o,
    items: (o.items || []).map((it) => {
      const options = it.options || {};
      const label = Object.values(options).filter(Boolean).join(' / ');
      return {
        ...it,
        image: orderItemImage(it),
        variantType: it.variant_type || '',
        variantLabel: label || [it.variant_type, it.volume_ml ? `${it.volume_ml}ml` : ''].filter(Boolean).join(' · '),
        options,
        volumeMl: it.volume_ml,
        unitPrice: it.unit_price,
        key: it.sku ? `${it.product_id}-${it.sku}` : `${it.product_id}-${it.variant_type || ''}-${it.volume_ml}`,
      };
    }),
  };
};

// POST /api/orders -> Order  (409 stok; 400 input/voucher). Melempar error dgn .response.
export const createOrder = async ({ items, address, shippingId, payment, voucherCode = null, note = '' }) => {
  const res = await apiClient.post(`${API}/orders`, {
    items: mapItems(items),
    address,
    shipping_id: shippingId,
    payment,
    voucher_code: voucherCode || null,
    note: note || '',
  });
  return normalizeOrder(res.data);
};

// GET /api/orders -> [Order,...] (milik user; butuh login)
export const fetchOrders = async () => {
  const res = await apiClient.get(`${API}/orders`);
  return asArray(res.data).map(normalizeOrder);
};

// GET /api/orders/{code} -> Order (pemilik / guest by code)
export const fetchOrder = async (code) => {
  const res = await apiClient.get(`${API}/orders/${encodeURIComponent(code)}`);
  return normalizeOrder(res.data);
};

// POST /api/orders/{code}/cancel -> Order (pemilik; pending/paid/packed -> cancelled)
export const cancelOrder = async (code) => {
  const res = await apiClient.post(`${API}/orders/${encodeURIComponent(code)}/cancel`);
  return normalizeOrder(res.data);
};

// Label status pesanan (Bahasa Indonesia) + warna badge.
export const ORDER_STATUS_LABEL = {
  pending: 'Menunggu Pembayaran',
  paid: 'Sudah Dibayar',
  packed: 'Sedang Dikemas',
  shipped: 'Dalam Pengiriman',
  completed: 'Selesai',
  cancelled: 'Dibatalkan',
};

export const PAYMENT_STATUS_LABEL = {
  belum_bayar: 'Belum Bayar',
  dp: 'DP / Sebagian',
  lunas: 'Lunas',
};

export const CANCELLABLE = new Set(['pending', 'paid', 'packed']);

// ---- Bukti bayar (Epic E6) — owner-scoped ----
// POST /api/orders/{code}/payment-proof {amount, ref?, image_url?} -> PaymentProof
export const submitPaymentProof = async (code, { amount, ref = null, image_url = null }) => {
  const res = await apiClient.post(`${API}/orders/${encodeURIComponent(code)}/payment-proof`, {
    amount: Number(amount) || 0, ref: ref || null, image_url: image_url || null,
  });
  return res.data;
};

// GET /api/orders/{code}/payment-proofs -> [PaymentProof,...]
// Unggah FOTO bukti transfer (E20) — berkas nyata, disimpan lokal di server.
// Kembalikan {url} untuk dikirim sebagai image_url pada submitPaymentProof.
export const uploadPaymentProofImage = async (code, file, onProgress) => {
  const fd = new FormData();
  fd.append('file', file);
  const res = await apiClient.post(
    `${API}/orders/${encodeURIComponent(code)}/payment-proof/upload`, fd, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 300000,
      onUploadProgress: (e) => {
        if (!onProgress) return;
        const total = e.total || file.size || 1;
        onProgress(Math.min(99, Math.round((e.loaded / total) * 100)));
      },
    },
  );
  return res.data;
};

export const fetchPaymentProofs = async (code) => {
  const res = await apiClient.get(`${API}/orders/${encodeURIComponent(code)}/payment-proofs`);
  return asArray(res.data);
};

export const PROOF_STATUS_LABEL = {
  pending: 'Menunggu Verifikasi',
  verified: 'Terverifikasi',
  rejected: 'Ditolak',
};
