// components/shared/ImageLightbox.js — Lightbox galeri produk (immersive zoom).
// A11y: Dialog WAJIB punya Title + Description (sr-only) agar Radix tidak memunculkan
// warning "Missing Description or aria-describedby". Tombol Close bawaan shadcn
// disembunyikan ([&>button:last-child]:hidden) karena kita pakai tombol glass sendiri —
// mencegah dua stop fokus di posisi yang sama.
import React from 'react';
import { X, ChevronLeft, ChevronRight } from 'lucide-react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '../ui/dialog';
import { handleImageError, resolveMediaUrl } from '../../lib/mediaUrl';

export const ImageLightbox = ({ images = [], index = 0, open, onOpenChange, onIndexChange, title = '' }) => {
  const total = images.length;

  const go = React.useCallback(
    (delta) => {
      if (!total) return;
      onIndexChange(((index + delta) % total + total) % total);
    },
    [index, total, onIndexChange]
  );

  React.useEffect(() => {
    if (!open) return undefined;
    const onKey = (e) => {
      if (e.key === 'ArrowRight') go(1);
      else if (e.key === 'ArrowLeft') go(-1);
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [open, go]);

  if (!total) return null;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent
        data-testid="pdp-lightbox"
        /* w-auto + max-w-fit: panel MENGIKUTI ukuran gambar (bukan lebar tetap max-w-lg
           bawaan shadcn) supaya tidak ada area kosong lebar di kiri/kanan gambar. */
        className="cp-store w-auto max-w-[96vw] sm:max-w-fit p-0 overflow-hidden border-white/30 cp-glass-panel [&>button:last-child]:hidden"
      >
        <DialogHeader className="sr-only">
          <DialogTitle>{title || 'Galeri produk'}</DialogTitle>
          <DialogDescription>
            Galeri gambar {title || 'produk'}. Gunakan tombol kiri/kanan atau tombol panah keyboard untuk berpindah gambar.
          </DialogDescription>
        </DialogHeader>

        <div className="relative">
          <img
            src={resolveMediaUrl(images[index])}
            onError={handleImageError}
            alt={`${title} — gambar ${index + 1}`}
            className="mx-auto block max-h-[84vh] max-w-[96vw] w-auto object-contain"
            data-testid="pdp-lightbox-image"
          />

          <button
            onClick={() => onOpenChange(false)}
            aria-label="Tutup galeri"
            data-testid="pdp-lightbox-close"
            className="absolute top-3 right-3 h-9 w-9 rounded-full cp-glass-pill inline-flex items-center justify-center"
          >
            <X className="h-4 w-4" />
          </button>

          {total > 1 ? (
            <>
              <button
                onClick={() => go(-1)}
                aria-label="Gambar sebelumnya"
                data-testid="pdp-lightbox-prev"
                className="absolute left-3 top-1/2 -translate-y-1/2 h-10 w-10 rounded-full cp-glass-pill inline-flex items-center justify-center"
              >
                <ChevronLeft className="h-4 w-4" />
              </button>
              <button
                onClick={() => go(1)}
                aria-label="Gambar berikutnya"
                data-testid="pdp-lightbox-next"
                className="absolute right-3 top-1/2 -translate-y-1/2 h-10 w-10 rounded-full cp-glass-pill inline-flex items-center justify-center"
              >
                <ChevronRight className="h-4 w-4" />
              </button>
              <div className="absolute bottom-3 left-1/2 -translate-x-1/2 cp-glass-pill rounded-full px-3 py-1 cp-mono text-[10px] tracking-[0.18em]">
                {index + 1} / {total}
              </div>
            </>
          ) : null}
        </div>
      </DialogContent>
    </Dialog>
  );
};
