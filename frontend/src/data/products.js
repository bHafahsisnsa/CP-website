// Collector Parfum product catalog (Bahasa Indonesia)
// Product bottle imagery is fully generated as SVG (unbranded, editorial).
// Category banner imagery uses editorial Unsplash (abstract/lifestyle, no branded bottles).

import { bottleImage } from '../lib/bottleArt';
import { moodBoard } from '../lib/moodArt';

const b = (name, concentration, category, variant = 0, labelSuffix = '') =>
  bottleImage({ name, concentration, category, variant, labelSuffix });

export const CATEGORIES = [
  { slug: 'citrus', name: 'Citrus', desc: 'Segar, ceria, penuh energi pagi.',
    image: moodBoard({ mood: 'citrus', ratio: '3:4', clean: true, accentText: 'SEGAR · CERIA' }) },
  { slug: 'floral', name: 'Floral', desc: 'Anggun, romantis, klasik.',
    image: moodBoard({ mood: 'floral', ratio: '3:4', clean: true, accentText: 'ANGGUN · ROMANTIS' }) },
  { slug: 'woody', name: 'Woody', desc: 'Hangat, tenang, membumi.',
    image: moodBoard({ mood: 'woody', ratio: '3:4', clean: true, accentText: 'HANGAT · TENANG' }) },
  { slug: 'gourmand', name: 'Gourmand', desc: 'Manis, addictive, cozy.',
    image: moodBoard({ mood: 'gourmand', ratio: '3:4', clean: true, accentText: 'MANIS · COZY' }) },
  { slug: 'fresh', name: 'Fresh Aquatic', desc: 'Sejuk, bersih, effortless.',
    image: moodBoard({ mood: 'fresh', ratio: '3:4', clean: true, accentText: 'SEJUK · BERSIH' }) },
  { slug: 'amber', name: 'Amber & Oud', desc: 'Mewah, sensual, timeless.',
    image: moodBoard({ mood: 'amber', ratio: '3:4', clean: true, accentText: 'MEWAH · TIMELESS' }) },
];

const makeProduct = (base) => ({
  ...base,
  images: [
    b(base.name, base.concentration, base.category, 0),
    b(base.name, base.concentration, base.category, 1),
    b(base.name, base.concentration, base.category, 2),
    b(base.name, base.concentration, base.category, 3),
  ],
});

