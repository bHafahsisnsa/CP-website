import React from 'react';
import { MarqueeStrip } from '../shared/MarqueeStrip';
import { useContent } from '../../store/ContentContext';

export const StripSection = ({ items, dark = false }) => (
  <MarqueeStrip
    items={items}
    dark={dark}
    speed="default"
    className={`${dark ? 'border-y border-white/10' : 'border-y border-black/10'}`}
  />
);

const STORY_DEFAULT = {
  eyebrow: 'Cerita Kami',
  text: 'Dimulai dari kecintaan pada kompleksitas aroma — kami mengkurasi parfum yang layak menjadi bagian dari cerita harianmu.',
};

export const StoryStrip = () => {
  const c = useContent('story_strip', STORY_DEFAULT);
  return (
    <div className="cp-container-wide cp-section-md text-center">
      <div className="max-w-3xl mx-auto">
        <div className="cp-eyebrow mb-4 justify-center inline-flex">{c.eyebrow}</div>
        <p className="cp-headline text-2xl sm:text-4xl leading-[1.1]">{c.text}</p>
      </div>
    </div>
  );
};
