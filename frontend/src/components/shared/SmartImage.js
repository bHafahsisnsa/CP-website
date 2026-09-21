// components/shared/SmartImage.js — <img> tahan-banting (E20).
//
// Tujuan: TIDAK PERNAH menampilkan ikon broken-image bawaan browser.
//  - loading  : skeleton dengan rasio sama (tanpa layout shift)
//  - sukses   : fade-in halus
//  - gagal    : placeholder bermerek + tombol "Coba lagi"
// URL relatif (/api/media/...) di-resolve ke absolut lewat resolveMediaUrl.
import React, { useCallback, useEffect, useState } from 'react';
import { ImageOff, RefreshCw } from 'lucide-react';
import { resolveMediaUrl } from '../../lib/mediaUrl';

export const SmartImage = ({
  src,
  alt = '',
  className = '',
  imgClassName = '',
  fit = 'cover',
  showRetry = true,
  fallbackLabel = 'Gambar tidak ditemukan',
  testId,
  ...rest
}) => {
  const resolved = resolveMediaUrl(src);
  const [state, setState] = useState(resolved ? 'loading' : 'error');
  const [bust, setBust] = useState(0);

  useEffect(() => {
    setState(resolved ? 'loading' : 'error');
    setBust(0);
  }, [resolved]);

  const retry = useCallback((e) => {
    if (e) { e.stopPropagation(); e.preventDefault(); }
    setBust((b) => b + 1);
    setState('loading');
  }, []);

  const finalSrc = bust ? `${resolved}${resolved.includes('?') ? '&' : '?'}_r=${bust}` : resolved;
  const fitCls = fit === 'contain' ? 'object-contain' : 'object-cover';

  return (
    <span className={`relative block overflow-hidden ${className}`} data-testid={testId}>
      {state === 'loading' ? (
        <span className="absolute inset-0 animate-pulse bg-muted" aria-hidden="true" />
      ) : null}

      {state !== 'error' ? (
        <img
          src={finalSrc}
          alt={alt}
          loading="lazy"
          decoding="async"
          onLoad={() => setState('loaded')}
          onError={() => setState('error')}
          className={`h-full w-full ${fitCls} transition-opacity duration-200 ${
            state === 'loaded' ? 'opacity-100' : 'opacity-0'
          } ${imgClassName}`}
          {...rest}
        />
      ) : (
        <span
          className="absolute inset-0 flex flex-col items-center justify-center gap-1.5 bg-muted px-2 text-center"
          data-testid="smart-image-missing-placeholder"
        >
          <ImageOff className="h-5 w-5 text-muted-foreground" aria-hidden="true" />
          <span className="text-[10px] leading-tight text-muted-foreground">{fallbackLabel}</span>
          {showRetry ? (
            <button
              type="button"
              onClick={retry}
              className="mt-0.5 inline-flex items-center gap-1 rounded-md border border-border bg-card px-1.5 py-0.5 text-[10px] font-medium text-foreground transition-colors hover:bg-muted"
              data-testid="smart-image-retry-button"
            >
              <RefreshCw className="h-3 w-3" /> Coba lagi
            </button>
          ) : null}
        </span>
      )}
    </span>
  );
};

export default SmartImage;
