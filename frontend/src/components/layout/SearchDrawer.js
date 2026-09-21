import React from 'react';
import { Link } from 'react-router-dom';
import { Search as SearchIcon, X, TrendingUp } from 'lucide-react';
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetDescription } from '../ui/sheet';
import { useCatalog } from '../../store/CatalogContext';
import { formatIDR } from '../../lib/format';

export const SearchDrawer = ({ open, onOpenChange }) => {
  const { products } = useCatalog();
  const [query, setQuery] = React.useState('');
  const [recent, setRecent] = React.useState([]);

  React.useEffect(() => {
    try {
      const r = JSON.parse(localStorage.getItem('cp:recent-search') || '[]');
      setRecent(r);
    } catch (e) {}
  }, [open]);

  const results = React.useMemo(() => {
    if (!query.trim()) return [];
    const q = query.toLowerCase();
    return products.filter(
      (p) =>
        p.name.toLowerCase().includes(q) ||
        p.category.toLowerCase().includes(q) ||
        (p.tags || []).join(' ').toLowerCase().includes(q)
    ).slice(0, 8);
  }, [query, products]);

  const suggestions = ['Woody', 'Floral', 'Oud', 'Vanilla', 'Citrus', 'Pria', 'Wanita', 'Best Seller'];

  const trending = products.filter((p) => p.bestSeller).slice(0, 4);

  const commit = (term) => {
    const t = String(term).trim();
    if (!t) return;
    const next = [t, ...recent.filter((r) => r !== t)].slice(0, 6);
    setRecent(next);
    localStorage.setItem('cp:recent-search', JSON.stringify(next));
  };

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent
        side="top"
        data-testid="search-drawer-panel"
        className="cp-store h-[85vh] sm:h-[520px] p-0 cp-glass-panel rounded-b-none"
      >
        <SheetHeader className="sr-only">
          <SheetTitle>Cari Produk</SheetTitle>
          <SheetDescription>
            Ketik nama parfum, notes, atau kategori untuk mencari di katalog.
          </SheetDescription>
        </SheetHeader>
        <div className="cp-container py-5">
          <div className="flex items-center gap-3 border-b border-black/15 pb-3">
            <SearchIcon className="h-5 w-5 text-black/60" />
            <input
              autoFocus
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') commit(query);
              }}
              placeholder="Cari parfum, notes, atau kategori…"
              data-testid="search-input"
              className="flex-1 bg-transparent outline-none text-lg sm:text-xl placeholder:text-black/40 py-2"
            />
            <button onClick={() => onOpenChange(false)} className="p-2 rounded-full hover:bg-black/5" aria-label="Tutup">
              <X className="h-5 w-5" />
            </button>
          </div>

          {/* Empty state / suggestions */}
          {!query.trim() ? (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 pt-6">
              <div>
                <div className="cp-mono uppercase text-[11px] tracking-[0.22em] text-black/60 mb-3">Pencarian Terbaru</div>
                {recent.length === 0 ? (
                  <div className="text-sm text-black/50">Belum ada pencarian. Coba mulai dari saran di kanan.</div>
                ) : (
                  <div className="flex flex-wrap gap-2">
                    {recent.map((r) => (
                      <button
                        key={r}
                        onClick={() => setQuery(r)}
                        className="px-3 py-1.5 rounded-full border border-black/15 text-sm hover:bg-black/5"
                      >
                        {r}
                      </button>
                    ))}
                  </div>
                )}
                <div className="cp-mono uppercase text-[11px] tracking-[0.22em] text-black/60 mt-6 mb-3">Kata Kunci Populer</div>
                <div className="flex flex-wrap gap-2">
                  {suggestions.map((s) => (
                    <button
                      key={s}
                      onClick={() => setQuery(s)}
                      className="px-3 py-1.5 rounded-full border border-black/15 text-sm hover:bg-black/5"
                    >
                      {s}
                    </button>
                  ))}
                </div>
              </div>
              <div>
                <div className="cp-mono uppercase text-[11px] tracking-[0.22em] text-black/60 mb-3 flex items-center gap-2">
                  <TrendingUp className="h-3.5 w-3.5" /> Trending
                </div>
                <div className="grid grid-cols-2 gap-3">
                  {trending.map((p) => (
                    <Link
                      key={p.id}
                      to={`/parfum/${p.slug}`}
                      onClick={() => onOpenChange(false)}
                      className="flex items-center gap-3 p-2 rounded-xl hover:bg-black/5"
                    >
                      <div className="h-14 w-14 rounded-lg overflow-hidden bg-[color:var(--cp-paper-fog)]">
                        <img src={p.images[0]} alt={p.name} className="h-full w-full object-cover" />
                      </div>
                      <div className="min-w-0">
                        <div className="text-sm font-medium truncate">{p.name}</div>
                        <div className="cp-mono text-xs text-black/60">{formatIDR(p.price)}</div>
                      </div>
                    </Link>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <div className="pt-6">
              <div className="cp-mono uppercase text-[11px] tracking-[0.22em] text-black/60 mb-3">
                {results.length} Hasil untuk “{query}”
              </div>
              {results.length === 0 ? (
                <div className="text-sm text-black/50">Tidak ada hasil. Coba kata kunci lain atau saran di atas.</div>
              ) : (
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  {results.map((p) => (
                    <Link
                      key={p.id}
                      to={`/parfum/${p.slug}`}
                      onClick={() => { commit(query); onOpenChange(false); }}
                      data-testid="search-result-item"
                      className="flex items-center gap-3 p-2 rounded-xl hover:bg-black/5"
                    >
                      <div className="h-14 w-14 rounded-lg overflow-hidden bg-[color:var(--cp-paper-fog)]">
                        <img src={p.images[0]} alt={p.name} className="h-full w-full object-cover" />
                      </div>
                      <div className="min-w-0">
                        <div className="text-sm font-medium truncate">{p.name}</div>
                        <div className="cp-mono text-xs text-black/60">{p.concentration} · {formatIDR(p.price)}</div>
                      </div>
                    </Link>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </SheetContent>
    </Sheet>
  );
};
