// components/admin/media/useMediaUpload.js — hook antrean upload dengan progress (E20).
//
// Menangani: validasi ukuran/tipe di sisi klien (pesan cepat), upload berurutan
// (agar progress akurat & server tidak dibanjiri), retry per berkas, dan
// pembersihan antrean. Selalu mengembalikan aset yang berhasil ke pemanggil.
import { useCallback, useRef, useState } from 'react';
import { MEDIA_MAX_MB, mediaErrorMessage, uploadAsset } from '../../../services/media';

const ALLOWED_EXT = ['jpg', 'jpeg', 'png', 'webp', 'gif', 'svg', 'avif', 'heic', 'heif', 'bmp', 'tif', 'tiff'];

const extOf = (name) => String(name || '').split('.').pop().toLowerCase();

export const validateFile = (file) => {
  if (!file) return 'Berkas tidak valid.';
  if (file.size > MEDIA_MAX_MB * 1024 * 1024) {
    return `Ukuran berkas melebihi ${MEDIA_MAX_MB}MB.`;
  }
  const isImageMime = (file.type || '').startsWith('image/');
  if (!isImageMime && !ALLOWED_EXT.includes(extOf(file.name))) {
    return 'Format berkas tidak didukung.';
  }
  return null;
};

let seq = 0;

export const useMediaUpload = ({ folderId = null, onUploaded } = {}) => {
  const [queue, setQueue] = useState([]);
  const [busy, setBusy] = useState(false);
  const folderRef = useRef(folderId);
  folderRef.current = folderId;

  const patch = useCallback((id, p) => {
    setQueue((q) => q.map((it) => (it.id === id ? { ...it, ...p } : it)));
  }, []);

  const runOne = useCallback(async (item) => {
    patch(item.id, { status: 'uploading', progress: 1, error: null });
    try {
      const asset = await uploadAsset(item.file, {
        folderId: item.folderId,
        onProgress: (p) => patch(item.id, { progress: p }),
      });
      patch(item.id, { status: 'done', progress: 100, asset });
      return asset;
    } catch (e) {
      patch(item.id, { status: 'error', error: mediaErrorMessage(e, 'Upload gagal.') });
      return null;
    }
  }, [patch]);

  /** Tambahkan berkas ke antrean & jalankan. Kembalikan array aset sukses. */
  const enqueue = useCallback(async (files) => {
    const list = Array.from(files || []);
    if (!list.length) return [];
    const items = list.map((file) => {
      seq += 1;
      const err = validateFile(file);
      return {
        id: `up_${Date.now()}_${seq}`,
        file,
        name: file.name || 'gambar',
        size: file.size || 0,
        folderId: folderRef.current || null,
        progress: 0,
        status: err ? 'error' : 'queued',
        error: err,
        asset: null,
      };
    });
    setQueue((q) => [...items, ...q].slice(0, 60));
    setBusy(true);
    const done = [];
    for (const it of items) {
      if (it.status === 'error') continue;
      // eslint-disable-next-line no-await-in-loop
      const asset = await runOne(it);
      if (asset) done.push(asset);
    }
    setBusy(false);
    if (done.length && onUploaded) onUploaded(done);
    return done;
  }, [runOne, onUploaded]);

  const retry = useCallback(async (id) => {
    const item = queue.find((it) => it.id === id);
    if (!item) return;
    const clientErr = validateFile(item.file);
    if (clientErr) { patch(id, { status: 'error', error: clientErr }); return; }
    setBusy(true);
    const asset = await runOne(item);
    setBusy(false);
    if (asset && onUploaded) onUploaded([asset]);
  }, [queue, runOne, patch, onUploaded]);

  const remove = useCallback((id) => setQueue((q) => q.filter((it) => it.id !== id)), []);
  const clearDone = useCallback(
    () => setQueue((q) => q.filter((it) => it.status !== 'done')), [],
  );
  const clearAll = useCallback(() => setQueue([]), []);

  const pending = queue.filter((it) => it.status === 'uploading' || it.status === 'queued').length;
  const failed = queue.filter((it) => it.status === 'error').length;

  return { queue, busy, pending, failed, enqueue, retry, remove, clearDone, clearAll };
};

export default useMediaUpload;
