// store/WishlistContext.js — wishlist HYBRID (Epic E4).
// Guest: localStorage. Login: sinkron ke server (GET/toggle) + MERGE guest→user saat login.
// API dipertahankan: { ids, has, toggle, clear } agar konsumen lama tak berubah.
import React, { createContext, useContext, useEffect, useMemo, useState, useCallback } from 'react';
import { useAuth } from './AuthContext';
import { getWishlist, toggleWishlist, mergeWishlist } from '../services/account';

const WishlistContext = createContext(null);
const STORAGE_KEY = 'cp:wishlist:v1';

const readLocal = () => {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch (e) {
    return [];
  }
};
const saveLocal = (ids) => {
  try { localStorage.setItem(STORAGE_KEY, JSON.stringify(ids)); } catch (e) {}
};
const clearLocal = () => {
  try { localStorage.removeItem(STORAGE_KEY); } catch (e) {}
};

export const WishlistProvider = ({ children }) => {
  const { isAuthenticated, loading } = useAuth();
  const [ids, setIds] = useState(readLocal);

  // Sinkronisasi saat status auth stabil: login→merge guest ke server; guest→localStorage.
  useEffect(() => {
    if (loading) return;
    let active = true;
    (async () => {
      if (isAuthenticated) {
        try {
          const local = readLocal();
          const server = local.length ? await mergeWishlist(local) : await getWishlist();
          if (active) { setIds(server); clearLocal(); }
        } catch (e) { /* pertahankan state saat ini bila gagal */ }
      } else if (active) {
        setIds(readLocal());
      }
    })();
    return () => { active = false; };
  }, [isAuthenticated, loading]);

  // Persist ke localStorage HANYA untuk guest.
  useEffect(() => {
    if (!loading && !isAuthenticated) saveLocal(ids);
  }, [ids, isAuthenticated, loading]);

  const toggle = useCallback((id) => {
    if (isAuthenticated) {
      setIds((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id])); // optimistic
      toggleWishlist(id).then((server) => setIds(server)).catch(() => {
        setIds((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id])); // rollback
      });
    } else {
      setIds((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]));
    }
  }, [isAuthenticated]);

  const clear = useCallback(() => {
    if (isAuthenticated) {
      const prev = ids;
      setIds([]);
      Promise.all(prev.map((id) => toggleWishlist(id))).catch(() => setIds(prev));
    } else {
      setIds([]);
    }
  }, [isAuthenticated, ids]);

  const value = useMemo(
    () => ({
      ids,
      has: (id) => ids.includes(id),
      toggle,
      clear,
    }),
    [ids, toggle, clear],
  );

  return <WishlistContext.Provider value={value}>{children}</WishlistContext.Provider>;
};

export const useWishlist = () => {
  const ctx = useContext(WishlistContext);
  if (!ctx) throw new Error('useWishlist must be used within WishlistProvider');
  return ctx;
};
