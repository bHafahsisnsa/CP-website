// pages/ShopPage.js — Katalog (PLP) versi IMMERSIVE.
// Prinsip desain: gambar produk mendapat porsi terbesar (container lebar + gutter tipis +
// kartu rasio 4:5 sesuai artwork botol 900x1125), tipografi meta diperkecil, dan panel
// filter dibuat ramping + collapsible (lihat components/shop/ShopFilters.js).
import React from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { Filter, Grid2X2, LayoutGrid, RefreshCw, Loader2, X } from 'lucide-react';
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetDescription } from '../components/ui/sheet';
import { Button } from '../components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { ProductCard } from '../components/shared/ProductCard';
import { ProductGridSkeleton } from '../components/shared/Skeletons';
import Seo from '../components/shared/Seo';
import { ShopFilters } from '../components/shop/ShopFilters';
import { useQuickView } from '../store/QuickViewContext';
import { useCatalog } from '../store/CatalogContext';
import { fetchProducts } from '../services/catalog';
import { Reveal } from '../components/shared/Reveal';
import { formatIDR } from '../lib/format';

const CONCENTRATIONS = ['EDP', 'EDT'];
const GENDERS = ['Pria', 'Wanita', 'Unisex'];
const NOTES = ['Woody', 'Floral', 'Citrus', 'Amber', 'Vanilla', 'Oud', 'Musk', 'Fresh'];
const SORTS = [
  { value: 'featured', label: 'Unggulan' },
  { value: 'newest', label: 'Terbaru' },
  { value: 'best', label: 'Terlaris' },
  { value: 'low', label: 'Harga: Termurah' },
  { value: 'high', label: 'Harga: Termahal' },
];
const PRICE_MAX = 1500000;
// 8 = tepat 2 baris pada grid 4 kolom, dan menyisakan produk untuk tombol "Muat lebih banyak".
const PAGE_SIZE = 8;

const cap = (s) => (s ? s[0].toUpperCase() + s.slice(1) : s);
const useQuery = () => new URLSearchParams(useLocation().search);
// Parse param CSV (mendukung multi-nilai, mis. ?occasion=office,gym) -> array bersih.
const csvParam = (v) => (v ? v.split(',').map((s) => s.trim()).filter(Boolean) : []);
const nameOf = (list, slug) => (list.find((x) => x.slug === slug) || {}).name || slug;

// Sidebar filter di-MOUNT hanya pada layar lg+ (bukan cuma `hidden` via CSS) supaya
// data-testid filter tidak pernah duplikat saat filter sheet mobile terbuka.
const useMinWidth = (px) => {
  const [matches, setMatches] = React.useState(
    () => typeof window !== 'undefined' && window.matchMedia(`(min-width: ${px}px)`).matches
  );
  React.useEffect(() => {
    const mq = window.matchMedia(`(min-width: ${px}px)`);
    const onChange = (e) => setMatches(e.matches);
    setMatches(mq.matches);
    mq.addEventListener('change', onChange);
    return () => mq.removeEventListener('change', onChange);
  }, [px]);
  return matches;
};

