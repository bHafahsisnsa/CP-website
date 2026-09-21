// components/admin/import/importBulkFill.js
// Logika MURNI "Isi Harga Massal (Matriks Tier)".
//
// PENTING — kontrak ini adalah CERMIN 1:1 dari:
//   - backend  services/product_tiers.py  (extract_tier / dim_order / combo key)
//   - POC uji  scripts/test_tier_matrix_poc.py  (row_combo_key / apply_bulk_fill)
// Jangan ubah salah satunya tanpa yang lain, kalau tidak harga bisa masuk ke sel yang salah.

export const COMBO_KEY_SEP = '|';
export const OPTION_SLOTS = 4;

const SPLIT_RE = /[,;|/\n]+/;
const TIER_TOKEN_RE = /^\s*tier\s*(?:harga)?\s*[:\-]?\s*(.+?)\s*$/i;
const CODE_RE = /^\s*([A-Za-z]{1,6})\s*\[?\s*(\d{1,3})\s*\]?\s*$/;

const cleanTier = (raw) => {
  const s = String(raw ?? '').trim().replace(/\s+/g, ' ');
  if (!s) return '';
  const m = CODE_RE.exec(s);
  if (m) return `${m[1].toUpperCase()}${String(parseInt(m[2], 10)).padStart(2, '0')}`;
  return s.toUpperCase().slice(0, 40);
};

/** Ambil label tier dari satu nilai sel (mendukung daftar dipisah koma/pipe). */
export function extractTier(value) {
  const txt = String(value ?? '');
  if (!txt.trim()) return '';
  const tokens = txt.split(SPLIT_RE);
  for (const tok of tokens) {
    const m = TIER_TOKEN_RE.exec(tok);
    if (m) {
      const label = cleanTier(m[1]);
      if (label) return label;
    }
  }
  for (const tok of tokens) {
    const t = tok.trim();
    if (CODE_RE.test(t)) return cleanTier(t);
  }
  return '';
}

/** Pasangan {namaDimensi: nilai} satu baris — hanya pasangan yang terpetakan DAN berisi. */
export function rowPairs(row, mapping = {}) {
  const pairs = {};
  for (let i = 1; i <= OPTION_SLOTS; i += 1) {
    const nh = mapping[`option${i}_name`];
    const vh = mapping[`option${i}_value`];
    if (!nh || !vh) continue;
    const n = String(row?.[nh] ?? '').trim();
    const v = String(row?.[vh] ?? '').trim();
    if (n && v) pairs[n] = v;
  }
  return pairs;
}

/** Kunci kombinasi dimensi satu baris mengikuti urutan dimensi dari /tiers. */
export function rowComboKey(row, mapping, dimOrder = []) {
  const pairs = rowPairs(row, mapping);
  const names = Object.keys(pairs);
  if (names.length !== dimOrder.length) return null;
  if (dimOrder.some((n) => !(n in pairs))) return null;
  return dimOrder.map((n) => pairs[n]).join(COMBO_KEY_SEP);
}

/**
 * Dimensi EFEKTIF = pasangan option{i} yang terpetakan DAN benar-benar berisi nilai di data.
 * Memperbaiki chip yang dulu menulis "4 dimensi" untuk file 2 dimensi (option3/4 terpetakan
 * tetapi selnya kosong).
 */
export function effectiveDimensionNames(rows = [], mapping = {}, sample = 300) {
  for (const row of rows.slice(0, sample)) {
    const names = Object.keys(rowPairs(row, mapping));
    if (names.length) return names;
  }
  return [];
}

/** 'Rp 385.000' | '385,000' | 385000 -> 385000 (0 bila kosong/invalid). */
export function parseRupiah(value) {
  if (value === null || value === undefined || value === '') return 0;
  if (typeof value === 'number') return Math.trunc(value);
  const s = String(value).trim();
  const neg = s.startsWith('-');
  const digits = s.replace(/[^\d]/g, '');
  if (!digits) return 0;
  const n = parseInt(digits, 10);
  return Number.isNaN(n) ? 0 : (neg ? -n : n);
}

export const formatRupiah = (n) => (Number(n) > 0 ? Number(n).toLocaleString('id-ID') : '');

/**
 * Indeks agregat baris -> (tier, kombinasi). Dibangun SEKALI per (rows, mapping, dimOrder,
 * tierColumn) supaya pratinjau matriks tidak menyapu 6.426 baris tiap ketikan.
 */
export function buildFillIndex(rows = [], mapping = {}, dimOrder = [], tierColumn = null) {
  const counts = new Map();  // `${tier}\u0000${comboKey}` -> {total, zeroPrice}
  const priceH = mapping.variant_price;
  let noTier = 0;
  let noCombo = 0;
  for (const row of rows) {
    const tier = tierColumn ? extractTier(row?.[tierColumn]) : '';
    if (!tier) { noTier += 1; continue; }
    const key = rowComboKey(row, mapping, dimOrder);
    if (!key) { noCombo += 1; continue; }
    const k = `${tier}\u0000${key}`;
    const slot = counts.get(k) || { total: 0, zeroPrice: 0 };
    slot.total += 1;
    if (!priceH || parseRupiah(row?.[priceH]) <= 0) slot.zeroPrice += 1;
    counts.set(k, slot);
  }
  return { counts, noTier, noCombo, rows: rows.length };
}

