// services/backup.js — SSOT klien Backup & Restore (admin-only).
// Semua endpoint /api/admin/backup/* butuh Bearer + role 'admin' (global via apiClient).
// Path DITULIS LITERAL agar terverifikasi verify_api_contract (FE↔BE).
import apiClient, { API } from './apiClient';

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

// Daftar koleksi + jumlah dokumen.
export const listBackupCollections = async () =>
  (await apiClient.get(`${API}/admin/backup/collections`)).data;

// Ekspor koleksi terpilih -> unduh file JSON.
export const exportBackup = async (collections) => {
  const res = await apiClient.post(`${API}/admin/backup/export`, { collections }, {
    responseType: 'blob', timeout: 120000,
  });
  const fallback = `backup_collector_${Date.now()}.json`;
  _downloadBlob(res.data, _filenameFromDisposition(res.headers['content-disposition'], fallback));
};

// Buat backup tersimpan di server.
export const createServerBackup = async (collections, note = '') =>
  (await apiClient.post(`${API}/admin/backup/server`, { collections, note }, { timeout: 120000 })).data;

// Daftar backup server.
export const listServerBackups = async () =>
  (await apiClient.get(`${API}/admin/backup/server`)).data;

// Unduh file backup server.
export const downloadServerBackup = async (bid, filename) => {
  const res = await apiClient.get(`${API}/admin/backup/server/${bid}/download`, {
    responseType: 'blob', timeout: 120000,
  });
  _downloadBlob(res.data, _filenameFromDisposition(res.headers['content-disposition'], filename || `${bid}.json`));
};

// Restore dari backup server. collections=null -> semua koleksi di backup.
export const restoreServerBackup = async (bid, mode, collections = null) =>
  (await apiClient.post(`${API}/admin/backup/server/${bid}/restore`, { mode, collections }, { timeout: 180000 })).data;

// Hapus backup server.
export const deleteServerBackup = async (bid) =>
  (await apiClient.delete(`${API}/admin/backup/server/${bid}`)).data;

// Restore dari file upload (multipart). collections = array (opsional).
export const restoreFromFile = async (file, mode, collections = null) => {
  const fd = new FormData();
  fd.append('file', file);
  fd.append('mode', mode);
  if (collections && collections.length) fd.append('collections', JSON.stringify(collections));
  return (await apiClient.post(`${API}/admin/backup/restore`, fd, {
    headers: { 'Content-Type': 'multipart/form-data' }, timeout: 180000,
  })).data;
};
