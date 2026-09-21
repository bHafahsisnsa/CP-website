// components/shared/GoogleReviews.js — ringkasan rating + kartu ulasan (Google/kurasi).
import React from 'react';
import { AutoCarousel } from './AutoCarousel';
import { Star } from 'lucide-react';

export const Stars = ({ rating = 5, size = 'h-4 w-4' }) => (
  <div className="flex items-center gap-0.5" aria-label={`Rating ${rating} dari 5`}>
    {[1, 2, 3, 4, 5].map((n) => (
      <Star
        key={n}
        className={`${size} ${n <= Math.round(rating) ? 'fill-[#F5A623] text-[#F5A623]' : 'text-black/20'}`}
      />
    ))}
  </div>
);

const initials = (name = '') =>
  name.split(' ').filter(Boolean).slice(0, 2).map((w) => w[0]).join('').toUpperCase() || '?';

const fmtCount = (n) => {
  const num = Number(n) || 0;
  return num.toLocaleString('id-ID');
};

export const RatingSummary = ({ summary, source }) => {
  const avg = Number(summary?.avg) || 0;
  const count = Number(summary?.count) || 0;
  if (!avg && !count) return null;
  return (
    <div className="inline-flex items-center gap-3 rounded-full border border-black/10 bg-[color:var(--cp-paper-warm)] pl-4 pr-5 py-2" data-testid="reviews-summary">
      <svg className="h-5 w-5" viewBox="0 0 48 48" aria-hidden="true">
        <path fill="#4285F4" d="M45.12 24.5c0-1.56-.14-3.06-.4-4.5H24v8.51h11.84c-.51 2.75-2.06 5.08-4.39 6.64v5.52h7.11c4.16-3.83 6.56-9.47 6.56-16.17z" />
        <path fill="#34A853" d="M24 46c5.94 0 10.92-1.97 14.56-5.33l-7.11-5.52c-1.97 1.32-4.49 2.1-7.45 2.1-5.73 0-10.58-3.87-12.31-9.07H4.34v5.7C7.96 41.07 15.4 46 24 46z" />
        <path fill="#FBBC05" d="M11.69 28.18C11.25 26.86 11 25.45 11 24s.25-2.86.69-4.18v-5.7H4.34C2.85 17.09 2 20.45 2 24s.85 6.91 2.34 9.88l7.35-5.7z" />
        <path fill="#EA4335" d="M24 10.75c3.23 0 6.13 1.11 8.41 3.29l6.31-6.31C34.91 4.18 29.93 2 24 2 15.4 2 7.96 6.93 4.34 14.12l7.35 5.7c1.73-5.2 6.58-9.07 12.31-9.07z" />
      </svg>
      <div className="flex items-center gap-2">
        <span className="cp-mono text-lg font-semibold">{avg.toFixed(1)}</span>
        <Stars rating={avg} size="h-3.5 w-3.5" />
      </div>
      <span className="text-sm text-black/60">{fmtCount(count)} ulasan{source === 'google' ? ' Google' : ''}</span>
    </div>
  );
};

const ReviewCard = ({ r }) => (
  <div className="rounded-2xl border border-black/10 bg-[color:var(--cp-paper-warm)] p-5 flex flex-col gap-3" data-testid="store-review-card">
    <div className="flex items-center gap-3">
      {r.avatar ? (
        <img src={r.avatar} alt={r.author} className="h-10 w-10 rounded-full object-cover" referrerPolicy="no-referrer" />
      ) : (
        <div className="h-10 w-10 rounded-full bg-[color:var(--cp-ink)] text-[color:var(--cp-paper)] flex items-center justify-center text-sm font-semibold">
          {initials(r.author)}
        </div>
      )}
      <div className="min-w-0">
        <div className="text-sm font-semibold truncate">{r.author}</div>
        <div className="cp-mono uppercase text-[10px] tracking-[0.18em] text-black/50">
          {r.relative_time || ''}{r.location ? `${r.relative_time ? ' · ' : ''}${r.location}` : ''}
        </div>
      </div>
    </div>
    <Stars rating={r.rating} size="h-3.5 w-3.5" />
    <p className="text-sm text-black/70 leading-relaxed">{r.text}</p>
  </div>
);

export const GoogleReviews = ({ reviews = [], source = 'manual' }) => {
  if (!reviews.length) return null;
  // Ulasan bergeser pelan sendiri (idle) dan berhenti saat di-hover agar mudah dibaca.
  return (
    <div data-testid="store-reviews-grid">
      <AutoCarousel
        speed={0.5}
        gapClass="gap-4"
        slideClass="w-[86%] sm:w-[48%] lg:w-[32%]"
        testId="store-reviews-carousel"
        prevTestId="store-reviews-prev"
        nextTestId="store-reviews-next"
        ariaLabel="Ulasan pelanggan, geser otomatis"
      >
        {reviews.map((r, i) => <ReviewCard key={i} r={r} />)}
      </AutoCarousel>
    </div>
  );
};

export default GoogleReviews;