export default function ShopPage() {
  const q = useQuery();
  const location = useLocation();
  const navigate = useNavigate();
  const { openQuickView } = useQuickView();
  const { categories, occasions, characters } = useCatalog();

  const [filterOpen, setFilterOpen] = React.useState(false);
  const [density, setDensity] = React.useState('normal'); // normal (kartu besar) | compact
  const isDesktop = useMinWidth(1024);

  const [cats, setCats] = React.useState(csvParam(q.get('cat')));
  const [occ, setOcc] = React.useState(csvParam(q.get('occasion')));
  const [chars, setChars] = React.useState(csvParam(q.get('character')));
  const [concs, setConcs] = React.useState([]);
  const [genders, setGenders] = React.useState(csvParam(q.get('gender')).map(cap));
  const [notes, setNotes] = React.useState([]);
  const [price, setPrice] = React.useState([0, PRICE_MAX]);
  const [debouncedPrice, setDebouncedPrice] = React.useState([0, PRICE_MAX]);
  const [sort, setSort] = React.useState('featured');
  const bestSellerOnly = q.get('bestSeller') === '1';
  const isNewOnly = q.get('isNew') === '1';

  const [items, setItems] = React.useState([]);
  const [total, setTotal] = React.useState(0);
  const [status, setStatus] = React.useState('loading'); // loading | ready | error
  const [loadingMore, setLoadingMore] = React.useState(false);
  const [reloadTick, setReloadTick] = React.useState(0);

  // Debounce slider harga agar tidak spam API.
  React.useEffect(() => {
    const t = setTimeout(() => setDebouncedPrice(price), 350);
    return () => clearTimeout(t);
  }, [price]);

  const buildParams = React.useCallback(
    (extra) => {
      const p = { sort, ...extra };
      if (cats.length) p.category = cats.join(',');
      if (occ.length) p.occasion = occ.join(',');
      if (chars.length) p.character = chars.join(',');
      if (genders.length) p.gender = genders.join(',');
      if (concs.length) p.concentration = concs.join(',');
      if (notes.length) p.tag = notes.join(',');
      if (debouncedPrice[0] > 0) p.min_price = debouncedPrice[0];
      if (debouncedPrice[1] < PRICE_MAX) p.max_price = debouncedPrice[1];
      if (bestSellerOnly) p.best_seller = 1;
      if (isNewOnly) p.is_new = 1;
      return p;
    },
    [cats, occ, chars, genders, concs, notes, debouncedPrice, sort, bestSellerOnly, isNewOnly]
  );

  // Fetch server-side saat filter/sort berubah (reset ke halaman pertama).
  React.useEffect(() => {
    let cancelled = false;
    setStatus('loading');
    fetchProducts(buildParams({ limit: PAGE_SIZE, skip: 0 }))
      .then((res) => {
        if (cancelled) return;
        setItems(res.items);
        setTotal(res.total);
        setStatus('ready');
      })
      .catch(() => {
        if (!cancelled) setStatus('error');
      });
    return () => {
      cancelled = true;
    };
  }, [buildParams, reloadTick]);

  // Sinkronkan filter aktif -> URL (shareable, restore saat refresh/back). Pakai replace
  // agar tidak menumpuk history; guard `target !== location.search` mencegah loop navigasi.
  React.useEffect(() => {
    const sp = new URLSearchParams();
    if (cats.length) sp.set('cat', cats.join(','));
    if (occ.length) sp.set('occasion', occ.join(','));
    if (chars.length) sp.set('character', chars.join(','));
    if (genders.length) sp.set('gender', genders.join(','));
    if (bestSellerOnly) sp.set('bestSeller', '1');
    if (isNewOnly) sp.set('isNew', '1');
    const qs = sp.toString();
    const target = qs ? `?${qs}` : '';
    if (target !== location.search) navigate({ search: target }, { replace: true });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [cats, occ, chars, genders, bestSellerOnly, isNewOnly]);

  const loadMore = async () => {
    setLoadingMore(true);
    try {
      const res = await fetchProducts(buildParams({ limit: PAGE_SIZE, skip: items.length }));
      setItems((prev) => [...prev, ...res.items]);
      setTotal(res.total);
    } catch (e) {
      /* biarkan tombol tetap; user bisa coba lagi */
    } finally {
      setLoadingMore(false);
    }
  };

  const toggleValue = (arr, setter, val) =>
    setter(arr.includes(val) ? arr.filter((v) => v !== val) : [...arr, val]);

  // Satu handler untuk semua facet -> props ShopFilters tetap ringkas.
  const handleToggle = React.useCallback(
    (kind, val) => {
      if (kind === 'cat') setCats((a) => (a.includes(val) ? a.filter((v) => v !== val) : [...a, val]));
      else if (kind === 'occasion') setOcc((a) => (a.includes(val) ? a.filter((v) => v !== val) : [...a, val]));
      else if (kind === 'character') setChars((a) => (a.includes(val) ? a.filter((v) => v !== val) : [...a, val]));
      else if (kind === 'concentration') setConcs((a) => (a.includes(val) ? a.filter((v) => v !== val) : [...a, val]));
      else if (kind === 'gender') setGenders((a) => (a.includes(val) ? a.filter((v) => v !== val) : [...a, val]));
      else if (kind === 'note') setNotes((a) => (a.includes(val) ? a.filter((v) => v !== val) : [...a, val]));
    },
    []
  );

  const clearAll = () => {
    setCats([]);
    setOcc([]);
    setChars([]);
    setConcs([]);
    setGenders([]);
    setNotes([]);
    setPrice([0, PRICE_MAX]);
    setSort('featured');
  };

  const hasMore = items.length < total;

  // Label facet aktif (occasion/character) untuk baris hitungan hasil.
  const activeFacetLabel = [
    ...occ.map((s) => nameOf(occasions, s)),
    ...chars.map((s) => nameOf(characters, s)),
  ]
    .filter(Boolean)
    .join(' · ');

  // Chip filter aktif (bisa dilepas satu-satu) di atas grid.
  const activeChips = [
    ...cats.map((s) => ({ k: `cat-${s}`, label: nameOf(categories, s), remove: () => toggleValue(cats, setCats, s) })),
    ...occ.map((s) => ({ k: `occasion-${s}`, label: nameOf(occasions, s), remove: () => toggleValue(occ, setOcc, s) })),
    ...chars.map((s) => ({ k: `character-${s}`, label: nameOf(characters, s), remove: () => toggleValue(chars, setChars, s) })),
    ...concs.map((s) => ({ k: `concentration-${s}`, label: s, remove: () => toggleValue(concs, setConcs, s) })),
    ...genders.map((s) => ({ k: `gender-${s}`, label: s, remove: () => toggleValue(genders, setGenders, s) })),
    ...notes.map((s) => ({ k: `note-${s}`, label: s, remove: () => toggleValue(notes, setNotes, s) })),
    ...(price[0] > 0 || price[1] < PRICE_MAX
      ? [{ k: 'price', label: `${formatIDR(price[0])} – ${formatIDR(price[1])}`, remove: () => setPrice([0, PRICE_MAX]) }]
      : []),
  ];

  const filterProps = {
    categories,
    occasions,
    characters,
    concentrationOptions: CONCENTRATIONS,
    genderOptions: GENDERS,
    noteOptions: NOTES,
    cats,
    occ,
    chars,
    concs,
    genders,
    notes,
    price,
    priceMax: PRICE_MAX,
    onToggle: handleToggle,
    onPriceChange: setPrice,
    onReset: clearAll,
  };

  // Grid: default kartu BESAR (maks 4 kolom di layar lebar), mode padat sampai 6 kolom.
  const gridClass =
    density === 'compact'
      ? 'grid gap-2.5 sm:gap-3 grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 2xl:grid-cols-6'
      : 'grid gap-3 sm:gap-4 grid-cols-2 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4';

  return (
    <div className="cp-container-wide pt-4 sm:pt-6 pb-16 sm:pb-20" data-testid="shop-page">
      <Seo
        title="Semua Parfum — Koleksi Collector Parfum"
        description="Jelajahi seluruh koleksi parfum original: filter berdasarkan kategori aroma, konsentrasi, gender, dan notes. Pengiriman nasional, original & bersegel."
      />

      {/* HEADER — kompak: tipografi dikecilkan agar fokus pindah ke gambar produk. */}
      <div className="flex flex-wrap items-end justify-between gap-x-8 gap-y-2">
        <div className="min-w-0">
          <div className="cp-eyebrow text-[9.5px] sm:text-[10px]">Toko</div>
          <Reveal>
            <h1 className="cp-headline mt-1 text-[28px] sm:text-[34px] lg:text-[42px] leading-[0.98]">
              Semua parfum, satu <em className="not-italic italic text-[color:var(--cp-brass)]">rak</em>.
            </h1>
          </Reveal>
        </div>
        <div className="cp-mono text-[10px] uppercase tracking-[0.18em] text-black/50 pb-1.5" data-testid="shop-count">
          {status === 'ready'
            ? `${total} produk ditemukan${activeFacetLabel ? ` · ${activeFacetLabel}` : ''}${bestSellerOnly ? ' · Best Seller' : ''}${isNewOnly ? ' · Baru' : ''}.`
            : 'Memuat koleksi…'}
        </div>
      </div>

      {/* TOOLBAR — pill glass yang menempel di bawah header saat scroll. */}
      <div className="sticky top-[var(--header-h)] z-20 pt-3 pb-2" data-testid="shop-toolbar">
        <div className="cp-glass rounded-full flex items-center gap-2 px-2 py-1.5">
          <button
            onClick={() => setFilterOpen(true)}
            className="lg:hidden inline-flex items-center gap-1.5 cp-mono uppercase text-[9px] tracking-[0.2em] rounded-full px-3 py-2 hover:bg-black/5"
            data-testid="shop-mobile-filter-button"
          >
            <Filter className="h-3.5 w-3.5" /> Filter
            {activeChips.length > 0 ? (
              <span className="cp-mono text-[9px] h-[15px] min-w-[15px] px-1 inline-flex items-center justify-center rounded-full bg-[color:var(--cp-ink)] text-[color:var(--cp-paper)]">
                {activeChips.length}
              </span>
            ) : null}
          </button>
          <span className="hidden lg:inline cp-mono uppercase text-[9px] tracking-[0.2em] text-black/45 pl-2">
            {status === 'ready' ? `${items.length}/${total} tampil` : '—'}
          </span>

          <div className="ml-auto flex items-center gap-1.5">
            <div className="hidden sm:inline-flex rounded-full border border-black/10 p-0.5">
              <button
                onClick={() => setDensity('normal')}
                className={`h-7 w-7 rounded-full flex items-center justify-center transition-colors ${density === 'normal' ? 'bg-black/[0.07]' : 'hover:bg-black/5'}`}
                aria-label="Kartu besar"
                title="Kartu besar"
                data-testid="shop-density-normal"
              >
                <Grid2X2 className="h-3.5 w-3.5" />
              </button>
              <button
                onClick={() => setDensity('compact')}
                className={`h-7 w-7 rounded-full flex items-center justify-center transition-colors ${density === 'compact' ? 'bg-black/[0.07]' : 'hover:bg-black/5'}`}
                aria-label="Kartu padat"
                title="Kartu padat"
                data-testid="shop-density-compact"
              >
                <LayoutGrid className="h-3.5 w-3.5" />
              </button>
            </div>
            <Select value={sort} onValueChange={setSort}>
              <SelectTrigger
                className="h-8 w-[148px] rounded-full border-black/10 bg-transparent cp-mono uppercase text-[9px] tracking-[0.18em]"
                data-testid="shop-sort-select"
              >
                <SelectValue />
              </SelectTrigger>
              <SelectContent className="cp-store">
                {SORTS.map((s) => (
                  <SelectItem key={s.value} value={s.value} className="text-[12px]">
                    {s.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>
      </div>

      {/* items-stretch (default) DIPERLUKAN: aside harus setinggi baris grid supaya panel
          filter `sticky` di dalamnya benar-benar menempel saat halaman discroll. Dengan
          items-start, tinggi aside = tinggi konten -> sticky ikut hilang saat scroll. */}
      <div className="flex gap-4 lg:gap-5 xl:gap-6">
        {isDesktop ? (
          <aside className="hidden lg:block w-[196px] xl:w-[214px] shrink-0" data-testid="shop-filters">
            <div className="sticky top-[calc(var(--header-h)+56px)] max-h-[calc(100vh-var(--header-h)-76px)] overflow-y-auto cp-thin-scroll pr-1">
              <ShopFilters variant="sidebar" {...filterProps} />
            </div>
          </aside>
        ) : null}

        <div className="flex-1 min-w-0">
          {activeChips.length > 0 ? (
            <div className="mb-3 flex flex-wrap items-center gap-1.5" data-testid="shop-active-filters">
              {activeChips.map((c) => (
                <button
                  key={c.k}
                  onClick={c.remove}
                  data-testid={`shop-active-filter-${c.k}`}
                  className="inline-flex items-center gap-1 cp-mono uppercase text-[9px] tracking-[0.16em] rounded-full border border-black/12 px-2.5 py-[6px] hover:bg-black/5 transition-colors"
                >
                  {c.label}
                  <X className="h-3 w-3 text-black/40" />
                </button>
              ))}
              <button
                onClick={clearAll}
                className="cp-mono uppercase text-[9px] tracking-[0.18em] text-black/45 hover:text-black/85 px-1.5 py-[6px] transition-colors"
                data-testid="shop-clear-all-chips"
              >
                Hapus semua
              </button>
            </div>
          ) : null}

          {status === 'loading' ? (
            <ProductGridSkeleton count={PAGE_SIZE} testId="shop-grid-loading" className={gridClass} />
          ) : status === 'error' ? (
            <div className="py-24 text-center" data-testid="shop-grid-error">
              <div className="cp-headline text-3xl">Gagal memuat produk.</div>
              <div className="text-sm text-black/60 mt-2">Periksa koneksi Anda lalu coba lagi.</div>
              <Button
                onClick={() => setReloadTick((t) => t + 1)}
                className="mt-6 rounded-full bg-[color:var(--cp-ink)] text-[color:var(--cp-paper)] hover:bg-black"
                data-testid="shop-retry-button"
              >
                <RefreshCw className="h-4 w-4 mr-2" /> Coba Lagi
              </Button>
            </div>
          ) : items.length === 0 ? (
            <div className="py-24 text-center" data-testid="shop-grid-empty">
              <div className="cp-headline text-3xl">Belum ada produk yang cocok.</div>
              <div className="text-sm text-black/60 mt-2">Coba ubah atau reset filter.</div>
              <Button
                onClick={clearAll}
                className="mt-6 rounded-full bg-[color:var(--cp-ink)] text-[color:var(--cp-paper)] hover:bg-black"
              >
                Reset Filter
              </Button>
            </div>
          ) : (
            <>
              <div className={gridClass} data-testid="shop-products-grid">
                {items.map((p, i) => (
                  <ProductCard key={p.id} product={p} onQuickView={openQuickView} priority={i < 4} />
                ))}
              </div>
              {hasMore ? (
                <div className="mt-10 flex justify-center">
                  <Button
                    onClick={loadMore}
                    disabled={loadingMore}
                    variant="outline"
                    className="rounded-full px-8 h-10 cp-mono uppercase text-[10px] tracking-[0.2em]"
                    data-testid="shop-load-more-button"
                  >
                    {loadingMore ? (
                      <>
                        <Loader2 className="h-4 w-4 mr-2 animate-spin" /> Memuat…
                      </>
                    ) : (
                      `Muat lebih banyak (${total - items.length})`
                    )}
                  </Button>
                </div>
              ) : null}
            </>
          )}
        </div>
      </div>

      <Sheet open={filterOpen} onOpenChange={setFilterOpen}>
        <SheetContent
          side="bottom"
          className="h-[86vh] p-0 bg-[color:var(--cp-paper-warm)]"
          data-testid="shop-mobile-filter-drawer"
        >
          <SheetHeader className="px-5 py-3.5 border-b border-black/10">
            <SheetTitle className="cp-mono uppercase text-[11px] tracking-[0.22em]">Filter</SheetTitle>
            <SheetDescription className="text-xs text-black/60">
              Saring katalog berdasarkan kategori aroma, occasion, character, konsentrasi, dan harga.
            </SheetDescription>
          </SheetHeader>
          <div className="px-5 py-4 overflow-y-auto h-[calc(86vh-64px)]">
            <ShopFilters variant="sheet" {...filterProps} onApply={() => setFilterOpen(false)} />
          </div>
        </SheetContent>
      </Sheet>
    </div>
  );
}
