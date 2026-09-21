import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Minus, Plus, Trash2, ArrowRight, Tag, ShoppingBag, X, Loader2, Ticket } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { useCart } from '../store/CartContext';
import { validateVoucher } from '../services/vouchers';
import { VoucherCenter } from '../components/shared/VoucherCenter';
import { formatIDR } from '../lib/format';
import { useCatalog } from '../store/CatalogContext';
import { ProductCard } from '../components/shared/ProductCard';
import { AutoCarousel } from '../components/shared/AutoCarousel';
import { useQuickView } from '../store/QuickViewContext';
import { toast } from 'sonner';
import { Reveal } from '../components/shared/Reveal';
import { maxStockForItem } from '../lib/stock';

export default function CartPage() {
  const cart = useCart();
  const navigate = useNavigate();
  const { openQuickView } = useQuickView();
  const { products, getById } = useCatalog();
  const recommended = products.slice(0, 4);
  const [voucherCode, setVoucherCode] = React.useState(cart.voucher ? cart.voucher.code : '');
  const [applying, setApplying] = React.useState(false);
  const [applyingCard, setApplyingCard] = React.useState(null);
  const [voucherError, setVoucherError] = React.useState(null);

  // Terapkan voucher: diskon dihitung SERVER (SSOT), FE hanya menampilkan hasil.
  const doApply = async (rawCode, fromCard = false) => {
    const code = String(rawCode || '').trim();
    if (!code) return;
    fromCard ? setApplyingCard(code) : setApplying(true);
    setVoucherError(null);
    try {
      const res = await validateVoucher({ code, subtotal: cart.subtotal, items: cart.items });
      if (res.valid) {
        cart.applyVoucher(res);
        setVoucherCode(res.code);
        toast.success('Voucher diterapkan', { description: res.label });
      } else {
        setVoucherError(res.reason || 'Voucher tidak valid');
        toast.error(res.reason || 'Voucher tidak valid');
      }
    } catch (e) {
      setVoucherError('Gagal memvalidasi voucher. Coba lagi.');
      toast.error('Gagal memvalidasi voucher');
    } finally {
      fromCard ? setApplyingCard(null) : setApplying(false);
    }
  };

  const removeVoucher = () => {
    cart.removeVoucher();
    setVoucherCode('');
    setVoucherError(null);
    toast.message('Voucher dihapus');
  };

  const empty = cart.items.length === 0;

  // Naikkan qty dengan validasi stok LIVE (katalog). Server tetap otoritatif (409).
  const incItem = (it) => {
    const maxStock = maxStockForItem(it, getById(it.productId));
    if (it.quantity >= maxStock) {
      toast.error(maxStock <= 0 ? 'Stok habis' : `Stok tersedia hanya ${maxStock}`);
      return;
    }
    cart.updateQty(it.key, it.quantity + 1);
  };

  return (
    <div className="cp-container cp-section" data-testid="cart-page">
      <div className="mb-8">
        <div className="cp-eyebrow">Keranjang</div>
        <Reveal>
          <h1 className="cp-headline text-4xl sm:text-6xl mt-2">Ringkasan belanja Anda.</h1>
        </Reveal>
      </div>

      {empty ? (
        <div className="py-24 flex flex-col items-center text-center gap-4">
          <div className="h-20 w-20 rounded-full border border-black/15 flex items-center justify-center">
            <ShoppingBag className="h-8 w-8 text-black/50" />
          </div>
          <div>
            <div className="cp-headline text-3xl">Keranjang Anda masih kosong</div>
            <div className="text-sm text-black/60 mt-2">Yuk mulai dari koleksi best seller kami.</div>
          </div>
          <Link to="/shop"><Button className="rounded-full bg-[color:var(--cp-ink)] text-[color:var(--cp-paper)] hover:bg-black">Lanjut Belanja</Button></Link>

          <div className="mt-16 w-full">
            <div className="cp-eyebrow mb-4">Rekomendasi</div>
            {/* Baris rekomendasi bergerak pelan sendiri, berhenti saat di-hover. */}
            <AutoCarousel
              speed={0.5}
              testId="cart-recommended-carousel"
              ariaLabel="Rekomendasi produk, geser otomatis"
              slideClass="w-[74%] sm:w-[42%] lg:w-[27%] xl:w-[22%]"
            >
              {recommended.map((p) => (
                <ProductCard key={p.id} product={p} onQuickView={openQuickView} />
              ))}
            </AutoCarousel>
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 lg:gap-10">
          <div className="lg:col-span-8">
            <div className="rounded-2xl border border-black/10 bg-[color:var(--cp-paper-warm)] overflow-hidden">
              <div className="px-5 py-3 border-b border-black/10 cp-mono uppercase text-[10px] tracking-[0.22em] text-black/60 grid grid-cols-6 gap-2">
                <div className="col-span-3">Produk</div>
                <div className="col-span-1 text-center hidden sm:block">Harga</div>
                <div className="col-span-1 text-center">Jumlah</div>
                <div className="col-span-1 text-right">Subtotal</div>
              </div>
              {cart.items.map((it) => (
                <div key={it.key} className="px-5 py-5 border-b border-black/10 last:border-0 grid grid-cols-6 gap-2 sm:gap-4 items-center" data-testid="cart-item">
                  <div className="col-span-6 sm:col-span-3 flex items-center gap-3 sm:gap-4">
                    <div className="h-20 w-16 sm:h-24 sm:w-20 rounded-xl overflow-hidden bg-[color:var(--cp-paper-fog)] flex-shrink-0">
                      <img src={it.image} alt={it.name} className="h-full w-full object-cover" />
                    </div>
                    <div className="min-w-0">
                      <Link to={`/parfum/${it.slug}`} className="text-sm font-medium truncate cp-hover-underline">{it.name}</Link>
                      <div className="cp-mono uppercase text-[10px] tracking-[0.22em] text-black/55 mt-1">{it.variantLabel || `${it.concentration ? it.concentration + ' · ' : ''}${it.variantType ? it.variantType + ' · ' : ''}${it.volumeMl}ml`}</div>
                      <button onClick={() => cart.removeItem(it.key)} className="mt-2 inline-flex items-center gap-1 cp-mono uppercase text-[10px] tracking-[0.22em] text-black/60 hover:text-black">
                        <Trash2 className="h-3 w-3" /> Hapus
                      </button>
                    </div>
                  </div>
                  <div className="col-span-2 sm:col-span-1 text-center cp-mono text-sm hidden sm:block">{formatIDR(it.unitPrice)}</div>
                  <div className="col-span-3 sm:col-span-1 flex sm:justify-center">
                    <div className="inline-flex items-center rounded-full border border-black/15">
                      <button onClick={() => cart.updateQty(it.key, it.quantity - 1)} className="h-9 w-9 flex items-center justify-center rounded-l-full hover:bg-black/5">
                        <Minus className="h-3.5 w-3.5" />
                      </button>
                      <span className="cp-mono w-8 text-center text-sm">{it.quantity}</span>
                      <button onClick={() => incItem(it)} disabled={it.quantity >= maxStockForItem(it, getById(it.productId))} className="h-9 w-9 flex items-center justify-center rounded-r-full hover:bg-black/5 disabled:opacity-40 disabled:cursor-not-allowed">
                        <Plus className="h-3.5 w-3.5" />
                      </button>
                    </div>
                  </div>
                  <div className="col-span-3 sm:col-span-1 text-right cp-mono text-sm font-semibold">{formatIDR(it.unitPrice * it.quantity)}</div>
                </div>
              ))}
            </div>

            <div className="mt-4 flex flex-wrap items-center gap-3">
              <Link to="/shop" className="cp-mono uppercase text-[11px] tracking-[0.22em] cp-hover-underline">← Lanjut Belanja</Link>
              <button onClick={cart.clear} className="ml-auto cp-mono uppercase text-[11px] tracking-[0.22em] text-black/60 hover:text-black">Kosongkan Keranjang</button>
            </div>

            {/* Voucher Center */}
            <div className="mt-8">
              <div className="flex items-center gap-2 mb-4">
                <Ticket className="h-5 w-5 text-[color:var(--cp-brass)]" />
                <div className="cp-mono uppercase text-[11px] tracking-[0.22em]">Voucher Tersedia</div>
                <Link to="/voucher" className="ml-auto cp-mono uppercase text-[10px] tracking-[0.22em] cp-hover-underline text-black/60">Lihat semua</Link>
              </div>
              <VoucherCenter
                subtotal={cart.subtotal}
                appliedCode={cart.voucher?.code || null}
                applyingCode={applyingCard}
                onApply={(code) => doApply(code, true)}
              />
            </div>
          </div>

          <aside className="lg:col-span-4">
            <div className="lg:sticky lg:top-28 rounded-2xl border border-black/10 bg-[color:var(--cp-paper-warm)] p-6">
              <div className="cp-mono uppercase text-[10px] tracking-[0.22em] text-black/60 mb-3">Voucher</div>
              <div className="flex items-center gap-2">
                <Input
                  placeholder="Masukkan kode voucher"
                  value={voucherCode}
                  onChange={(e) => setVoucherCode(e.target.value)}
                  onKeyDown={(e) => { if (e.key === 'Enter') doApply(voucherCode); }}
                  data-testid="cart-voucher-input"
                  aria-describedby="cart-voucher-error"
                  className="h-11 rounded-full bg-[color:var(--cp-paper)]"
                />
                <Button
                  onClick={() => doApply(voucherCode)}
                  disabled={applying || !voucherCode.trim()}
                  className="h-11 rounded-full bg-[color:var(--cp-ink)] text-[color:var(--cp-paper)] hover:bg-black disabled:opacity-60"
                  data-testid="cart-voucher-apply"
                >
                  {applying ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Terapkan'}
                </Button>
              </div>
              {voucherError && (
                <div id="cart-voucher-error" className="mt-2 text-[12px] text-red-600" data-testid="cart-voucher-error">
                  {voucherError}
                </div>
              )}
              {cart.voucher && (
                <div className="mt-3 flex items-center gap-2 cp-mono uppercase text-[10px] tracking-[0.22em] bg-[color:var(--cp-paper-fog)] rounded-full pl-3 pr-1 py-1 w-fit" data-testid="cart-voucher-chip">
                  <Tag className="h-3 w-3" /> {cart.voucher.code}
                  <button
                    onClick={removeVoucher}
                    aria-label="Hapus voucher"
                    data-testid="cart-voucher-remove"
                    className="h-6 w-6 rounded-full hover:bg-black/10 flex items-center justify-center"
                  >
                    <X className="h-3.5 w-3.5" />
                  </button>
                </div>
              )}

              <hr className="my-6 border-black/10" />

              <div className="space-y-2 text-sm">
                <div className="flex items-center justify-between">
                  <span className="text-black/60">Subtotal ({cart.totalQty} item)</span>
                  <span className="cp-mono">{formatIDR(cart.subtotal)}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-black/60">Diskon</span>
                  <span className="cp-mono text-[color:var(--cp-brass)]" data-testid="cart-discount">- {formatIDR(cart.discount)}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-black/60">Ongkir</span>
                  <span className="cp-mono text-black/50">Dihitung saat checkout</span>
                </div>
              </div>

              <hr className="my-6 border-black/10" />

              <div className="flex items-center justify-between">
                <span className="cp-mono uppercase text-[11px] tracking-[0.22em]">Total Sementara</span>
                <span className="cp-mono text-lg font-semibold" data-testid="cart-total">{formatIDR(Math.max(0, cart.subtotal - cart.discount))}</span>
              </div>

              <Button
                onClick={() => navigate('/checkout')}
                data-testid="cart-checkout-button"
                className="mt-6 w-full h-12 rounded-full cp-btn-gold"
              >
                Lanjut ke Checkout <ArrowRight className="h-4 w-4 ml-2" />
              </Button>
              <div className="mt-3 text-center cp-mono uppercase text-[10px] tracking-[0.22em] text-black/50">
                Pembayaran aman · Transfer / E-Wallet / COD
              </div>
            </div>
          </aside>
        </div>
      )}
    </div>
  );
}
