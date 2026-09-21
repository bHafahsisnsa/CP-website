// components/home/BestSellersSection.js — baris produk IMMERSIVE.
// Barisnya bergeser pelan sendiri (auto-scroll) dan BERHENTI saat di-hover supaya kartu
// mudah diklik. Lebar memakai cp-container-wide agar gambar produk lebih besar.
import React from 'react';
import { Link } from 'react-router-dom';
import { ProductCard } from '../shared/ProductCard';
import { ProductRowSkeleton } from '../shared/Skeletons';
import { AutoCarousel } from '../shared/AutoCarousel';
import { useQuickView } from '../../store/QuickViewContext';
import { Reveal } from '../shared/Reveal';

export const BestSellersSection = ({
  products = [],
  loading = false,
  title = 'Best Seller',
  eyebrow = 'Trending',
  linkTo = '/shop?bestSeller=1',
  testId = 'home-best-sellers',
  speed = 0.7,
}) => {
  const { openQuickView } = useQuickView();

  return (
    <section className="py-14 sm:py-20 bg-[color:var(--cp-paper-warm)]" data-testid={testId}>
      <div className="cp-container-wide">
        <div className="flex items-end justify-between gap-4 mb-6 sm:mb-8">
          <Reveal>
            <div>
              <div className="cp-eyebrow">{eyebrow}</div>
              <h2 className="cp-headline mt-2 text-3xl sm:text-5xl lg:text-[56px]">{title}</h2>
            </div>
          </Reveal>
          <Link
            to={linkTo}
            className="hidden sm:inline-flex cp-mono uppercase text-[10px] tracking-[0.22em] border border-black/15 rounded-full px-4 py-2 hover:bg-black/5 transition-colors"
            data-testid={`${testId}-view-all`}
          >
            Lihat Semua
          </Link>
        </div>

        {loading ? (
          <ProductRowSkeleton count={5} testId={`${testId}-loading`} />
        ) : (
          <AutoCarousel
            speed={speed}
            testId={`${testId}-carousel`}
            prevTestId={`${testId}-prev`}
            nextTestId={`${testId}-next`}
            ariaLabel={`${title} — daftar produk geser otomatis`}
            slideClass="w-[74%] sm:w-[42%] lg:w-[27%] xl:w-[21%]"
          >
            {products.map((p) => (
              <ProductCard key={p.id} product={p} onQuickView={openQuickView} />
            ))}
          </AutoCarousel>
        )}
      </div>
    </section>
  );
};
