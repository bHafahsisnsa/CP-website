// components/shared/AppReadySignal.js — memberi sinyal ke BOOT SPLASH (public/index.html)
// bahwa prefetch inti (katalog + taksonomi + konten CMS) sudah selesai, sehingga splash
// boleh fade-out. Sengaja terpisah dari logika splash agar kebal StrictMode/cache bundle.
import React from 'react';
import { useCatalog } from '../../store/CatalogContext';
import { useContentReady } from '../../store/ContentContext';

export const AppReadySignal = () => {
  const { ready: catalogReady } = useCatalog();
  const contentReady = useContentReady();
  React.useEffect(() => {
    if (catalogReady && contentReady) {
      window.__CP_APP_READY = true;
    }
  }, [catalogReady, contentReady]);
  return null;
};
