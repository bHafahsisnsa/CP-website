// components/shared/VariantSelector.js — pemilih varian N-dimensi (controlled).
// Menampilkan satu baris chip per dimensi (options). Untuk dimensi ukuran, chip juga
// menampilkan harga varian relevan. Sold-out dicoret namun tetap bisa diklik (auto re-resolve).
import React from 'react';
import { formatIDR } from '../../lib/format';
import { isSizeDim, findVariant } from '../../lib/variants';

const slugv = (s) => String(s || '').toLowerCase().replace(/\s+/g, '-');

export const VariantSelector = ({ product, sel, onChange, testidPrefix = 'pdp' }) => {
  const options = product.options || [];
  const variants = product.variants || [];
  if (!options.length) return null;

  const otherMatch = (v, dim) =>
    options.every((o) => o.name === dim || (v.options || {})[o.name] === sel[o.name]);

  const pick = (dim, val) => {
    let next = { ...sel, [dim]: val };
    if (!findVariant(product, next)) {
      const cand = variants.filter((v) => (v.options || {})[dim] === val);
      const best = cand.find((v) => (v.stock || 0) > 0) || cand[0];
      if (best) next = { ...best.options };
    }
    onChange(next);
  };

  return (
    <div className="space-y-5">
      {options.map((o) => {
        const isSize = isSizeDim(o.name);
        return (
          <div key={o.name}>
            <div className="cp-mono uppercase text-[10px] tracking-[0.22em] text-black/60 mb-2">
              Pilih {o.name}
            </div>
            <div className="flex flex-wrap gap-2" data-testid={`${testidPrefix}-opt-${slugv(o.name)}`}>
              {o.values.map((val) => {
                const active = sel[o.name] === val;
                const relevant = variants.filter(
                  (v) => (v.options || {})[o.name] === val && otherMatch(v, o.name)
                );
                const soldOut = relevant.length > 0 && relevant.every((v) => (v.stock || 0) <= 0);
                const priceV = isSize ? (relevant.find((v) => (v.stock || 0) > 0) || relevant[0]) : null;
                return (
                  <button
                    key={val}
                    type="button"
                    onClick={() => pick(o.name, val)}
                    data-testid={`${testidPrefix}-optval-${slugv(o.name)}-${slugv(val)}`}
                    aria-pressed={active}
                    className={`cp-mono text-xs px-4 py-2.5 rounded-full border transition-colors ${
                      active
                        ? 'bg-[color:var(--cp-ink)] text-[color:var(--cp-paper)] border-[color:var(--cp-ink)]'
                        : soldOut
                        ? 'border-black/10 text-black/35 line-through hover:bg-black/5'
                        : 'border-black/15 text-black hover:bg-black/5'
                    }`}
                  >
                    {val}
                    {priceV ? ` • ${formatIDR(priceV.price).replace('Rp ', 'Rp')}` : ''}
                  </button>
                );
              })}
            </div>
          </div>
        );
      })}
    </div>
  );
};
