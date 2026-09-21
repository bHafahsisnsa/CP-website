import React from 'react';
import { Link } from 'react-router-dom';
import { Instagram, Facebook, MessageCircle } from 'lucide-react';
import { MarqueeStrip } from '../shared/MarqueeStrip';
import { SITEMAP_URL } from '../../services/analytics';
import { useContent } from '../../store/ContentContext';
import { useStoreSettings } from '../../store/SettingsContext';
import { growthTestIds as G } from '../../constants/testIds/growth';

const digits = (s) => String(s || '').replace(/[^0-9]/g, '');

const FOOTER_DEFAULT = {
  tagline: 'Kurasi parfum original untuk momen yang membekas. Pengalaman belanja premium, checkout ala marketplace.',
  shop_title: 'Belanja',
  shop_links: [
    { label: 'Semua Parfum', to: '/shop' },
    { label: 'Citrus', to: '/shop?cat=citrus' },
    { label: 'Floral', to: '/shop?cat=floral' },
    { label: 'Woody', to: '/shop?cat=woody' },
    { label: 'Amber & Oud', to: '/shop?cat=amber' },
  ],
  help_title: 'Bantuan',
  help_links: [
    { label: 'Kontak', to: '/kontak' },
    { label: 'Tentang Kami', to: '/tentang' },
    { label: 'Voucher', to: '/voucher' },
  ],
  newsletter_title: 'Newsletter',
  newsletter_desc: 'Aroma baru, promo, dan cerita di email Anda.',
  payment_badges: ['BCA', 'BNI', 'Mandiri', 'OVO', 'GoPay', 'DANA', 'COD'],
};

export const SiteFooter = () => {
  const { settings } = useStoreSettings();
  const c = useContent('footer', FOOTER_DEFAULT);

  const socials = [
    { icon: Instagram, url: settings?.social_instagram },
    { icon: Facebook, url: settings?.social_facebook },
  ].filter((s) => s.url);
  const wa = digits(settings?.whatsapp_number);
  const shopLinks = Array.isArray(c.shop_links) && c.shop_links.length ? c.shop_links : FOOTER_DEFAULT.shop_links;
  const helpLinks = Array.isArray(c.help_links) && c.help_links.length ? c.help_links : FOOTER_DEFAULT.help_links;
  const badges = Array.isArray(c.payment_badges) && c.payment_badges.length ? c.payment_badges : FOOTER_DEFAULT.payment_badges;

  return (
    <footer className="mt-8 bg-[color:var(--cp-ink)] text-[color:var(--cp-paper)]">
      <MarqueeStrip
        dark
        speed="default"
        className="border-b border-white/10"
        items={[
          'Aroma yang Membekas',
          'Kurasi Editorial',
          'Pengiriman Nasional',
          'Original & Bersegel',
          'Kemasan Rapi',
        ]}
      />
      <div className="cp-container-wide py-16 grid grid-cols-2 lg:grid-cols-5 gap-10">
        <div className="col-span-2">
          <div className="flex items-baseline gap-2">
            <span className="cp-logo text-4xl">Collector</span>
            <span className="cp-logo text-4xl">Parfum</span>
          </div>
          <p className="mt-4 text-sm text-white/70 max-w-sm">
            {c.tagline}
          </p>
          <div className="mt-6 flex items-center gap-3">
            {socials.map(({ icon: Icon, url }, i) => (
              <a
                key={i}
                href={url}
                target="_blank"
                rel="noopener noreferrer"
                aria-label="Sosial media"
                className="inline-flex h-9 w-9 items-center justify-center rounded-full border border-white/20 hover:bg-white/10 transition-colors"
              >
                <Icon className="h-4 w-4" />
              </a>
            ))}
            {wa ? (
              <a
                href={`https://wa.me/${wa}`}
                target="_blank"
                rel="noopener noreferrer"
                aria-label="WhatsApp"
                className="inline-flex h-9 w-9 items-center justify-center rounded-full border border-white/20 hover:bg-white/10 transition-colors"
              >
                <MessageCircle className="h-4 w-4" />
              </a>
            ) : null}
          </div>
        </div>

        <div>
          <h4 className="cp-mono uppercase text-[11px] tracking-[0.22em] text-white/60 mb-4">{c.shop_title}</h4>
          <ul className="space-y-2 text-sm">
            {shopLinks.map((l, i) => (
              <li key={i}><Link to={l.to || '/shop'} className="cp-hover-underline text-white/85">{l.label}</Link></li>
            ))}
          </ul>
        </div>

        <div>
          <h4 className="cp-mono uppercase text-[11px] tracking-[0.22em] text-white/60 mb-4">{c.help_title}</h4>
          <ul className="space-y-2 text-sm">
            {helpLinks.map((l, i) => (
              <li key={i}><Link to={l.to || '/'} className="cp-hover-underline text-white/85">{l.label}</Link></li>
            ))}
            <li>
              <a
                href={SITEMAP_URL}
                target="_blank"
                rel="noopener noreferrer"
                data-testid={G.footerSitemap}
                className="cp-hover-underline text-white/85"
              >
                Peta Situs
              </a>
            </li>
          </ul>
        </div>

        <div>
          <h4 className="cp-mono uppercase text-[11px] tracking-[0.22em] text-white/60 mb-4">{c.newsletter_title}</h4>
          <p className="text-sm text-white/70 mb-3">{c.newsletter_desc}</p>
          <form
            onSubmit={(e) => e.preventDefault()}
            className="flex items-center gap-2 border border-white/20 rounded-full pl-4 pr-1 py-1"
          >
            <input
              type="email"
              placeholder="email@anda.com"
              data-testid="footer-newsletter-input"
              className="bg-transparent placeholder:text-white/40 text-sm outline-none flex-1 py-2"
            />
            <button
              type="submit"
              className="bg-[color:var(--cp-paper)] text-[color:var(--cp-ink)] rounded-full text-xs cp-mono uppercase tracking-[0.2em] px-4 py-2"
              data-testid="footer-newsletter-submit"
            >
              Daftar
            </button>
          </form>
        </div>
      </div>
      <div className="border-t border-white/10">
        <div className="cp-container-wide py-6 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs text-white/60">
          <div className="cp-mono uppercase tracking-[0.22em]">© {new Date().getFullYear()} Collector Parfum</div>
          <div className="flex items-center gap-4 flex-wrap">
            {badges.map((b, i) => <span key={i}>{b}</span>)}
          </div>
        </div>
      </div>
    </footer>
  );
};
