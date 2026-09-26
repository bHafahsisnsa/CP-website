// pages/StoreLocationsPage.js — halaman "Lokasi Toko" (/lokasi): peta cabang + Google Reviews.
import React from 'react';
import { MapPin, Phone, Clock, MessageCircle, Navigation, ExternalLink } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Skeleton } from '../components/ui/skeleton';
import { Reveal } from '../components/shared/Reveal';
import Seo from '../components/shared/Seo';
import { fetchStores, fetchStoreReviews } from '../services/stores';
import { StoreMap } from '../components/shared/StoreMap';
import { GoogleReviews, RatingSummary } from '../components/shared/GoogleReviews';
import { handleImageError, resolveMediaUrl } from '../lib/mediaUrl';
import { useContent } from '../store/ContentContext';

const LOC_DEFAULT = {
  eyebrow: 'Lokasi Toko', title: 'Kunjungi', title_accent: 'butik', title_after: 'kami.',
  reviews_eyebrow: 'Ulasan', reviews_title: 'Apa kata', reviews_accent: 'pelanggan', reviews_after: '.',
  seo_title: 'Lokasi Toko — Collector Parfum',
  seo_description: 'Kunjungi butik Collector Parfum di Bandung. Alamat, jam buka, dan petunjuk arah lengkap.',
};

const digits = (s) => String(s || '').replace(/[^0-9]/g, '');
const directionsUrl = (loc) =>
  loc.map_url || `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(loc.maps_query || loc.address)}`;

const LocationCard = ({ loc, config, index }) => {
  const wa = digits(loc.whatsapp || loc.phone);
  return (
    <div className="rounded-2xl border border-black/10 overflow-hidden bg-[color:var(--cp-paper-warm)]" data-testid="store-location-card">
      <div className="grid grid-cols-1 lg:grid-cols-2">
        <div className={`h-64 lg:h-full min-h-[260px] bg-[color:var(--cp-paper-fog)] ${index % 2 === 1 ? 'lg:order-2' : ''}`}>
          <StoreMap loc={loc} config={config} className="h-full w-full min-h-[260px]" />
        </div>
        <div className="p-6 sm:p-8 flex flex-col">
          {loc.photo ? (
            <div className="mb-4 overflow-hidden rounded-xl border border-black/10 bg-[color:var(--cp-paper-fog)]">
              <img
                src={resolveMediaUrl(loc.photo)}
                alt={`Foto ${loc.name}`}
                loading="lazy"
                onError={handleImageError}
                className="h-40 w-full object-cover"
                data-testid="store-location-photo"
              />
            </div>
          ) : null}
          <div className="cp-mono uppercase text-[10px] tracking-[0.22em] text-[color:var(--cp-brass)]">Cabang {index + 1}</div>
          <h3 className="cp-headline text-2xl sm:text-3xl mt-1 leading-tight">{loc.name}</h3>
          <div className="mt-5 space-y-3 text-sm">
            <div className="flex items-start gap-3">
              <MapPin className="h-4 w-4 text-[color:var(--cp-brass)] mt-0.5 flex-shrink-0" />
              <span className="text-black/75">{loc.address}</span>
            </div>
            {loc.hours ? (
              <div className="flex items-start gap-3">
                <Clock className="h-4 w-4 text-[color:var(--cp-brass)] mt-0.5 flex-shrink-0" />
                <span className="text-black/75">{loc.hours}</span>
              </div>
            ) : null}
            {loc.phone ? (
              <div className="flex items-start gap-3">
                <Phone className="h-4 w-4 text-[color:var(--cp-brass)] mt-0.5 flex-shrink-0" />
                <a href={`tel:${digits(loc.phone)}`} className="text-black/75 cp-hover-underline">{loc.phone}</a>
              </div>
            ) : null}
          </div>
          <div className="mt-6 flex flex-wrap gap-2">
            <a href={directionsUrl(loc)} target="_blank" rel="noopener noreferrer" data-testid="store-directions-button">
              <Button className="rounded-full h-10 px-5 bg-[color:var(--cp-ink)] text-[color:var(--cp-paper)] hover:bg-black gap-2">
                <Navigation className="h-4 w-4" /> Petunjuk Arah
              </Button>
            </a>
            {wa ? (
              <a href={`https://wa.me/${wa}`} target="_blank" rel="noopener noreferrer">
                <Button variant="outline" className="rounded-full h-10 px-5 border-black/20 gap-2">
                  <MessageCircle className="h-4 w-4" /> WhatsApp
                </Button>
              </a>
            ) : null}
            <a href={directionsUrl(loc)} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1 cp-mono uppercase text-[10px] tracking-[0.2em] text-black/55 hover:text-black self-center px-1">
              Lihat di Google Maps <ExternalLink className="h-3 w-3" />
            </a>
          </div>
        </div>
      </div>
    </div>
  );
};

