// components/admin/ProductPreview.js — live preview PDP-akurat (token & komponen storefront).
// Dipakai editor produk agar admin melihat tampilan sebelum simpan (BR-9, no publish drift).
import React, { useState } from 'react';
import { bottleImage } from '../../lib/bottleArt';
import { formatIDR } from '../../lib/format';
import { Badge } from '../ui/badge';
import { adminTestIds as T } from './../../constants/testIds/admin';
import { handleImageError, resolveMediaUrl } from '../../lib/mediaUrl';

const Chips = ({ items = [], tone }) => (
  <div className="flex flex-wrap gap-1.5">
    {items.filter(Boolean).map((n, i) => (
      <span key={i} className={`rounded-full border px-2.5 py-1 text-[11px] tracking-[0.08em] ${tone}`}>{n}</span>
    ))}
  </div>
);

export const ProductPreview = ({ product }) => {
  const {
    name = 'Nama Produk', brand = 'Collector', concentration = 'EDP', gender = 'Unisex',
    category = 'amber', volumes = [], notes = {}, images = [], description = '',
    compare_at_price: compareAt,
  } = product || {};
  const [selType, setSelType] = useState('');
  const [selMl, setSelMl] = useState(null);
  const vols = volumes.length ? volumes : [{ type: '', ml: 50, price: 0, stock: 0 }];
  const typeOptions = [...new Set(vols.map((v) => v.type || ''))];
  const hasTypes = typeOptions.some((t) => t !== '');
  const activeType = typeOptions.includes(selType) ? selType : (typeOptions[0] || '');
  const sizesForType = vols.filter((v) => (v.type || '') === activeType);
  const active = sizesForType.find((v) => v.ml === selMl) || sizesForType[0] || vols[0];
  const price = active?.price || 0;
  const cmp = active?.compare_at_price || (compareAt && active && compareAt > price ? compareAt : null);
  const img = images.find(Boolean) || bottleImage({ name, concentration, category });

  const pickType = (t) => {
    setSelType(t);
    const sizes = vols.filter((v) => (v.type || '') === t);
    if (!sizes.find((s) => s.ml === selMl)) setSelMl((sizes[0] || {}).ml ?? null);
  };

  return (
    <div
      className="rounded-2xl border border-border bg-[#FFFCF6] text-[#141414] overflow-hidden"
      data-testid={T.previewPane}
    >
      <div className="px-4 py-2 border-b border-black/10 text-[10px] uppercase tracking-[0.2em] text-black/50">
        Pratinjau Storefront
      </div>
      <div className="grid sm:grid-cols-2 gap-0">
        <div className="bg-[#EEE7DC] aspect-square">
          <img src={resolveMediaUrl(img)} alt={name} onError={handleImageError} className="h-full w-full object-cover" />
        </div>
        <div className="p-5 space-y-3">
          <div className="text-[11px] uppercase tracking-[0.18em] text-black/50">{brand}</div>
          <h3 className="font-[\'DM_Serif_Display\',serif] text-2xl leading-tight">{name}</h3>
          <div className="flex items-center gap-2">
            <Badge variant="outline" className="font-[\'Azeret_Mono\',monospace] text-[11px] border-black/20">{concentration}</Badge>
            <Badge variant="outline" className="text-[11px] border-black/20">{gender}</Badge>
          </div>
          <div className="flex items-end gap-2">
            <span className="font-[\'Azeret_Mono\',monospace] text-xl font-semibold">{formatIDR(price)}</span>
            {cmp ? <span className="text-sm text-black/40 line-through">{formatIDR(cmp)}</span> : null}
          </div>
          {hasTypes ? (
            <div className="flex flex-wrap gap-1.5">
              {typeOptions.map((t, i) => (
                <button
                  key={i}
                  type="button"
                  onClick={() => pickType(t)}
                  className={`rounded-full border px-3 py-1 text-xs font-[\'Azeret_Mono\',monospace] ${activeType === t ? 'border-black bg-black text-white' : 'border-black/20'}`}
                >
                  {t || 'Reguler'}
                </button>
              ))}
            </div>
          ) : null}
          <div className="flex flex-wrap gap-1.5">
            {sizesForType.map((v, i) => (
              <button
                key={i}
                type="button"
                onClick={() => setSelMl(v.ml)}
                className={`rounded-full border px-3 py-1 text-xs font-[\'Azeret_Mono\',monospace] ${active && active.ml === v.ml ? 'border-black bg-black text-white' : 'border-black/20'}`}
              >
                {v.ml}ml
              </button>
            ))}
          </div>
          {notes?.top?.length || notes?.heart?.length || notes?.base?.length ? (
            <div className="space-y-2 pt-1">
              {notes?.top?.length ? (<div><div className="text-[10px] uppercase tracking-[0.16em] text-black/45 mb-1">Top</div><Chips items={notes.top} tone="border-black/15 bg-white/70" /></div>) : null}
              {notes?.heart?.length ? (<div><div className="text-[10px] uppercase tracking-[0.16em] text-black/45 mb-1">Heart</div><Chips items={notes.heart} tone="border-black/15 bg-white/70" /></div>) : null}
              {notes?.base?.length ? (<div><div className="text-[10px] uppercase tracking-[0.16em] text-black/45 mb-1">Base</div><Chips items={notes.base} tone="border-black/15 bg-white/70" /></div>) : null}
            </div>
          ) : null}
          {description ? <p className="text-sm text-black/70 leading-relaxed line-clamp-4">{description}</p> : null}
        </div>
      </div>
    </div>
  );
};
