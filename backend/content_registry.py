"""content_registry.py — SSOT konten storefront (Epic E9 — Storefront CMS).

Setiap section = satu dokumen koleksi `content` (id = key). `fields` mendefinisikan
skema form generik yang dirender admin; `default` = konten storefront saat ini (agar
tampilan tak berubah bila admin belum mengedit). Tipe field: text, textarea, image,
list (list string), repeater (list objek dgn sub-field `item`).
"""


def T(name, label):
    return {"name": name, "label": label, "type": "text"}


def TA(name, label):
    return {"name": name, "label": label, "type": "textarea"}


def IMG(name, label):
    return {"name": name, "label": label, "type": "image"}


def LST(name, label):
    return {"name": name, "label": label, "type": "list"}


def REP(name, label, item):
    return {"name": name, "label": label, "type": "repeater", "item": item}


def TOG(name, label):
    return {"name": name, "label": label, "type": "toggle"}


def SEL(name, label, options):
    """options: list of {"value","label"}."""
    return {"name": name, "label": label, "type": "select", "options": options}


def GAL(name, label):
    """Galeri gambar: list {image, caption, to} — dipilih multi dari Media Manager."""
    return {"name": name, "label": label, "type": "gallery"}


# Urutan & visibilitas section Beranda (dipakai HomePage + section home_layout).
HOME_SECTIONS = [
    {"value": "hero", "label": "Hero"},
    {"value": "marquee_words", "label": "Marquee (kata berjalan)"},
    {"value": "story_strip", "label": "Cerita Kami (strip)"},
    {"value": "occasion_section", "label": "Shop by Occasion"},
    {"value": "character_section", "label": "Shop by Character"},
    {"value": "trending", "label": "Sedang Trending"},
    {"value": "media_editorial", "label": "Editorial (media grid)"},
    {"value": "trust", "label": "Trust Strip"},
    {"value": "featured", "label": "Koleksi Unggulan"},
    {"value": "big_word", "label": "Manifesto (kata besar)"},
    {"value": "new_arrivals", "label": "Baru Datang"},
    {"value": "gallery", "label": "Galeri"},
    {"value": "video", "label": "Video / Behind the Scenes"},
    {"value": "testimonials", "label": "Testimoni"},
    {"value": "faq", "label": "FAQ"},
]


