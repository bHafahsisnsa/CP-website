// lib/realImages.js — Sumber gambar editorial homepage (foto nyata, bukan SVG).
// Aset dikurasi dari Pexels (tema: dominan hitam/dark, elemen parfum, fokus model)
// dan disimpan lokal di `frontend/public/images/home/` agar stabil untuk produksi.
//
// Catatan: komponen tetap menghormati konten CMS (`useContent`). Konstanta di sini
// dipakai sebagai DEFAULT (menggantikan placeholder SVG lama dari `moodArt.js`).

const BASE = '/images/home';

export const HOME_IMAGES = {
  hero: {
    // Siluet model dalam cahaya dramatis (dark, model-focused)
    main: `${BASE}/hero-main.jpg`,
    // Botol parfum di atas kain gelap (dark, perfume)
    float: `${BASE}/hero-float.jpg`,
  },
  media: {
    // Editorial: model wanita, bayangan dramatis (dark)
    large: `${BASE}/media-large.jpg`,
    cards: [
      `${BASE}/media-card-1.jpg`, // model + ring light biru
      `${BASE}/media-card-2.jpg`, // model blazer hitam
    ],
  },
  // Urutan mengikuti daftar FEATURED di FeaturedCollection.js:
  // [0] Best of Woody, [1] Floral Baru, [2] Promo, [3] Pria, [4] Wanita
  featured: [
    `${BASE}/featured-woody.jpg`,
    `${BASE}/featured-floral.jpg`,
    `${BASE}/featured-promo.jpg`,
    `${BASE}/featured-men.jpg`,
    `${BASE}/featured-women.jpg`,
  ],
  video: {
    // Poster film: tangan menuang parfum, gelap
    poster: `${BASE}/video-poster.jpg`,
  },
  faq: {
    // Detail botol parfum dengan spotlight
    image: `${BASE}/faq.jpg`,
  },
};

// Fallback gambar kategori per-slug (dipakai bila backend tidak mengirim `image`).
export const CATEGORY_IMAGES_BY_SLUG = {
  amber: `${BASE}/cat-amber.jpg`,
  citrus: `${BASE}/cat-citrus.jpg`,
  floral: `${BASE}/cat-floral.jpg`,
  fresh: `${BASE}/cat-fresh.jpg`,
  gourmand: `${BASE}/cat-gourmand.jpg`,
  woody: `${BASE}/cat-woody.jpg`,
};
