// lib/brand.js — label merek untuk storefront.
//
// Katalog memuat produk yang "inspired by" merek luar (Hugo Boss, Bvlgari, Dior, ...).
// Menampilkan merek itu mentah-mentah bisa menyesatkan pembeli, jadi merek NON-RUMAH
// ditampilkan sebagai "Inspired by <merek>" (label & daftar merek rumah bisa diatur
// admin di Pengaturan > Toko). Merek rumah tetap tampil apa adanya.
//
// Catatan SEO: JSON-LD tetap memakai merek RUMAH (lihat houseBrandName) supaya data
// terstruktur tidak mengklaim merek pihak lain.

const DEFAULT_HOUSE = ['collector parfum', 'collector'];
const DEFAULT_LABEL = 'Inspired by';

const norm = (s) => String(s || '').trim().toLowerCase();

/** Daftar merek rumah (lowercase) dari settings, dengan fallback aman. */
export function houseBrandList(settings) {
  const raw = settings?.house_brands;
  const list = Array.isArray(raw) && raw.length ? raw : null;
  return (list || DEFAULT_HOUSE).map(norm).filter(Boolean);
}

/** Apakah merek ini milik toko sendiri? */
export function isHouseBrand(brand, settings) {
  const b = norm(brand);
  if (!b) return true;
  return houseBrandList(settings).includes(b);
}

/** Nama merek rumah untuk SEO/JSON-LD. */
export function houseBrandName(settings) {
  const raw = settings?.house_brands;
  if (Array.isArray(raw) && raw.length && String(raw[0] || '').trim()) return String(raw[0]).trim();
  return settings?.store_name || 'Collector Parfum';
}

/**
 * Label merek yang layak tampil.
 * @returns {{text: string, inspired: boolean}|null} null bila tak ada merek.
 */
export function brandLabel(brand, settings) {
  const b = String(brand || '').trim();
  if (!b) return null;
  const enabled = settings?.inspired_by_enabled !== false; // default ON
  if (!enabled || isHouseBrand(b, settings)) return { text: b, inspired: false };
  const label = String(settings?.inspired_by_label || DEFAULT_LABEL).trim() || DEFAULT_LABEL;
  return { text: `${label} ${b}`, inspired: true };
}

/** Versi ringkas untuk teks satu baris (mis. meta kartu produk). */
export function brandText(brand, settings) {
  const l = brandLabel(brand, settings);
  return l ? l.text : '';
}
