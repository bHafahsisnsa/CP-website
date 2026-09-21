// services/admin.js — SSOT klien Admin Backoffice (Epic E5).
// Semua endpoint /api/admin/* butuh Bearer + role 'admin' (dipasang global via apiClient).
// Path DITULIS LITERAL agar terverifikasi verify_api_contract (FE↔BE).
import apiClient, { API } from './apiClient';

// ---- Dashboard ----
export const getDashboard = async () => (await apiClient.get(`${API}/admin/dashboard`)).data;

// ---- Produk ----
// Daftar produk admin — TER-PAGINASI (katalog bisa ribuan produk hasil impor massal).
// Total baris dibaca dari header X-Total-Count; kembalikan { items, total }.
export const listProducts = async ({ status = '', q = '', limit = 50, skip = 0 } = {}) => {
  const p = new URLSearchParams();
  if (status) p.set('status', status);
  if (q) p.set('q', q);
  if (limit) p.set('limit', String(limit));
  if (skip) p.set('skip', String(skip));
  const qs = p.toString();
  const res = await apiClient.get(`${API}/admin/products` + (qs ? `?${qs}` : ''));
  const header = res.headers && (res.headers['x-total-count'] || res.headers['X-Total-Count']);
  const items = Array.isArray(res.data) ? res.data : [];
  const total = Number(header);
  return { items, total: Number.isFinite(total) ? total : items.length };
};
export const getProduct = async (id) => (await apiClient.get(`${API}/admin/products/${id}`)).data;
export const createProduct = async (body) => (await apiClient.post(`${API}/admin/products`, body)).data;
export const updateProduct = async (id, body) => (await apiClient.put(`${API}/admin/products/${id}`, body)).data;
export const archiveProduct = async (id) => (await apiClient.delete(`${API}/admin/products/${id}`)).data;
export const restoreProduct = async (id) => (await apiClient.post(`${API}/admin/products/${id}/restore`)).data;

// Aksi massal status produk. Cakupan: {ids:[...]} ATAU {filterStatus, q}.
export const bulkProductStatus = async ({
  status, ids = [], filterStatus = null, q = '', confirmCount = null,
} = {}) => (await apiClient.post(`${API}/admin/products/bulk-status`, {
  status,
  ids,
  filter_status: filterStatus,
  q: q || null,
  confirm_count: confirmCount,
}, { timeout: 120000 })).data;

// ---- Kategori ----
export const listCategories = async () => (await apiClient.get(`${API}/admin/categories`)).data;
export const createCategory = async (body) => (await apiClient.post(`${API}/admin/categories`, body)).data;
export const updateCategory = async (id, body) => (await apiClient.put(`${API}/admin/categories/${id}`, body)).data;
export const deleteCategory = async (id) => (await apiClient.delete(`${API}/admin/categories/${id}`)).data;

// ---- Facet: Occasions ----
export const listOccasions = async () => (await apiClient.get(`${API}/admin/occasions`)).data;
export const createOccasion = async (body) => (await apiClient.post(`${API}/admin/occasions`, body)).data;
export const updateOccasion = async (id, body) => (await apiClient.put(`${API}/admin/occasions/${id}`, body)).data;
export const deleteOccasion = async (id) => (await apiClient.delete(`${API}/admin/occasions/${id}`)).data;

// ---- Facet: Characters ----
export const listCharactersAdmin = async () => (await apiClient.get(`${API}/admin/characters`)).data;
export const createCharacter = async (body) => (await apiClient.post(`${API}/admin/characters`, body)).data;
export const updateCharacter = async (id, body) => (await apiClient.put(`${API}/admin/characters/${id}`, body)).data;
export const deleteCharacter = async (id) => (await apiClient.delete(`${API}/admin/characters/${id}`)).data;

// ---- Voucher ----
export const listVouchers = async () => (await apiClient.get(`${API}/admin/vouchers`)).data;
export const createVoucher = async (body) => (await apiClient.post(`${API}/admin/vouchers`, body)).data;
export const updateVoucher = async (id, body) => (await apiClient.put(`${API}/admin/vouchers/${id}`, body)).data;
export const deleteVoucher = async (id) => (await apiClient.delete(`${API}/admin/vouchers/${id}`)).data;

// ---- Pesanan ----
export const listOrders = async (status = '') =>
  (await apiClient.get(`${API}/admin/orders` + (status ? `?status=${status}` : ''))).data;
export const getOrder = async (code) => (await apiClient.get(`${API}/admin/orders/${code}`)).data;
export const setOrderStatus = async (code, status) =>
  (await apiClient.put(`${API}/admin/orders/${code}/status`, { status })).data;

// ---- Ulasan ----
export const listReviews = async (status = '') =>
  (await apiClient.get(`${API}/admin/reviews` + (status ? `?status=${status}` : ''))).data;
export const setReviewStatus = async (id, status) =>
  (await apiClient.put(`${API}/admin/reviews/${id}/status`, { status })).data;

