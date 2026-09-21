// store/CatalogContext.js — cache katalog storefront (produk + taksonomi) sekali muat.
// Menjaga SATU ruang-id (prd_) konsisten lintas halaman (Home, Wishlist, Search,
// CategoryGrid, rekomendasi). ShopPage tetap query server-side sendiri untuk filter.
// `ready` dipakai oleh SplashScreen sebagai gate prefetch awal.
import React, { createContext, useContext, useEffect, useState, useCallback } from 'react';
import { fetchProducts, fetchCategories, fetchOccasions, fetchCharacters } from '../services/catalog';

const CatalogContext = createContext(null);

export const CatalogProvider = ({ children }) => {
  const [products, setProducts] = useState([]);
  const [categories, setCategories] = useState([]);
  const [occasions, setOccasions] = useState([]);
  const [characters, setCharacters] = useState([]);
  const [loading, setLoading] = useState(true);
  const [ready, setReady] = useState(false);
  const [error, setError] = useState(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    // Retry beberapa kali: cegah homepage "kosong" saat request awal ter-abort
    // (mis. Cloudflare challenge / navigasi awal). Grid produk tidak boleh hilang
    // hanya karena kegagalan transien.
    const MAX_ATTEMPTS = 3;
    for (let attempt = 1; attempt <= MAX_ATTEMPTS; attempt += 1) {
      try {
        const [p, c, occ, ch] = await Promise.all([
          fetchProducts({ limit: 100 }),
          fetchCategories(),
          fetchOccasions(),
          fetchCharacters(),
        ]);
        setProducts(p.items);
        setCategories(c);
        setOccasions(occ);
        setCharacters(ch);
        setError(null);
        setLoading(false);
        setReady(true);
        return;
      } catch (e) {
        if (attempt === MAX_ATTEMPTS) {
          setError('Gagal memuat katalog. Coba muat ulang.');
          setLoading(false);
          setReady(true); // jangan tahan splash selamanya bila API gagal total
          return;
        }
        // backoff singkat sebelum mencoba lagi
        await new Promise((r) => setTimeout(r, 400 * attempt));
      }
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const value = {
    products,
    categories,
    occasions,
    characters,
    loading,
    ready,
    error,
    refetch: load,
    getBySlug: (slug) => products.find((p) => p.slug === slug) || null,
    getById: (id) => products.find((p) => p.id === id) || null,
    getRelated: (id, limit = 4) => products.filter((p) => p.id !== id).slice(0, limit),
  };

  return <CatalogContext.Provider value={value}>{children}</CatalogContext.Provider>;
};

export const useCatalog = () => {
  const ctx = useContext(CatalogContext);
  if (!ctx) throw new Error('useCatalog must be used within CatalogProvider');
  return ctx;
};
