import React from 'react';
import { motion, useScroll, useTransform } from 'framer-motion';
import { Reveal } from '../shared/Reveal';

export const BigScrollingWord = ({
  words = ['Aroma', 'yang', 'membekas'],
  caption = 'Setiap notes menceritakan kisahnya sendiri.',
}) => {
  const ref = React.useRef(null);
  const { scrollYProgress } = useScroll({ target: ref, offset: ['start end', 'end start'] });
  // Drift halus & SELALU non-negatif supaya huruf tidak pernah "terpotong" di tepi kiri.
  // (Sebelumnya nilai negatif mendorong kata ke luar layar kiri → huruf awal terpotong.)
  const x1 = useTransform(scrollYProgress, [0, 1], ['0%', '5%']);
  const x2 = useTransform(scrollYProgress, [0, 1], ['5%', '0%']);
  const x3 = useTransform(scrollYProgress, [0, 1], ['0%', '3%']);

  const transforms = [x1, x2, x3];

  return (
    <section
      ref={ref}
      className="cp-section-md bg-[color:var(--cp-paper-fog)] overflow-hidden relative"
      data-testid="home-big-word"
    >
      <div className="cp-container-wide">
        <Reveal>
          <div className="cp-eyebrow mb-6">Manifesto</div>
        </Reveal>

        <div className="space-y-2 sm:space-y-4">
          {words.map((w, i) => (
            <motion.div
              key={i}
              style={{ x: transforms[i % transforms.length] }}
              className="cp-headline text-[clamp(2.75rem,14vw,11.5rem)] leading-[0.9] whitespace-nowrap will-change-transform"
            >
              {i === 1 ? (
                <em className="not-italic italic text-[color:var(--cp-brass)]">{w}</em>
              ) : (
                w
              )}
              {i === words.length - 1 && '.'}
            </motion.div>
          ))}
        </div>

        <Reveal delay={0.15}>
          <div className="max-w-xl mt-10 text-sm sm:text-base text-black/70">{caption}</div>
        </Reveal>
      </div>
    </section>
  );
};
