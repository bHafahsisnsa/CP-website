// components/admin/import/importConstants.js
// Konstanta pemetaan kolom impor produk (SSOT selaras services/product_import.CANONICAL_SPEC).
// Model VARIAN N-DIMENSI (Shopify-style): tiap dimensi = pasangan kolom option{i}_name/value
// (hingga 4 dimensi). Kolom legacy variant_type/variant_ml tetap didukung untuk file lama.
export const NONE = '__none__';
export const DISPLAY_CAP = 200;
export const OPTION_SLOTS = 4;

// Field kanonik + label + wajib + grup (agar UI pemetaan rapi & terkelompok).
export const CANON = [
  // --- Field produk ---
  { key: 'name', label: 'Nama Produk', req: true, group: 'product' },
  { key: 'category', label: 'Kategori (slug)', req: true, group: 'product' },
  { key: 'slug', label: 'Slug', group: 'product' },
  { key: 'brand', label: 'Merek', group: 'product' },
  { key: 'gender', label: 'Gender', group: 'product' },
  { key: 'concentration', label: 'Konsentrasi', group: 'product' },
  { key: 'description', label: 'Deskripsi', group: 'product' },
  { key: 'ingredients', label: 'Bahan', group: 'product' },
  { key: 'tags', label: 'Tag', group: 'product' },
  { key: 'occasions', label: 'Occasion (slug)', group: 'product' },
  { key: 'characters', label: 'Character (slug)', group: 'product' },
  { key: 'images', label: 'Gambar (URL)', group: 'product' },
  { key: 'video_url', label: 'Video URL', group: 'product' },
  { key: 'best_seller', label: 'Best Seller', group: 'product' },
  { key: 'is_new', label: 'Produk Baru', group: 'product' },
  { key: 'status', label: 'Status', group: 'product' },
  // --- Dimensi varian (N-dimensi, Shopify-style) ---
  { key: 'option1_name', label: 'Dimensi 1 — Nama', group: 'dimension' },
  { key: 'option1_value', label: 'Dimensi 1 — Nilai', group: 'dimension' },
  { key: 'option2_name', label: 'Dimensi 2 — Nama', group: 'dimension' },
  { key: 'option2_value', label: 'Dimensi 2 — Nilai', group: 'dimension' },
  { key: 'option3_name', label: 'Dimensi 3 — Nama', group: 'dimension' },
  { key: 'option3_value', label: 'Dimensi 3 — Nilai', group: 'dimension' },
  { key: 'option4_name', label: 'Dimensi 4 — Nama', group: 'dimension' },
  { key: 'option4_value', label: 'Dimensi 4 — Nilai', group: 'dimension' },
  // --- Harga & stok varian ---
  { key: 'variant_price', label: 'Harga', req: true, group: 'variant' },
  { key: 'variant_compare_at_price', label: 'Harga Coret', group: 'variant' },
  { key: 'variant_stock', label: 'Stok', group: 'variant' },
  { key: 'variant_sku', label: 'SKU', group: 'variant' },
  // --- Kompatibilitas file lama (opsional) ---
  { key: 'variant_type', label: 'Tipe Varian (lama)', group: 'legacy' },
  { key: 'variant_ml', label: 'Ukuran ml (lama)', group: 'legacy' },
];

export const LABEL = Object.fromEntries(CANON.map((c) => [c.key, c.label]));
export const REQUIRED = CANON.filter((c) => c.req).map((c) => c.key); // name, category, variant_price

// Grup untuk render mapping editor (urutan tetap).
export const GROUPS = [
  { id: 'product', title: 'Field Produk', hint: 'Info dasar produk (dikelompokkan per nama/slug).' },
  { id: 'dimension', title: 'Dimensi Varian (option1–4)', hint: 'Tiap dimensi = pasangan Nama + Nilai. Wajib ada dimensi ukuran (mis. "Ukuran" = 50ml).' },
  { id: 'variant', title: 'Harga & Stok Varian', hint: 'Nilai per baris varian.' },
  { id: 'legacy', title: 'Kompatibilitas File Lama (opsional)', hint: 'Isi hanya bila file memakai kolom variant_type/variant_ml.' },
];

// Pasangan kolom dimensi (option{i}_name/value).
export const OPTION_PAIRS = [1, 2, 3, 4].map((i) => ({
  idx: i, name: `option${i}_name`, value: `option${i}_value`,
}));

// Bangun kolom PREVIEW secara DINAMIS berdasarkan mapping aktif.
// Urutan: identitas produk (name, slug bila dipetakan, category) -> dimensi terpetakan
// (berurutan 1..4) -> legacy -> harga/stok/SKU. Kolom yang tidak dipetakan tidak ditampilkan
// supaya tabel tetap ringkas walau file punya 4 dimensi (max 8 kolom dimensi).
export function buildPreviewCols(mapping = {}) {
  const cols = ['name'];
  if (mapping.slug) cols.push('slug');
  cols.push('category');
  if (mapping.status) cols.push('status');
  for (const { name, value } of OPTION_PAIRS) {
    if (mapping[name] || mapping[value]) cols.push(name, value);
  }
  if (mapping.variant_type) cols.push('variant_type');
  if (mapping.variant_ml) cols.push('variant_ml');
  cols.push('variant_price');
  for (const k of ['variant_compare_at_price', 'variant_stock', 'variant_sku']) {
    if (mapping[k]) cols.push(k);
  }
  return cols;
}

// Apakah minimal SATU dimensi terpetakan (pasangan option lengkap) atau legacy ml?
// (Nilai ukuran > 0 tetap divalidasi backend per-baris.)
export function hasDimensionMapped(mapping = {}) {
  if (mapping.variant_ml) return true;
  return OPTION_PAIRS.some(({ name, value }) => mapping[name] && mapping[value]);
}

// Berapa pasangan dimensi option{i}_name+value yang terpetakan penuh (0..4).
export function mappedDimensionCount(mapping = {}) {
  return OPTION_PAIRS.filter(({ name, value }) => mapping[name] && mapping[value]).length;
}

// Pasangan dimensi yang HANYA sebagian terpetakan (name tanpa value, atau sebaliknya).
// Backend akan mengabaikannya — beri peringatan eksplisit ke admin.
export function partialDimensionPairs(mapping = {}) {
  return OPTION_PAIRS
    .filter(({ name, value }) => Boolean(mapping[name]) !== Boolean(mapping[value]))
    .map(({ idx, name, value }) => ({
      idx,
      missing: mapping[name] ? value : name,
      filled: mapping[name] ? name : value,
    }));
}
