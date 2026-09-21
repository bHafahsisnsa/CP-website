import React from 'react';
import { Link } from 'react-router-dom';
import { ArrowUpRight, Sparkles } from 'lucide-react';
import { Reveal, Stagger, Item } from '../shared/Reveal';
import { useContent } from '../../store/ContentContext';

import { HOME_IMAGES } from '../../lib/realImages';

const FEATURED = [
  {
    title: 'Koleksi Best of Woody',
    tag: 'Curated',
    image: HOME_IMAGES.featured[0],
    to: '/shop?cat=woody',
    size: 'col-span-12 lg:col-span-8 h-[420px] lg:h-[520px]',
  },
  {
    title: 'Floral Baru',
    tag: 'Baru',
    image: HOME_IMAGES.featured[1],
    to: '/shop?cat=floral',
    size: 'col-span-12 lg:col-span-4 h-[260px] lg:h-[520px]',
  },
  {
    title: 'Diskon s.d. 30%',
    tag: 'Promo',
    image: HOME_IMAGES.featured[2],
    to: '/shop?promo=1',
    size: 'col-span-6 lg:col-span-4 h-[260px]',
  },
  {
    title: 'Best Seller Untuk Pria',
    tag: 'Populer',
    image: HOME_IMAGES.featured[3],
    to: '/shop?gender=pria',
    size: 'col-span-6 lg:col-span-4 h-[260px]',
  },
  {
    title: 'Signature Wanita',
    tag: 'Editorial',
    image: HOME_IMAGES.featured[4],
    to: '/shop?gender=wanita',
    size: 'col-span-12 lg:col-span-4 h-[220px] lg:h-[260px]',
  },
];

const FEATURED_DEFAULT = { eyebrow: 'Pilihan Kurator', title: 'Koleksi unggulan.' };

export const FeaturedCollection = () => {
  const c = useContent('featured', FEATURED_DEFAULT);
  // Konten kartu dari CMS di-merge di atas layout/gambar default (jaga tata letak).
  const cmsItems = Array.isArray(c.items) ? c.items : [];
  const items = FEATURED.map((base, i) => ({
    ...base,
    ...(cmsItems[i] || {}),
    image: (cmsItems[i] && cmsItems[i].image) || base.image,
    size: base.size,
  }));
  return (
    <section className="cp-section-md" data-testid="home-featured-collection">
      <div className="cp-container-wide">
        <div className="flex items-end justify-between gap-6 mb-8">
          <Reveal>
            <div>
              <div className="cp-eyebrow flex items-center gap-2">
                <Sparkles className="h-3.5 w-3.5" /> {c.eyebrow}
              </div>
              <h2 className="cp-headline mt-2 text-3xl sm:text-5xl lg:text-6xl">{c.title}</h2>
            </div>
          </Reveal>
          <Link
            to="/shop"
            className="hidden sm:inline-flex cp-mono uppercase text-[10px] tracking-[0.22em] border border-black/15 rounded-full px-4 py-2 hover:bg-black/5"
          >
            Semua Koleksi
          </Link>
        </div>

        <Stagger className="grid grid-cols-12 gap-3 md:gap-5">
          {items.map((f, i) => (
            <Item key={i} className={f.size}>
              <Link to={f.to || '/shop'} className="group relative block h-full rounded-2xl overflow-hidden bg-[color:var(--cp-paper-fog)]">
                <div className="absolute inset-0 overflow-hidden cp-kb">
                  <img
                    src={f.image}
                    alt={f.title}
                    loading="lazy"
                    className="h-full w-full object-cover transition-transform [transition-duration:1400ms] ease-out group-hover:scale-[1.06]"
                  />
                </div>
                <span aria-hidden className="cp-sheen" />
                <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-black/10 to-transparent" />
                <div className="absolute inset-x-0 bottom-0 p-5 sm:p-6 text-white">
                  <div className="cp-mono uppercase text-[10px] tracking-[0.22em] opacity-80">{f.tag}</div>
                  <div className="cp-headline text-2xl sm:text-3xl mt-1 flex items-center gap-2">
                    {f.title}
                    <ArrowUpRight className="h-5 w-5 opacity-70 group-hover:translate-x-1 group-hover:-translate-y-1 transition-transform" />
                  </div>
                </div>
              </Link>
            </Item>
          ))}
        </Stagger>
      </div>
    </section>
  );
};
