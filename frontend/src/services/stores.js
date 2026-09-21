// services/stores.js — SSOT klien Lokasi Toko + Google Reviews.
// Publik: fetchStores / fetchStoreReviews. Admin (/api/admin/*): CRUD lokasi & ulasan + config.
import apiClient, { API, asArray } from './apiClient';

// ---------------- Publik ----------------
// GET /api/stores -> { locations:[...], config:{maps_mode, reviews_source, maps_api_key?, rating, intro} }
export const fetchStores = async () => {
  const res = await apiClient.get(`${API}/stores`);
  const d = res.data || {};
  return { locations: asArray(d.locations), config: d.config || {} };
};

// GET /api/store-reviews -> { source, summary:{avg,count}, reviews:[...] }
export const fetchStoreReviews = async () => {
  const res = await apiClient.get(`${API}/store-reviews`);
  const d = res.data || {};
  return { source: d.source || 'manual', summary: d.summary || { avg: 0, count: 0 }, reviews: asArray(d.reviews) };
};

// ---------------- Admin: Lokasi ----------------
export const listStoreLocations = async () => (await apiClient.get(`${API}/admin/store-locations`)).data;
export const createStoreLocation = async (body) => (await apiClient.post(`${API}/admin/store-locations`, body)).data;
export const updateStoreLocation = async (id, body) => (await apiClient.put(`${API}/admin/store-locations/${id}`, body)).data;
export const deleteStoreLocation = async (id) => (await apiClient.delete(`${API}/admin/store-locations/${id}`)).data;

// ---------------- Admin: Ulasan kurasi ----------------
export const listStoreReviews = async () => (await apiClient.get(`${API}/admin/store-reviews`)).data;
export const createStoreReview = async (body) => (await apiClient.post(`${API}/admin/store-reviews`, body)).data;
export const updateStoreReview = async (id, body) => (await apiClient.put(`${API}/admin/store-reviews/${id}`, body)).data;
export const deleteStoreReview = async (id) => (await apiClient.delete(`${API}/admin/store-reviews/${id}`)).data;

// ---------------- Admin: Config maps & reviews ----------------
export const getStoreConfig = async () => (await apiClient.get(`${API}/admin/store-config`)).data;
export const updateStoreConfig = async (body) => (await apiClient.put(`${API}/admin/store-config`, body)).data;
