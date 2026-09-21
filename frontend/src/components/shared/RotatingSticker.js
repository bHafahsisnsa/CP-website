import React from 'react';

export const RotatingSticker = ({ text = 'SALE • HURRY UP • 50% OFF •', size = 128, className = '' }) => {
  const radius = size / 2 - 12;
  const cx = size / 2;
  const cy = size / 2;
  return (
    <div
      data-testid="rotating-sticker"
      className={`relative inline-flex items-center justify-center ${className}`}
      style={{ width: size, height: size }}
    >
      <div className="cp-spin-slow" style={{ width: size, height: size }}>
        <svg viewBox={`0 0 ${size} ${size}`} width={size} height={size}>
          <defs>
            <path
              id={`cp-circ-${size}`}
              d={`M ${cx}, ${cy} m -${radius}, 0 a ${radius},${radius} 0 1,1 ${radius * 2},0 a ${radius},${radius} 0 1,1 -${radius * 2},0`}
              fill="none"
            />
          </defs>
          <text fill="currentColor" className="cp-mono uppercase" style={{ fontSize: 11, letterSpacing: '0.22em' }}>
            <textPath href={`#cp-circ-${size}`} startOffset="0">
              {text}
              {text}
            </textPath>
          </text>
        </svg>
      </div>
      <div className="absolute inset-0 flex items-center justify-center">
        <div className="cp-headline text-2xl text-[color:var(--cp-ink)]">%</div>
      </div>
    </div>
  );
};