/** Pratinjau dampak matriks tanpa menyentuh rows. */
export function previewFill(index, matrix = {}, overwritePrice = false) {
  const out = {
    willFill: 0, cellsUsed: 0, rowsWithoutCell: 0,
    noTier: index?.noTier || 0, noCombo: index?.noCombo || 0,
  };
  if (!index) return out;
  const seen = new Set();
  index.counts.forEach((slot, k) => {
    const sep = k.indexOf('\u0000');
    const tier = k.slice(0, sep);
    const key = k.slice(sep + 1);
    const cell = parseRupiah((matrix[tier] || {})[key]);
    if (cell > 0) {
      out.willFill += overwritePrice ? slot.total : slot.zeroPrice;
      seen.add(k);
    } else {
      out.rowsWithoutCell += slot.total;
    }
  });
  out.cellsUsed = seen.size;
  return out;
}

/** Jumlah sel matriks yang terisi angka > 0. */
export function countMatrixCells(matrix = {}) {
  let n = 0;
  Object.values(matrix).forEach((row) => {
    Object.values(row || {}).forEach((v) => { if (parseRupiah(v) > 0) n += 1; });
  });
  return n;
}

/** Matriks siap-kirim: {tier: {comboKey: number}} (hanya nilai > 0). */
export function numericMatrix(matrix = {}) {
  const out = {};
  Object.entries(matrix).forEach(([tier, row]) => {
    const bucket = {};
    Object.entries(row || {}).forEach(([key, v]) => {
      const n = parseRupiah(v);
      if (n > 0) bucket[key] = n;
    });
    if (Object.keys(bucket).length) out[tier] = bucket;
  });
  return out;
}

/**
 * Pratinjau dampak matriks memakai `cell_rows` dari GET /tiers
 * ({tier: {comboKey: {rows, zero}}}) — dihitung SERVER atas SEMUA baris.
 *
 * Kenapa bukan menyapu rows di browser: sejak E12 baris tidak lagi disimpan di
 * memori browser (dulu 6.426 baris ikut dikirim ulang tiap validasi dan menyebabkan
 * timeout "Gagal memvalidasi baris."). Angka pratinjau tetap eksak karena server
 * melaporkan jumlah baris per sel.
 */
export function previewFromCellRows(cellRows, matrix = {}, overwritePrice = false) {
  const out = { willFill: 0, cellsUsed: 0, rowsWithoutCell: 0 };
  if (!cellRows || typeof cellRows !== 'object') return out;
  Object.entries(cellRows).forEach(([tier, combos]) => {
    Object.entries(combos || {}).forEach(([key, stat]) => {
      const rows = Number(stat?.rows) || 0;
      const zero = Number(stat?.zero) || 0;
      const cell = parseRupiah((matrix[tier] || {})[key]);
      if (cell > 0) {
        out.willFill += overwritePrice ? rows : zero;
        out.cellsUsed += 1;
      } else {
        out.rowsWithoutCell += rows;
      }
    });
  });
  return out;
}

/**
 * Terapkan matriks + nilai kolom lain ke rows (IMMUTABLE — kembalikan array baru).
 *
 * DUA semantik berbeda (temuan POC, jangan disatukan):
 *   - fillIfEmpty : hanya mengisi sel yang kosong atau "0".
 *   - forceValues : SELALU menimpa. Wajib untuk Status, karena file klien sudah menulis
 *     `status=active` di semua baris sehingga mode "isi bila kosong" tak akan pernah
 *     membuat produk menjadi draft.
 */
export function applyBulkFill(rows, mapping, dimOrder, tierColumn, matrix, opts = {}) {
  const {
    overwritePrice = false,
    priceField = 'variant_price',
    fillIfEmpty = {},
    forceValues = {},
  } = opts;
  const priceH = mapping?.[priceField];
  const stats = {
    priceFilled: 0, noTier: 0, noCombo: 0, noCell: 0, filledIfEmpty: 0, forced: 0,
  };
  const fillEntries = Object.entries(fillIfEmpty)
    .filter(([, v]) => v !== '' && v !== null && v !== undefined);
  const forceEntries = Object.entries(forceValues)
    .filter(([, v]) => v !== '' && v !== null && v !== undefined);

  const out = (rows || []).map((row) => {
    const next = { ...row };
    for (const [canon, val] of fillEntries) {
      const h = mapping?.[canon];
      if (!h) continue;
      const cur = String(next[h] ?? '').trim();
      if (cur === '' || cur === '0') { next[h] = String(val); stats.filledIfEmpty += 1; }
    }
    for (const [canon, val] of forceEntries) {
      const h = mapping?.[canon];
      if (!h) continue;
      next[h] = String(val);
      stats.forced += 1;
    }
    if (!priceH) return next;
    const tier = tierColumn ? extractTier(next[tierColumn]) : '';
    if (!tier) { stats.noTier += 1; return next; }
    const key = rowComboKey(next, mapping, dimOrder);
    if (!key) { stats.noCombo += 1; return next; }
    const cell = parseRupiah((matrix?.[tier] || {})[key]);
    if (cell <= 0) { stats.noCell += 1; return next; }
    if (overwritePrice || parseRupiah(next[priceH]) <= 0) {
      next[priceH] = String(cell);
      stats.priceFilled += 1;
    }
    return next;
  });
  return { rows: out, stats };
}
