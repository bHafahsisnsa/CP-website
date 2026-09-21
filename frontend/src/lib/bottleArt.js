// Generate SVG data URLs for editorial "bottle" placeholders per product.
// Fully unbranded, elegant, consistent with luxury perfume aesthetic.

const PALETTES = {
  amber: {
    bg: ['#3a2214', '#5c341f'],
    glass: '#7c4a2a',
    liquid: '#c78349',
    cap: '#eddac6',
    ring: '#d6c3a3',
    label: '#eddac6',
  },
  woody: {
    bg: ['#25201a', '#3f342a'],
    glass: '#4b3d31',
    liquid: '#8a6a4c',
    cap: '#c0a882',
    ring: '#a68a63',
    label: '#e4d7c1',
  },
  floral: {
    bg: ['#3b2833', '#5e3f52'],
    glass: '#e5b2c1',
    liquid: '#f5cad4',
    cap: '#f8ded9',
    ring: '#d6c3a3',
    label: '#faf1ea',
  },
  citrus: {
    bg: ['#3f3821', '#605735'],
    glass: '#a58d3d',
    liquid: '#e6c65e',
    cap: '#f2e6b6',
    ring: '#e2c98a',
    label: '#f7f0d8',
  },
  fresh: {
    bg: ['#1f2b32', '#324752'],
    glass: '#5a7787',
    liquid: '#a4c1cf',
    cap: '#d5e6ec',
    ring: '#c0d3d9',
    label: '#e8eff2',
  },
  gourmand: {
    bg: ['#3a2618', '#5b3c22'],
    glass: '#7a4d2b',
    liquid: '#c68b53',
    cap: '#efd9b8',
    ring: '#d1ab7e',
    label: '#f4e4c8',
  },
  ivory: {
    bg: ['#efe8d9', '#f7f3ea'],
    glass: '#1a1a1a',
    liquid: '#2a2a2a',
    cap: '#141414',
    ring: '#b89b6a',
    label: '#141414',
  },
};

const getPalette = (category, variant = 0) => {
  const pal = PALETTES[category] || PALETTES.amber;
  if (variant === 1) return { ...pal, bg: [pal.bg[1], pal.bg[0]] };
  if (variant === 2) return { ...PALETTES.ivory };
  if (variant === 3)
    return {
      ...pal,
      bg: ['#0f0f10', '#1a1a1a'],
      label: pal.ring,
    };
  return pal;
};

// Komposisi per varian. Varian 1 = "macro/detail shot": botol diperbesar sehingga
// terpotong oleh kanvas (kesan close-up editorial). Sebelumnya varian 1 hanya menukar
// arah gradien latar sehingga terlihat NYARIS IDENTIK dengan varian 0 — galeri PDP jadi
// membosankan dan efek hover kartu produk hampir tak terlihat.
const getComposition = (variant = 0) => {
  if (variant === 1) return { zoom: 1.62, cy: 660, floor: false };
  if (variant === 2) return { zoom: 1.08, cy: 560, floor: true };
  if (variant === 3) return { zoom: 0.94, cy: 520, floor: true };
  return { zoom: 1, cy: 540, floor: true };
};

