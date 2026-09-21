import React from 'react';
import { Link } from 'react-router-dom';
import { HeartOff } from 'lucide-react';
import { Button } from '../components/ui/button';
import { useWishlist } from '../store/WishlistContext';
import { useCatalog } from '../store/CatalogContext';
import { ProductCard } from '../components/shared/ProductCard';
import { ProductGridSkeleton } from '../components/shared/Skeletons';
import { useQuickView } from '../store/QuickViewContext';
import { Reveal } from '../components/shared/Reveal';

export default function WishlistPage() {
  const wish = useWishlist();
  const { products, loading } = useCatalog();
  const { openQuickView } = useQuickView();
  const items = products.filter((p) => wish.has(p.id));

  return (
    <div className="cp-container cp-section" data-testid="wishlist-page">
      <div className="mb-8 flex items-end justify-between gap-4">
        <div>
          <div className="cp-eyebrow">Wishlist</div>
          <Reveal>
            <h1 className="cp-headline text-4xl sm:text-6xl mt-2">
              Aroma yang <em className="not-italic italic text-[color:var(--cp-brass)]">Anda</em> incar.
            </h1>
          </Reveal>
          <div className="mt-2 text-sm text-black/60">{items.length} produk tersimpan.</div>
        </div>
        {items.length > 0 && (
          <button onClick={wish.clear} className="cp-mono uppercase text-[11px] tracking-[0.22em] text-black/60 hover:text-black" data-testid="wishlist-clear-button">
            Kosongkan
          </button>
        )}
      </div>

      {loading ? (
        <ProductGridSkeleton count={8} testId="wishlist-loading" className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4 sm:gap-6" />
      ) : items.length === 0 ? (
        <div className="py-24 text-center">
          <div className="h-20 w-20 mx-auto rounded-full border border-black/15 flex items-center justify-center">
            <HeartOff className="h-8 w-8 text-black/50" />
          </div>
          <div className="cp-headline text-3xl mt-6">Wishlist Anda masih kosong</div>
          <div className="text-sm text-black/60 mt-2">Tap ikon hati di kartu produk untuk menyimpan aroma favorit.</div>
          <Link to="/shop">
            <Button className="mt-6 rounded-full bg-[color:var(--cp-ink)] text-[color:var(--cp-paper)] hover:bg-black">Jelajahi Koleksi</Button>
          </Link>
        </div>
      ) : (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4 sm:gap-6">
          {items.map((p) => (
            <ProductCard key={p.id} product={p} onQuickView={openQuickView} />
          ))}
        </div>
      )}
    </div>
  );
}
