import React from 'react';
import { Quote } from 'lucide-react';
import { Reveal } from '../shared/Reveal';
import { AutoCarousel } from '../shared/AutoCarousel';
import { useContent } from '../../store/ContentContext';

const initials = (name = '') =>
  name.split(' ').filter(Boolean).slice(0, 2).map((w) => w[0]).join('').toUpperCase() || 'CP';

const TESTI_DEFAULT = { eyebrow: 'Cerita Pelanggan', title: 'Cerita yang', title_accent: 'menginspirasi.' };

// Testimoni bergeser pelan tanpa henti (kesan "tembok cerita" yang hidup) dan berhenti
// saat pembaca hover / fokus keyboard.
export const TestimonialsSection = ({ reviews = [] }) => {
  const items = Array.isArray(reviews) ? reviews : [];
  const c = useContent('testimonials', TESTI_DEFAULT);

  if (items.length === 0) return null;

  return (
    <section
      className="py-14 sm:py-20 lg:py-24 bg-[color:var(--cp-ink)] text-[color:var(--cp-paper)] relative overflow-hidden"
      data-testid="home-testimonials"
    >
      <div
        aria-hidden
        className="absolute inset-0 opacity-30"
        style={{ background: 'radial-gradient(1000px circle at 20% 0%, rgba(214,195,163,0.15), transparent 55%)' }}
      />
      <div className="cp-container-wide relative">
        <div className="flex items-end justify-between mb-8 lg:mb-10">
          <Reveal>
            <div>
              <div className="cp-mono uppercase text-[11px] tracking-[0.22em] text-white/60">{c.eyebrow}</div>
              <h2 className="cp-headline mt-2 text-3xl sm:text-5xl lg:text-[56px]">
                {c.title} <em className="not-italic italic text-[color:var(--cp-brass)]">{c.title_accent}</em>
              </h2>
            </div>
          </Reveal>
        </div>

        <AutoCarousel
          speed={0.55}
          tone="dark"
          gapClass="gap-4 sm:gap-6"
          slideClass="w-[86%] sm:w-[52%] lg:w-[34%] xl:w-[28%]"
          testId="home-testimonials-carousel"
          prevTestId="home-testimonials-prev"
          nextTestId="home-testimonials-next"
          ariaLabel="Testimoni pelanggan, geser otomatis"
        >
          {items.map((t, i) => (
            <div
              key={t.id || i}
              className="group h-full rounded-2xl border border-white/10 bg-white/[0.03] p-6 sm:p-7 transition-colors duration-300 hover:bg-white/[0.06] hover:border-white/20"
              data-testid="testimonial-card"
            >
              <Quote className="h-6 w-6 text-[color:var(--cp-brass)] mb-4 transition-transform duration-500 group-hover:-translate-y-0.5 group-hover:scale-110" />
              <p className="text-[15px] sm:text-base leading-relaxed">&ldquo;{t.quote}&rdquo;</p>
              <div className="mt-6 flex items-center gap-3">
                <div className="h-10 w-10 rounded-full overflow-hidden bg-[color:var(--cp-brass)]/20 flex items-center justify-center cp-mono text-xs tracking-widest text-[color:var(--cp-brass)]">
                  {initials(t.name)}
                </div>
                <div>
                  <div className="text-sm font-medium">{t.name}</div>
                  <div className="cp-mono uppercase text-[10px] tracking-[0.22em] text-white/60">{t.city}</div>
                </div>
              </div>
            </div>
          ))}
        </AutoCarousel>
      </div>
    </section>
  );
};
