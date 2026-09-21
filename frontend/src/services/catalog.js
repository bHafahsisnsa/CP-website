// services/catalog.js — SSOT read-path katalog (Epic E1).
// Semua panggilan API katalog lewat modul ini. Respons BE = ARRAY/OBJEK telanjang.
// Normalisasi snake_case -> camelCase yang dibaca komponen storefront, dan derivasi
// gambar botol (SVG generatif) bila API tidak mengirim images (parity 100% dgn UI lama).
import apiClient, { API, asArray } from './apiClient';
import { bottleImage } from '../lib/bottleArt';
import { moodBoard } from '../lib/moodArt';
import { CATEGORY_IMAGES_BY_SLUG } from '../lib/realImages';

// Derive 4 varian bottle-art deterministik (identik dgn storefront lama).
const deriveImages = (p) =>
  [0, 1, 2, 3].map((variant) =>
    bottleImage({ name: p.name, concentration: p.concentration, category: p.category, variant })
  );

export const normalizeProduct = (p) => {
  if (!p) return null;
  const images = Array.isArray(p.images) && p.images.length ? p.images : deriveImages(p);
  return {
    ...p,
    compareAtPrice: p.compare_at_price ?? null,
    priceMin: p.price_min ?? p.price ?? 0,
    priceMax: p.price_max ?? p.price ?? 0,
    compareAtMin: p.compare_at_min ?? null,
    compareAtMax: p.compare_at_max ?? null,
    bestSeller: !!p.best_seller,
    isNew: !!p.is_new,
    ratingAvg: typeof p.rating_avg === 'number' ? p.rating_avg : 0,
    ratingCount: p.rating_count ?? 0,
    videoUrl: p.video_url ?? null,
    tags: Array.isArray(p.tags) ? p.tags : [],
    occasions: Array.isArray(p.occasions) ? p.occasions : [],
    characters: Array.isArray(p.characters) ? p.characters : [],
    volumes: Array.isArray(p.volumes) ? p.volumes : [],
    options: Array.isArray(p.options) ? p.options : [],
    variants: Array.isArray(p.variants) ? p.variants : [],
    notes: p.notes || { top: [], heart: [], base: [] },
    performance: p.performance || {},
    seo: p.seo || {},
    images,
  };
};

export const normalizeCategory = (c) => {
  if (!c) return null;
  return {
    ...c,
    image:
      c.image ||
      CATEGORY_IMAGES_BY_SLUG[c.slug] ||
      moodBoard({ mood: c.slug, ratio: '3:4', clean: true, accentText: (c.name || '').toUpperCase() }),
  };
};

// GET /api/products — server-side filter/sort/paginate. Kembalikan { items, total }.
export const fetchProducts = async (params = {}) => {
  const res = await apiClient.get(`${API}/products`, { params });
  const header = res.headers && (res.headers['x-total-count'] || res.headers['X-Total-Count']);
  const items = asArray(res.data).map(normalizeProduct);
  const total = Number(header);
  return { items, total: Number.isFinite(total) ? total : items.length };
};

// GET /api/products/{slug} — detail (throw bila 404).
export const fetchProductBySlug = async (slug) => {
  const res = await apiClient.get(`${API}/products/${encodeURIComponent(slug)}`);
  return normalizeProduct(res.data);
};

// GET /api/categories — kategori aktif (image diturunkan bila kosong).
export const fetchCategories = async () => {
  const res = await apiClient.get(`${API}/categories`);
  return asArray(res.data).map(normalizeCategory);
};

// GET /api/occasions — facet MULTI "Shop by Occasion" (aktif, terurut order).
export const fetchOccasions = async () => {
  const res = await apiClient.get(`${API}/occasions`);
  return asArray(res.data);
};

// GET /api/characters — facet MULTI "Shop by Character" (aktif, terurut order).
export const fetchCharacters = async () => {
  const res = await apiClient.get(`${API}/characters`);
  return asArray(res.data);
};

// GET /api/reviews?product_id — ulasan published.
export const fetchReviews = async (productId) => {
  const res = await apiClient.get(`${API}/reviews`, {
    params: productId ? { product_id: productId } : {},
  });
  return asArray(res.data);
};
