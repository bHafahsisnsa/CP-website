import React from 'react';
import { Star } from 'lucide-react';

const initials = (n = '') =>
  n.split(' ').filter(Boolean).slice(0, 2).map((w) => w[0]).join('').toUpperCase() || 'CP';

export const Stars = ({ value = 0, size = 'h-4 w-4' }) => (
  <div className="flex items-center gap-0.5">
    {[1, 2, 3, 4, 5].map((i) => (
      <Star
        key={i}
        className={`${size} ${i <= Math.round(value) ? 'fill-[color:var(--cp-brass)] text-[color:var(--cp-brass)]' : 'text-black/20'}`}
      />
    ))}
  </div>
);

export const RatingInline = ({ avg = 0, count = 0 }) => {
  if (!count) {
    return (
      <span className="cp-mono uppercase text-[10px] tracking-[0.22em] text-black/45" data-testid="pdp-rating">
        Belum ada ulasan
      </span>
    );
  }
  return (
    <div className="flex items-center gap-2" data-testid="pdp-rating">
      <Stars value={avg} size="h-3.5 w-3.5" />
      <span className="cp-mono text-xs text-black/60">{avg.toFixed(1)} · {count} ulasan</span>
    </div>
  );
};

export const ProductReviews = ({ reviews = [], loading = false, avg = 0, count = 0 }) => (
  <section className="cp-section" data-testid="pdp-reviews">
    <div className="cp-container-wide">
      <div className="mb-8 flex flex-wrap items-end justify-between gap-4">
        <div>
          <div className="cp-eyebrow">Ulasan</div>
          <h3 className="cp-headline text-2xl sm:text-4xl mt-2">Kata mereka.</h3>
        </div>
        <div className="text-right">
          <div className="cp-headline text-4xl leading-none">{count ? avg.toFixed(1) : '—'}</div>
          <div className="mt-1 flex justify-end">
            <Stars value={avg} />
          </div>
          <div className="cp-mono text-xs text-black/55 mt-1">{count} ulasan</div>
        </div>
      </div>

      {loading ? (
        <div className="text-sm text-black/50" data-testid="pdp-reviews-loading">Memuat ulasan…</div>
      ) : reviews.length === 0 ? (
        <div className="rounded-2xl border border-black/10 p-8 text-center" data-testid="pdp-reviews-empty">
          <div className="cp-headline text-2xl">Belum ada ulasan</div>
          <div className="text-sm text-black/60 mt-2">Jadilah yang pertama berbagi pengalaman aromamu.</div>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {reviews.map((r) => (
            <div
              key={r.id}
              className="rounded-2xl border border-black/10 bg-[color:var(--cp-paper-warm)] p-6"
              data-testid="pdp-review-item"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="h-9 w-9 rounded-full bg-[color:var(--cp-brass)]/15 flex items-center justify-center cp-mono text-[11px] text-[color:var(--cp-brass)]">
                    {initials(r.name)}
                  </div>
                  <div>
                    <div className="text-sm font-medium">{r.name}</div>
                    <div className="cp-mono uppercase text-[10px] tracking-[0.22em] text-black/50">{r.city}</div>
                  </div>
                </div>
                <Stars value={r.rating} size="h-3.5 w-3.5" />
              </div>
              <p className="text-sm text-black/70 mt-3 leading-relaxed">“{r.quote}”</p>
            </div>
          ))}
        </div>
      )}
    </div>
  </section>
);
