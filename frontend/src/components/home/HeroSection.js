import React from 'react';
import { Link } from 'react-router-dom';
import { motion, useReducedMotion } from 'framer-motion';
import { ArrowRight, ArrowDown } from 'lucide-react';
import { useContent } from '../../store/ContentContext';
import { HOME_IMAGES } from '../../lib/realImages';

const HERO_IMAGE = HOME_IMAGES.hero.main;

const HERO_DEFAULT = {
  eyebrow: 'Koleksi 2026 · Edisi Terbatas',
  title: 'Aroma yang membekas.',
  title_accent: 'Dari layar ke kulit.',
  subtitle:
    'Kurasi parfum original dengan notes yang jelas dan pengalaman belanja premium — untuk momen yang layak diingat.',
  primary_label: 'Belanja Sekarang', primary_to: '/shop',
  secondary_label: 'Lihat Best Seller', secondary_to: '/shop?bestSeller=1',
  chip: 'Best of Woody · Amber',
  scroll_hint: 'Gulir untuk menjelajahi',
  // Background media (foto/video). bg_type: 'video' | 'image'
  bg_type: 'video',
  bg_video: '/videos/hero.mp4',
  bg_image: '',
};

export const HeroSection = () => {
  const prefersReduced = useReducedMotion();
  const c = useContent('hero', HERO_DEFAULT);
  const videoRef = React.useRef(null);

  const poster = c.bg_image || HERO_IMAGE;
  const useVideo = c.bg_type !== 'image' && !!c.bg_video && !prefersReduced;

  // React doesn't reliably set the `muted` HTML attribute; browsers require it for
  // autoplay. Force muted + kick off playback via ref.
  React.useEffect(() => {
    const v = videoRef.current;
    if (!v || !useVideo) return;
    v.muted = true;
    v.defaultMuted = true;
    const p = v.play?.();
    if (p && typeof p.catch === 'function') p.catch(() => {});
  }, [useVideo, c.bg_video]);

  return (
    <section
      data-testid="home-hero"
      className="relative overflow-hidden min-h-[86vh] lg:min-h-[92vh] flex items-end"
    >
      {/* ---- Background media (video or photo) ---- */}
      {/* Wrapper ber-ken-burns: pan+zoom sangat lambat -> hero terasa "bernapas". */}
      <div className="absolute inset-0 cp-kb-hero" data-testid="home-hero-media">
        {useVideo ? (
          <video
            ref={videoRef}
            className="h-full w-full object-cover"
            src={c.bg_video}
            poster={poster}
            autoPlay
            muted
            loop
            playsInline
            preload="auto"
            data-testid="home-hero-video"
          />
        ) : (
          <img
            src={poster}
            alt="Suasana Collector Parfum"
            className="h-full w-full object-cover"
            data-testid="home-hero-image"
          />
        )}
      </div>

      {/* ---- Cinematic overlays for text legibility (works on any theme) ---- */}
      <div
        aria-hidden
        className="absolute inset-0"
        style={{
          background:
            'linear-gradient(90deg, rgba(6,6,8,0.82) 0%, rgba(6,6,8,0.5) 42%, rgba(6,6,8,0.15) 72%, rgba(6,6,8,0.05) 100%)',
        }}
      />
      <div
        aria-hidden
        className="absolute inset-0"
        style={{
          background:
            'linear-gradient(180deg, rgba(6,6,8,0.35) 0%, transparent 26%, transparent 55%, rgba(6,6,8,0.75) 100%)',
        }}
      />
      {/* Brass ambient glow */}
      <div
        aria-hidden
        className="absolute inset-0 opacity-80"
        style={{
          background:
            'radial-gradient(1100px circle at 12% 18%, rgba(214,195,163,0.16), transparent 55%)',
        }}
      />

      {/* ---- Content ---- */}
      <div className="cp-container-wide relative z-10 w-full pt-36 pb-16 lg:pt-40 lg:pb-24">
        <div className="max-w-2xl">
          <motion.div
            initial={prefersReduced ? { opacity: 0 } : { opacity: 0, letterSpacing: '0.14em' }}
            animate={{ opacity: 1, letterSpacing: '0em' }}
            transition={{ duration: 1.1, ease: [0.22, 1, 0.36, 1] }}
            className="cp-mono uppercase text-[11px] sm:text-xs tracking-[0.22em] text-[color:var(--cp-champagne)]"
          >
            {c.eyebrow}
          </motion.div>

          <motion.h1
            initial={prefersReduced ? { opacity: 0 } : { opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.9, delay: 0.1, ease: [0.22, 1, 0.36, 1] }}
            className="cp-headline mt-4 text-[13vw] sm:text-[9vw] lg:text-[6.4vw] leading-[0.95] text-white drop-shadow-[0_2px_30px_rgba(0,0,0,0.35)]"
          >
            {c.title}
            {c.title_accent ? (
              <>
                <br />
                <span className="italic text-[color:var(--cp-champagne)]">{c.title_accent}</span>
              </>
            ) : null}
          </motion.h1>

          <motion.p
            initial={{ opacity: 0, y: 14 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.9, delay: 0.35, ease: [0.22, 1, 0.36, 1] }}
            className="mt-6 max-w-md text-sm sm:text-base text-white/80 leading-relaxed"
          >
            {c.subtitle}
          </motion.p>

          <motion.div
            initial={{ opacity: 0, y: 14 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.9, delay: 0.5, ease: [0.22, 1, 0.36, 1] }}
            className="mt-8 flex flex-wrap items-center gap-3"
          >
            <Link
              to={c.primary_to || '/shop'}
              data-testid="home-hero-primary-cta"
              className="h-12 px-6 rounded-full inline-flex items-center bg-[#f7f3ea] text-[#141414] hover:bg-white transition-colors cp-mono uppercase text-[11px] tracking-[0.22em] shadow-[0_14px_36px_rgba(0,0,0,0.35)]"
            >
              {c.primary_label} <ArrowRight className="h-4 w-4 ml-2" />
            </Link>
            <Link
              to={c.secondary_to || '/shop?bestSeller=1'}
              data-testid="home-hero-secondary-cta"
              className="h-12 px-6 rounded-full inline-flex items-center border border-white/45 text-white hover:bg-white/10 backdrop-blur-[6px] transition-colors cp-mono uppercase text-[11px] tracking-[0.22em]"
            >
              {c.secondary_label}
            </Link>
          </motion.div>

          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.7, duration: 0.9 }}
            className="mt-12 flex items-center gap-3 cp-mono uppercase text-[11px] tracking-[0.22em] text-white/60"
          >
            <ArrowDown className="h-3.5 w-3.5 cp-pulse-soft" /> {c.scroll_hint}
          </motion.div>
        </div>
      </div>

      {/* Floating glass curation chip (desktop) */}
      <div className="hidden lg:flex absolute right-10 bottom-10 z-10 items-center gap-3 rounded-full px-4 py-2.5 cp-glass-dark cp-glass-3d cp-float-slow">
        <span className="h-2 w-2 rounded-full bg-[color:var(--cp-brass)] cp-pulse-soft" />
        <span className="cp-mono uppercase text-[10px] tracking-[0.22em]">{c.chip}</span>
      </div>
    </section>
  );
};
