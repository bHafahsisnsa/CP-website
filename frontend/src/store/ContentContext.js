// store/ContentContext.js — Storefront CMS content (Epic E9).
// Fetch /api/content SEKALI, sediakan via useContent(key, fallback). Fallback = konten
// inline komponen → storefront tetap tampil sempurna walau API gagal/belum ada override.
//
// PREVIEW MODE (E9+): jika URL punya ?cms_preview=1, komponen ini juga LISTEN pesan
// postMessage bertipe { type: 'CMS_DRAFT', content } dari parent (admin CMS editor)
// dan meng-override state `content` secara live tanpa mengubah DB — memungkinkan
// visual-builder preview real-time.
import React, { createContext, useContext, useEffect, useMemo, useState } from 'react';
import apiClient, { API } from '../services/apiClient';

const ContentContext = createContext({ content: {}, ready: false, previewMode: false });

const isPreviewMode = () => {
  if (typeof window === 'undefined') return false;
  try { return new URLSearchParams(window.location.search).get('cms_preview') === '1'; }
  catch { return false; }
};

export const ContentProvider = ({ children }) => {
  const [content, setContent] = useState({});
  const [draftOverride, setDraftOverride] = useState(null);
  const [ready, setReady] = useState(false);
  const previewMode = useMemo(() => isPreviewMode(), []);

  useEffect(() => {
    let active = true;
    apiClient
      .get(`${API}/content`)
      .then((r) => { if (active) setContent(r.data || {}); })
      .catch(() => { if (active) setContent({}); })
      .finally(() => { if (active) setReady(true); });
    return () => { active = false; };
  }, []);

  // Live preview: dengarkan postMessage dari parent admin editor.
  useEffect(() => {
    if (!previewMode || typeof window === 'undefined') return undefined;
    const onMsg = (ev) => {
      const data = ev && ev.data;
      if (!data || typeof data !== 'object') return;
      if (data.type === 'CMS_DRAFT' && data.content && typeof data.content === 'object') {
        setDraftOverride(data.content);
      } else if (data.type === 'CMS_DRAFT_CLEAR') {
        setDraftOverride(null);
      }
    };
    window.addEventListener('message', onMsg);
    // Beritahu parent bahwa iframe siap
    try { window.parent && window.parent.postMessage({ type: 'CMS_PREVIEW_READY' }, '*'); } catch (_) {}
    return () => window.removeEventListener('message', onMsg);
  }, [previewMode]);

  const merged = useMemo(() => {
    if (!draftOverride) return content;
    return { ...content, ...draftOverride };
  }, [content, draftOverride]);

  return (
    <ContentContext.Provider value={{ content: merged, ready, previewMode }}>
      {children}
    </ContentContext.Provider>
  );
};

// Ambil satu section, di-merge di atas fallback (konten default inline komponen).
export const useContent = (key, fallback = {}) => {
  const { content } = useContext(ContentContext);
  const stored = content[key];
  if (!stored) return fallback;
  return { ...fallback, ...stored };
};

export const useContentReady = () => useContext(ContentContext).ready;
export const useCmsPreview = () => useContext(ContentContext).previewMode;
