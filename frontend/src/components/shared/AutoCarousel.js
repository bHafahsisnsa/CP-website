// components/shared/AutoCarousel.js — carousel IMMERSIVE: bergerak pelan sendiri saat idle,
// BERHENTI saat di-hover / difokus keyboard, lalu lanjut lagi saat pointer menjauh.
//
// Kenapa hover-handler ditulis manual (bukan opsi `stopOnMouseEnter` plugin)?
// Karena kita juga menyediakan tombol Play/Pause manual. Bila plugin yang mengurus
// mouse-enter, plugin akan memanggil play() lagi saat pointer keluar sehingga jeda manual
// pengguna terabaikan. Dengan handler sendiri, `userPaused` selalu dihormati (WCAG 2.2.2:
// gerak otomatis > 5 detik wajib bisa dijedakan).
//
// A11y & performa: `prefers-reduced-motion` -> plugin tidak dipasang sama sekali;
// wrapper diberi role="region" + aria-label; drag tetap jalan (dragFree).
import React from 'react';
import useEmblaCarousel from 'embla-carousel-react';
import AutoScroll from 'embla-carousel-auto-scroll';
import { useReducedMotion } from 'framer-motion';
import { ChevronLeft, ChevronRight, Pause, Play } from 'lucide-react';

const toneCls = {
  light: 'cp-glass-pill text-[color:var(--cp-ink)]',
  dark: 'border border-white/25 bg-white/5 text-white hover:bg-white/12 backdrop-blur-[6px]',
};

export const AutoCarousel = ({
  children,
  speed = 0.8,
  slideClass = 'w-[74%] sm:w-[42%] lg:w-[26%] xl:w-[21%]',
  gapClass = 'gap-3 sm:gap-4',
  tone = 'light',
  edgeFade = true,
  arrows = true,
  playPause = true,
  className = '',
  testId,
  prevTestId,
  nextTestId,
  minSlides = 3,
  ariaLabel = 'Daftar geser otomatis',
}) => {
  const reduce = useReducedMotion();
  const plugins = React.useMemo(
    () =>
      reduce
        ? []
        : [
            AutoScroll({
              playOnInit: true,
              speed,
              stopOnMouseEnter: false,
              stopOnInteraction: false,
              stopOnFocusIn: false,
            }),
          ],
    [reduce, speed]
  );
  const [emblaRef, emblaApi] = useEmblaCarousel(
    { loop: true, align: 'start', dragFree: true, containScroll: false },
    plugins
  );

  const [userPaused, setUserPaused] = React.useState(false);
  const pausedRef = React.useRef(false);   // jeda MANUAL (tombol Jeda/Jalan)
  const hoveredRef = React.useRef(false);  // pointer/fokus sedang di dalam carousel

  const auto = () => (emblaApi ? emblaApi.plugins().autoScroll : null);

  const stopAuto = React.useCallback(() => {
    const a = auto();
    if (a && a.isPlaying()) a.stop();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [emblaApi]);

  const playAuto = React.useCallback(() => {
    const a = auto();
    if (a && !a.isPlaying()) a.play();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [emblaApi]);

  const hold = React.useCallback(() => {
    hoveredRef.current = true;
    stopAuto();
  }, [stopAuto]);

  const release = React.useCallback(() => {
    hoveredRef.current = false;
    if (!pausedRef.current) playAuto();
  }, [playAuto]);

  // Tombol Jeda/Jalan: keputusan berdasar STATE `userPaused`, BUKAN `isPlaying()`.
  // (Saat tombol diklik, pointer pasti sedang hover -> autoScroll sudah dalam kondisi
  // stop, sehingga isPlaying() selalu false dan dulu membuat klik "Jeda" justru
  // mengaktifkan kembali gerak otomatis.)
  const toggle = () => {
    const next = !pausedRef.current;
    pausedRef.current = next;
    setUserPaused(next);
    if (next) stopAuto();
    else if (!hoveredRef.current) playAuto();
  };

  const slides = React.Children.toArray(children);
  const btn = toneCls[tone] || toneCls.light;

  // Terlalu sedikit slide -> tidak ada yang bisa digeser. Tampilkan grid statis saja
  // (tanpa kontrol) supaya tidak muncul carousel "kosong" dengan panah yang tak berguna.
  if (slides.length < minSlides) {
    return (
      <div
        className={`grid gap-3 sm:gap-4 grid-cols-2 ${slides.length >= 2 ? 'md:grid-cols-2 lg:grid-cols-3' : 'md:grid-cols-1 max-w-sm'} ${className}`}
        data-testid={testId}
      >
        {slides}
      </div>
    );
  }

  return (
    <div
      className={`group/carousel relative ${className}`}
      role="region"
      aria-label={ariaLabel}
      onMouseEnter={hold}
      onMouseLeave={release}
      onFocus={hold}
      onBlur={release}
      onTouchStart={hold}
      onTouchEnd={release}
      data-testid={testId}
    >
      <div className={`overflow-hidden ${edgeFade ? 'cp-fade-x' : ''}`} ref={emblaRef}>
        <div className={`flex ${gapClass}`}>
          {slides.map((child, i) => (
            <div key={i} className={`shrink-0 min-w-0 ${slideClass}`}>
              {child}
            </div>
          ))}
        </div>
      </div>

      {arrows ? (
        <>
          <button
            type="button"
            onClick={() => emblaApi && emblaApi.scrollPrev()}
            aria-label="Sebelumnya"
            data-testid={prevTestId}
            className={`absolute left-2 sm:left-3 top-1/2 -translate-y-1/2 h-10 w-10 rounded-full grid place-items-center transition-opacity duration-300 opacity-0 group-hover/carousel:opacity-100 focus-visible:opacity-100 max-sm:opacity-80 ${btn}`}
          >
            <ChevronLeft className="h-4 w-4" />
          </button>
          <button
            type="button"
            onClick={() => emblaApi && emblaApi.scrollNext()}
            aria-label="Berikutnya"
            data-testid={nextTestId}
            className={`absolute right-2 sm:right-3 top-1/2 -translate-y-1/2 h-10 w-10 rounded-full grid place-items-center transition-opacity duration-300 opacity-0 group-hover/carousel:opacity-100 focus-visible:opacity-100 max-sm:opacity-80 ${btn}`}
          >
            <ChevronRight className="h-4 w-4" />
          </button>
        </>
      ) : null}

      {playPause && !reduce ? (
        <button
          type="button"
          onClick={toggle}
          aria-label={userPaused ? 'Lanjutkan gerak otomatis' : 'Jeda gerak otomatis'}
          data-testid="carousel-autoplay-toggle"
          /* Diletakkan DI BAWAH viewport (bukan di atas) supaya tidak menimpa tombol
             "Lihat Semua" / judul section, dan tidak menutupi tombol di dalam kartu. */
          className={`absolute right-2 sm:right-3 -bottom-10 h-8 px-3 rounded-full inline-flex items-center gap-1.5 cp-mono uppercase text-[9px] tracking-[0.18em] transition-opacity duration-300 opacity-0 group-hover/carousel:opacity-100 focus-visible:opacity-100 ${btn}`}
        >
          {userPaused ? <Play className="h-3 w-3" /> : <Pause className="h-3 w-3" />}
          {userPaused ? 'Jalan' : 'Jeda'}
        </button>
      ) : null}
    </div>
  );
};

export default AutoCarousel;
