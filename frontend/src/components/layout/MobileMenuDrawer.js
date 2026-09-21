import React from 'react';
import { Link } from 'react-router-dom';
import { X, ChevronRight } from 'lucide-react';
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetDescription } from '../ui/sheet';
import { useCatalog } from '../../store/CatalogContext';

export const MobileMenuDrawer = ({ open, onOpenChange }) => {
  const { categories } = useCatalog();
  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent
        side="left"
        data-testid="mobile-menu-panel"
        className="cp-store w-full sm:w-[420px] p-0 cp-glass-panel"
      >
        <SheetHeader className="sr-only">
          <SheetTitle>Menu Navigasi</SheetTitle>
          <SheetDescription>Jelajahi kategori dan halaman Collector Parfum.</SheetDescription>
        </SheetHeader>
        <div className="h-full flex flex-col">
          <div className="flex items-center justify-between p-5 border-b border-black/10">
            <div className="flex items-baseline gap-1.5">
              <span className="cp-logo text-2xl">Collector</span>
              <span className="cp-logo text-2xl">Parfum</span>
            </div>
            <button onClick={() => onOpenChange(false)} className="p-2 rounded-full hover:bg-black/5" aria-label="Tutup">
              <X className="h-5 w-5" />
            </button>
          </div>

          <div className="flex-1 overflow-y-auto px-5 py-6">
            <div className="cp-mono uppercase text-[10px] tracking-[0.22em] text-black/50 mb-3">Navigasi</div>
            <nav className="space-y-1 mb-8">
              {[
                { label: 'Beranda', to: '/' },
                { label: 'Toko', to: '/shop' },
                { label: 'Lokasi', to: '/lokasi' },
                { label: 'Wishlist', to: '/wishlist' },
                { label: 'Keranjang', to: '/keranjang' },
                { label: 'Tentang', to: '/tentang' },
                { label: 'Kontak', to: '/kontak' },
              ].map((n) => (
                <Link
                  key={n.to}
                  to={n.to}
                  onClick={() => onOpenChange(false)}
                  data-testid="mobile-menu-nav-link"
                  className="flex items-center justify-between py-3 border-b border-black/5 cp-headline text-2xl"
                >
                  {n.label}
                  <ChevronRight className="h-4 w-4 text-black/50" />
                </Link>
              ))}
            </nav>

            <div className="cp-mono uppercase text-[10px] tracking-[0.22em] text-black/50 mb-3">Keluarga Aroma</div>
            <div className="grid grid-cols-2 gap-3">
              {categories.map((c) => (
                <Link
                  key={c.slug}
                  to={`/shop?cat=${c.slug}`}
                  onClick={() => onOpenChange(false)}
                  className="relative overflow-hidden rounded-xl border border-black/10 aspect-[4/3]"
                >
                  <img src={c.image} alt={c.name} className="h-full w-full object-cover" />
                  <div className="absolute inset-0 bg-black/20" />
                  <div className="absolute inset-x-0 bottom-0 p-3 text-white">
                    <div className="cp-headline text-lg leading-none">{c.name}</div>
                    <div className="cp-mono uppercase text-[10px] tracking-[0.22em] opacity-80">Lihat koleksi</div>
                  </div>
                </Link>
              ))}
            </div>
          </div>

          <div className="p-5 border-t border-black/10">
            <div className="cp-mono uppercase text-[10px] tracking-[0.22em] text-black/60">
              Butuh bantuan? · <a href="mailto:cs@collectorparfum.com" className="underline">cs@collectorparfum.com</a>
            </div>
          </div>
        </div>
      </SheetContent>
    </Sheet>
  );
};
