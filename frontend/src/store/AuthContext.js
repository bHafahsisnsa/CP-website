// store/AuthContext.js — status autentikasi global (Epic E3) + KETAHANAN SESI (INV-AUTH-01).
// Restore sesi dari token tersimpan (apiClient) via GET /api/auth/me saat mount.
//
// BUG-AUTH-01 (ditemukan 2026-08-03): dulu SETIAP kegagalan fetchMe() memanggil apiLogout(),
// sehingga blip jaringan / timeout / 502 saat pod restart MENGHAPUS token dan memaksa user
// (termasuk admin di tengah wizard impor) login ulang. Sekarang:
//   · token HANYA dihapus bila server MENOLAK secara definitif (401/403);
//   · kegagalan transient (offline, timeout, 5xx, 502 ingress) dicoba ulang dengan backoff
//     dan token DIPERTAHANKAN;
//   · setelah percobaan habis -> sessionError=true (UI menawarkan "Coba Lagi", bukan form login);
//   · pulih otomatis saat event `online` atau tab kembali terlihat.
import React, { createContext, useContext, useEffect, useState, useCallback, useRef } from 'react';
import { login as apiLogin, register as apiRegister, fetchMe, logout as apiLogout } from '../services/auth';
import { getStoredToken } from '../services/apiClient';

const AuthContext = createContext(null);

// Penolakan DEFINITIF dari server -> token memang tidak sah, baru boleh dihapus.
const AUTH_REJECT_STATUS = [401, 403];
const isAuthReject = (e) => AUTH_REJECT_STATUS.includes(Number(e?.response?.status));
// Backoff percobaan ulang untuk kegagalan TRANSIENT (offline / timeout / 502 / 503).
const RETRY_MS = [900, 2200, 4500];

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  // true = token ADA tapi server tak terjangkau (bukan sesi kedaluwarsa).
  const [sessionError, setSessionError] = useState(false);
  const alive = useRef(true);
  const timer = useRef(null);

  const restore = useCallback(async (attempt = 0) => {
    if (!getStoredToken()) {
      if (alive.current) { setUser(null); setSessionError(false); setLoading(false); }
      return;
    }
    try {
      const u = await fetchMe();
      if (!alive.current) return;
      setUser(u);
      setSessionError(false);
      setLoading(false);
    } catch (e) {
      if (!alive.current) return;
      if (isAuthReject(e)) {
        // Sesi benar-benar tidak sah/kedaluwarsa -> bersihkan token.
        apiLogout();
        setUser(null);
        setSessionError(false);
        setLoading(false);
        return;
      }
      // Transient: JANGAN hapus token. Coba ulang dulu.
      if (attempt < RETRY_MS.length) {
        timer.current = setTimeout(() => restore(attempt + 1), RETRY_MS[attempt]);
        return;
      }
      setSessionError(true);
      setLoading(false);
    }
  }, []);

  const retrySession = useCallback(() => {
    if (timer.current) clearTimeout(timer.current);
    setSessionError(false);
    setLoading(true);
    restore(0);
  }, [restore]);

  useEffect(() => {
    alive.current = true;
    restore(0);
    return () => {
      alive.current = false;
      if (timer.current) clearTimeout(timer.current);
    };
  }, [restore]);

  // Pulih otomatis begitu jaringan kembali / tab kembali aktif.
  useEffect(() => {
    if (!sessionError) return undefined;
    const again = () => { if (getStoredToken()) retrySession(); };
    const onVisible = () => { if (document.visibilityState === 'visible') again(); };
    window.addEventListener('online', again);
    document.addEventListener('visibilitychange', onVisible);
    return () => {
      window.removeEventListener('online', again);
      document.removeEventListener('visibilitychange', onVisible);
    };
  }, [sessionError, retrySession]);

  const login = useCallback(async (email, password) => {
    const u = await apiLogin(email, password);
    setUser(u);
    setSessionError(false);
    setLoading(false);
    return u;
  }, []);

  const register = useCallback(async (payload) => {
    const u = await apiRegister(payload);
    setUser(u);
    setSessionError(false);
    setLoading(false);
    return u;
  }, []);

  const logout = useCallback(() => {
    if (timer.current) clearTimeout(timer.current);
    apiLogout();
    setUser(null);
    setSessionError(false);
  }, []);

  const updateUser = useCallback((u) => setUser(u), []);

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        isAuthenticated: !!user,
        sessionError,
        retrySession,
        login,
        register,
        logout,
        updateUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
};
