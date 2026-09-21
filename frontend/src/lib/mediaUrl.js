// lib/mediaUrl.js — SSOT util URL media (E20).
//
// Aturan penting: yang DISIMPAN ke database selalu URL RELATIF (`/api/media/...`).
// Resolusi ke absolut dilakukan saat RENDER memakai REACT_APP_BACKEND_URL sehingga
// pindah domain / deploy ulang TIDAK merusak tautan gambar (penyebab broken image).

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || '';

export const MEDIA_PREFIX = '/api/media/';

/** URL relatif media lokal -> absolut. URL eksternal & data URI dibiarkan. */
export const resolveMediaUrl = (url) => {
  const u = typeof url === 'string' ? url.trim() : '';
  if (!u) return '';
  if (/^(https?:)?\/\//i.test(u) || u.startsWith('data:') || u.startsWith('blob:')) return u;
  if (u.startsWith('/')) return `${BACKEND_URL}${u}`;
  return u;
};

/** True bila URL menunjuk berkas yang tersimpan di penyimpanan lokal kita. */
export const isLocalMedia = (url) => typeof url === 'string' && url.includes(MEDIA_PREFIX);

/** Ambil nama berkas dari URL apa pun (untuk label & alt fallback). */
export const fileNameFromUrl = (url) => {
  const u = (url || '').split('?')[0].replace(/\/+$/, '');
  const last = u.split('/').pop() || 'media';
  try { return decodeURIComponent(last); } catch (e) { return last; }
};

export const fileExt = (url) => {
  const n = fileNameFromUrl(url);
  return n.includes('.') ? n.split('.').pop().toLowerCase() : '';
};

/** Format byte -> string ramah manusia (id-ID). */
export const formatBytes = (bytes) => {
  const n = Number(bytes || 0);
  if (!n) return '0 KB';
  if (n < 1024) return `${n} B`;
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(n / 1024 >= 10 ? 0 : 1)} KB`;
  return `${(n / 1024 / 1024).toFixed(n / 1024 / 1024 >= 10 ? 0 : 1)} MB`;
};

/** Label badge tipe berkas (SVG/GIF/AVIF/HEIC/EKSTERNAL) atau null. */
export const mediaTypeBadge = (asset) => {
  if (!asset) return null;
  if (asset.source === 'external' || asset.external) return 'EKSTERNAL';
  const ext = (asset.mime || '').split('/')[1] || fileExt(asset.url);
  const map = {
    'svg+xml': 'SVG', svg: 'SVG', gif: 'GIF', avif: 'AVIF',
    heic: 'HEIC', heif: 'HEIC', webp: 'WEBP',
  };
  return map[ext] || null;
};

/** Perlu latar kotak-kotak (transparansi mungkin ada)? */
export const needsCheckerboard = (asset) => {
  const m = (asset?.mime || '').toLowerCase();
  return m.includes('png') || m.includes('svg') || m.includes('webp') || !m;
};

/** Gaya latar kotak-kotak untuk gambar transparan. */
export const CHECKER_STYLE = {
  backgroundImage:
    'linear-gradient(45deg, rgba(0,0,0,0.06) 25%, transparent 25%, transparent 75%, rgba(0,0,0,0.06) 75%),'
    + 'linear-gradient(45deg, rgba(0,0,0,0.06) 25%, transparent 25%, transparent 75%, rgba(0,0,0,0.06) 75%)',
  backgroundSize: '14px 14px',
  backgroundPosition: '0 0, 7px 7px',
};

/** Bentuk aset minimal dari URL telanjang (untuk field lama yang hanya menyimpan URL). */
export const assetFromUrl = (url) => (url
  ? {
    id: `url:${url}`, url, thumb_url: url, medium_url: url,
    filename: fileNameFromUrl(url), mime: '', size: 0,
    source: isLocalMedia(url) ? 'upload' : 'external',
  }
  : null);

/** Placeholder SVG inline (tanpa request jaringan) untuk gambar yang hilang. */
export const MEDIA_PLACEHOLDER = "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='640' height='480'><rect width='100%25' height='100%25' fill='%23f7f3ea'/><rect x='24' y='24' width='592' height='432' rx='24' fill='%23fffcf6' stroke='%23d6c3a3' stroke-width='2'/><circle cx='260' cy='200' r='22' fill='%23141414' fill-opacity='0.18'/><path d='M240 320l70-80 60 70 40-45 90 105H240z' fill='%23141414' fill-opacity='0.12'/></svg>";

/**
 * Handler onError untuk <img> biasa: ganti ke placeholder bermerek satu kali saja
 * (tanpa loop) sehingga pengguna TIDAK pernah melihat ikon broken-image browser.
 */
export const handleImageError = (e) => {
  const el = e && e.target;
  if (!el || el.dataset.mediaFallback === '1') return;
  el.dataset.mediaFallback = '1';
  el.src = MEDIA_PLACEHOLDER;
};