// Build a stylized bottle SVG as data URL
export const bottleImage = ({
  name = 'Collector Parfum',
  concentration = 'EDP',
  category = 'amber',
  variant = 0,
  width = 900,
  height = 1125,
  labelSuffix = '',
} = {}) => {
  const pal = getPalette(category, variant);
  const comp = getComposition(variant);
  const [bg1, bg2] = pal.bg;
  const gradId = `bg-${Math.random().toString(36).slice(2, 8)}`;
  const glassGrad = `g-${Math.random().toString(36).slice(2, 8)}`;

  const svg = `<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 900 1125" width="${width}" height="${height}">
  <defs>
    <linearGradient id="${gradId}" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="${bg1}"/>
      <stop offset="100%" stop-color="${bg2}"/>
    </linearGradient>
    <linearGradient id="${glassGrad}" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="${pal.glass}" stop-opacity="0.35"/>
      <stop offset="50%" stop-color="${pal.glass}" stop-opacity="0.7"/>
      <stop offset="100%" stop-color="${pal.glass}" stop-opacity="0.45"/>
    </linearGradient>
    <radialGradient id="halo-${gradId}" cx="50%" cy="35%" r="55%">
      <stop offset="0%" stop-color="${pal.ring}" stop-opacity="0.35"/>
      <stop offset="100%" stop-color="${pal.ring}" stop-opacity="0"/>
    </radialGradient>
  </defs>

  <rect width="900" height="1125" fill="url(#${gradId})"/>
  <rect width="900" height="1125" fill="url(#halo-${gradId})"/>

  <!-- soft floor shadow -->
  ${comp.floor ? '<ellipse cx="450" cy="960" rx="230" ry="14" fill="#000" opacity="0.28"/>' : ''}

  <!-- Bottle group -->
  <g transform="translate(450,${comp.cy}) scale(${comp.zoom})">
    <!-- cap -->
    <rect x="-80" y="-330" width="160" height="70" rx="8" fill="${pal.cap}"/>
    <rect x="-70" y="-260" width="140" height="22" rx="4" fill="${pal.ring}"/>
    <!-- neck -->
    <rect x="-52" y="-238" width="104" height="46" fill="${pal.glass}" opacity="0.7"/>
    <!-- shoulder curve -->
    <path d="M -190 -190 C -190 -230 -140 -240 -60 -240 L 60 -240 C 140 -240 190 -230 190 -190 L 190 300 C 190 350 150 380 100 380 L -100 380 C -150 380 -190 350 -190 300 Z"
      fill="url(#${glassGrad})" stroke="${pal.ring}" stroke-width="2" opacity="0.98"/>
    <!-- liquid level -->
    <path d="M -170 20 L 170 20 L 170 300 C 170 340 140 360 100 360 L -100 360 C -140 360 -170 340 -170 300 Z"
      fill="${pal.liquid}" opacity="0.85"/>
    <!-- highlight -->
    <path d="M -150 -190 L -110 -190 L -110 260 L -150 260 Z" fill="#ffffff" opacity="0.08"/>
    <path d="M 100 -180 L 130 -180 L 130 260 L 100 260 Z" fill="#ffffff" opacity="0.05"/>

    <!-- label -->
    <rect x="-110" y="80" width="220" height="130" rx="4" fill="${pal.label}" opacity="0.94"/>
    <line x1="-90" y1="120" x2="90" y2="120" stroke="${pal.bg[0]}" stroke-opacity="0.4" stroke-width="1"/>
    <text x="0" y="140" text-anchor="middle" font-family="Times New Roman, serif" font-size="20" fill="${pal.bg[0]}" opacity="0.9" letter-spacing="1">${escapeXml(name).slice(0, 22)}</text>
    <text x="0" y="170" text-anchor="middle" font-family="Courier, monospace" font-size="11" fill="${pal.bg[0]}" opacity="0.65" letter-spacing="3">${escapeXml(concentration)}${labelSuffix ? ' · ' + escapeXml(labelSuffix) : ''}</text>
    <text x="0" y="196" text-anchor="middle" font-family="Courier, monospace" font-size="9" fill="${pal.bg[0]}" opacity="0.5" letter-spacing="4">COLLECTOR · BANDUNG</text>
  </g>

  <!-- corner mark -->
  <text x="60" y="80" font-family="Courier, monospace" font-size="16" fill="${pal.label}" opacity="0.5" letter-spacing="4">COLLECTOR</text>
  <text x="60" y="105" font-family="Courier, monospace" font-size="10" fill="${pal.label}" opacity="0.35" letter-spacing="6">PARFUM</text>

  <!-- bottom code -->
  <text x="60" y="1060" font-family="Courier, monospace" font-size="10" fill="${pal.label}" opacity="0.35" letter-spacing="3">EDITION · 2026</text>
  <text x="840" y="1060" text-anchor="end" font-family="Courier, monospace" font-size="10" fill="${pal.label}" opacity="0.35" letter-spacing="3">${escapeXml(category).toUpperCase()}</text>
</svg>`;

  const encoded = encodeURIComponent(svg)
    .replace(/'/g, '%27')
    .replace(/"/g, '%22');
  return `data:image/svg+xml;charset=utf-8,${encoded}`;
};

function escapeXml(s) {
  return String(s || '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&apos;');
}

// Helper to generate a full set (primary + 3 alternatives) per product
export const bottleSet = ({ name, concentration, category }) => [
  bottleImage({ name, concentration, category, variant: 0 }),
  bottleImage({ name, concentration, category, variant: 1, labelSuffix: '30ml' }),
  bottleImage({ name, concentration, category, variant: 2, labelSuffix: 'Ivory' }),
  bottleImage({ name, concentration, category, variant: 3, labelSuffix: 'Noir' }),
];

// Editorial / lifestyle unbranded photos (curated Unsplash — abstract/editorial, no clear branded bottles)
export const EDITORIAL_UNSPLASH = {
  moody_dark: 'https://images.unsplash.com/photo-1615634260167-c8cdede054de?auto=format&fit=crop&w=1600&q=85',
  amber_fabric: 'https://images.unsplash.com/photo-1592945403244-b3fbafd7f539?auto=format&fit=crop&w=1600&q=85',
  soft_pastel: 'https://images.unsplash.com/photo-1608528577891-eb055944f2e7?auto=format&fit=crop&w=1600&q=85',
  liquid_gold: 'https://images.unsplash.com/photo-1587017539504-67cfbddac569?auto=format&fit=crop&w=1600&q=85',
};
