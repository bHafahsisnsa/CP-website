// services/account.js — SSOT klien Akun (profil, alamat, wishlist) — Epic E4.
// Semua owner-scoped di server (user_id dari sesi). Wishlist mengembalikan array id.
import apiClient, { API, asArray } from './apiClient';

// ---- Profil ----
export const updateProfile = async ({ name, phone }) => {
  const res = await apiClient.put(`${API}/account/profile`, { name, phone });
  return res.data;
};

// ---- Alamat ----
export const listAddresses = async () => asArray((await apiClient.get(`${API}/addresses`)).data);
export const createAddress = async (a) => (await apiClient.post(`${API}/addresses`, a)).data;
export const updateAddress = async (id, a) => (await apiClient.put(`${API}/addresses/${id}`, a)).data;
export const setDefaultAddress = async (id) => asArray((await apiClient.post(`${API}/addresses/${id}/default`)).data);
export const deleteAddress = async (id) => (await apiClient.delete(`${API}/addresses/${id}`)).data;

// ---- Wishlist (kembalikan array product_ids) ----
const ids = (data) => (data && Array.isArray(data.product_ids) ? data.product_ids : []);
export const getWishlist = async () => ids((await apiClient.get(`${API}/wishlist`)).data);
export const toggleWishlist = async (productId) => ids((await apiClient.post(`${API}/wishlist/toggle`, { product_id: productId })).data);
export const mergeWishlist = async (productIds) => ids((await apiClient.post(`${API}/wishlist/merge`, { product_ids: productIds })).data);
