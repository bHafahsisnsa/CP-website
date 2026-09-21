// services/media.js — SSOT klien Media Manager (E20).
// Semua path DITULIS LITERAL agar terverifikasi verify_api_contract (FE<->BE).
import apiClient, { API } from './apiClient';

const UPLOAD_TIMEOUT = 300000; // 15MB di koneksi lambat butuh waktu

// ---------------- Folder ----------------
export const listFolders = async () =>
  (await apiClient.get(`${API}/admin/media/folders`)).data;

export const getFolderTree = async () =>
  (await apiClient.get(`${API}/admin/media/folders/tree`)).data;

export const createFolder = async (name, parentId = null) =>
  (await apiClient.post(`${API}/admin/media/folders`, {
    name, parent_id: parentId || null,
  })).data;

export const renameFolder = async (id, name) =>
  (await apiClient.patch(`${API}/admin/media/folders/${id}`, { name })).data;

export const moveFolder = async (id, parentId) =>
  (await apiClient.patch(`${API}/admin/media/folders/${id}`, {
    parent_id: parentId || null, move: true,
  })).data;

export const deleteFolder = async (id, cascade = false) =>
  (await apiClient.delete(`${API}/admin/media/folders/${id}`, {
    params: { cascade },
  })).data;

// ---------------- Aset ----------------
export const listAssets = async ({
  folderId = '', q = '', kind = '', sort = 'newest', page = 1, limit = 40,
  recursive = false,
} = {}) => {
  const params = { sort, page, limit };
  if (folderId) params.folder_id = folderId;
  if (q) params.q = q;
  if (kind) params.kind = kind;
  if (recursive) params.recursive = true;
  const res = await apiClient.get(`${API}/admin/media/assets`, { params });
  const d = res.data || {};
  return {
    items: Array.isArray(d.items) ? d.items : [],
    total: Number(d.total || 0),
    page: Number(d.page || 1),
    limit: Number(d.limit || limit),
  };
};

export const getAsset = async (id) =>
  (await apiClient.get(`${API}/admin/media/assets/${id}`)).data;

/** Upload satu berkas dengan progress (0-100). Kembalikan aset. */
export const uploadAsset = async (file, { folderId = null, alt = null, onProgress } = {}) => {
  const fd = new FormData();
  fd.append('files', file);
  if (folderId) fd.append('folder_id', folderId);
  if (alt) fd.append('alt', alt);
  const res = await apiClient.post(`${API}/admin/media/upload`, fd, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: UPLOAD_TIMEOUT,
    onUploadProgress: (e) => {
      if (!onProgress) return;
      const total = e.total || file.size || 1;
      onProgress(Math.min(99, Math.round((e.loaded / total) * 100)));
    },
  });
  const body = res.data || {};
  if (Array.isArray(body.uploaded) && body.uploaded.length) return body.uploaded[0];
  const err = (body.failed || [])[0];
  throw new Error(err?.error || 'Upload gagal.');
};

export const ingestUrl = async (url, { folderId = null, alt = null } = {}) =>
  (await apiClient.post(`${API}/admin/media/from-url`, {
    url, folder_id: folderId || null, alt: alt || null, download: true,
  }, { timeout: 120000 })).data;

export const updateAsset = async (id, patch) =>
  (await apiClient.patch(`${API}/admin/media/assets/${id}`, patch)).data;

export const moveAsset = async (id, folderId) =>
  (await apiClient.patch(`${API}/admin/media/assets/${id}`, {
    folder_id: folderId || null, move: true,
  })).data;

export const replaceAsset = async (id, file) => {
  const fd = new FormData();
  fd.append('file', file);
  return (await apiClient.post(`${API}/admin/media/assets/${id}/replace`, fd, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: UPLOAD_TIMEOUT,
  })).data;
};

export const deleteAsset = async (id) =>
  (await apiClient.delete(`${API}/admin/media/assets/${id}`)).data;

export const bulkDeleteAssets = async (ids) =>
  (await apiClient.post(`${API}/admin/media/assets/bulk-delete`, { ids },
    { timeout: 120000 })).data;

export const bulkMoveAssets = async (ids, folderId) =>
  (await apiClient.post(`${API}/admin/media/assets/bulk-move`, {
    ids, folder_id: folderId || null,
  }, { timeout: 120000 })).data;

export const getMediaStats = async () =>
  (await apiClient.get(`${API}/admin/media/stats`)).data;

// Unduh semua gambar ber-URL eksternal ke penyimpanan lokal + perbarui referensinya
// di produk, kategori, konten CMS, lokasi toko, dan metode pembayaran.
export const localizeExternalMedia = async () =>
  (await apiClient.post(`${API}/admin/media/maintenance/localize`, {},
    { timeout: 600000 })).data;

export const migrateMediaLegacy = async () =>
  (await apiClient.post(`${API}/admin/media/maintenance/migrate`, {},
    { timeout: 120000 })).data;

// Pesan error yang JUJUR (bedakan jaringan vs penolakan server).
export const mediaErrorMessage = (err, fallback = 'Terjadi kesalahan.') => {
  if (err?.code === 'ECONNABORTED' || /timeout/i.test(err?.message || '')) {
    return 'Koneksi terputus sebelum server menjawab. Coba lagi.';
  }
  const detail = err?.response?.data?.detail;
  if (typeof detail === 'string' && detail) return detail;
  if (Array.isArray(detail) && detail.length) return detail[0]?.msg || fallback;
  if (err?.response?.status === 413) return 'Berkas terlalu besar untuk diunggah.';
  if (err?.message && !err?.response) return err.message;
  if (!err?.response) return 'Tidak dapat menghubungi server. Periksa koneksi Anda.';
  return fallback;
};

export const MEDIA_ACCEPT = 'image/jpeg,image/png,image/webp,image/gif,image/svg+xml,image/avif,image/heic,image/heif,.jpg,.jpeg,.png,.webp,.gif,.svg,.avif,.heic,.heif';
export const MEDIA_MAX_MB = 15;

// Opsi urutan & filter (dipakai toolbar + picker).
export const SORT_OPTIONS = [
  { value: 'newest', label: 'Terbaru' },
  { value: 'oldest', label: 'Terlama' },
  { value: 'name', label: 'Nama A–Z' },
  { value: 'name_desc', label: 'Nama Z–A' },
  { value: 'largest', label: 'Ukuran terbesar' },
  { value: 'smallest', label: 'Ukuran terkecil' },
];

export const KIND_OPTIONS = [
  { value: 'all', label: 'Semua tipe' },
  { value: 'local', label: 'Berkas lokal' },
  { value: 'external', label: 'URL eksternal' },
];
