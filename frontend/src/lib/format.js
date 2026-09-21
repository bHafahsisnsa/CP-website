// Format helpers for Collector Parfum (Bahasa Indonesia)

export const formatIDR = (value) => {
  if (value === null || value === undefined) return 'Rp 0';
  const n = Number(value) || 0;
  return 'Rp ' + n.toLocaleString('id-ID');
};

export const clamp = (v, min, max) => Math.min(Math.max(v, min), max);

export const slug = (str = '') =>
  String(str)
    .toLowerCase()
    .trim()
    .replace(/[^\w\s-]/g, '')
    .replace(/\s+/g, '-');

export const readingTime = (words) => Math.max(1, Math.round(words / 220));
