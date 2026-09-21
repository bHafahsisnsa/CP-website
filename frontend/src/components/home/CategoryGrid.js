import React from 'react';
import { Link } from 'react-router-dom';
import { ArrowUpRight } from 'lucide-react';
import { useCatalog } from '../../store/CatalogContext';
import { useContent } from '../../store/ContentContext';
import { Skeleton } from '../ui/skeleton';
import { Reveal, Stagger, Item } from '../shared/Reveal';
import { handleImageError, resolveMediaUrl } from '../../lib/mediaUrl';

const CAT_DEFAULT = {
  eyebrow: 'Keluarga Aroma', title: 'Temukan karaktermu.',
  subtitle: 'Setiap keluarga aroma punya kepribadian sendiri. Pilih yang paling cocok dengan cerita hari-harimu.',
};

export const CategoryGrid = () => {
  const { categories, loading } = useCatalog();
  const c = useContent('category_section', CAT_DEFAULT);
  return (
    <section className="cp-section" data-testid="home-category-section">
      <div className="cp-container-wide">
        <div className="flex items-end justify-between gap-6 mb-10">
          <Reveal>
            <div>
              <div className="cp-eyebrow">{c.eyebrow}</div>
              <h2 className="cp-headline mt-2 text-3xl sm:text-5xl lg:text-6xl">{c.title}</h2>
            </div>
          </Reveal>
          <Reveal delay={0.1} className="hidden sm:block max-w-sm text-sm text-black/60">
            {c.subtitle}
          </Reveal>
        </div>

        {loading && categories.length === 0 ? (
          <div className="grid grid-cols-2 md:grid-cols-3 gap-3 md:gap-5" data-testid="home-category-loading">
            {Array.from({ length: 6 }).map((_, i) => (
              <Skeleton key={i} className="aspect-[3/4] rounded-2xl" />
            ))}
          </div>
        ) : (
          <Stagger className="grid grid-cols-2 md:grid-cols-3 gap-3 md:gap-5">
            {categories.map((c) => (
              <Item key={c.slug}>
                <Link
                  to={`/shop?cat=${c.slug}`}
                  data-testid="category-card"
                  className="group relative block overflow-hidden rounded-2xl aspect-[3/4] bg-[color:var(--cp-paper-fog)]"
                >
                  {/* Ken Burns lambat saat idle, TENANG saat hover; ditambah zoom halus
                      via CSS transform pada <img> (transform bersarang -> tidak bentrok). */}
                  <div className="absolute inset-0 overflow-hidden cp-kb">
                    <img
                      src={resolveMediaUrl(c.image)}
                      alt={c.name}
                      loading="lazy"
                      onError={handleImageError}
                      className="h-full w-full object-cover transition-transform [transition-duration:1200ms] ease-out group-hover:scale-[1.06]"
                    />
                  </div>
                  <span aria-hidden className="cp-sheen" />
                  <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-black/10 to-transparent" />
                  <div className="absolute inset-x-0 bottom-0 p-5 text-white">
                    <div className="cp-mono uppercase text-[10px] tracking-[0.22em] opacity-80">Kategori</div>
                    <div className="cp-headline text-2xl md:text-3xl mt-1 flex items-center gap-2">
                      {c.name}
                      <ArrowUpRight className="h-5 w-5 opacity-70 transition-transform group-hover:translate-x-1 group-hover:-translate-y-1" />
                    </div>
                    <div className="text-xs opacity-80 mt-1 hidden md:block">{c.desc}</div>
                  </div>
                </Link>
              </Item>
            ))}
          </Stagger>
        )}
      </div>
    </section>
  );
};
