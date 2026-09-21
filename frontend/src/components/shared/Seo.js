// components/shared/Seo.js — SEO head manager tanpa dependency (Epic E7).
// Mengatur <title>, meta description, canonical, Open Graph/Twitter, dan JSON-LD
// secara imperatif via document.head (kompatibel React 19, tanpa react-helmet).
import { useEffect } from 'react';

function upsert(selector, create, attrs) {
  let el = document.head.querySelector(selector);
  if (!el) {
    el = create();
    document.head.appendChild(el);
  }
  Object.entries(attrs).forEach(([k, v]) => el.setAttribute(k, v));
  return el;
}

function setMeta(name, content, prop = false) {
  if (!content) return;
  const attr = prop ? 'property' : 'name';
  upsert(
    `meta[${attr}="${name}"]`,
    () => {
      const m = document.createElement('meta');
      m.setAttribute(attr, name);
      return m;
    },
    { content }
  );
}

export default function Seo({ title, description, canonical, image, type = 'website', jsonLd }) {
  useEffect(() => {
    if (title) document.title = title;
    setMeta('description', description);
    setMeta('og:title', title, true);
    setMeta('og:description', description, true);
    setMeta('og:type', type, true);
    if (image) setMeta('og:image', image, true);
    setMeta('twitter:card', image ? 'summary_large_image' : 'summary');

    const canon = canonical || (typeof window !== 'undefined' ? window.location.href : '');
    if (canon) {
      upsert(
        'link[rel="canonical"]',
        () => {
          const l = document.createElement('link');
          l.setAttribute('rel', 'canonical');
          return l;
        },
        { href: canon }
      );
    }

    const SID = 'cp-jsonld';
    let s = document.getElementById(SID);
    if (jsonLd) {
      if (!s) {
        s = document.createElement('script');
        s.type = 'application/ld+json';
        s.id = SID;
        document.head.appendChild(s);
      }
      s.textContent = JSON.stringify(jsonLd);
    } else if (s) {
      s.remove();
    }
  }, [title, description, canonical, image, type, jsonLd]);

  return null;
}
