import React from 'react';

export const MarqueeStrip = ({ items = [], speed = 'default', className = '', dot = '•', dark = false }) => {
  const speedClass = speed === 'fast' ? 'fast' : speed === 'slow' ? 'slow' : '';
  const bg = dark ? 'bg-[color:var(--cp-ink)] text-[color:var(--cp-paper)]' : 'bg-transparent text-[color:var(--cp-ink)]';
  const content = (
    <div className={`cp-marquee-track ${speedClass}`}>
      {[...items, ...items].map((it, i) => (
        <span key={i} className="flex items-center gap-6 whitespace-nowrap cp-mono text-[11px] sm:text-xs uppercase tracking-[0.22em]">
          <span>{it}</span>
          <span className="opacity-40">{dot}</span>
        </span>
      ))}
    </div>
  );

  return (
    <div
      data-testid="marquee-strip"
      className={`cp-marquee overflow-hidden ${bg} ${className}`}
      role="presentation"
      aria-hidden
    >
      <div className="py-3">{content}</div>
    </div>
  );
};

export const BigMarquee = ({ text = 'Collector Parfum', className = '' }) => {
  return (
    <div className={`cp-marquee overflow-hidden ${className}`} aria-hidden>
      <div className="cp-marquee-track slow py-4 sm:py-6">
        {Array.from({ length: 6 }).map((_, i) => (
          <span
            key={i}
            className="cp-headline text-[16vw] sm:text-[14vw] lg:text-[12vw] leading-none whitespace-nowrap px-6"
          >
            {text}
            <span className="inline-block mx-8 align-middle text-[color:var(--cp-brass)]">✦</span>
          </span>
        ))}
      </div>
    </div>
  );
};