export default function StoreLocationsPage() {
  const [data, setData] = React.useState({ locations: [], config: {} });
  const [reviews, setReviews] = React.useState({ source: 'manual', summary: { avg: 0, count: 0 }, reviews: [] });
  const [loading, setLoading] = React.useState(true);
  const cms = useContent('locations_page', LOC_DEFAULT);

  React.useEffect(() => {
    let cancelled = false;
    setLoading(true);
    Promise.all([fetchStores(), fetchStoreReviews()])
      .then(([s, r]) => { if (!cancelled) { setData(s); setReviews(r); } })
      .catch(() => {})
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, []);

  const { locations, config } = data;

  return (
    <div className="cp-container cp-section" data-testid="store-locations-page">
      <Seo title={cms.seo_title} description={cms.seo_description} />

      <div className="max-w-3xl">
        <div className="cp-eyebrow">{cms.eyebrow}</div>
        <Reveal>
          <h1 className="cp-headline text-4xl sm:text-6xl mt-2 leading-none">
            {cms.title} <em className="not-italic italic text-[color:var(--cp-brass)]">{cms.title_accent}</em> {cms.title_after}
          </h1>
        </Reveal>
        {config.intro ? <p className="mt-4 text-sm sm:text-base text-black/70">{config.intro}</p> : null}
        <div className="mt-6">
          <RatingSummary summary={reviews.summary} source={reviews.source} />
        </div>
      </div>

      {loading ? (
        <div className="mt-10 space-y-6">
          {[0, 1].map((i) => <Skeleton key={i} className="h-72 w-full rounded-2xl" />)}
        </div>
      ) : locations.length === 0 ? (
        <div className="mt-16 text-center py-16 border border-dashed border-black/15 rounded-2xl" data-testid="store-locations-empty">
          <MapPin className="h-8 w-8 mx-auto text-black/30" />
          <div className="cp-headline text-2xl mt-3">Belum ada lokasi toko</div>
          <div className="text-sm text-black/60 mt-1">Lokasi akan ditampilkan di sini setelah dikonfigurasi admin.</div>
        </div>
      ) : (
        <div className="mt-10 space-y-6" data-testid="store-locations-list">
          {locations.map((loc, i) => (
            <Reveal key={loc.id} delay={i * 0.05}>
              <LocationCard loc={loc} config={config} index={i} />
            </Reveal>
          ))}
        </div>
      )}

      {reviews.reviews.length > 0 && (
        <section className="mt-16">
          <div className="flex items-end justify-between flex-wrap gap-4 mb-8">
            <div>
              <div className="cp-eyebrow">{cms.reviews_eyebrow}</div>
              <Reveal>
                <h2 className="cp-headline text-3xl sm:text-5xl mt-2 leading-none">
                  {cms.reviews_title} <em className="not-italic italic text-[color:var(--cp-brass)]">{cms.reviews_accent}</em>{cms.reviews_after}
                </h2>
              </Reveal>
            </div>
            <RatingSummary summary={reviews.summary} source={reviews.source} />
          </div>
          <GoogleReviews reviews={reviews.reviews} source={reviews.source} />
        </section>
      )}
    </div>
  );
}
