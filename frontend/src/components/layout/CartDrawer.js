import React from 'react';
import { Link } from 'react-router-dom';
import { Minus, Plus, Trash2, ShoppingBag, ArrowRight } from 'lucide-react';
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetDescription } from '../ui/sheet';
import { Button } from '../ui/button';
import { Separator } from '../ui/separator';
import { useCart } from '../../store/CartContext';
import { useCatalog } from '../../store/CatalogContext';
import { formatIDR } from '../../lib/format';
import { maxStockForItem } from '../../lib/stock';
import { toast } from 'sonner';

export const CartDrawer = () => {
  const cart = useCart();
  const { getById } = useCatalog();
  const empty = cart.items.length === 0;

  // Naikkan qty dengan validasi stok LIVE (katalog). Server tetap otoritatif (409).
  const incItem = (item) => {
    const maxStock = maxStockForItem(item, getById(item.productId));
    if (item.quantity >= maxStock) {
      toast.error(maxStock <= 0 ? 'Stok habis' : `Stok tersedia hanya ${maxStock}`);
      return;
    }
    cart.updateQty(item.key, item.quantity + 1);
  };

  return (
    <Sheet open={cart.isOpen} onOpenChange={(o) => (o ? cart.open() : cart.close())}>
      <SheetContent
        side="right"
        data-testid="cart-drawer-panel"
        className="cp-store w-[92vw] sm:w-[440px] p-0 flex flex-col cp-glass-panel"
      >
        <SheetHeader className="px-6 py-5 border-b border-black/10">
          <SheetTitle className="cp-mono uppercase text-[11px] tracking-[0.22em] flex items-center gap-2">
            <ShoppingBag className="h-4 w-4" /> Keranjang Belanja
            <span className="ml-auto text-black/60">{cart.totalQty} item</span>
          </SheetTitle>
          <SheetDescription className="sr-only">
            Daftar produk di keranjang Anda. Ubah jumlah, hapus item, atau lanjut ke checkout.
          </SheetDescription>
        </SheetHeader>

        {empty ? (
          <div className="flex-1 flex flex-col items-center justify-center text-center p-8 gap-4">
            <div className="h-16 w-16 rounded-full border border-black/15 flex items-center justify-center">
              <ShoppingBag className="h-6 w-6 text-black/50" />
            </div>
            <div>
              <div className="cp-headline text-2xl">Keranjang Anda kosong</div>
              <div className="text-sm text-black/60 mt-1">Mulai jelajahi koleksi kami dan temukan aroma favorit.</div>
            </div>
            <Link to="/shop" onClick={() => cart.close()}>
              <Button data-testid="cart-drawer-empty-shop-button" className="rounded-full">Lanjut Belanja</Button>
            </Link>
          </div>
        ) : (
          <>
            <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4">
              {cart.items.map((item) => (
                <div key={item.key} className="flex gap-4" data-testid="cart-drawer-item">
                  <div className="h-24 w-20 rounded-lg overflow-hidden bg-[color:var(--cp-paper-fog)] flex-shrink-0">
                    <img src={item.image} alt={item.name} className="h-full w-full object-cover" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between gap-2">
                      <div className="min-w-0">
                        <div className="text-sm font-semibold truncate">{item.name}</div>
                        <div className="cp-mono uppercase text-[10px] tracking-[0.2em] text-black/60 mt-1">
                          {item.variantLabel || `${item.concentration ? item.concentration + ' · ' : ''}${item.variantType ? item.variantType + ' · ' : ''}${item.volumeMl}ml`}
                        </div>
                      </div>
                      <button
                        onClick={() => cart.removeItem(item.key)}
                        className="p-1 rounded-full hover:bg-black/5"
                        aria-label="Hapus item"
                        data-testid="cart-drawer-remove-item"
                      >
                        <Trash2 className="h-4 w-4 text-black/50" />
                      </button>
                    </div>
                    <div className="mt-3 flex items-center justify-between">
                      <div className="inline-flex items-center rounded-full border border-black/15">
                        <button
                          onClick={() => cart.updateQty(item.key, item.quantity - 1)}
                          className="h-8 w-8 flex items-center justify-center hover:bg-black/5 rounded-l-full"
                          aria-label="Kurangi"
                        >
                          <Minus className="h-3.5 w-3.5" />
                        </button>
                        <span className="cp-mono text-sm w-8 text-center" data-testid="cart-drawer-item-qty">{item.quantity}</span>
                        <button
                          onClick={() => incItem(item)}
                          disabled={item.quantity >= maxStockForItem(item, getById(item.productId))}
                          className="h-8 w-8 flex items-center justify-center hover:bg-black/5 rounded-r-full disabled:opacity-40 disabled:cursor-not-allowed"
                          aria-label="Tambah"
                        >
                          <Plus className="h-3.5 w-3.5" />
                        </button>
                      </div>
                      <div className="cp-mono text-sm font-semibold">{formatIDR(item.unitPrice * item.quantity)}</div>
                    </div>
                  </div>
                </div>
              ))}
            </div>

            <div className="border-t border-black/10 p-6 bg-[color:var(--cp-paper)]">
              <div className="flex items-center justify-between mb-3">
                <span className="cp-mono uppercase text-[11px] tracking-[0.22em]">Subtotal</span>
                <span className="cp-mono font-semibold" data-testid="cart-drawer-subtotal">{formatIDR(cart.subtotal)}</span>
              </div>
              <div className="text-[11px] text-black/55 mb-4">Ongkir & pajak dihitung saat checkout.</div>
              <div className="grid grid-cols-2 gap-2">
                <Link to="/keranjang" onClick={() => cart.close()}>
                  <Button variant="outline" className="w-full rounded-full" data-testid="cart-drawer-view-cart">
                    Lihat Keranjang
                  </Button>
                </Link>
                <Link to="/checkout" onClick={() => cart.close()}>
                  <Button
                    className="w-full rounded-full bg-[color:var(--cp-ink)] hover:bg-black text-[color:var(--cp-paper)]"
                    data-testid="cart-drawer-checkout-button"
                  >
                    Checkout <ArrowRight className="h-4 w-4 ml-1" />
                  </Button>
                </Link>
              </div>
            </div>
          </>
        )}
      </SheetContent>
    </Sheet>
  );
};
