// services/apiClient.js — SSOT klien HTTP Collector Parfum.
// Semua panggilan API HARUS lewat modul ini (jangan fetch mentah / hardcode URL).
// Kontrak: respons BE = ARRAY/OBJEK telanjang; token field = 'token' (prefiks sess_).
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || '';

// API selalu berprefiks /api (Kubernetes ingress). JANGAN hardcode host.
export const API = `${BACKEND_URL}/api`;

const apiClient = axios.create({
  baseURL: API,
  headers: { 'Content-Type': 'application/json' },
  timeout: 20000,
});

const TOKEN_KEY = 'cp:token:v1';

// Pasang / hapus token sesi secara global (Authorization: Bearer sess_...).
export const setAuthToken = (token) => {
  if (token) {
    apiClient.defaults.headers.common.Authorization = `Bearer ${token}`;
    try { localStorage.setItem(TOKEN_KEY, token); } catch (e) { /* ignore */ }
  } else {
    delete apiClient.defaults.headers.common.Authorization;
    try { localStorage.removeItem(TOKEN_KEY); } catch (e) { /* ignore */ }
  }
};

export const getStoredToken = () => {
  try { return localStorage.getItem(TOKEN_KEY); } catch (e) { return null; }
};

// Restore token saat app dimuat ulang.
const _existing = getStoredToken();
if (_existing) setAuthToken(_existing);

// Guard array — selalu pakai untuk endpoint list (respons = ARRAY telanjang).
export const asArray = (data) => (Array.isArray(data) ? data : []);

export default apiClient;
