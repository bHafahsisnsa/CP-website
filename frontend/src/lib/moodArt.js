// Editorial "mood board" SVG generator for category cards and lifestyle sections.
// Fully unbranded — uses color blocks, gradients, abstract shapes, and typography.

const MOODS = {
  citrus: {
    bg: ['#f3e6a8', '#e9d179', '#d4a83a'],
    accent: '#a5771a',
    ink: '#2b2410',
    shapes: 'sun',
  },
  floral: {
    bg: ['#fce8ea', '#f5c1cf', '#c88a99'],
    accent: '#8f4757',
    ink: '#3a1f28',
    shapes: 'petals',
  },
  woody: {
    bg: ['#4a3826', '#755841', '#a68259'],
    accent: '#c9a675',
    ink: '#e8dcc4',
    shapes: 'grain',
  },
  gourmand: {
    bg: ['#c68b53', '#8d5a2f', '#4f2f1c'],
    accent: '#f0d1a2',
    ink: '#f3e2c6',
    shapes: 'drops',
  },
  fresh: {
    bg: ['#b4d0d9', '#7ba0ae', '#3d5866'],
    accent: '#e8f0f4',
    ink: '#0f2027',
    shapes: 'waves',
  },
  amber: {
    bg: ['#3a2318', '#5d3421', '#7a4a2b'],
    accent: '#dcb887',
    ink: '#f2e0c3',
    shapes: 'smoke',
  },
};

const drawShapes = (kind, palette) => {
  switch (kind) {
    case 'sun':
      return `<circle cx='300' cy='140' r='120' fill='${palette.accent}' opacity='0.45'/>
              <circle cx='300' cy='140' r='170' fill='none' stroke='${palette.accent}' stroke-width='1.5' opacity='0.35'/>
              <circle cx='300' cy='140' r='220' fill='none' stroke='${palette.accent}' stroke-width='1' opacity='0.2'/>`;
    case 'petals':
      return `<ellipse cx='300' cy='260' rx='170' ry='60' fill='${palette.accent}' opacity='0.35' transform='rotate(-20 300 260)'/>
              <ellipse cx='300' cy='260' rx='170' ry='60' fill='${palette.accent}' opacity='0.3' transform='rotate(30 300 260)'/>
              <ellipse cx='300' cy='260' rx='170' ry='60' fill='${palette.accent}' opacity='0.28' transform='rotate(80 300 260)'/>`;
    case 'grain':
      return `<path d='M0 400 C 200 340 400 460 600 380 L 600 500 L 0 500 Z' fill='${palette.accent}' opacity='0.25'/>
              <path d='M0 380 C 200 320 400 440 600 360 L 600 500 L 0 500 Z' fill='${palette.accent}' opacity='0.35'/>`;
    case 'drops':
      return `<circle cx='140' cy='260' r='45' fill='${palette.accent}' opacity='0.5'/>
              <circle cx='450' cy='180' r='30' fill='${palette.accent}' opacity='0.4'/>
              <circle cx='500' cy='340' r='60' fill='${palette.accent}' opacity='0.45'/>`;
    case 'waves':
      return `<path d='M0 250 Q 150 200 300 260 T 600 250 L 600 500 L 0 500 Z' fill='${palette.accent}' opacity='0.3'/>
              <path d='M0 320 Q 150 280 300 340 T 600 320 L 600 500 L 0 500 Z' fill='${palette.accent}' opacity='0.35'/>
              <path d='M0 390 Q 150 350 300 400 T 600 390 L 600 500 L 0 500 Z' fill='${palette.accent}' opacity='0.4'/>`;
    case 'smoke':
    default:
      return `<ellipse cx='150' cy='300' rx='220' ry='120' fill='${palette.accent}' opacity='0.25'/>
              <ellipse cx='500' cy='180' rx='180' ry='100' fill='${palette.accent}' opacity='0.2'/>
              <ellipse cx='350' cy='420' rx='260' ry='90' fill='${palette.accent}' opacity='0.18'/>`;
  }
};

const escapeXml = (s) =>
  String(s || '')
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;').replace(/'/g, '&apos;');

export const moodBoard = ({ title = 'Aroma', subtitle = '', mood = 'amber', ratio = '3:4', accentText = '', clean = false } = {}) => {
  const pal = MOODS[mood] || MOODS.amber;
  const [w, h] = ratio === '4:3' ? [800, 600] : ratio === '16:9' ? [1400, 787] : ratio === '1:1' ? [800, 800] : [600, 800];
  const id = Math.random().toString(36).slice(2, 8);

  const svg = `<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${w} ${h}" preserveAspectRatio="xMidYMid slice" width="${w}" height="${h}">
  <defs>
    <linearGradient id="bg-${id}" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="${pal.bg[0]}"/>
      <stop offset="55%" stop-color="${pal.bg[1]}"/>
      <stop offset="100%" stop-color="${pal.bg[2] || pal.bg[1]}"/>
    </linearGradient>
    <radialGradient id="glow-${id}" cx="30%" cy="30%" r="70%">
      <stop offset="0%" stop-color="#ffffff" stop-opacity="0.14"/>
      <stop offset="100%" stop-color="#000000" stop-opacity="0"/>
    </radialGradient>
    <filter id="noise-${id}">
      <feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="2" seed="4"/>
      <feColorMatrix values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 0.08 0"/>
      <feComposite in2="SourceGraphic" operator="in"/>
    </filter>
  </defs>
  <rect width="${w}" height="${h}" fill="url(#bg-${id})"/>
  <g transform="translate(${(w - 600) / 2},${(h - 500) / 2})" opacity="0.9">
    ${drawShapes(pal.shapes, pal)}
  </g>
  <rect width="${w}" height="${h}" fill="url(#glow-${id})"/>
  <rect width="${w}" height="${h}" filter="url(#noise-${id})"/>

  <!-- corner marks -->
  <text x="30" y="45" font-family="Courier, monospace" font-size="10" fill="${pal.ink}" opacity="0.55" letter-spacing="4">COLLECTOR</text>
  <text x="30" y="65" font-family="Courier, monospace" font-size="9" fill="${pal.ink}" opacity="0.4" letter-spacing="6">PARFUM · EDISI 2026</text>

  <text x="${w - 30}" y="45" text-anchor="end" font-family="Courier, monospace" font-size="10" fill="${pal.ink}" opacity="0.55" letter-spacing="4">${escapeXml(mood).toUpperCase()}</text>

  <text x="${w - 30}" y="${h - 30}" text-anchor="end" font-family="Courier, monospace" font-size="10" fill="${pal.ink}" opacity="0.4" letter-spacing="3">${escapeXml(accentText || 'MOOD BOARD')}</text>

  ${clean ? '' : `<!-- Big label -->
  <g transform="translate(30, ${h - 100})">
    <text x="0" y="0" font-family="DM Serif Display, Times New Roman, serif" font-size="52" fill="${pal.ink}" opacity="0.98">${escapeXml(title)}</text>
    <text x="0" y="38" font-family="Courier, monospace" font-size="11" fill="${pal.ink}" opacity="0.55" letter-spacing="4">${escapeXml(subtitle)}</text>
  </g>`}
</svg>`;
  return `data:image/svg+xml;charset=utf-8,${encodeURIComponent(svg)}`;
};

// Hero/editorial full-bleed variant
export const editorialBanner = ({ title = 'Collector', subtitle = '', accent = 'ORIGINAL · KURASI · EDITORIAL', ratio = '4:5', mood = 'amber' } = {}) =>
  moodBoard({ title, subtitle, mood, ratio, accentText: accent });
