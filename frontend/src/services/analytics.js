// services/analytics.js — first-party analytics (Epic E7). Fire-and-forget, PII-free.
// Event dikirim ke POST /api/analytics/event; kegagalan DIDIAMKAN (analitik tak boleh ganggu UX).
import apiClient, { API } from './apiClient';

const SKEY = 'cp_sid';

// session hint anonim (bukan PII) — untuk deduplikasi funnel di sisi analitik.
function sessionHint() {
  try {
    let s = localStorage.getItem(SKEY);
    if (!s) {
      s = 'sid_' + Math.random().toString(36).slice(2) + Date.now().toString(36);
      localStorage.setItem(SKEY, s);
    }
    return s;
  } catch (e) {
    return 'anon';
  }
}

// Kirim satu event analitik. TIDAK melempar error.
export async function track(type, extra = {}) {
  try {
    await apiClient.post(`${API}/analytics/event`, {
      type,
      path: typeof window !== 'undefined' ? window.location.pathname : '',
      product_id: extra.product_id || null,
      order_code: extra.order_code || null,
      session_hint: sessionHint(),
      meta: extra.meta || {},
    });
  } catch (e) {
    /* diam — analitik best-effort */
  }
}

// URL sitemap publik (dipakai footer sebagai tautan “Peta Situs”).
export const SITEMAP_URL = `${API}/sitemap.xml`;
