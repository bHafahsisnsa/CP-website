// components/home/GallerySection.js — Galeri foto dari CMS (section `gallery`).
// Tiga tata letak: masonry, grid, strip. Klik foto -> lightbox (atau tautan bila diisi).
import React from 'react';
import { Link } from 'react-router-dom';
import { ArrowUpRight } from 'lucide-react';
import { Reveal } from '../shared/Reveal';
import { SmartImage } from '../shared/SmartImage';
import { ImageLightbox } from '../shared/ImageLightbox';
import { useContent } from '../../store/ContentContext';

const GALLERY_DEFAULT = {
  eyebrow: 'Galeri', title: 'Dari rak', title_accent: 'ke tanganmu.',
  subtitle: 'Suasana toko, botol pilihan, dan momen pelanggan kami.',
  layout: 'masonry', items: [], cta_label: '', cta_to: '',
};

const isExternal = (to) => /^https?:\/\//i.test(to || '');

const Tile = ({ item, index, layout, onOpen }) => {
  const shape = layout === 'grid' ? 'aspect-square'
    : layout === 'strip' ? 'h-64 sm:h-80 w-[240px] sm:w-[300px] shrink-0'
      : ['aspect-[4/5]', 'aspect-square', 'aspect-[3/4]', 'aspect-[5/4]'][index % 4];
  const inner = (
    <>
      <SmartImage src={item.image} alt={item.caption || `Galeri ${index + 1}`} className="h-full w-full" imgClassName="h-full w-full object-cover transition-transform duration-700 group-hover:scale-[1.04]" showRetry={false} />
      {item.caption ? (
        <div className="absolute inset-x-0 bottom-0 p-3 sm:p-4 bg-gradient-to-t from-black/70 via-black/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300">
          <div className="text-white text-xs sm:text-sm leading-snug">{item.caption}</div>
        </div>
      ) : null}
    </>
  );
  const cls = `group relative block overflow-hidden rounded-2xl bg-[color:var(--cp-paper-fog)] ${shape} ${layout === 'masonry' ? 'mb-3 sm:mb-4 break-inside-avoid' : ''}`;
  if (item.to) {
    return isExternal(item.to)
      ? <a href={item.to} target="_blank" rel="noopener noreferrer" className={cls} data-testid={`home-gallery-item-${index}`}>{inner}</a>
      : <Link to={item.to} className={cls} data-testid={`home-gallery-item-${index}`}>{inner}</Link>;
  }
  return (
    <button type="button" onClick={() => onOpen(index)} className={`${cls} text-left`} data-testid={`home-gallery-item-${index}`}>
      {inner}
    </button>
  );
};

export const GallerySection = () => {
  const c = useContent('gallery', GALLERY_DEFAULT);
  const items = Array.isArray(c.items) ? c.items.filter((it) => it && it.image) : [];
  const [open, setOpen] = React.useState(false);
  const [idx, setIdx] = React.useState(0);
  if (items.length === 0) return null;
  const layout = c.layout || 'masonry';
  const onOpen = (i) => { setIdx(i); setOpen(true); };

  return (
    <section className="cp-section-md" data-testid="home-gallery">
      <div className="cp-container-wide">
        <div className="flex items-end justify-between gap-6 mb-8 md:mb-10 flex-wrap">
          <Reveal>
            <div>
              <div className="cp-eyebrow">{c.eyebrow}</div>
              <h2 className="cp-headline mt-2 text-3xl sm:text-5xl lg:text-6xl">
                {c.title} <em className="not-italic italic text-[color:var(--cp-brass)]">{c.title_accent}</em>
              </h2>
            </div>
          </Reveal>
          {c.subtitle ? <Reveal delay={0.1} className="max-w-sm text-sm text-black/60">{c.subtitle}</Reveal> : null}
        </div>

        {layout === 'strip' ? (
          <div className="flex gap-3 sm:gap-4 overflow-x-auto pb-3 -mx-4 px-4 sm:mx-0 sm:px-0 snap-x" data-testid="home-gallery-strip">
            {items.map((it, i) => <div key={`${it.image}-${i}`} className="snap-start"><Tile item={it} index={i} layout={layout} onOpen={onOpen} /></div>)}
          </div>
        ) : layout === 'grid' ? (
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3 sm:gap-4" data-testid="home-gallery-grid">
            {items.map((it, i) => <Tile key={`${it.image}-${i}`} item={it} index={i} layout={layout} onOpen={onOpen} />)}
          </div>
        ) : (
          <div className="columns-2 sm:columns-3 lg:columns-4 gap-3 sm:gap-4" data-testid="home-gallery-masonry">
            {items.map((it, i) => <Tile key={`${it.image}-${i}`} item={it} index={i} layout={layout} onOpen={onOpen} />)}
          </div>
        )}

        {c.cta_label && c.cta_to ? (
          <div className="mt-8 flex justify-center">
            {isExternal(c.cta_to) ? (
              <a href={c.cta_to} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1.5 cp-mono uppercase text-[11px] tracking-[0.2em] text-black/70 hover:text-black cp-hover-underline" data-testid="home-gallery-cta">
                {c.cta_label} <ArrowUpRight className="h-3.5 w-3.5" />
              </a>
            ) : (
              <Link to={c.cta_to} className="inline-flex items-center gap-1.5 cp-mono uppercase text-[11px] tracking-[0.2em] text-black/70 hover:text-black cp-hover-underline" data-testid="home-gallery-cta">
                {c.cta_label} <ArrowUpRight className="h-3.5 w-3.5" />
              </Link>
            )}
          </div>
        ) : null}
      </div>
      <ImageLightbox images={items.map((it) => it.image)} index={idx} open={open} onOpenChange={setOpen} onIndexChange={setIdx} title={c.title} />
    </section>
  );
};
