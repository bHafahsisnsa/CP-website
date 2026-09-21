// components/shared/StoreMap.js — peta lokasi toko.
// Mode 'embed' (default, TANPA API key) via iframe Google Maps.
// Mode 'js' (disiapkan) via Maps JavaScript API bila admin mengisi API key di Pengaturan;
// gagal load/geocode -> fallback otomatis ke embed. Loader script singleton (anti duplikasi).
import React from 'react';

let _mapsPromise = null;
const loadMaps = (key) => {
  if (window.google && window.google.maps) return Promise.resolve(window.google.maps);
  if (_mapsPromise) return _mapsPromise;
  _mapsPromise = new Promise((resolve, reject) => {
    const s = document.createElement('script');
    s.src = `https://maps.googleapis.com/maps/api/js?key=${encodeURIComponent(key)}`;
    s.async = true;
    s.defer = true;
    s.onload = () => resolve(window.google.maps);
    s.onerror = () => reject(new Error('maps-load-failed'));
    document.head.appendChild(s);
  });
  return _mapsPromise;
};

const embedSrc = (loc) => {
  if (loc && loc.embed_url) return loc.embed_url;
  const q = (loc && (loc.maps_query || loc.address)) || 'Bandung';
  return `https://www.google.com/maps?q=${encodeURIComponent(q)}&output=embed`;
};

const EmbedMap = ({ loc, className }) => (
  <iframe
    title={`Peta ${loc?.name || 'toko'}`}
    src={embedSrc(loc)}
    className={className}
    width="100%"
    height="100%"
    style={{ border: 0 }}
    allowFullScreen
    loading="lazy"
    referrerPolicy="no-referrer-when-downgrade"
    data-testid="store-map-embed"
  />
);

const JsMap = ({ loc, apiKey, className }) => {
  const ref = React.useRef(null);
  const [failed, setFailed] = React.useState(false);
  React.useEffect(() => {
    let cancelled = false;
    loadMaps(apiKey)
      .then((maps) => {
        if (cancelled || !ref.current) return;
        const draw = (center) => {
          const map = new maps.Map(ref.current, {
            center, zoom: 16, mapTypeControl: false, streetViewControl: false, fullscreenControl: true,
          });
          new maps.Marker({ position: center, map, title: loc.name });
        };
        const lat = Number(loc.lat);
        const lng = Number(loc.lng);
        if (Number.isFinite(lat) && Number.isFinite(lng)) {
          draw({ lat, lng });
        } else {
          const geocoder = new maps.Geocoder();
          geocoder.geocode({ address: loc.maps_query || loc.address }, (results, status) => {
            if (!cancelled && status === 'OK' && results[0]) draw(results[0].geometry.location.toJSON());
            else if (!cancelled) setFailed(true);
          });
        }
      })
      .catch(() => { if (!cancelled) setFailed(true); });
    return () => { cancelled = true; };
  }, [loc, apiKey]);
  if (failed) return <EmbedMap loc={loc} className={className} />;
  return <div ref={ref} className={className} data-testid="store-map-js" />;
};

export const StoreMap = ({ loc, config, className = 'h-full w-full' }) => {
  const useJs = config && config.maps_mode === 'js' && config.maps_api_key;
  if (useJs) return <JsMap loc={loc} apiKey={config.maps_api_key} className={className} />;
  return <EmbedMap loc={loc} className={className} />;
};

export default StoreMap;
