import React from 'react';
import { Truck, RotateCcw, ShieldCheck } from 'lucide-react';
import { MarqueeStrip } from '../shared/MarqueeStrip';
import { useContent } from '../../store/ContentContext';

const ANNOUNCE_DEFAULT = {
  items: [
    'Gratis Ongkir Min. Belanja Rp 350.000',
    'COD Tersedia di Seluruh Kota',
    'Parfum Original & Bersegel',
    'Cicilan 0% via E-Wallet',
    'Kartu Autentikasi di Setiap Paket',
  ],
};

export const AnnouncementBar = () => {
  const c = useContent('announcement', ANNOUNCE_DEFAULT);
  const items = (Array.isArray(c.items) && c.items.length ? c.items : ANNOUNCE_DEFAULT.items);
  return (
    <div
      data-testid="announcement-bar"
      className="bg-[color:var(--cp-ink)] text-[color:var(--cp-paper)] cp-mono uppercase text-[10px] sm:text-[11px] tracking-[0.2em]"
      style={{ height: 'var(--announcement-h)' }}
    >
      <div className="h-full flex items-center">
        <MarqueeStrip className="w-full" dark speed="default" items={items} />
      </div>
    </div>
  );
};

const TRUST_DEFAULT = {
  items: [
    { title: 'Gratis Ongkir', desc: 'Min. Rp 350.000, ke seluruh Indonesia.' },
    { title: '100% Original', desc: 'Bersegel & kartu autentikasi.' },
    { title: 'Retur 3 Hari', desc: 'Untuk produk yang belum dibuka.' },
  ],
};
const TRUST_ICONS = [Truck, ShieldCheck, RotateCcw];

export const TrustStrip = () => {
  const c = useContent('trust', TRUST_DEFAULT);
  const items = (Array.isArray(c.items) && c.items.length ? c.items : TRUST_DEFAULT.items);
  return (
    <div className="grid grid-cols-1 sm:grid-cols-3 border-y border-black/10">
      {items.map(({ title, desc }, i) => {
        const Icon = TRUST_ICONS[i % TRUST_ICONS.length];
        return (
          <div key={i} className="flex items-center gap-4 px-5 sm:px-8 py-5 border-b sm:border-b-0 sm:border-r border-black/10 last:border-r-0">
            <Icon className="h-5 w-5 text-[color:var(--cp-brass)]" />
            <div>
              <div className="cp-mono uppercase text-[11px] tracking-[0.22em]">{title}</div>
              <div className="text-xs text-black/60">{desc}</div>
            </div>
          </div>
        );
      })}
    </div>
  );
};
