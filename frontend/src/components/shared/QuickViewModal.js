import React from 'react';
import { Link } from 'react-router-dom';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '../ui/dialog';
import { Button } from '../ui/button';
import { Minus, Plus, X } from 'lucide-react';
import { formatIDR } from '../../lib/format';
import { useCart } from '../../store/CartContext';
import { toast } from 'sonner';
import { VariantSelector } from './VariantSelector';
import { findVariant, firstVariant, toCartVolume, priceRange } from '../../lib/variants';
import { brandText } from '../../lib/brand';
import { useStoreSettings } from '../../store/SettingsContext';
import { handleImageError, resolveMediaUrl } from '../../lib/mediaUrl';

export const QuickViewModal = ({ product, open, onOpenChange }) => {
  const cart = useCart();
  const { settings } = useStoreSettings();
  const [sel, setSel] = React.useState({});
  const [qty, setQty] = React.useState(1);

  React.useEffect(() => {
    if (product) {
      const fv = firstVariant(product);
      setSel(fv ? { ...fv.options } : {});
      setQty(1);
    }
  }, [product]);

  if (!product) return null;

  const options = product.options || [];
  const range = priceRange(product);
  const selectedVariant = findVariant(product, sel);
  const priceNow = selectedVariant ? selectedVariant.price : product.price;
  const cmp = selectedVariant?.compare_at_price
    || (product.compareAtPrice && selectedVariant && product.compareAtPrice > selectedVariant.price ? product.compareAtPrice : null);
  const outOfStock = !selectedVariant || (selectedVariant.stock || 0) <= 0;
  const variantLabelNow = selectedVariant
    ? options.map((o) => selectedVariant.options[o.name]).filter(Boolean).join(' / ')
    : '';

  const handleAdd = () => {
    if (!selectedVariant) { toast.error('Pilih varian terlebih dahulu'); return; }
    if (outOfStock) { toast.error('Varian ini sedang habis'); return; }
    cart.addItem(product, toCartVolume(product, selectedVariant), qty);
    toast.success(`${product.name} ditambahkan ke keranjang`, {
      description: `${variantLabelNow} · ${qty}x`,
    });
    onOpenChange(false);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent
        data-testid="quick-view-modal"
        /* [&>button:last-child]:hidden -> sembunyikan tombol Close bawaan shadcn (child terakhir
           DialogContent) karena modal ini sudah punya tombol tutup glass-pill sendiri. Mencegah
           dua tombol tutup bertumpuk (dua stop fokus keyboard di posisi yang sama). */
        className="cp-store max-w-3xl p-0 overflow-hidden cp-glass-panel border-white/40 [&>button:last-child]:hidden"
      >
        <DialogHeader className="sr-only">
          <DialogTitle>{product.name}</DialogTitle>
          <DialogDescription>
            Pratinjau cepat {product.name} — pilih varian lalu tambahkan ke keranjang.
          </DialogDescription>
        </DialogHeader>
        <button
          onClick={() => onOpenChange(false)}
          className="absolute top-3 right-3 z-20 h-9 w-9 rounded-full cp-glass-pill flex items-center justify-center"
          aria-label="Tutup"
        >
          <X className="h-4 w-4" />
        </button>
        <div className="grid grid-cols-1 md:grid-cols-2">
          <div className="bg-[color:var(--cp-paper-fog)] aspect-[3/4] md:aspect-auto md:h-full">
            <img src={resolveMediaUrl((product.images || [])[0])} alt={product.name} onError={handleImageError} className="h-full w-full object-cover" />
          </div>
          <div className="p-6 md:p-8 flex flex-col overflow-y-auto max-h-[80vh]">
            <div className="cp-mono uppercase text-[10px] tracking-[0.22em] text-black/55">
              {product.concentration} · {product.gender}
              {brandText(product.brand, settings)
                ? ` · ${brandText(product.brand, settings)}`
                : ''}
            </div>
            <h3 className="cp-headline text-2xl md:text-3xl mt-1">{product.name}</h3>
            <div className="mt-2 flex items-baseline gap-3 flex-wrap">
              <div className="cp-mono text-lg font-semibold" data-testid="quick-view-price">
                {formatIDR(priceNow)}
              </div>
              {cmp && (
                <div className="cp-mono text-sm text-black/40 line-through">{formatIDR(cmp)}</div>
              )}
              {range.hasRange && (
                <span className="cp-mono text-[11px] text-black/45">
                  Rentang {formatIDR(range.min)} – {formatIDR(range.max)}
                </span>
              )}
            </div>
            <p className="text-sm text-black/70 mt-3">{product.description}</p>

            <div className="mt-5">
              <VariantSelector product={product} sel={sel} onChange={setSel} testidPrefix="quick-view" />
              <div className="mt-2 cp-mono uppercase text-[10px] tracking-[0.22em] text-[color:var(--cp-brass)]" data-testid="quick-view-stock">
                {selectedVariant && selectedVariant.stock > 0 ? `Stok tersedia (${selectedVariant.stock})` : 'Habis'}
                {selectedVariant?.sku ? <span className="text-black/40 normal-case tracking-normal"> · SKU {selectedVariant.sku}</span> : null}
              </div>
            </div>

            <div className="mt-5 flex items-center gap-3">
              <div className="cp-mono uppercase text-[10px] tracking-[0.22em] text-black/60">Jumlah</div>
              <div className="inline-flex items-center rounded-full border border-black/15">
                <button onClick={() => setQty((q) => Math.max(1, q - 1))} className="h-9 w-9 flex items-center justify-center rounded-l-full hover:bg-black/5">
                  <Minus className="h-4 w-4" />
                </button>
                <span className="cp-mono w-10 text-center text-sm" data-testid="quick-view-qty">{qty}</span>
                <button onClick={() => setQty((q) => q + 1)} className="h-9 w-9 flex items-center justify-center rounded-r-full hover:bg-black/5">
                  <Plus className="h-4 w-4" />
                </button>
              </div>
            </div>

            <div className="mt-6 grid grid-cols-1 sm:grid-cols-2 gap-2">
              <Button
                onClick={handleAdd}
                disabled={outOfStock}
                data-testid="quick-view-add-to-cart-button"
                className="rounded-full bg-[color:var(--cp-ink)] hover:bg-black text-[color:var(--cp-paper)] disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {outOfStock ? 'Stok Habis' : 'Tambah ke Keranjang'}
              </Button>
              <Link to={`/parfum/${product.slug}`} onClick={() => onOpenChange(false)}>
                <Button variant="outline" className="w-full rounded-full">
                  Lihat Detail
                </Button>
              </Link>
            </div>

            <div className="mt-5 grid grid-cols-3 gap-2 text-[11px]">
              <div className="px-3 py-2 rounded-lg bg-[color:var(--cp-paper-fog)] cp-mono uppercase tracking-[0.16em]">
                <div className="text-black/55">Top</div>
                <div className="text-black mt-1">{product.notes.top.slice(0, 2).join(', ')}</div>
              </div>
              <div className="px-3 py-2 rounded-lg bg-[color:var(--cp-paper-fog)] cp-mono uppercase tracking-[0.16em]">
                <div className="text-black/55">Heart</div>
                <div className="text-black mt-1">{product.notes.heart.slice(0, 2).join(', ')}</div>
              </div>
              <div className="px-3 py-2 rounded-lg bg-[color:var(--cp-paper-fog)] cp-mono uppercase tracking-[0.16em]">
                <div className="text-black/55">Base</div>
                <div className="text-black mt-1">{product.notes.base.slice(0, 2).join(', ')}</div>
              </div>
            </div>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};
