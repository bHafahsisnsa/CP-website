import React from 'react';
import { Link } from 'react-router-dom';
import { ArrowUpRight } from 'lucide-react';
import { Reveal } from '../shared/Reveal';
import { RotatingSticker } from '../shared/RotatingSticker';
import { useContent } from '../../store/ContentContext';

import { HOME_IMAGES } from '../../lib/realImages';

const IMG_1 = HOME_IMAGES.media.large;
const IMG_2 = HOME_IMAGES.media.cards[0];
const IMG_3 = HOME_IMAGES.media.cards[1];

const MEDIA_DEFAULT = {
  eyebrow: 'Cerita Aroma', title: 'Editorial yang menemani harimu.',
  large_tag: 'Featured', large_title: 'Malam yang membekas.',
  large_desc: 'Amber dan oud yang hangat untuk momen paling personal.',
  large_to: '/shop?cat=amber', large_image: '',
  cards: [
    { tag: 'Baru', title: 'Bouquet putih, siang cerah.', to: '/shop?cat=floral', image: '' },
    { tag: 'Trending', title: 'Woody yang tenang.', to: '/shop?cat=woody', image: '' },
  ],
};

export const MediaGridSection = () => {
  const c = useContent('media_editorial', MEDIA_DEFAULT);
  const cards = (Array.isArray(c.cards) && c.cards.length ? c.cards : MEDIA_DEFAULT.cards);
  const rightImgs = [IMG_2, IMG_3];
  return (
    <section className="cp-section-md" data-testid="home-media-grid">
      <div className="cp-container-wide">
        <Reveal>
          <div className="max-w-2xl mb-10">
            <div className="cp-eyebrow">{c.eyebrow}</div>
            <h2 className="cp-headline mt-2 text-3xl sm:text-5xl lg:text-6xl">{c.title}</h2>
          </div>
        </Reveal>

        <div className="grid grid-cols-12 gap-3 md:gap-5">
          {/* Big feature card */}
          <Link
            to={c.large_to || '/shop?cat=amber'}
            data-testid="home-media-grid-large"
            className="col-span-12 lg:col-span-7 group relative overflow-hidden rounded-2xl aspect-[4/3] lg:aspect-auto lg:h-[540px] bg-[color:var(--cp-ink)]"
          >
            <div className="absolute inset-0 overflow-hidden cp-kb cp-kb-slow">
              <img
                src={c.large_image || IMG_1}
                alt="Editorial parfum"
                className="h-full w-full object-cover opacity-90 transition-transform [transition-duration:1400ms] ease-out group-hover:scale-[1.06]"
              />
            </div>
            <span aria-hidden className="cp-sheen" />
            <div className="absolute inset-0 bg-gradient-to-t from-black/70 via-black/20 to-transparent" />
            <div className="absolute top-6 right-6 text-[color:var(--cp-paper)]">
              <RotatingSticker text="BEST DEAL • UP TO 30% • EDISI TERBATAS •" />
            </div>
            <div className="absolute inset-x-0 bottom-0 p-8 text-white">
              <div className="cp-mono uppercase text-[10px] tracking-[0.22em] opacity-80">{c.large_tag}</div>
              <div className="cp-headline text-3xl sm:text-4xl mt-2">{c.large_title}</div>
              <div className="text-sm opacity-80 mt-2 max-w-md">
                {c.large_desc}
              </div>
              <div className="mt-4 inline-flex items-center gap-2 cp-mono uppercase text-[11px] tracking-[0.22em] group-hover:gap-3 transition-all">
                Jelajahi <ArrowUpRight className="h-4 w-4" />
              </div>
            </div>
          </Link>

          {/* Right column stack */}
          <div className="col-span-12 lg:col-span-5 grid grid-cols-1 gap-3 md:gap-5">
            {cards.slice(0, 2).map((it, i) => (
              <Link
                key={i}
                to={it.to || '/shop'}
                className="group relative overflow-hidden rounded-2xl aspect-[16/10] lg:aspect-auto lg:h-[260px] bg-[color:var(--cp-paper-fog)]"
              >
                <div className="absolute inset-0 overflow-hidden cp-kb">
                  <img
                    src={it.image || rightImgs[i]}
                    alt={it.title}
                    loading="lazy"
                    className="h-full w-full object-cover transition-transform [transition-duration:1400ms] ease-out group-hover:scale-[1.06]"
                  />
                </div>
                <span aria-hidden className="cp-sheen" />
                <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-black/10 to-transparent" />
                <div className="absolute inset-x-0 bottom-0 p-5 text-white">
                  <div className="cp-mono uppercase text-[10px] tracking-[0.22em] opacity-80">{it.tag}</div>
                  <div className="cp-headline text-2xl mt-1 flex items-center gap-2">
                    {it.title}
                    <ArrowUpRight className="h-4 w-4 opacity-70 group-hover:translate-x-1 group-hover:-translate-y-1 transition-transform" />
                  </div>
                </div>
              </Link>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
};
