import React from 'react';
import { Link } from 'react-router-dom';
import { Heart } from 'lucide-react';
import { useCatalog } from '../../store/CatalogContext';
import { useWishlist } from '../../store/WishlistContext';
import { ProductCard } from '../shared/ProductCard';
import { Button } from '../ui/button';

// Tab Wishlist di akun — resolusi produk dari katalog (sumber id: WishlistContext).
export default function WishlistTab() {
  const { products } = useCatalog();
  const wish = useWishlist();
  const items = products.filter((p) => wish.has(p.id));

  return (
    <div className="rounded-2xl border border-black/10 bg-[color:var(--cp-paper-warm)] p-6" data-testid="account-wishlist-tab">
      <div className="flex items-center justify-between mb-4">
        <div className="cp-mono uppercase text-[11px] tracking-[0.22em]">Wishlist ({items.length})</div>
        <Link to="/wishlist" className="cp-mono uppercase text-[10px] tracking-[0.22em] text-[color:var(--cp-market-blue)] hover:underline">Buka halaman penuh</Link>
      </div>
      {items.length === 0 ? (
        <div className="py-12 text-center" data-testid="account-wishlist-empty">
          <Heart className="h-8 w-8 mx-auto text-black/25" />
          <div className="text-sm text-black/60 mt-3">Wishlist Anda masih kosong.</div>
          <Link to="/shop"><Button variant="outline" className="rounded-full mt-4">Jelajahi Koleksi</Button></Link>
        </div>
      ) : (
        <div className="grid grid-cols-2 lg:grid-cols-3 gap-4">
          {items.map((p) => <ProductCard key={p.id} product={p} />)}
        </div>
      )}
    </div>
  );
}