export const PRODUCTS = [
  makeProduct({
    id: 'noir-01',
    slug: 'noir-oud-intense',
    name: 'Noir Oud Intense',
    brand: 'Collector',
    category: 'amber',
    concentration: 'EDP',
    gender: 'Unisex',
    price: 685000,
    compareAtPrice: 850000,
    bestSeller: true,
    isNew: false,
    tags: ['Woody', 'Oud', 'Musk'],
    volumes: [
      { ml: 30, price: 385000, stock: 12 },
      { ml: 50, price: 685000, stock: 8 },
      { ml: 100, price: 1150000, stock: 4 },
    ],
    notes: {
      top: ['Bergamot Italia', 'Lada Hitam'],
      heart: ['Oud Cambodia', 'Rose Turki'],
      base: ['Musk Putih', 'Amber', 'Cendana'],
    },
    description:
      'Aroma malam yang membekas — perpaduan oud dalam dengan sentuhan mawar dan musk yang menenangkan. Cocok untuk momen istimewa.',
    performance: { longevity: 'Sangat Lama (8–10 jam)', sillage: 'Kuat', season: 'Malam & Musim Dingin' },
  }),
  makeProduct({
    id: 'blanc-02',
    slug: 'blanc-neroli-bloom',
    name: 'Blanc Neroli Bloom',
    brand: 'Collector',
    category: 'floral',
    concentration: 'EDP',
    gender: 'Wanita',
    price: 495000,
    compareAtPrice: null,
    bestSeller: true,
    isNew: true,
    tags: ['Neroli', 'White Floral'],
    volumes: [
      { ml: 30, price: 295000, stock: 20 },
      { ml: 50, price: 495000, stock: 15 },
      { ml: 100, price: 850000, stock: 9 },
    ],
    notes: {
      top: ['Neroli', 'Lemon Sisilia'],
      heart: ['Melati', 'Bunga Jeruk'],
      base: ['Musk', 'Amber Putih'],
    },
    description:
      'Bouquet putih yang lembut dan bercahaya — segar dari pagi hingga sore, tanpa terasa berlebihan.',
    performance: { longevity: 'Lama (6–8 jam)', sillage: 'Sedang', season: 'Sepanjang tahun' },
  }),
  makeProduct({
    id: 'citra-03',
    slug: 'citra-bergamot-solar',
    name: 'Citra Bergamot Solar',
    brand: 'Collector',
    category: 'citrus',
    concentration: 'EDT',
    gender: 'Unisex',
    price: 385000,
    compareAtPrice: 450000,
    bestSeller: false,
    isNew: true,
    tags: ['Citrus', 'Herbal'],
    volumes: [
      { ml: 30, price: 225000, stock: 30 },
      { ml: 50, price: 385000, stock: 22 },
      { ml: 100, price: 665000, stock: 11 },
    ],
    notes: {
      top: ['Bergamot', 'Lemon', 'Grapefruit'],
      heart: ['Basil', 'Teh Hijau'],
      base: ['Kayu Cedar', 'Musk'],
    },
    description: 'Segar seperti pagi Mediterania — ringan, ceria, dan penuh cahaya matahari.',
    performance: { longevity: 'Sedang (5–6 jam)', sillage: 'Sedang', season: 'Musim Panas' },
  }),
  makeProduct({
    id: 'velvet-04',
    slug: 'velvet-vanilla-noir',
    name: 'Velvet Vanilla Noir',
    brand: 'Collector',
    category: 'gourmand',
    concentration: 'EDP',
    gender: 'Wanita',
    price: 545000,
    compareAtPrice: null,
    bestSeller: true,
    isNew: false,
    tags: ['Vanilla', 'Sweet', 'Cozy'],
    volumes: [
      { ml: 30, price: 315000, stock: 14 },
      { ml: 50, price: 545000, stock: 10 },
      { ml: 100, price: 950000, stock: 5 },
    ],
    notes: {
      top: ['Pir', 'Bergamot'],
      heart: ['Vanilla Madagascar', 'Melati'],
      base: ['Praline', 'Musk', 'Kayu Manis'],
    },
    description: 'Manis lembut yang addictive — hangat seperti pelukan di malam hari.',
    performance: { longevity: 'Sangat Lama (8–10 jam)', sillage: 'Kuat', season: 'Musim Dingin' },
  }),
  makeProduct({
    id: 'atlas-05',
    slug: 'atlas-cedar-storm',
    name: 'Atlas Cedar Storm',
    brand: 'Collector',
    category: 'woody',
    concentration: 'EDP',
    gender: 'Pria',
    price: 625000,
    compareAtPrice: 720000,
    bestSeller: false,
    isNew: false,
    tags: ['Woody', 'Spicy'],
    volumes: [
      { ml: 30, price: 355000, stock: 18 },
      { ml: 50, price: 625000, stock: 12 },
      { ml: 100, price: 1085000, stock: 6 },
    ],
    notes: {
      top: ['Kapulaga', 'Bergamot'],
      heart: ['Cedar Atlas', 'Iris'],
      base: ['Vetiver', 'Amber', 'Musk'],
    },
    description: 'Kayu cedar yang tegas dengan rempah lembut — modern, elegan, dan penuh karakter.',
    performance: { longevity: 'Lama (7–9 jam)', sillage: 'Kuat', season: 'Musim Semi & Gugur' },
  }),
  makeProduct({
    id: 'marine-06',
    slug: 'marine-driftwood',
    name: 'Marine Driftwood',
    brand: 'Collector',
    category: 'fresh',
    concentration: 'EDT',
    gender: 'Pria',
    price: 425000,
    compareAtPrice: null,
    bestSeller: false,
    isNew: true,
    tags: ['Aquatic', 'Salty'],
    volumes: [
      { ml: 30, price: 245000, stock: 25 },
      { ml: 50, price: 425000, stock: 16 },
      { ml: 100, price: 745000, stock: 8 },
    ],
    notes: {
      top: ['Aksen Laut', 'Mandarin'],
      heart: ['Lavender', 'Rosemary'],
      base: ['Driftwood', 'Ambergris'],
    },
    description: 'Sejuknya angin laut dan kayu apung — bersih, effortless, siap dipakai setiap hari.',
    performance: { longevity: 'Sedang (5–7 jam)', sillage: 'Sedang', season: 'Musim Panas' },
  }),
  makeProduct({
    id: 'rose-07',
    slug: 'rose-taipa-velvet',
    name: 'Rose Taipa Velvet',
    brand: 'Collector',
    category: 'floral',
    concentration: 'EDP',
    gender: 'Wanita',
    price: 715000,
    compareAtPrice: 895000,
    bestSeller: true,
    isNew: false,
    tags: ['Rose', 'Musk'],
    volumes: [
      { ml: 30, price: 415000, stock: 10 },
      { ml: 50, price: 715000, stock: 7 },
      { ml: 100, price: 1250000, stock: 3 },
    ],
    notes: {
      top: ['Lychee', 'Raspberry'],
      heart: ['Rose Turki', 'Peony'],
      base: ['Patchouli', 'Musk Merah'],
    },
    description: 'Mawar yang sensual dengan sentuhan buah beri — feminine, dewasa, dan penuh percaya diri.',
    performance: { longevity: 'Lama (7–9 jam)', sillage: 'Kuat', season: 'Malam' },
  }),
  makeProduct({
    id: 'kayu-08',
    slug: 'kayu-sandal-rain',
    name: 'Kayu Sandal Rain',
    brand: 'Collector',
    category: 'woody',
    concentration: 'EDP',
    gender: 'Unisex',
    price: 565000,
    compareAtPrice: null,
    bestSeller: false,
    isNew: false,
    tags: ['Sandalwood', 'Petrichor'],
    volumes: [
      { ml: 30, price: 325000, stock: 15 },
      { ml: 50, price: 565000, stock: 11 },
      { ml: 100, price: 985000, stock: 5 },
    ],
    notes: {
      top: ['Ozonic', 'Bambu'],
      heart: ['Cendana Mysore', 'Teh Putih'],
      base: ['Vetiver', 'Musk Putih'],
    },
    description: 'Aroma hujan pertama di atas kayu cendana — meditatif dan nostalgia.',
    performance: { longevity: 'Lama (6–8 jam)', sillage: 'Sedang', season: 'Sepanjang tahun' },
  }),
  makeProduct({
    id: 'sunset-09',
    slug: 'sunset-fig-jakarta',
    name: 'Sunset Fig Jakarta',
    brand: 'Collector',
    category: 'gourmand',
    concentration: 'EDP',
    gender: 'Unisex',
    price: 475000,
    compareAtPrice: 590000,
    bestSeller: false,
    isNew: true,
    tags: ['Fig', 'Green', 'Cozy'],
    volumes: [
      { ml: 30, price: 275000, stock: 22 },
      { ml: 50, price: 475000, stock: 14 },
      { ml: 100, price: 825000, stock: 7 },
    ],
    notes: {
      top: ['Daun Fig', 'Bergamot'],
      heart: ['Buah Fig', 'Kelapa'],
      base: ['Kayu Cedar', 'Susu Almond'],
    },
    description: 'Manis buah fig dengan sentuhan hijau — hangat seperti senja di tepi kota.',
    performance: { longevity: 'Sedang (5–7 jam)', sillage: 'Sedang', season: 'Musim Semi & Gugur' },
  }),
  makeProduct({
    id: 'onyx-10',
    slug: 'onyx-tobacco-leather',
    name: 'Onyx Tobacco Leather',
    brand: 'Collector',
    category: 'amber',
    concentration: 'EDP',
    gender: 'Pria',
    price: 745000,
    compareAtPrice: 895000,
    bestSeller: true,
    isNew: false,
    tags: ['Tobacco', 'Leather', 'Amber'],
    volumes: [
      { ml: 30, price: 425000, stock: 9 },
      { ml: 50, price: 745000, stock: 6 },
      { ml: 100, price: 1295000, stock: 3 },
    ],
    notes: {
      top: ['Rum', 'Bergamot'],
      heart: ['Daun Tembakau', 'Kulit'],
      base: ['Vanilla', 'Amber', 'Benzoin'],
    },
    description: 'Tembakau, kulit, dan rum — aroma penuh percaya diri untuk malam yang panjang.',
    performance: { longevity: 'Sangat Lama (9–12 jam)', sillage: 'Sangat Kuat', season: 'Musim Dingin & Malam' },
  }),
  makeProduct({
    id: 'iris-11',
    slug: 'iris-powder-silk',
    name: 'Iris Powder Silk',
    brand: 'Collector',
    category: 'floral',
    concentration: 'EDP',
    gender: 'Wanita',
    price: 585000,
    compareAtPrice: null,
    bestSeller: false,
    isNew: false,
    tags: ['Iris', 'Powdery'],
    volumes: [
      { ml: 30, price: 335000, stock: 13 },
      { ml: 50, price: 585000, stock: 9 },
      { ml: 100, price: 1020000, stock: 4 },
    ],
    notes: {
      top: ['Aldehid', 'Mandarin'],
      heart: ['Iris Butter', 'Violet'],
      base: ['Musk Putih', 'Kayu Cashmere'],
    },
    description: 'Iris seperti kain sutra — lembut, dingin, dan penuh anggun.',
    performance: { longevity: 'Lama (6–8 jam)', sillage: 'Sedang', season: 'Sepanjang tahun' },
  }),
  makeProduct({
    id: 'green-12',
    slug: 'green-basil-lime',
    name: 'Green Basil Lime',
    brand: 'Collector',
    category: 'citrus',
    concentration: 'EDT',
    gender: 'Unisex',
    price: 355000,
    compareAtPrice: null,
    bestSeller: false,
    isNew: true,
    tags: ['Citrus', 'Green'],
    volumes: [
      { ml: 30, price: 205000, stock: 28 },
      { ml: 50, price: 355000, stock: 18 },
      { ml: 100, price: 620000, stock: 9 },
    ],
    notes: {
      top: ['Jeruk Nipis', 'Mint'],
      heart: ['Basil', 'Daun Verbena'],
      base: ['Cedar', 'Musk Bersih'],
    },
    description: 'Sesegar salad herbal di siang hari — ceria, ringan, dan effortless.',
    performance: { longevity: 'Sedang (4–6 jam)', sillage: 'Sedang', season: 'Musim Panas' },
  }),
];

