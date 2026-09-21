// services/auth.js — SSOT klien auth (fondasi + E3).
// Token 'sess_' dipasang global via apiClient.setAuthToken (persist localStorage).
import apiClient, { API, setAuthToken } from './apiClient';

// POST /api/auth/login -> {token, user}
export const login = async (email, password) => {
  const res = await apiClient.post(`${API}/auth/login`, { email, password });
  if (res.data?.token) setAuthToken(res.data.token);
  return res.data.user;
};

// POST /api/auth/register -> {token, user}
export const register = async ({ name, email, password, phone = null }) => {
  const res = await apiClient.post(`${API}/auth/register`, { name, email, password, phone });
  if (res.data?.token) setAuthToken(res.data.token);
  return res.data.user;
};

// GET /api/auth/me -> user (butuh Bearer)
export const fetchMe = async () => {
  const res = await apiClient.get(`${API}/auth/me`);
  return res.data;
};

export const logout = () => setAuthToken(null);
