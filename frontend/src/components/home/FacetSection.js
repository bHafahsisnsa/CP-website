// components/home/FacetSection.js — section chip generik untuk facet MULTI storefront
// (Shop by Occasion / Shop by Character). Ikon dari lucide (dipetakan via taxonomyIcons),
// heading dikelola via CMS (useContent). Klik chip -> /shop?<paramKey>=<slug>.
import React from 'react';
import { Link } from 'react-router-dom';
import { useContent } from '../../store/ContentContext';
import { getFacetIcon } from '../../lib/taxonomyIcons';
import { Skeleton } from '../ui/skeleton';
import { Reveal, Stagger, Item } from '../shared/Reveal';

export const FacetSection = ({
  items = [],
  loading = false,
  contentKey,
  defaults,
  paramKey,
  testidPrefix,
  gridClass,
  skeletonCount = 8,
}) => {
  const c = useContent(contentKey, defaults);
  const showSkeleton = loading && items.length === 0;

  return (
    <section className="cp-section-md" data-testid={`${testidPrefix}-section`}>
      <div className="cp-container-wide">
        <div className="flex items-end justify-between gap-6 mb-8 md:mb-10">
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

        {showSkeleton ? (
          <div className={gridClass} data-testid={`${testidPrefix}-loading`}>
            {Array.from({ length: skeletonCount }).map((_, i) => (
              <Skeleton key={i} className="h-[104px] rounded-2xl" />
            ))}
          </div>
        ) : (
          <Stagger className={gridClass}>
            {items.map((f) => {
              const Icon = getFacetIcon(f.icon);
              return (
                <Item key={f.slug}>
                  <Link
                    to={`/shop?${paramKey}=${f.slug}`}
                    title={f.desc || f.name}
                    aria-label={`${f.name}`}
                    data-testid={`${testidPrefix}-chip`}
                    className="group cp-glass rounded-2xl px-3 py-5 flex flex-col items-center justify-center gap-2.5 text-center outline-none transition-transform duration-200 hover:-translate-y-1 focus-visible:-translate-y-1 focus-visible:ring-2 focus-visible:ring-[color:var(--cp-brass)]/50"
                  >
                    <span className="h-12 w-12 rounded-full grid place-items-center bg-[color:var(--cp-brass)]/15 text-[color:var(--cp-brass)] transition-all duration-300 group-hover:bg-[color:var(--cp-brass)] group-hover:text-white group-hover:scale-110 group-hover:-rotate-6">
                      <Icon className="h-5 w-5" strokeWidth={1.6} />
                    </span>
                    <span className="cp-mono uppercase text-[10.5px] tracking-[0.16em] leading-tight text-[color:var(--cp-ink)]">
                      {f.name}
                    </span>
                  </Link>
                </Item>
              );
            })}
          </Stagger>
        )}
      </div>
    </section>
  );
};

export const ShopByOccasion = ({ items, loading }) => (
  <FacetSection
    items={items}
    loading={loading}
    contentKey="occasion_section"
    defaults={{
      eyebrow: 'Shop by Occasion',
      title: 'Pilih sesuai momen.',
      subtitle: 'Dari meeting pagi hingga malam istimewa — temukan aroma yang pas untuk setiap kesempatan.',
    }}
    paramKey="occasion"
    testidPrefix="home-occasion"
    gridClass="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-8 gap-2.5 md:gap-3"
    skeletonCount={8}
  />
);

export const ShopByCharacter = ({ items, loading }) => (
  <FacetSection
    items={items}
    loading={loading}
    contentKey="character_section"
    defaults={{
      eyebrow: 'Shop by Character',
      title: 'Temukan karaktermu.',
      subtitle: 'Setiap karakter aroma punya kepribadian sendiri. Pilih yang paling mewakili dirimu.',
    }}
    paramKey="character"
    testidPrefix="home-character"
    gridClass="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-6 gap-2.5 md:gap-3"
    skeletonCount={12}
  />
);
