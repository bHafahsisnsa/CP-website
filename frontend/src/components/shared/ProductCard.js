import React from 'react';
import { Link } from 'react-router-dom';
import { motion, useReducedMotion } from 'framer-motion';
import { Heart, Eye, ShoppingBag } from 'lucide-react';
import { toast } from 'sonner';
import { formatIDR } from '../../lib/format';
import { useWishlist } from '../../store/WishlistContext';
import { useCart } from '../../store/CartContext';
import { cheapestVariant, toCartVolume, priceRange } from '../../lib/variants';
import { brandText } from '../../lib/brand';
import { useStoreSettings } from '../../store/SettingsContext';
import { MEDIA_PLACEHOLDER, resolveMediaUrl } from '../../lib/mediaUrl';

// Kartu produk — versi IMMERSIVE: frame glass dipersempit, gambar memakai rasio 4:5
// (identik dengan artwork botol 900x1125 sehingga tidak terpotong), dan blok meta
// dibuat satu kolom dengan tipografi kecil supaya gambar mendominasi.
export const ProductCard = ({ product, onQuickView, priority = false }) => {
  const wish = useWishlist();
  const cart = useCart();
  const { settings } = useStoreSettings();
  const prefersReduced = useReducedMotion();
  const [hovered, setHovered] = React.useState(false);

  const images = Array.isArray(product.images) ? product.images : [];
  const primaryImage = resolveMediaUrl(images[0]) || MEDIA_PLACEHOLDER;
  const secondaryImage = resolveMediaUrl(images[1] || images[0]) || MEDIA_PLACEHOLDER;
  const onImgError = (e) => {
    // Berkas hilang / URL eksternal mati -> tampilkan placeholder, JANGAN ikon broken.
    if (e.target.dataset.fallback === '1') return;
    e.target.dataset.fallback = '1';
    e.target.src = MEDIA_PLACEHOLDER;
  };
  const range = priceRange(product);
  const tagLine = (product.tags || []).slice(0, 3).join(' · ');
  const brandLine = brandText(product.brand, settings);

  const handleQuickAdd = (e) => {
    e.preventDefault();
    // Varian default = termurah (selaras dgn harga "mulai dari" yang tampil).
    const variant = cheapestVariant(product);
    const vol = variant ? toCartVolume(product, variant) : (product.volumes || [])[0];
    if (!vol) { toast.error('Varian tidak tersedia'); return; }
    cart.addItem(product, vol, 1);
    toast.success(`${product.name} ditambahkan ke keranjang`, {
      description: `${vol.label || `${vol.ml}ml`} · ${formatIDR(vol.price)}`,
    });
  };

  const handleWishlist = (e) => {
    e.preventDefault();
    wish.toggle(product.id);
    toast(wish.has(product.id) ? 'Dihapus dari wishlist' : 'Ditambahkan ke wishlist');
  };

  return (
    <div
      data-testid="product-card"
      className="group relative cp-glass cp-glass-hover rounded-[var(--cp-radius-lg)] p-1.5 sm:p-2"
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
    >
      <Link to={`/parfum/${product.slug}`} className="block relative z-[1]">
        <div className="relative overflow-hidden rounded-[15px] bg-[color:var(--cp-paper-fog)] border border-black/5 aspect-[4/5]">
          {/* Top row: badges (left) + wishlist (right) in one flex row so they
              can never overlap or get clipped on narrow cards. Wrapper is
              non-interactive; only the heart re-enables pointer events so the
              underlying image link stays clickable. */}
          <div className="absolute z-10 inset-x-2 top-2 flex items-start justify-between gap-2 pointer-events-none">
            <div className="flex flex-col gap-1 items-start min-w-0">
              {product.compareAtPrice ? (
                <span className="bg-[color:var(--cp-ink)] text-[color:var(--cp-paper)] cp-mono uppercase text-[8.5px] tracking-[0.18em] px-2 py-[3px] rounded-full">
                  Promo
                </span>
              ) : product.isNew ? (
                <span className="bg-[color:var(--cp-paper-warm)] text-[color:var(--cp-ink)] cp-mono uppercase text-[8.5px] tracking-[0.18em] px-2 py-[3px] rounded-full border border-black/10">
                  Baru
                </span>
              ) : null}
              {product.bestSeller && (
                <span className="bg-[color:var(--cp-brass)] text-[color:var(--cp-paper-warm)] cp-mono uppercase text-[8.5px] tracking-[0.18em] px-2 py-[3px] rounded-full">
                  Best Seller
                </span>
              )}
            </div>

            {/* Wishlist */}
            <button
              onClick={handleWishlist}
              aria-label="Simpan ke wishlist"
              data-testid="product-card-wishlist-button"
              className="pointer-events-auto shrink-0 h-8 w-8 rounded-full cp-glass-pill flex items-center justify-center"
            >
              <Heart
                className={`h-3.5 w-3.5 ${wish.has(product.id) ? 'fill-[color:var(--cp-ink)] text-[color:var(--cp-ink)]' : 'text-black/70'}`}
              />
            </button>
          </div>

          {/* Image A */}
          <motion.img
            src={primaryImage}
            alt={product.name}
            loading={priority ? 'eager' : 'lazy'}
            onError={onImgError}
            initial={false}
            animate={{ opacity: hovered && !prefersReduced ? 0 : 1 }}
            transition={{ duration: 0.35, ease: 'easeOut' }}
            className="absolute inset-0 h-full w-full object-cover"
          />
          {/* Image B (hover) */}
          <motion.img
            src={secondaryImage}
            alt={`${product.name} tampilan alternatif`}
            loading="lazy"
            onError={onImgError}
            initial={false}
            animate={{
              opacity: hovered && !prefersReduced ? 1 : 0,
              scale: hovered && !prefersReduced ? 1.06 : 1.0,
            }}
            transition={{ duration: 0.7, ease: [0.22, 1, 0.36, 1] }}
            className="absolute inset-0 h-full w-full object-cover"
          />

          {/* Kilau menyapu saat hover (immersive) — di DOM setelah gambar & sebelum
              tombol aksi, supaya tombol tetap tampil di atas kilau. */}
          <span aria-hidden className="cp-sheen" />

          {/* Bottom overlay actions — Quick View as compact icon pill so the
              primary "Tambah" button has room and never wraps to two lines. */}
          <div
            className={`absolute inset-x-2 bottom-2 flex items-center gap-1.5 transition-all duration-300 ${
              hovered ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-2 sm:opacity-0'
            }`}
          >
            <button
              onClick={(e) => {
                e.preventDefault();
                onQuickView && onQuickView(product);
              }}
              aria-label="Quick View"
              title="Quick View"
              data-testid="product-card-quick-view-button"
              className="cp-glass-pill text-[color:var(--cp-ink)] h-9 w-9 shrink-0 rounded-full inline-flex items-center justify-center"
            >
              <Eye className="h-3.5 w-3.5" />
            </button>
            <button
              onClick={handleQuickAdd}
              data-testid="product-card-add-to-cart-button"
              className="flex-1 bg-[color:var(--cp-ink)] text-[color:var(--cp-paper)] cp-mono uppercase text-[9px] tracking-[0.16em] py-2.5 rounded-full hover:bg-black transition-colors inline-flex items-center justify-center gap-1.5 whitespace-nowrap"
            >
              <ShoppingBag className="h-3.5 w-3.5" /> Tambah
            </button>
          </div>
        </div>

        {/* Meta — satu kolom, tipografi kecil (gambar yang jadi bintang). */}
        <div className="pt-2.5 pb-0.5 px-1">
          <div className="cp-mono uppercase text-[8.5px] tracking-[0.2em] text-black/45 truncate">
            {product.concentration} · {product.gender}
          </div>
          {brandLine && (
            <div
              className="cp-mono uppercase text-[8.5px] tracking-[0.18em] text-black/35 truncate mt-[2px]"
              data-testid="product-card-brand"
            >
              {brandLine}
            </div>
          )}
          <div className="mt-1 text-[12.5px] sm:text-[13.5px] font-medium leading-snug truncate">{product.name}</div>
          <div className="mt-[3px] flex items-baseline gap-1.5">
            <span className="cp-mono text-[11.5px] font-semibold tracking-tight whitespace-nowrap" data-testid="product-card-price">
              {/* Layar sempit: tampilkan "harga termurah+" agar tidak pecah dua baris
                  (tinggi kartu jadi tidak seragam). Layar >=sm: rentang penuh. */}
              <span className="sm:hidden">
                {range.hasRange ? `${formatIDR(range.min)}+` : formatIDR(product.price)}
              </span>
              <span className="hidden sm:inline">
                {range.hasRange ? `${formatIDR(range.min)} – ${formatIDR(range.max)}` : formatIDR(product.price)}
              </span>
            </span>
            {product.compareAtPrice ? (
              <span className="cp-mono text-[9.5px] text-black/35 line-through whitespace-nowrap">{formatIDR(product.compareAtPrice)}</span>
            ) : null}
          </div>
          {tagLine ? (
            <div className="mt-1 cp-mono uppercase text-[8px] tracking-[0.18em] text-black/35 truncate">{tagLine}</div>
          ) : null}
        </div>
      </Link>

      {/* Mobile quick actions */}
      <div className="sm:hidden mt-2 px-1 grid grid-cols-2 gap-1.5 relative z-[1]">
        <button
          onClick={() => onQuickView && onQuickView(product)}
          className="cp-mono uppercase text-[9px] tracking-[0.18em] border border-black/15 py-2 rounded-full"
          data-testid="product-card-mobile-quick-view"
        >
          Quick View
        </button>
        <button
          onClick={handleQuickAdd}
          className="cp-mono uppercase text-[9px] tracking-[0.18em] bg-[color:var(--cp-ink)] text-[color:var(--cp-paper)] py-2 rounded-full"
          data-testid="product-card-mobile-add-to-cart"
        >
          Tambah
        </button>
      </div>
    </div>
  );
};