// ---- Konfigurasi: kurir / pembayaran / settings ----
export const listShipping = async () => (await apiClient.get(`${API}/admin/shipping-methods`)).data;
export const createShipping = async (body) => (await apiClient.post(`${API}/admin/shipping-methods`, body)).data;
export const updateShipping = async (id, body) => (await apiClient.put(`${API}/admin/shipping-methods/${id}`, body)).data;
export const deleteShipping = async (id) => (await apiClient.delete(`${API}/admin/shipping-methods/${id}`)).data;
export const listPayments = async () => (await apiClient.get(`${API}/admin/payment-methods`)).data;
export const createPayment = async (body) => (await apiClient.post(`${API}/admin/payment-methods`, body)).data;
export const updatePayment = async (id, body) => (await apiClient.put(`${API}/admin/payment-methods/${id}`, body)).data;
export const deletePayment = async (id) => (await apiClient.delete(`${API}/admin/payment-methods/${id}`)).data;
export const getSettings = async () => (await apiClient.get(`${API}/admin/settings`)).data;
export const updateSettings = async (body) => (await apiClient.put(`${API}/admin/settings`, body)).data;

// ---- Media library ----
export const listMedia = async () => (await apiClient.get(`${API}/admin/media`)).data;
export const addMedia = async (body) => (await apiClient.post(`${API}/admin/media`, body)).data;
export const deleteMedia = async (id) => (await apiClient.delete(`${API}/admin/media/${id}`)).data;

// ---- Users (read-only) ----
export const listUsers = async () => (await apiClient.get(`${API}/admin/users`)).data;

// ---- Verifikasi bukti bayar (Epic E6) ----
export const listPaymentProofs = async (status = '') =>
  (await apiClient.get(`${API}/admin/payments` + (status ? `?status=${status}` : ''))).data;
export const verifyPaymentProof = async (id, approve, note = null) =>
  (await apiClient.put(`${API}/admin/payments/${id}/verify`, { approve, note: note || null })).data;

// ---- Growth & Analytics (Epic E7) ----
export const getAnalytics = async (range = 30) =>
  (await apiClient.get(`${API}/admin/analytics` + (range ? `?range=${range}` : ''))).data;
export const getCrmSegments = async (type = '') =>
  (await apiClient.get(`${API}/admin/crm/segments` + (type ? `?type=${type}` : ''))).data;

// ---- Storefront CMS (Epic E9) ----
export const getContentSchema = async () =>
  (await apiClient.get(`${API}/admin/content/schema`)).data;
export const getContentAdmin = async () =>
  (await apiClient.get(`${API}/admin/content`)).data;
export const updateContentSection = async (key, data) =>
  (await apiClient.put(`${API}/admin/content/${key}`, { data })).data;
export const listContentRevisions = async (key) =>
  (await apiClient.get(`${API}/admin/content/${key}/revisions`)).data;
export const revertContentSection = async (key, payload) =>
  (await apiClient.post(`${API}/admin/content/${key}/revert`, payload)).data;

// ============ Media upload (E9+) ============
export const uploadMedia = async (file) => {
  const fd = new FormData();
  fd.append('file', file);
  return (await apiClient.post(`${API}/admin/uploads`, fd, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })).data;
};
export const listUploads = async () =>
  (await apiClient.get(`${API}/admin/uploads`)).data;

// ============ Ekspor / Impor Produk (Epic E10) ============
// Path DITULIS LITERAL (tanpa query di dalam backtick) agar lolos verify_api_contract.
const _filenameFromDisposition = (disposition, fallback) => {
  if (!disposition) return fallback;
  const m = /filename="?([^";]+)"?/i.exec(disposition);
  return m ? m[1].trim() : fallback;
};

const _downloadBlob = (blob, filename) => {
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  window.URL.revokeObjectURL(url);
};

// Unduh semua produk (1 baris/varian) sebagai CSV/XLSX.
export const exportProducts = async (format = 'csv') => {
  const res = await apiClient.get(`${API}/admin/products/io/export`, {
    params: { format }, responseType: 'blob', timeout: 60000,
  });
  const fallback = `produk_export.${format === 'xlsx' ? 'xlsx' : 'csv'}`;
  _downloadBlob(res.data, _filenameFromDisposition(res.headers['content-disposition'], fallback));
};

// Unduh template impor + panduan.
export const downloadTemplate = async (format = 'csv') => {
  const res = await apiClient.get(`${API}/admin/products/io/template`, {
    params: { format }, responseType: 'blob', timeout: 60000,
  });
  const fallback = `template_impor_produk.${format === 'xlsx' ? 'xlsx' : 'csv'}`;
  _downloadBlob(res.data, _filenameFromDisposition(res.headers['content-disposition'], fallback));
};