export const getProduct = (idOrSlug) =>
  PRODUCTS.find((p) => p.id === idOrSlug || p.slug === idOrSlug) || null;

export const getRelated = (id, limit = 4) =>
  PRODUCTS.filter((p) => p.id !== id).slice(0, limit);

// Avatar SVGs (initials, elegant, unbranded)
const initialAvatar = (initials, bg = '#e5d9c1') => {
  const svg = `<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><rect width='100' height='100' fill='${bg}'/><text x='50' y='58' font-family='DM Serif Display, serif' font-size='36' fill='#141414' text-anchor='middle'>${initials}</text></svg>`;
  return `data:image/svg+xml;charset=utf-8,${encodeURIComponent(svg)}`;
};

export const TESTIMONIALS = [
  { name: 'Alika P.', city: 'Jakarta', quote: 'Notes-nya sesuai deskripsi, tahan lama, dan botolnya cantik banget. Belanja di Collector Parfum udah kaya buka boutique.', avatar: initialAvatar('AP', '#efdfc4') },
  { name: 'Renata S.', city: 'Bandung', quote: 'Website-nya smooth banget, foto-fotonya editorial, dan checkoutnya cepat mirip di marketplace. Recommended.', avatar: initialAvatar('RS', '#dcd0be') },
  { name: 'Bagas R.', city: 'Surabaya', quote: 'Sampel dan kemasan rapi, aroma masih fresh saat sampai. Blanc Neroli Bloom jadi signature aku sekarang.', avatar: initialAvatar('BR', '#e7d5b6') },
  { name: 'Dita M.', city: 'Denpasar', quote: 'Suka banget notes pyramid-nya jelas dan pengiriman on time. Bakal repeat order untuk hadiah teman.', avatar: initialAvatar('DM', '#f0e2c9') },
  { name: 'Fajar A.', city: 'Medan', quote: 'Atlas Cedar Storm cocok dipakai kerja, elegan dan gak overpowering. Layanan customer service-nya juga ramah.', avatar: initialAvatar('FA', '#ded1b8') },
  { name: 'Kirana W.', city: 'Yogyakarta', quote: 'Aroma Rose Taipa Velvet bikin banyak yang nanya. Kesan pertama sampai afternote-nya balance banget.', avatar: initialAvatar('KW', '#eddec1') },
];

