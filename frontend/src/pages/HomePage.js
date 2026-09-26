import React from 'react';
import { useCatalog } from '../store/CatalogContext';
import { useContent } from '../store/ContentContext';
import { fetchReviews } from '../services/catalog';
import Seo from '../components/shared/Seo';
import { HeroSection } from '../components/home/HeroSection';
import { MarqueeStrip } from '../components/shared/MarqueeStrip';
import { ShopByOccasion, ShopByCharacter } from '../components/home/FacetSection';
import { BestSellersSection } from '../components/home/BestSellersSection';
import { MediaGridSection } from '../components/home/MediaGridSection';
import { BigScrollingWord } from '../components/home/BigScrollingWord';
import { TestimonialsSection } from '../components/home/TestimonialsSection';
import { FAQSection } from '../components/home/FAQSection';
import { VideoOverlaySection } from '../components/home/VideoOverlaySection';
import { FeaturedCollection } from '../components/home/FeaturedCollection';
import { TrustStrip } from '../components/layout/AnnouncementBar';
import { StoryStrip } from '../components/home/StripSection';
import { GallerySection } from '../components/home/GallerySection';

const DEFAULT_ORDER = [
  'hero', 'marquee_words', 'story_strip', 'occasion_section', 'character_section', 'trending',
  'media_editorial', 'trust', 'featured', 'big_word', 'new_arrivals', 'gallery', 'video', 'testimonials', 'faq',
].map((key) => ({ key, visible: true }));

const STRIP_ITEMS = [
  'ELEGAN',
  'BERKARAKTER',
  'ORIGINAL',
  'MEWAH',
  'MEMBEKAS',
  'SELAMANYA',
];

export default function HomePage() {
  const { products, occasions, characters, loading } = useCatalog();
  const [reviews, setReviews] = React.useState([]);

  React.useEffect(() => {
    let active = true;
    fetchReviews()
      .then((r) => { if (active) setReviews(r); })
      .catch(() => { if (active) setReviews([]); });
    return () => { active = false; };
  }, []);

  const bestSellers = products.filter((p) => p.bestSeller);
  const newArrivals = products.filter((p) => p.isNew);
  const allTrending = products.slice(0, 8);

  // CMS (E9) — konten editorial dari admin (fallback = default inline).
  const marquee = useContent('marquee_words', { items: STRIP_ITEMS });
  const trending = useContent('trending', { eyebrow: 'Trending', title: 'Sedang Trending' });
  const newArr = useContent('new_arrivals', { eyebrow: 'New Arrivals', title: 'Baru Datang' });
  const bigWord = useContent('big_word', {
    words: ['Aroma', 'yang', 'membekas'],
    caption: 'Kami percaya parfum bukan sekadar pelengkap gaya — ia adalah tanda tangan yang tersisa saat Anda meninggalkan ruangan.',
  });
  const seo = useContent('seo', {
    home_title: 'Collector Parfum — Aroma yang Membekas',
    home_description: 'Distributor parfum refill di Bandung sejak 1970. Biang impor pilihan, 30–100 ml, kirim ke seluruh Indonesia.',
    og_image: '',
  });
  const layout = useContent('home_layout', { sections: [] });

  // Peta section -> elemen; urutan & visibilitas dari CMS `home_layout`.
  const SECTIONS = {
    hero: <HeroSection />,
    marquee_words: (
      <MarqueeStrip items={marquee.items} speed="default" className="border-y border-black/10 bg-[color:var(--cp-paper-fog)]" />
    ),
    story_strip: <StoryStrip />,
    occasion_section: <ShopByOccasion items={occasions} loading={loading} />,
    character_section: <ShopByCharacter items={characters} loading={loading} />,
    trending: (
      <BestSellersSection title={trending.title} eyebrow={trending.eyebrow} products={allTrending} loading={loading} linkTo="/shop" />
    ),
    media_editorial: <MediaGridSection />,
    trust: <TrustStrip />,
    featured: <FeaturedCollection />,
    big_word: <BigScrollingWord words={bigWord.words} caption={bigWord.caption} />,
    new_arrivals: (
      <BestSellersSection
        title={newArr.title}
        eyebrow={newArr.eyebrow}
        products={newArrivals.length > 0 ? newArrivals : bestSellers}
        loading={loading}
        linkTo="/shop?isNew=1"
        testId="home-new-arrivals"
        speed={0.55}
      />
    ),
    gallery: <GallerySection />,
    video: <VideoOverlaySection />,
    testimonials: <TestimonialsSection reviews={reviews} />,
    faq: <FAQSection />,
  };
  const rows = Array.isArray(layout.sections) && layout.sections.length ? layout.sections : DEFAULT_ORDER;
  const order = [...new Set(rows.filter((r) => r && r.visible !== false && SECTIONS[r.key]).map((r) => r.key))];

  return (
    <div data-testid="home-page">
      <Seo
        title={seo.home_title}
        description={seo.home_description}
        image={seo.og_image || undefined}
        jsonLd={{
          '@context': 'https://schema.org',
          '@type': 'WebSite',
          name: 'Collector Parfum',
          url: typeof window !== 'undefined' ? window.location.origin : '',
        }}
      />
      {order.map((key) => <React.Fragment key={key}>{SECTIONS[key]}</React.Fragment>)}
    </div>
  );
}