// ── Impor produk berbasis SESI (E12) ───────────────────────────────────────────
// Dulu wizard mengirim ULANG seluruh baris (katalog 6.426 baris = ~5,2 MB) pada SETIAP
// validasi dan menerima ~6,4 MB balik. Di koneksi normal itu melewati timeout dan admin
// melihat "Gagal memvalidasi baris." padahal filenya sah. Sekarang baris disimpan di
// sesi server: unggah SEKALI, lalu kirim `session_id` + perubahan kecil saja.
export const IMPORT_PREVIEW_LIMIT = 200;   // baris yang ditarik untuk tabel pratinjau
export const IMPORT_REPORT_LIMIT = 200;    // laporan per-baris yang dibawa ke UI
export const IMPORT_PRODUCT_LIMIT = 24;    // produk contoh untuk panel struktur
export const IMPORT_ERROR_LIMIT = 300;     // baris error yang bisa ditinjau/diperbaiki

// Pesan error yang JUJUR: bedakan timeout/jaringan dari penolakan server.
export const importErrorMessage = (err, fallback = 'Permintaan gagal.') => {
  if (err?.code === 'ECONNABORTED' || /timeout/i.test(err?.message || '')) {
    return 'Koneksi terlalu lambat / terputus sebelum server menjawab. Coba lagi — data unggahan Anda masih tersimpan di server.';
  }
  const detail = err?.response?.data?.detail;
  if (typeof detail === 'string' && detail) return detail;
  if (err?.response?.status === 404) return 'Sesi impor kedaluwarsa. Unggah ulang file untuk melanjutkan.';
  if (err?.response?.status === 413) return 'File terlalu besar untuk diunggah.';
  if (!err?.response) return 'Tidak dapat menghubungi server. Periksa koneksi Anda lalu coba lagi.';
  return fallback;
};

// Parse file (CSV/XLSX) -> {session_id, headers, suggested_mapping, total, preview_rows}.
// `light` (default) TIDAK menarik seluruh baris ke browser.
export const analyzeImport = async (file, { light = true, preview = IMPORT_PREVIEW_LIMIT } = {}) => {
  const fd = new FormData();
  fd.append('file', file);
  return (await apiClient.post(`${API}/admin/products/io/analyze`, fd, {
    headers: { 'Content-Type': 'multipart/form-data' },
    params: { include_rows: light ? 'false' : 'true', preview },
    timeout: 180000,
  })).data;
};

// Validasi -> {summary, reports_head, error_reports, products_head, products_total}.
export const validateImport = async ({
  sessionId = null, rows = null, mapping,
  reportLimit = IMPORT_REPORT_LIMIT, productLimit = IMPORT_PRODUCT_LIMIT,
  errorLimit = IMPORT_ERROR_LIMIT,
}) => (await apiClient.post(`${API}/admin/products/io/validate`, {
  session_id: sessionId, rows: rows || [], mapping,
  report_limit: reportLimit, product_limit: productLimit, error_limit: errorLimit,
}, { timeout: 120000 })).data;

// Struktur matriks harga massal -> {tier_column, tiers, dimensions, combos, cell_rows, summary}.
export const detectImportTiers = async ({ sessionId = null, rows = null, mapping, tierColumn = null }) =>
  (await apiClient.post(`${API}/admin/products/io/tiers`, {
    session_id: sessionId, rows: rows || [], mapping, tier_column: tierColumn,
  }, { timeout: 120000 })).data;

// Commit tulis produk. mode: 'add-only' | 'upsert'.
export const commitImport = async ({ sessionId = null, rows = null, mapping, mode }) =>
  (await apiClient.post(`${API}/admin/products/io/commit`, {
    session_id: sessionId, rows: rows || [], mapping, mode,
    report_limit: IMPORT_REPORT_LIMIT, error_limit: IMPORT_ERROR_LIMIT,
  }, { timeout: 300000 })).data;

// Jendela baris sesi untuk tabel pratinjau (berurutan atau indeks tertentu).
export const fetchImportRows = async (sessionId, { offset = 0, limit = IMPORT_PREVIEW_LIMIT, indexes = null } = {}) =>
  (await apiClient.get(`${API}/admin/products/io/session/${sessionId}/rows`, {
    params: indexes && indexes.length
      ? { indexes: indexes.join(','), limit: Math.min(limit, indexes.length) }
      : { offset, limit },
    timeout: 60000,
  })).data;

// Simpan hasil edit sel pratinjau (payload kecil).
export const patchImportCells = async (sessionId, cells) =>
  (await apiClient.post(`${API}/admin/products/io/session/${sessionId}/cells`,
    { cells }, { timeout: 120000 })).data;

// Terapkan matriks harga massal DI SERVER (UI cukup mengirim angka matriksnya).
export const applyImportFill = async (sessionId, spec) =>
  (await apiClient.post(`${API}/admin/products/io/session/${sessionId}/fill`,
    spec, { timeout: 180000 })).data;

// Buang sesi impor (ganti file / selesai).
export const closeImportSession = async (sessionId) =>
  (await apiClient.post(`${API}/admin/products/io/session/${sessionId}/close`,
    {}, { timeout: 30000 })).data;