export const FAQ_ITEMS = [
  { q: 'Apakah semua parfum Collector 100% original?', a: 'Ya, seluruh produk kami dikurasi langsung dan bersegel dari distributor resmi. Setiap paket disertai kartu autentikasi.' },
  { q: 'Berapa lama estimasi pengiriman?', a: 'Pesanan diproses maksimal 1x24 jam kerja. Pengiriman JNE/J&T reguler 2–4 hari, ekspres 1–2 hari, tergantung kota.' },
  { q: 'Apakah tersedia opsi COD?', a: 'Ya, pembayaran COD tersedia di seluruh kota yang dilayani oleh kurir mitra kami.' },
  { q: 'Bagaimana cara memilih aroma yang cocok?', a: 'Gunakan filter notes/keluarga aroma di halaman Toko, atau baca notes pyramid di setiap produk. Kami juga menyediakan travel size 30ml untuk mencoba.' },
  { q: 'Apakah bisa retur atau tukar?', a: 'Retur diterima maksimal 3 hari setelah paket sampai untuk produk yang belum dibuka segelnya.' },
];

export const SHIPPING_OPTIONS = [
  { id: 'jne-reg', name: 'JNE Reguler', eta: '2–4 hari', price: 22000 },
  { id: 'jne-yes', name: 'JNE YES', eta: '1–2 hari', price: 32000 },
  { id: 'jnt-exp', name: 'J&T Express', eta: '2–3 hari', price: 21000 },
  { id: 'sicepat', name: 'SiCepat REG', eta: '2–3 hari', price: 20000 },
  { id: 'anteraja', name: 'AnterAja Reguler', eta: '2–4 hari', price: 19000 },
];

export const PAYMENT_METHODS = {
  transfer: [
    { id: 'bca', name: 'Transfer BCA', extra: 'Verifikasi otomatis' },
    { id: 'bni', name: 'Transfer BNI', extra: 'Verifikasi otomatis' },
    { id: 'mandiri', name: 'Transfer Mandiri', extra: 'Verifikasi otomatis' },
  ],
  ewallet: [
    { id: 'shopeepay', name: 'ShopeePay', extra: 'Cashback s.d. 5%' },
    { id: 'ovo', name: 'OVO', extra: '' },
    { id: 'gopay', name: 'GoPay', extra: '' },
    { id: 'dana', name: 'DANA', extra: '' },
  ],
  cod: [{ id: 'cod', name: 'Bayar di Tempat (COD)', extra: 'Biaya tambahan Rp 4.000' }],
};
