// services/config.js — SSOT konfigurasi toko (ongkir, pembayaran, settings) — Epic E3.
// Data dari backend seeded (BUKAN gateway eksternal). FE tidak lagi memakai konstanta statis.
import apiClient, { API, asArray } from './apiClient';

// GET /api/shipping-methods -> [{id,name,eta,price}]
export const fetchShippingMethods = async () => {
  const res = await apiClient.get(`${API}/shipping-methods`);
  return asArray(res.data);
};

// GET /api/payment-methods -> [{id,group,name,extra,fee}]  (dikelompokkan by group)
export const fetchPaymentMethods = async () => {
  const res = await apiClient.get(`${API}/payment-methods`);
  const list = asArray(res.data);
  const grouped = { transfer: [], ewallet: [], cod: [] };
  list.forEach((m) => {
    if (grouped[m.group]) grouped[m.group].push(m);
  });
  return { list, grouped };
};

// GET /api/settings -> {store_name, currency, cod_fee, ...}
export const fetchSettings = async () => {
  const res = await apiClient.get(`${API}/settings`);
  return res.data || {};
};
