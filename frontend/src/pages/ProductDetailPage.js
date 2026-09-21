// pages/ProductDetailPage.js — PDP versi IMMERSIVE.
// Perubahan utama: container lebar (gutter tipis), galeri mosaik 2x2 rasio 4:5 (artwork
// botol 900x1125 -> tidak terpotong seperti crop 16:10 sebelumnya), klik gambar membuka
// lightbox, dan tipografi panel info dirapikan/diperkecil agar gambar mendominasi.
import React from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import useEmblaCarousel from 'embla-carousel-react';
import {
  Heart, Minus, Plus, ShoppingBag, ChevronLeft, ChevronRight,
  Truck, RotateCcw, ShieldCheck, RefreshCw, Maximize2,
} from 'lucide-react';
import { Button } from '../components/ui/button';
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '../components/ui/accordion';
import { Skeleton } from '../components/ui/skeleton';
import { fetchProductBySlug, fetchProducts, fetchReviews } from '../services/catalog';
import { formatIDR } from '../lib/format';
import Seo from '../components/shared/Seo';
import { track } from '../services/analytics';
import { useCart } from '../store/CartContext';
import { useWishlist } from '../store/WishlistContext';
import { ProductCard } from '../components/shared/ProductCard';
import { ProductReviews, RatingInline } from '../components/shared/ProductReviews';
import { ImageLightbox } from '../components/shared/ImageLightbox';
import { AutoCarousel } from '../components/shared/AutoCarousel';
import { useQuickView } from '../store/QuickViewContext';
import { toast } from 'sonner';
import { Reveal } from '../components/shared/Reveal';
import { VariantSelector } from '../components/shared/VariantSelector';
import { findVariant, firstVariant, toCartVolume, priceRange } from '../lib/variants';
import { brandLabel, houseBrandName } from '../lib/brand';
import { useStoreSettings } from '../store/SettingsContext';
import { handleImageError, resolveMediaUrl } from '../lib/mediaUrl';

const PDPSkeleton = () => (
  <div className="cp-container-wide pt-6 pb-20" data-testid="pdp-loading">
    <Skeleton className="h-3 w-52 mb-6" />
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 lg:gap-10">
      <div className="lg:col-span-7 grid grid-cols-2 gap-3">
        <Skeleton className="aspect-[4/5] rounded-[20px]" />
        <Skeleton className="aspect-[4/5] rounded-[20px]" />
        <Skeleton className="aspect-[4/5] rounded-[20px]" />
        <Skeleton className="aspect-[4/5] rounded-[20px]" />
      </div>
      <div className="lg:col-span-5 space-y-4">
        <Skeleton className="h-3 w-40" />
        <Skeleton className="h-10 w-3/4" />
        <Skeleton className="h-5 w-1/3" />
        <Skeleton className="h-16 w-full" />
        <div className="flex gap-2">
          <Skeleton className="h-9 w-24 rounded-full" />
          <Skeleton className="h-9 w-24 rounded-full" />
          <Skeleton className="h-9 w-24 rounded-full" />
        </div>
        <Skeleton className="h-11 w-full rounded-full" />
      </div>
    </div>
  </div>
);

