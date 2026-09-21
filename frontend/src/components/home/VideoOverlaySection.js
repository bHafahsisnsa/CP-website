import React from 'react';
import { Link } from 'react-router-dom';
import { motion, useScroll, useTransform } from 'framer-motion';
import { PlayCircle } from 'lucide-react';
import { Reveal } from '../shared/Reveal';
import { useContent } from '../../store/ContentContext';

import { HOME_IMAGES } from '../../lib/realImages';

const VIDEO_POSTER = HOME_IMAGES.video.poster;
const VIDEO_DEFAULT = {
  eyebrow: 'Behind the Scenes', title: 'Kurasi yang', title_accent: 'manusiawi.',
  text: 'Kami mengunjungi pembuat aroma, mencium ribuan sampel, hanya untuk memilih beberapa yang layak masuk koleksi.',
  play_label: 'Tonton Cerita', secondary_label: 'Baca Selengkapnya', secondary_to: '/tentang', poster: '',
};

export const VideoOverlaySection = () => {
  const ref = React.useRef(null);
  const c = useContent('video', VIDEO_DEFAULT);
  const { scrollYProgress } = useScroll({ target: ref, offset: ['start end', 'end start'] });
  const y = useTransform(scrollYProgress, [0, 1], ['-10%', '10%']);
  const scale = useTransform(scrollYProgress, [0, 1], [1.1, 1.02]);

  return (
    <section ref={ref} className="relative overflow-hidden" data-testid="home-video-overlay">
      <div className="relative h-[70vh] sm:h-[80vh]">
        <motion.img
          src={c.poster || VIDEO_POSTER}
          alt="Editorial botol parfum"
          style={{ y, scale }}
          className="absolute inset-0 h-[110%] w-full object-cover"
        />
        <div className="absolute inset-0 bg-black/45" />

        <div className="absolute inset-0 flex items-center">
          <div className="cp-container-wide w-full">
            <Reveal>
              <div className="cp-mono uppercase text-[11px] tracking-[0.22em] text-white/80">{c.eyebrow}</div>
              <h3 className="cp-headline text-4xl sm:text-6xl lg:text-7xl text-white mt-3 max-w-2xl">
                {c.title} <em className="not-italic italic text-[color:var(--cp-brass)]">{c.title_accent}</em>
              </h3>
            </Reveal>
            <Reveal delay={0.12}>
              <p className="mt-4 max-w-md text-white/80 text-sm sm:text-base">
                {c.text}
              </p>
            </Reveal>
            <Reveal delay={0.2}>
              <div className="mt-8 inline-flex items-center gap-4">
                <button
                  className="inline-flex items-center gap-3 text-white cp-mono uppercase text-[11px] tracking-[0.22em]"
                  data-testid="home-video-play-button"
                >
                  <span className="h-14 w-14 rounded-full bg-white/15 backdrop-blur border border-white/30 flex items-center justify-center">
                    <PlayCircle className="h-6 w-6" />
                  </span>
                  {c.play_label}
                </button>
                <Link
                  to={c.secondary_to || '/tentang'}
                  className="text-white/80 cp-mono uppercase text-[11px] tracking-[0.22em] cp-hover-underline"
                >
                  {c.secondary_label}
                </Link>
              </div>
            </Reveal>
          </div>
        </div>
      </div>
    </section>
  );
};