SECTIONS = [
    # ----------------------------- GLOBAL -----------------------------
    {
        "key": "announcement", "label": "Announcement Bar", "group": "Global",
        "fields": [LST("items", "Teks berjalan (atas)")],
        "default": {"items": [
            "Refill Perfume Distributor Since 1970",
            "3 Cabang di Bandung — Paledang · Pasir Kaliki · Gatot Subroto",
            "Tersedia Ukuran 30 ml · 50 ml · 60 ml · 100 ml",
            "Kirim ke Seluruh Indonesia, Brunei & Malaysia",
            "Same-day Bandung — pembayaran sebelum 10.00 WIB",
        ]},
    },
    {
        "key": "header", "label": "Header / Navigasi", "group": "Global",
        "fields": [
            T("logo_name", "Nama logo"), T("logo_suffix", "Sufiks logo"),
            REP("nav", "Menu navigasi", [T("label", "Label"), T("to", "Tautan")]),
        ],
        "default": {
            "logo_name": "Collector", "logo_suffix": "Parfum",
            "nav": [
                {"label": "Beranda", "to": "/"}, {"label": "Toko", "to": "/shop"},
                {"label": "Koleksi", "to": "/shop?featured=1"},
                {"label": "Lokasi", "to": "/lokasi"},
                {"label": "Tentang", "to": "/tentang"}, {"label": "Kontak", "to": "/kontak"},
            ],
        },
    },
    {
        "key": "footer", "label": "Footer", "group": "Global",
        "fields": [
            TA("tagline", "Tagline"),
            T("shop_title", "Judul kolom Belanja"),
            REP("shop_links", "Tautan Belanja", [T("label", "Label"), T("to", "Tautan")]),
            T("help_title", "Judul kolom Bantuan"),
            REP("help_links", "Tautan Bantuan", [T("label", "Label"), T("to", "Tautan")]),
            T("newsletter_title", "Judul Newsletter"),
            TA("newsletter_desc", "Deskripsi Newsletter"),
            LST("payment_badges", "Badge pembayaran"),
        ],
        "default": {
            "tagline": "Distributor parfum refill sejak 1970. Paledang · Pasir Kaliki · Gatot Subroto, Bandung.",
            "shop_title": "Belanja",
            "shop_links": [
                {"label": "Semua Parfum", "to": "/shop"},
                {"label": "Citrus", "to": "/shop?cat=citrus"},
                {"label": "Floral", "to": "/shop?cat=floral"},
                {"label": "Woody", "to": "/shop?cat=woody"},
                {"label": "Amber & Oud", "to": "/shop?cat=amber"},
            ],
            "help_title": "Bantuan",
            "help_links": [
                {"label": "Kontak", "to": "/kontak"},
                {"label": "Lokasi Toko", "to": "/lokasi"},
                {"label": "Tentang Kami", "to": "/tentang"},
                {"label": "Voucher", "to": "/voucher"},
            ],
            "newsletter_title": "Newsletter",
            "newsletter_desc": "Aroma baru, promo, dan cerita di email Anda.",
            "payment_badges": ["BCA", "BNI", "Mandiri", "OVO", "GoPay", "DANA", "COD"],
        },
    },
    {
        "key": "seo", "label": "SEO & Meta (global)", "group": "Global",
        "fields": [
            T("site_name", "Nama situs (akhiran judul tab)"),
            T("home_title", "Judul halaman Beranda"),
            TA("home_description", "Deskripsi meta Beranda"),
            TA("default_description", "Deskripsi meta default (halaman lain)"),
            IMG("og_image", "Gambar berbagi (Open Graph)"),
        ],
        "default": {
            "site_name": "Collector Parfum",
            "home_title": "Collector Parfum — Aroma yang Membekas",
            "home_description": "Distributor parfum refill di Bandung sejak 1970. Biang impor pilihan, 30–100 ml, kirim ke seluruh Indonesia.",
            "default_description": "Collector Parfum — parfum refill sejak 1970. Paledang · Pasir Kaliki · Gatot Subroto, Bandung.",
            "og_image": "",
        },
    },
    # ----------------------------- HOMEPAGE -----------------------------
    {
        "key": "home_layout", "label": "Tata Letak Beranda", "group": "Beranda",
        "fields": [REP("sections", "Urutan & tampil/sembunyikan section (geser untuk mengurutkan)",
                       [SEL("key", "Section", HOME_SECTIONS), TOG("visible", "Tampilkan")])],
        "default": {"sections": [{"key": o["value"], "visible": True} for o in HOME_SECTIONS]},
    },
    {
        "key": "hero", "label": "Hero (Beranda)", "group": "Beranda",
        "fields": [
            T("eyebrow", "Eyebrow"), T("title", "Judul (baris atas)"),
            T("title_accent", "Judul aksen (brass, baris bawah)"),
            TA("subtitle", "Subjudul"),
            T("primary_label", "Tombol utama - teks"), T("primary_to", "Tombol utama - tautan"),
            T("secondary_label", "Tombol kedua - teks"), T("secondary_to", "Tombol kedua - tautan"),
            T("chip", "Chip pada gambar"), T("scroll_hint", "Teks gulir"),
            T("bg_type", "Latar belakang: 'video' atau 'image'"),
            T("bg_video", "URL video latar (.mp4) — dipakai bila tipe = video"),
            IMG("bg_image", "Foto latar / poster (URL)"),
        ],
        "default": {
            "eyebrow": "Refill Perfume Distributor · Sejak 1970",
            "title": "Aroma yang membekas.", "title_accent": "Diracik ulang di Bandung.",
            "subtitle": "Sejak 1970 kami memilih biang parfum impor terbaik dan mengisinya ulang untuk Anda — variasi aroma luas, harga bersaing, tersedia 30 ml hingga 100 ml.",
            "primary_label": "Lihat Katalog", "primary_to": "/shop",
            "secondary_label": "Lihat Best Seller", "secondary_to": "/shop?bestSeller=1",
            "chip": "Best Seller · Parfum Refill", "scroll_hint": "Gulir untuk menjelajahi",
            "bg_type": "video", "bg_video": "/videos/hero.mp4", "bg_image": "",
        },
    },
    {
        "key": "marquee_words", "label": "Marquee (kata berjalan)", "group": "Beranda",
        "fields": [LST("items", "Kata")],
        "default": {"items": ["ELEGAN", "BERKARAKTER", "REFILL", "SEJAK 1970", "MEMBEKAS", "BANDUNG"]},
    },
    {
        "key": "story_strip", "label": "Cerita Kami (strip)", "group": "Beranda",
        "fields": [T("eyebrow", "Eyebrow"), TA("text", "Kalimat")],
        "default": {
            "eyebrow": "Cerita Kami",
            "text": "Dari kios sempit di Jalan Kolektor tahun 1970 hingga tiga cabang di Bandung — kami masih melakukan hal yang sama: memilih biang parfum terbaik, lalu mengisinya ulang untuk Anda.",
        },
    },
    {
        "key": "occasion_section", "label": "Shop by Occasion (heading)", "group": "Beranda",
        "fields": [T("eyebrow", "Eyebrow"), T("title", "Judul"), TA("subtitle", "Subjudul")],
        "default": {
            "eyebrow": "Shop by Occasion", "title": "Pilih sesuai momen.",
            "subtitle": "Dari meeting pagi hingga malam istimewa — temukan aroma yang pas untuk setiap kesempatan.",
        },
    },
    {
        "key": "character_section", "label": "Shop by Character (heading)", "group": "Beranda",
        "fields": [T("eyebrow", "Eyebrow"), T("title", "Judul"), TA("subtitle", "Subjudul")],
        "default": {
            "eyebrow": "Shop by Character", "title": "Temukan karaktermu.",
            "subtitle": "Setiap karakter aroma punya kepribadian sendiri. Pilih yang paling mewakili dirimu.",
        },
    },
    {
        "key": "trending", "label": "Sedang Trending (heading)", "group": "Beranda",
        "fields": [T("eyebrow", "Eyebrow"), T("title", "Judul")],
        "default": {"eyebrow": "Trending", "title": "Sedang Trending"},
    },
    {
        "key": "media_editorial", "label": "Editorial (media grid)", "group": "Beranda",
        "fields": [
            T("eyebrow", "Eyebrow"), T("title", "Judul"),
            T("large_tag", "Kartu besar - tag"), T("large_title", "Kartu besar - judul"),
            TA("large_desc", "Kartu besar - deskripsi"), T("large_to", "Kartu besar - tautan"),
            IMG("large_image", "Kartu besar - gambar (URL)"),
            REP("cards", "Kartu kanan", [T("tag", "Tag"), T("title", "Judul"), T("to", "Tautan"), IMG("image", "Gambar (URL)")]),
        ],
        "default": {
            "eyebrow": "Cerita Aroma", "title": "Editorial yang menemani harimu.",
            "large_tag": "Featured", "large_title": "Malam yang membekas.",
            "large_desc": "Amber dan oud yang hangat untuk momen paling personal.",
            "large_to": "/shop?cat=amber", "large_image": "",
            "cards": [
                {"tag": "Baru", "title": "Bouquet putih, siang cerah.", "to": "/shop?cat=floral", "image": ""},
                {"tag": "Trending", "title": "Woody yang tenang.", "to": "/shop?cat=woody", "image": ""},
            ],
        },
    },
    {
        "key": "featured", "label": "Koleksi Unggulan", "group": "Beranda",
        "fields": [
            T("eyebrow", "Eyebrow"), T("title", "Judul"),
            REP("items", "Kartu", [T("tag", "Tag"), T("title", "Judul"), T("to", "Tautan"), IMG("image", "Gambar (URL)")]),
        ],
        "default": {
            "eyebrow": "Pilihan Kurator", "title": "Koleksi unggulan.",
            "items": [
                {"tag": "Curated", "title": "Koleksi Best of Woody", "to": "/shop?cat=woody", "image": ""},
                {"tag": "Baru", "title": "Floral Baru", "to": "/shop?cat=floral", "image": ""},
                {"tag": "Promo", "title": "Diskon s.d. 30%", "to": "/shop?promo=1", "image": ""},
                {"tag": "Populer", "title": "Best Seller Untuk Pria", "to": "/shop?gender=pria", "image": ""},
                {"tag": "Editorial", "title": "Signature Wanita", "to": "/shop?gender=wanita", "image": ""},
            ],
        },
    },
    {
        "key": "big_word", "label": "Manifesto (kata besar)", "group": "Beranda",
        "fields": [LST("words", "Kata besar"), TA("caption", "Caption")],
        "default": {
            "words": ["Aroma", "yang", "membekas"],
            "caption": "Kami percaya parfum bukan sekadar pelengkap gaya — ia adalah tanda tangan yang tersisa saat Anda meninggalkan ruangan.",
        },
    },
    {
        "key": "new_arrivals", "label": "Baru Datang (heading)", "group": "Beranda",
        "fields": [T("eyebrow", "Eyebrow"), T("title", "Judul")],
        "default": {"eyebrow": "New Arrivals", "title": "Baru Datang"},
    },
    {
        "key": "gallery", "label": "Galeri (foto toko / Instagram)", "group": "Beranda",
        "fields": [
            T("eyebrow", "Eyebrow"), T("title", "Judul"), T("title_accent", "Judul aksen (brass)"),
            TA("subtitle", "Subjudul"),
            SEL("layout", "Tata letak", [{"value": "masonry", "label": "Masonry (tinggi bervariasi)"},
                                          {"value": "grid", "label": "Grid rapi (persegi)"},
                                          {"value": "strip", "label": "Strip geser horizontal"}]),
            GAL("items", "Foto galeri"),
            T("cta_label", "Tautan bawah - teks"), T("cta_to", "Tautan bawah - URL"),
        ],
        "default": {
            "eyebrow": "Galeri", "title": "Dari rak", "title_accent": "ke tanganmu.",
            "subtitle": "Suasana toko, botol pilihan, dan momen pelanggan kami.",
            "layout": "masonry", "items": [],
            "cta_label": "Ikuti @collectorparfum", "cta_to": "https://instagram.com/collectorparfum",
        },
    },
    {
        "key": "video", "label": "Video / Behind the Scenes", "group": "Beranda",
        "fields": [
            T("eyebrow", "Eyebrow"), T("title", "Judul"), T("title_accent", "Judul aksen (brass)"),
            TA("text", "Deskripsi"), T("play_label", "Teks tombol play"),
            T("secondary_label", "Tautan sekunder - teks"), T("secondary_to", "Tautan sekunder - tautan"),
            IMG("poster", "Poster/gambar (URL)"),
        ],
        "default": {
            "eyebrow": "Di Balik Botol", "title": "Refill yang", "title_accent": "teliti.",
            "text": "Setiap aroma dimulai dari pemilihan biang impor, uji ketahanan, lalu pengisian ulang ke botol pilihan Anda — dari 30 ml hingga 100 ml.",
            "play_label": "Tonton Cerita", "secondary_label": "Baca Sejarah Kami", "secondary_to": "/tentang",
            "poster": "",
        },
    },
    {
        "key": "testimonials", "label": "Testimoni (heading)", "group": "Beranda",
        "fields": [T("eyebrow", "Eyebrow"), T("title", "Judul"), T("title_accent", "Judul aksen (brass)")],
        "default": {"eyebrow": "Cerita Pelanggan", "title": "Cerita yang", "title_accent": "menginspirasi."},
    },
    {
        "key": "faq", "label": "FAQ", "group": "Beranda",
        "fields": [
            T("eyebrow", "Eyebrow"), T("title", "Judul"), T("title_accent", "Judul aksen (brass)"),
            T("cta_label", "Teks tautan bantuan"), T("cta_to", "Tautan bantuan"),
            REP("items", "Pertanyaan", [T("q", "Pertanyaan"), TA("a", "Jawaban")]),
        ],
        "default": {
            "eyebrow": "Pusat Bantuan", "title": "Pertanyaan yang", "title_accent": "sering ditanya.",
            "cta_label": "Hubungi Tim Kami", "cta_to": "/kontak",
            "items": [
                {"q": "Bagaimana cara memesan?",
                 "a": "Anda bisa checkout langsung di situs ini, atau kirim format orderan lewat WhatsApp +62 857-2000-0105 / +62 857-2013-7777 atau LINE @collectorparfum: Nama Lengkap, Alamat Lengkap, Kota, Provinsi, Kode Pos, dan Pesanan (nama parfum + ukuran botol). Admin akan mengirim total belanja beserta instruksi pembayaran."},
                {"q": "Berapa lama pesanan saya diproses?",
                 "a": "Pesanan partai kecil diproses 1×24 jam setelah pembayaran diterima. Pesanan partai besar diproses 2–5 hari kerja."},
                {"q": "Berapa lama barang sampai?",
                 "a": "Area Jabodetabek 1–3 hari kerja dan luar Jabodetabek 2–7 hari kerja setelah barang dikirim. Pengiriman dilakukan Senin–Jumat; Sabtu, Minggu, dan hari libur nasional kami tutup untuk pengiriman."},
                {"q": "Apakah bisa kirim ke luar negeri?",
                 "a": "Kami mengirim ke seluruh Indonesia, Brunei, dan Malaysia. Biaya pengiriman ditanggung pembeli."},
                {"q": "Bisakah barang diterima di hari yang sama?",
                 "a": "Bisa untuk wilayah Bandung, dengan syarat pembayaran sudah berhasil diproses tim kami sebelum pukul 10.00 WIB."},
                {"q": "Ukuran botol apa saja yang tersedia?",
                 "a": "Tersedia 30 ml, 50 ml, 60 ml, dan 100 ml — ketersediaan mengikuti stok tiap aroma."},
                {"q": "Apakah nama merek pada katalog adalah produk asli merek tersebut?",
                 "a": "Tidak. Kami menjual parfum refill dengan aroma yang terinspirasi merek tersebut, sehingga di katalog ditandai \u201cInspired by <merek>\u201d. Nama dan foto hanya ilustrasi."},
            ],
        },
    },
    {
        "key": "trust", "label": "Trust Strip (keunggulan)", "group": "Beranda",
        "fields": [REP("items", "Keunggulan", [T("title", "Judul"), TA("desc", "Deskripsi")])],
        "default": {"items": [
            {"title": "Sejak 1970", "desc": "Pelopor usaha refill parfum di Indonesia."},
            {"title": "Biang Impor Pilihan", "desc": "Diseleksi teliti sebelum masuk ke rak."},
            {"title": "3 Cabang di Bandung", "desc": "Paledang · Pasir Kaliki · Gatot Subroto."},
        ]},
    },
    # ----------------------------- PAGES -----------------------------
    {
        "key": "shop_page", "label": "Halaman Toko (/shop)", "group": "Halaman",
        "fields": [
            T("eyebrow", "Eyebrow"), T("title", "Judul"), T("title_accent", "Judul aksen (brass)"),
            T("title_after", "Judul (setelah aksen)"),
            T("seo_title", "Judul tab (SEO)"), TA("seo_description", "Deskripsi meta (SEO)"),
            T("empty_title", "Teks saat tidak ada produk"), T("empty_hint", "Petunjuk saat kosong"),
        ],
        "default": {
            "eyebrow": "Toko", "title": "Semua parfum, satu", "title_accent": "rak", "title_after": ".",
            "seo_title": "Semua Parfum — Koleksi Collector Parfum",
            "seo_description": "Jelajahi seluruh koleksi parfum refill: filter keluarga aroma, ukuran, gender, dan occasion. Kirim ke seluruh Indonesia.",
            "empty_title": "Belum ada produk yang cocok.", "empty_hint": "Coba ubah filter atau kata kunci pencarian.",
        },
    },
    {
        "key": "locations_page", "label": "Halaman Lokasi (/lokasi)", "group": "Halaman",
        "fields": [
            T("eyebrow", "Eyebrow"), T("title", "Judul"), T("title_accent", "Judul aksen (brass)"),
            T("title_after", "Judul (setelah aksen)"),
            T("reviews_eyebrow", "Ulasan - eyebrow"), T("reviews_title", "Ulasan - judul"),
            T("reviews_accent", "Ulasan - aksen (brass)"), T("reviews_after", "Ulasan - setelah aksen"),
            T("seo_title", "Judul tab (SEO)"), TA("seo_description", "Deskripsi meta (SEO)"),
        ],
        "default": {
            "eyebrow": "Lokasi Toko", "title": "Kunjungi", "title_accent": "butik", "title_after": "kami.",
            "reviews_eyebrow": "Ulasan", "reviews_title": "Apa kata", "reviews_accent": "pelanggan", "reviews_after": ".",
            "seo_title": "Lokasi Toko — Collector Parfum",
            "seo_description": "Kunjungi toko Collector Parfum di Bandung: Paledang, Pasir Kaliki, Gatot Subroto. Alamat, jam buka, dan petunjuk arah.",
        },
    },
    {
        "key": "voucher_page", "label": "Halaman Voucher (/voucher)", "group": "Halaman",
        "fields": [
            T("eyebrow", "Eyebrow"), T("title", "Judul"), TA("subtitle", "Subjudul"),
            T("list_title", "Judul daftar voucher"),
        ],
        "default": {
            "eyebrow": "Voucher", "title": "Kumpulkan & pakai voucher.",
            "subtitle": "Diskon dihitung langsung oleh sistem saat checkout — angka di keranjang dan di pembayaran selalu sama.",
            "list_title": "Voucher Tersedia",
        },
    },
    {
        "key": "about", "label": "Halaman Tentang", "group": "Halaman",
        "fields": [
            T("eyebrow", "Eyebrow"), T("title", "Judul"), T("title_accent", "Judul aksen (brass)"),
            TA("intro", "Paragraf intro"), IMG("hero_image", "Gambar hero (URL)"),
            T("marquee", "Teks marquee"),
            T("values_eyebrow", "Nilai - eyebrow"), T("values_title", "Nilai - judul"),
            REP("values", "Nilai", [T("title", "Judul"), TA("desc", "Deskripsi")]),
            T("journey_eyebrow", "Perjalanan - eyebrow"), T("journey_title", "Perjalanan - judul"),
            IMG("journey_image", "Perjalanan - gambar (URL)"),
            REP("timeline", "Timeline", [T("year", "Tahun"), T("title", "Judul"), TA("text", "Teks")]),
            T("cta_eyebrow", "CTA - eyebrow"), T("cta_title", "CTA - judul"), T("cta_accent", "CTA - aksen (brass)"),
            T("cta_label", "CTA - tombol teks"), T("cta_to", "CTA - tombol tautan"),
        ],
        "default": {
            "eyebrow": "Cerita Kami", "title": "Refill parfum pertama", "title_accent": "di Indonesia, sejak 1970.",
            "intro": "Pada 8 September 1970, usaha refill parfum pertama di Indonesia didirikan di Jalan Kolektor, Bandung. Karena jalannya sempit, toko berpindah ke Jalan Paledang No. 14, lalu memantapkan nama menjadi Collector Parfum dan menetap di Jalan Paledang No. 58, Bandung.",
            "hero_image": "", "marquee": "Refill Perfume Distributor Since 1970",
            "values_eyebrow": "Nilai Kami", "values_title": "Biang pilihan, harga bersaing.",
            "values": [
                {"title": "Biang Impor Pilihan", "desc": "Kami sangat teliti memilih produk biang unggulan (impor) sebelum dipasarkan."},
                {"title": "Harga Bersaing", "desc": "Variasi aroma yang luas dengan harga relatif murah dan bersaing."},
                {"title": "Dipercaya sebagai Supplier", "desc": "Selain ritel, kami melayani pelanggan yang menjadikan kami supplier parfum refill."},
                {"title": "3 Cabang di Bandung", "desc": "Paledang, Pasir Kaliki, dan Gatot Subroto — cium langsung sebelum membeli."},
            ],
            "journey_eyebrow": "Perjalanan", "journey_title": "Dari Jalan Kolektor ke tiga cabang.", "journey_image": "",
            "timeline": [
                {"year": "1970", "title": "Berdiri di Jalan Kolektor",
                 "text": "8 September 1970 — untuk pertama kalinya di Indonesia, usaha refill parfum didirikan di Jalan Kolektor, Bandung."},
                {"year": "Awal", "title": "Pindah ke Paledang No. 14",
                 "text": "Toko pertama berada di jalan yang sempit, sehingga kami berpindah ke Jalan Paledang No. 14."},
                {"year": "Kini", "title": "Menetap di Paledang No. 58",
                 "text": "Nama Collector Parfum dimantapkan dan toko menetap di Jalan Paledang No. 58, Bandung."},
                {"year": "Berkembang", "title": "Cabang Pasir Kaliki & Gatot Subroto",
                 "text": "Respons baik masyarakat dan kepercayaan sebagai supplier mendorong kami membuka cabang di Jalan Pasirkaliki No. 148A dan Jalan Gatot Subroto No. 271, Bandung."},
            ],
            "cta_eyebrow": "Mulai perjalanan", "cta_title": "Temukan aroma yang", "cta_accent": "berbicara tentangmu.",
            "cta_label": "Lihat Katalog", "cta_to": "/shop",
        },
    },
    {
        "key": "contact", "label": "Halaman Kontak", "group": "Halaman",
        "fields": [
            T("eyebrow", "Eyebrow"), T("title", "Judul"), T("title_accent", "Judul aksen (brass)"),
            TA("subtitle", "Subjudul"), T("response_note", "Catatan respons"),
            REP("items", "Info kontak", [T("label", "Label"), T("value", "Nilai"), T("href", "Tautan")]),
            TA("map_embed", "URL embed peta (Google Maps)"),
            T("stores_eyebrow", "Toko offline - eyebrow"), T("stores_title", "Toko offline - judul"),
            T("stores_accent", "Toko offline - aksen (brass)"), T("stores_after", "Toko offline - setelah aksen"),
            T("stores_link_label", "Toko offline - teks tautan"),
            T("form_success", "Pesan sukses form"),
        ],
        "default": {
            "stores_eyebrow": "Kunjungi Kami", "stores_title": "Toko", "stores_accent": "offline", "stores_after": "kami.",
            "stores_link_label": "Lihat semua lokasi", "form_success": "Tim kami akan membalas dalam 1x24 jam.",
            "eyebrow": "Kontak", "title": "Mari", "title_accent": "ngobrol.",
            "subtitle": "Tanya ketersediaan aroma, minta rekomendasi, atau berdiskusi soal pembelian dalam jumlah besar — tim kami siap membantu pada jam kerja.",
            "response_note": "Senin–Jumat 09.00–17.00 · Sabtu 09.00–14.00 WIB",
            "items": [
                {"label": "WhatsApp 1", "value": "+62 857-2000-0105", "href": "https://wa.me/6285720000105"},
                {"label": "WhatsApp 2", "value": "+62 857-2013-7777", "href": "https://wa.me/6285720137777"},
                {"label": "Email", "value": "cs@collectorparfum.com", "href": "mailto:cs@collectorparfum.com"},
                {"label": "LINE", "value": "@collectorparfum", "href": "https://line.me/R/ti/p/@collectorparfum"},
                {"label": "Instagram", "value": "@collectorparfum", "href": "https://instagram.com/collectorparfum"},
                {"label": "Toko Pusat", "value": "Jl. Paledang No. 58, Bandung", "href": "https://www.google.com/maps?q=Collector+Parfum+Jl.+Paledang+No.58+Bandung"},
            ],
            "map_embed": "https://www.google.com/maps?q=Collector+Parfum+Jl.+Paledang+No.58+Bandung&output=embed",
        },
    },
]

SECTION_MAP = {s["key"]: s for s in SECTIONS}


def default_content():
    """Map {key: default_data} untuk seed & fallback."""
    return {s["key"]: s["default"] for s in SECTIONS}


def schema():
    """Skema untuk form admin (tanpa data)."""
    return [{"key": s["key"], "label": s["label"], "group": s["group"], "fields": s["fields"], "default": s["default"]}
            for s in SECTIONS]