export default function ProductDetailPage() {
  const { slug } = useParams();
  const navigate = useNavigate();
  const cart = useCart();
  const wish = useWishlist();
  const { openQuickView } = useQuickView();
  const { settings } = useStoreSettings();

  const [product, setProduct] = React.useState(null);
  const [status, setStatus] = React.useState('loading'); // loading | ready | notfound | error
  const [sel, setSel] = React.useState({});
  const [qty, setQty] = React.useState(1);
  const [related, setRelated] = React.useState([]);
  const [reviews, setReviews] = React.useState([]);
  const [reviewsLoading, setReviewsLoading] = React.useState(true);
  const [reloadTick, setReloadTick] = React.useState(0);

  const [emblaRef, emblaApi] = useEmblaCarousel({ loop: true });
  const [selectedImg, setSelectedImg] = React.useState(0);

  // Lightbox galeri
  const [lbOpen, setLbOpen] = React.useState(false);
  const [lbIndex, setLbIndex] = React.useState(0);
  const openLightbox = (i) => { setLbIndex(i); setLbOpen(true); };

  // Tandai body selama PDP terbuka: sticky bar "Tambah/Beli" (mobile) ada di bawah, jadi
  // FAB chat digeser ke atas lewat CSS agar tidak menutupi tombol Beli. (lihat index.css)
  React.useEffect(() => {
    document.body.classList.add('cp-has-sticky-atc');
    return () => document.body.classList.remove('cp-has-sticky-atc');
  }, []);

  React.useEffect(() => {
    if (!emblaApi) return;
    const onSelect = () => setSelectedImg(emblaApi.selectedScrollSnap());
    emblaApi.on('select', onSelect);
    onSelect();
  }, [emblaApi, product]);

  React.useEffect(() => {
    let cancelled = false;
    setStatus('loading');
    setProduct(null);
    setQty(1);
    setReviews([]);
    setReviewsLoading(true);
    window.scrollTo({ top: 0, behavior: 'instant' });

    fetchProductBySlug(slug)
      .then(async (p) => {
        if (cancelled) return;
        setProduct(p);
        const fv = firstVariant(p);
        setSel(fv ? { ...fv.options } : {});
        setStatus('ready');
        // Analytics first-party (E7): event product_view (best-effort, PII-free).
        track('product_view', { product_id: p.id, meta: { category: p.category } });
        try {
          // Rekomendasi: kategori sama dulu, lalu dilengkapi produk terlaris lain sampai
          // cukup untuk mengisi baris carousel (minimal 6) — mencegah baris nyaris kosong.
          const rel = await fetchProducts({ category: p.category, limit: 12 });
          let list = rel.items.filter((x) => x.id !== p.id);
          if (list.length < 6) {
            const extra = await fetchProducts({ sort: 'best', limit: 12 });
            const seen = new Set([p.id, ...list.map((x) => x.id)]);
            list = [...list, ...extra.items.filter((x) => !seen.has(x.id))];
          }
          if (!cancelled) setRelated(list.slice(0, 8));
        } catch (e) { /* related opsional */ }
        try {
          const rev = await fetchReviews(p.id);
          if (!cancelled) setReviews(rev);
        } catch (e) { /* review opsional */ }
        finally { if (!cancelled) setReviewsLoading(false); }
      })
      .catch((err) => {
        if (cancelled) return;
        if (err && err.response && err.response.status === 404) setStatus('notfound');
        else setStatus('error');
      });
    return () => { cancelled = true; };
  }, [slug, reloadTick]);

  if (status === 'loading') return <PDPSkeleton />;

  if (status === 'notfound') {
    return (
      <div className="cp-container py-24 text-center" data-testid="pdp-not-found">
        <div className="cp-headline text-3xl">Produk tidak ditemukan.</div>
        <div className="text-sm text-black/60 mt-2">Mungkin produk sudah tidak tersedia.</div>
        <Link to="/shop" className="inline-block mt-6 cp-mono uppercase text-[11px] tracking-[0.22em] border border-black/15 rounded-full px-4 py-2">
          Kembali ke Toko
        </Link>
      </div>
    );
  }

  if (status === 'error') {
    return (
      <div className="cp-container py-24 text-center" data-testid="pdp-error">
        <div className="cp-headline text-3xl">Gagal memuat produk.</div>
        <div className="text-sm text-black/60 mt-2">Periksa koneksi Anda lalu coba lagi.</div>
        <Button
          onClick={() => setReloadTick((t) => t + 1)}
          className="mt-6 rounded-full bg-[color:var(--cp-ink)] text-[color:var(--cp-paper)] hover:bg-black"
          data-testid="pdp-retry-button"
        >
          <RefreshCw className="h-4 w-4 mr-2" /> Coba Lagi
        </Button>
      </div>
    );
  }

  const inWish = wish.has(product.id);

  const options = product.options || [];
  const range = priceRange(product);
  const selectedVariant = findVariant(product, sel);
  const priceNow = selectedVariant ? selectedVariant.price : product.price;
  const bLabel = brandLabel(product.brand, settings);
  const cmp = selectedVariant?.compare_at_price
    || (product.compareAtPrice && selectedVariant && product.compareAtPrice > selectedVariant.price ? product.compareAtPrice : null);
  const outOfStock = !selectedVariant || (selectedVariant.stock || 0) <= 0;
  const stockNow = selectedVariant?.stock || 0;
  const skuNow = selectedVariant?.sku;
  const variantLabelNow = selectedVariant
    ? options.map((o) => selectedVariant.options[o.name]).filter(Boolean).join(' / ')
    : '';

  const handleAdd = () => {
    if (!selectedVariant) { toast.error('Pilih varian terlebih dahulu'); return; }
    if (outOfStock) { toast.error('Varian ini sedang habis'); return; }
    cart.addItem(product, toCartVolume(product, selectedVariant), qty);
    toast.success(`${product.name} ditambahkan`, { description: `${variantLabelNow} · ${qty}x` });
  };
  const handleBuyNow = () => {
    if (!selectedVariant) { toast.error('Pilih varian terlebih dahulu'); return; }
    if (outOfStock) { toast.error('Varian ini sedang habis'); return; }
    cart.addItem(product, toCartVolume(product, selectedVariant), qty);
    navigate('/checkout');
  };

  return (
    <div data-testid="pdp-page">
      <Seo
        title={`${product.name} | ${settings?.store_name || 'Collector Parfum'}`}
        description={(product.description || '').slice(0, 160) || `Beli ${product.name} original & bersegel di Collector Parfum.`}
        image={product.images?.[0]}
        type="product"
        jsonLd={{
          '@context': 'https://schema.org',
          '@type': 'Product',
          name: product.name,
          // JSON-LD memakai merek RUMAH: data terstruktur tidak boleh mengklaim merek pihak lain
          // untuk produk "inspired by".
          brand: { '@type': 'Brand', name: houseBrandName(settings) },
          image: product.images || [],
          description: product.description || '',
          category: product.category,
          offers: {
            '@type': 'Offer',
            priceCurrency: 'IDR',
            price: priceNow || 0,
            availability: 'https://schema.org/InStock',
          },
          ...(product.ratingCount
            ? { aggregateRating: { '@type': 'AggregateRating', ratingValue: product.ratingAvg, reviewCount: product.ratingCount } }
            : {}),
        }}
      />
      <div className="cp-container-wide pt-4 sm:pt-5">
        <div className="cp-mono uppercase text-[9.5px] tracking-[0.2em] text-black/50">
          <Link to="/" className="cp-hover-underline">Beranda</Link> · <Link to="/shop" className="cp-hover-underline">Toko</Link> · <span className="text-black/80">{product.name}</span>
        </div>
      </div>

      <div className="cp-container-wide mt-4 lg:mt-6 grid grid-cols-1 lg:grid-cols-12 gap-6 lg:gap-10">
        {/* ---------------- GALERI ---------------- */}
        <div className="lg:col-span-7 xl:col-span-8">
          {/* Mobile: carousel penuh, tap untuk perbesar */}
          <div className="lg:hidden relative" data-testid="product-gallery">
            <div className="overflow-hidden rounded-[18px] bg-[color:var(--cp-paper-fog)]" ref={emblaRef}>
              <div className="flex">
                {product.images.map((src, i) => (
                  <div key={i} className="min-w-0 flex-[0_0_100%] aspect-[4/5]">
                    <img
                      src={resolveMediaUrl(src)}
                      alt={`${product.name} ${i + 1}`}
                      className="h-full w-full object-cover"
                      onError={handleImageError}
                      onClick={() => openLightbox(i)}
                    />
                  </div>
                ))}
              </div>
            </div>
            <button onClick={() => emblaApi && emblaApi.scrollPrev()} aria-label="Sebelumnya" data-testid="pdp-gallery-prev" className="absolute left-2 top-1/2 -translate-y-1/2 h-9 w-9 rounded-full cp-glass-pill flex items-center justify-center">
              <ChevronLeft className="h-4 w-4" />
            </button>
            <button onClick={() => emblaApi && emblaApi.scrollNext()} aria-label="Berikutnya" data-testid="pdp-gallery-next" className="absolute right-2 top-1/2 -translate-y-1/2 h-9 w-9 rounded-full cp-glass-pill flex items-center justify-center">
              <ChevronRight className="h-4 w-4" />
            </button>
            <div className="mt-3 flex items-center justify-center gap-1.5" data-testid="mobile-gallery-dots">
              {product.images.map((_, i) => (
                <button key={i} onClick={() => emblaApi && emblaApi.scrollTo(i)} aria-label={`Slide ${i + 1}`} className={`h-1.5 rounded-full transition-all ${selectedImg === i ? 'w-6 bg-[color:var(--cp-ink)]' : 'w-2 bg-black/25'}`} />
              ))}
            </div>
          </div>

          {/* Desktop: mosaik 2 kolom, semua gambar utuh (4:5). Idle -> ken-burns pelan;
              hover -> ken-burns berhenti, gambar zoom halus + kilau menyapu; klik -> lightbox. */}
          <div className="hidden lg:grid grid-cols-2 gap-3" data-testid="product-gallery-desktop">
            {product.images.map((src, i) => (
              <button
                key={i}
                type="button"
                onClick={() => openLightbox(i)}
                aria-label={`Perbesar gambar ${i + 1}`}
                data-testid={`pdp-gallery-image-${i}`}
                className="group relative overflow-hidden rounded-[20px] bg-[color:var(--cp-paper-fog)] border border-black/5 aspect-[4/5]"
              >
                <span className={`absolute inset-0 block overflow-hidden cp-kb ${i % 2 ? 'cp-kb-slow' : ''}`}>
                  <img
                    src={resolveMediaUrl(src)}
                    alt={`${product.name} ${i + 1}`}
                    loading={i === 0 ? 'eager' : 'lazy'}
                    onError={handleImageError}
                    className="h-full w-full object-cover transition-transform [transition-duration:900ms] ease-out group-hover:scale-[1.05]"
                  />
                </span>
                <span aria-hidden className="cp-sheen" />
                <span className="absolute bottom-3 right-3 h-9 w-9 rounded-full cp-glass-pill inline-flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
                  <Maximize2 className="h-3.5 w-3.5" />
                </span>
              </button>
            ))}
          </div>
        </div>

        {/* ---------------- PANEL INFO ---------------- */}
        <div className="lg:col-span-5 xl:col-span-4">
          <div className="lg:sticky lg:top-[calc(var(--header-h)+16px)]">
            <div className="cp-mono uppercase text-[9px] tracking-[0.2em] text-black/50">
              {product.concentration} · {product.gender}
            </div>
            {bLabel && (
              <div
                className={`cp-mono uppercase text-[9px] tracking-[0.2em] mt-1 ${bLabel.inspired ? 'text-black/40' : 'text-black/50'}`}
                data-testid="pdp-brand"
              >
                {bLabel.text}
              </div>
            )}
            <h1 className="cp-headline text-[26px] sm:text-[32px] lg:text-[38px] mt-1.5 leading-[1.02]">{product.name}</h1>
            <div className="mt-2">
              <RatingInline avg={product.ratingAvg} count={product.ratingCount} />
            </div>
            <div className="mt-2.5 flex items-baseline gap-2.5 flex-wrap">
              <div className="cp-mono text-[19px] font-semibold tracking-tight" data-testid="pdp-price">
                {formatIDR(priceNow)}
              </div>
              {cmp && (
                <div className="cp-mono text-[12px] text-black/40 line-through">{formatIDR(cmp)}</div>
              )}
              {cmp && selectedVariant && (
                <span className="cp-mono uppercase text-[9px] tracking-[0.18em] bg-[color:var(--cp-ink)] text-[color:var(--cp-paper)] px-2 py-1 rounded-full">
                  Hemat {formatIDR((cmp || 0) - selectedVariant.price)}
                </span>
              )}
              {range.hasRange && (
                <span className="cp-mono text-[10px] text-black/45" data-testid="pdp-price-range">
                  Rentang {formatIDR(range.min)} – {formatIDR(range.max)}
                </span>
              )}
            </div>
            <p className="text-[13px] text-black/70 mt-3 leading-relaxed">{product.description}</p>

            <div className="mt-5">
              <VariantSelector product={product} sel={sel} onChange={setSel} testidPrefix="pdp" />
              <div className="mt-2.5 cp-mono uppercase text-[9.5px] tracking-[0.2em] text-[color:var(--cp-brass)]" data-testid="pdp-stock-status">
                {stockNow > 0 ? `Stok tersedia (${stockNow})` : 'Habis'}
                {skuNow ? <span className="text-black/40 normal-case tracking-normal"> · SKU {skuNow}</span> : null}
              </div>
            </div>

            <div className="mt-5 flex flex-wrap items-center gap-2.5">
              <div className="inline-flex items-center rounded-full border border-black/15">
                <button onClick={() => setQty((q) => Math.max(1, q - 1))} aria-label="Kurangi jumlah" className="h-10 w-10 flex items-center justify-center rounded-l-full hover:bg-black/5">
                  <Minus className="h-3.5 w-3.5" />
                </button>
                <span className="cp-mono w-9 text-center text-[13px]" data-testid="pdp-quantity-input">{qty}</span>
                <button onClick={() => setQty((q) => q + 1)} aria-label="Tambah jumlah" className="h-10 w-10 flex items-center justify-center rounded-r-full hover:bg-black/5">
                  <Plus className="h-3.5 w-3.5" />
                </button>
              </div>
              <Button onClick={handleAdd} disabled={outOfStock} data-testid="pdp-add-to-cart-button" className="h-10 rounded-full bg-[color:var(--cp-ink)] hover:bg-black text-[color:var(--cp-paper)] px-5 text-[12px] disabled:opacity-50 disabled:cursor-not-allowed">
                <ShoppingBag className="h-3.5 w-3.5 mr-2" /> {outOfStock ? 'Stok Habis' : 'Tambah ke Keranjang'}
              </Button>
              <Button onClick={handleBuyNow} disabled={outOfStock} data-testid="pdp-buy-now-button" className="h-10 rounded-full px-5 text-[12px] cp-btn-gold disabled:opacity-50 disabled:cursor-not-allowed">
                Beli Sekarang
              </Button>
              <button
                onClick={() => { wish.toggle(product.id); toast(inWish ? 'Dihapus dari wishlist' : 'Ditambahkan ke wishlist'); }}
                data-testid="pdp-wishlist-button"
                className={`h-10 w-10 rounded-full border border-black/20 flex items-center justify-center ${inWish ? 'bg-black/5' : ''}`}
                aria-label="Wishlist"
              >
                <Heart className={`h-3.5 w-3.5 ${inWish ? 'fill-[color:var(--cp-ink)] text-[color:var(--cp-ink)]' : ''}`} />
              </button>
            </div>

            <div className="mt-6">
              <div className="cp-mono uppercase text-[9px] tracking-[0.2em] text-black/55 mb-2">Piramida Aroma</div>
              <div className="grid grid-cols-3 gap-2">
                {[
                  { label: 'Top', items: product.notes.top },
                  { label: 'Heart', items: product.notes.heart },
                  { label: 'Base', items: product.notes.base },
                ].map((row, idx) => (
                  <div key={row.label} className={`rounded-[16px] p-3 ${idx === 0 ? 'bg-[color:var(--cp-paper-fog)]' : idx === 1 ? 'bg-[color:var(--cp-paper-warm)] border border-black/10' : 'bg-[color:var(--cp-ink)] text-[color:var(--cp-paper)]'}`}>
                    <div className="cp-mono uppercase text-[8.5px] tracking-[0.2em] opacity-60">{row.label}</div>
                    <div className="mt-1.5 text-[12px] leading-snug">{(row.items || []).join(', ')}</div>
                  </div>
                ))}
              </div>
            </div>

            <div className="mt-5 grid grid-cols-3 gap-2 text-[10.5px]">
              {[
                { icon: Truck, label: 'Gratis Ongkir', desc: 'Min. Rp 350.000' },
                { icon: ShieldCheck, label: 'Original', desc: 'Kartu autentikasi' },
                { icon: RotateCcw, label: 'Retur 3 Hari', desc: 'Segel utuh' },
              ].map((r, i) => (
                <div key={i} className="flex items-start gap-1.5">
                  <r.icon className="h-3.5 w-3.5 text-[color:var(--cp-brass)] mt-0.5 shrink-0" />
                  <div className="min-w-0">
                    <div className="font-semibold">{r.label}</div>
                    <div className="text-black/55">{r.desc}</div>
                  </div>
                </div>
              ))}
            </div>

            <Accordion type="single" collapsible className="mt-6" data-testid="pdp-accordion">
              <AccordionItem value="desc" data-testid="accordion-item">
                <AccordionTrigger className="cp-mono uppercase text-[10px] tracking-[0.2em] py-3">Deskripsi Lengkap</AccordionTrigger>
                <AccordionContent className="text-[12.5px] text-black/70">
                  {product.description} Dikemas dalam botol premium dengan atomiser presisi. Cocok untuk pemakaian harian maupun momen istimewa.
                </AccordionContent>
              </AccordionItem>
              <AccordionItem value="perf" data-testid="accordion-item">
                <AccordionTrigger className="cp-mono uppercase text-[10px] tracking-[0.2em] py-3">Ketahanan &amp; Sillage</AccordionTrigger>
                <AccordionContent className="text-[12.5px] text-black/70">
                  <ul className="space-y-1">
                    <li>Longevity: {product.performance.longevity}</li>
                    <li>Sillage: {product.performance.sillage}</li>
                    <li>Musim: {product.performance.season}</li>
                  </ul>
                </AccordionContent>
              </AccordionItem>
              <AccordionItem value="ingredients" data-testid="accordion-item">
                <AccordionTrigger className="cp-mono uppercase text-[10px] tracking-[0.2em] py-3">Kandungan</AccordionTrigger>
                <AccordionContent className="text-[12.5px] text-black/70">
                  {product.ingredients || 'Alcohol Denat., Parfum (Fragrance), Aqua, dan bahan aromatik pilihan.'}
                </AccordionContent>
              </AccordionItem>
              <AccordionItem value="ship" data-testid="accordion-item">
                <AccordionTrigger className="cp-mono uppercase text-[10px] tracking-[0.2em] py-3">Pengiriman</AccordionTrigger>
                <AccordionContent className="text-[12.5px] text-black/70">
                  Diproses maksimal 1x24 jam kerja. Reguler 2–4 hari, ekspres 1–2 hari. COD tersedia.
                </AccordionContent>
              </AccordionItem>
            </Accordion>
          </div>
        </div>
      </div>

      <ProductReviews reviews={reviews} loading={reviewsLoading} avg={product.ratingAvg} count={product.ratingCount} />

      {related.length > 0 && (
        <section className="pb-16 sm:pb-20">
          <div className="cp-container-wide">
            <div className="mb-5">
              <div className="cp-eyebrow text-[9.5px]">Anda mungkin suka</div>
              <Reveal>
                <h3 className="cp-headline text-2xl sm:text-[32px] mt-1.5">Aroma yang <em className="italic not-italic text-[color:var(--cp-brass)]">senada</em>.</h3>
              </Reveal>
            </div>
            {/* Baris rekomendasi bergeser pelan sendiri, berhenti saat di-hover. */}
            <AutoCarousel
              speed={0.5}
              testId="pdp-related-carousel"
              prevTestId="pdp-related-prev"
              nextTestId="pdp-related-next"
              ariaLabel="Produk terkait, geser otomatis"
              slideClass="w-[74%] sm:w-[42%] lg:w-[27%] xl:w-[22%]"
            >
              {related.map((p) => (
                <ProductCard key={p.id} product={p} onQuickView={openQuickView} />
              ))}
            </AutoCarousel>
          </div>
        </section>
      )}

      <ImageLightbox
        images={product.images}
        index={lbIndex}
        open={lbOpen}
        onOpenChange={setLbOpen}
        onIndexChange={setLbIndex}
        title={product.name}
      />

      <div
        data-testid="pdp-sticky-atc-bar"
        className="lg:hidden fixed bottom-16 left-0 right-0 z-40 bg-[color:var(--cp-paper-warm)] border-t border-black/10 shadow-[0_-10px_30px_rgba(0,0,0,0.08)]"
        style={{ paddingBottom: 'env(safe-area-inset-bottom, 0px)' }}
      >
        <div className="px-4 py-3 flex items-center gap-3">
          <div className="h-10 w-10 rounded-lg overflow-hidden bg-[color:var(--cp-paper-fog)] flex-shrink-0">
            <img src={resolveMediaUrl((product.images || [])[0])} alt={product.name} onError={handleImageError} className="h-full w-full object-cover" />
          </div>
          <div className="min-w-0 flex-1">
            <div className="cp-mono text-sm font-semibold truncate">{formatIDR(priceNow)}</div>
            <div className="cp-mono uppercase text-[10px] tracking-[0.2em] text-black/60">{variantLabelNow || '—'}</div>
          </div>
          <Button onClick={handleAdd} disabled={outOfStock} data-testid="pdp-sticky-atc-button" className="h-10 rounded-full bg-[color:var(--cp-ink)] text-[color:var(--cp-paper)] hover:bg-black px-4 cp-mono uppercase text-[10px] tracking-[0.22em] disabled:opacity-50 disabled:cursor-not-allowed">
            <ShoppingBag className="h-3.5 w-3.5 mr-1" /> {outOfStock ? 'Habis' : 'Tambah'}
          </Button>
          <Button onClick={handleBuyNow} disabled={outOfStock} className="h-10 rounded-full cp-btn-gold px-4 cp-mono uppercase text-[10px] tracking-[0.22em] disabled:opacity-50 disabled:cursor-not-allowed">
            Beli
          </Button>
        </div>
      </div>
    </div>
  );
}
