// components/shop/ShopFilters.js — Panel filter katalog: RAMPING + COLLAPSIBLE.
//
// Catatan arsitektur (penting):
// Komponen ini SENGAJA berada di file sendiri, bukan sebagai fungsi lokal di dalam
// ShopPage. Versi lama mendefinisikan `const FiltersPanel = () => (...)` di dalam body
// ShopPage lalu memakainya sebagai <FiltersPanel />, sehingga setiap render menciptakan
// TIPE komponen baru -> React melakukan unmount/mount penuh pada Checkbox/Slider
// (kehilangan fokus, animasi ter-reset). Sekarang identitas komponen stabil sehingga
// state internal (section mana yang terbuka) aman disimpan di sini.
//
// UX: tiap section bisa dibuka/tutup (default: hanya Kategori & Harga terbuka), status
// buka/tutup diingat di localStorage, dan section yang punya filter aktif otomatis terbuka.
import React from 'react';
import { Check, ChevronDown, RotateCcw, SlidersHorizontal } from 'lucide-react';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '../ui/collapsible';
import { Slider } from '../ui/slider';
import { formatIDR } from '../../lib/format';

const OPEN_KEY = 'cp:shop-filter-sections:v1';

const DEFAULT_OPEN = {
  kategori: true,
  harga: true,
  occasion: false,
  character: false,
  konsentrasi: false,
  untuk: false,
  notes: false,
};

const readStoredOpen = () => {
  try {
    const raw = window.localStorage.getItem(OPEN_KEY);
    return raw ? { ...DEFAULT_OPEN, ...JSON.parse(raw) } : { ...DEFAULT_OPEN };
  } catch (e) {
    return { ...DEFAULT_OPEN };
  }
};

const CountBadge = ({ n }) =>
  n > 0 ? (
    <span className="cp-mono text-[9px] leading-none h-[15px] min-w-[15px] px-1 inline-flex items-center justify-center rounded-full bg-[color:var(--cp-ink)] text-[color:var(--cp-paper)]">
      {n}
    </span>
  ) : null;

const Section = ({ id, title, count, open, onOpenChange, children }) => (
  <Collapsible open={open} onOpenChange={onOpenChange}>
    <CollapsibleTrigger
      className="w-full flex items-center gap-2 py-[9px] text-left group"
      data-testid={`shop-filter-section-${id}`}
    >
      <span className="cp-mono uppercase text-[9.5px] tracking-[0.2em] text-black/60 group-hover:text-black/85 transition-colors">
        {title}
      </span>
      <CountBadge n={count} />
      <ChevronDown
        className={`ml-auto h-3.5 w-3.5 text-black/35 transition-transform duration-200 ${open ? 'rotate-180' : ''}`}
      />
    </CollapsibleTrigger>
    <CollapsibleContent className="cp-collapsible">
      <div className="pb-3">{children}</div>
    </CollapsibleContent>
  </Collapsible>
);

const Chip = ({ active, onClick, testId, children }) => (
  <button
    type="button"
    onClick={onClick}
    aria-pressed={active}
    data-testid={testId}
    className={`cp-mono uppercase text-[9px] leading-none tracking-[0.16em] px-2.5 py-[7px] rounded-full border transition-colors ${
      active
        ? 'bg-[color:var(--cp-ink)] text-[color:var(--cp-paper)] border-[color:var(--cp-ink)]'
        : 'border-black/12 text-black/65 hover:bg-black/5 hover:text-black/85'
    }`}
  >
    {children}
  </button>
);

const CheckRow = ({ active, onClick, testId, children }) => (
  <button
    type="button"
    onClick={onClick}
    aria-pressed={active}
    data-testid={testId}
    className="w-full flex items-center gap-2 py-[5px] text-left group"
  >
    <span
      className={`h-[15px] w-[15px] shrink-0 rounded-[4px] border flex items-center justify-center transition-colors ${
        active
          ? 'bg-[color:var(--cp-ink)] border-[color:var(--cp-ink)]'
          : 'border-black/25 group-hover:border-black/45'
      }`}
    >
      {active ? <Check className="h-2.5 w-2.5 text-[color:var(--cp-paper)]" strokeWidth={3} /> : null}
    </span>
    <span className={`text-[12.5px] leading-tight truncate ${active ? 'text-black/90 font-medium' : 'text-black/70'}`}>
      {children}
    </span>
  </button>
);

export const ShopFilters = ({
  variant = 'sidebar',
  categories = [],
  occasions = [],
  characters = [],
  concentrationOptions = [],
  genderOptions = [],
  noteOptions = [],
  cats = [],
  occ = [],
  chars = [],
  concs = [],
  genders = [],
  notes = [],
  price = [0, 0],
  priceMax = 0,
  onToggle,
  onPriceChange,
  onReset,
  onApply,
}) => {
  const counts = {
    kategori: cats.length,
    harga: price[0] > 0 || price[1] < priceMax ? 1 : 0,
    occasion: occ.length,
    character: chars.length,
    konsentrasi: concs.length,
    untuk: genders.length,
    notes: notes.length,
  };
  const activeTotal = Object.values(counts).reduce((a, b) => a + b, 0);

  // Initializer hanya jalan sekali: section dengan filter aktif (mis. dari URL) dibuka.
  const [open, setOpen] = React.useState(() => {
    const base = readStoredOpen();
    Object.keys(counts).forEach((k) => {
      if (counts[k] > 0) base[k] = true;
    });
    return base;
  });

  const setSection = (id) => (value) => {
    setOpen((prev) => {
      const next = { ...prev, [id]: value };
      try {
        window.localStorage.setItem(OPEN_KEY, JSON.stringify(next));
      } catch (e) {
        /* localStorage bisa diblokir — abaikan */
      }
      return next;
    });
  };

  const header = (
    <div className="flex items-center gap-2 pb-1.5">
      <SlidersHorizontal className="h-3.5 w-3.5 text-black/45" />
      <span className="cp-mono uppercase text-[9.5px] tracking-[0.22em] text-black/70">Filter</span>
      <CountBadge n={activeTotal} />
      <button
        type="button"
        onClick={onReset}
        data-testid="shop-clear-filters"
        className="ml-auto inline-flex items-center gap-1 cp-mono uppercase text-[9px] tracking-[0.18em] text-black/45 hover:text-black/85 transition-colors"
      >
        <RotateCcw className="h-3 w-3" /> Reset
      </button>
    </div>
  );

  const body = (
    <div className="divide-y divide-black/10">
      <Section
        id="kategori"
        title="Kategori Aroma"
        count={counts.kategori}
        open={open.kategori}
        onOpenChange={setSection('kategori')}
      >
        <div className="space-y-0.5">
          {categories.map((c) => (
            <CheckRow
              key={c.slug}
              active={cats.includes(c.slug)}
              onClick={() => onToggle('cat', c.slug)}
              testId={`shop-filter-cat-${c.slug}`}
            >
              {c.name}
            </CheckRow>
          ))}
        </div>
      </Section>

      <Section
        id="harga"
        title="Kisaran Harga"
        count={counts.harga}
        open={open.harga}
        onOpenChange={setSection('harga')}
      >
        <div className="px-0.5 pt-1">
          <Slider
            min={0}
            max={priceMax}
            step={50000}
            value={price}
            onValueChange={onPriceChange}
            data-testid="shop-filter-price-range-slider"
          />
          <div className="mt-2.5 flex items-center justify-between cp-mono text-[10px] text-black/60">
            <span>{formatIDR(price[0])}</span>
            <span>{formatIDR(price[1])}</span>
          </div>
        </div>
      </Section>

      <Section
        id="occasion"
        title="Occasion"
        count={counts.occasion}
        open={open.occasion}
        onOpenChange={setSection('occasion')}
      >
        <div className="flex flex-wrap gap-1.5">
          {occasions.map((o) => (
            <Chip
              key={o.slug}
              active={occ.includes(o.slug)}
              onClick={() => onToggle('occasion', o.slug)}
              testId={`shop-filter-occasion-${o.slug}`}
            >
              {o.name}
            </Chip>
          ))}
        </div>
      </Section>

      <Section
        id="character"
        title="Character"
        count={counts.character}
        open={open.character}
        onOpenChange={setSection('character')}
      >
        <div className="flex flex-wrap gap-1.5">
          {characters.map((ch) => (
            <Chip
              key={ch.slug}
              active={chars.includes(ch.slug)}
              onClick={() => onToggle('character', ch.slug)}
              testId={`shop-filter-character-${ch.slug}`}
            >
              {ch.name}
            </Chip>
          ))}
        </div>
      </Section>

      <Section
        id="konsentrasi"
        title="Konsentrasi"
        count={counts.konsentrasi}
        open={open.konsentrasi}
        onOpenChange={setSection('konsentrasi')}
      >
        <div className="flex flex-wrap gap-1.5">
          {concentrationOptions.map((c) => (
            <Chip
              key={c}
              active={concs.includes(c)}
              onClick={() => onToggle('concentration', c)}
              testId={`shop-filter-concentration-${c.toLowerCase()}`}
            >
              {c}
            </Chip>
          ))}
        </div>
      </Section>

      <Section id="untuk" title="Untuk" count={counts.untuk} open={open.untuk} onOpenChange={setSection('untuk')}>
        <div className="flex flex-wrap gap-1.5">
          {genderOptions.map((g) => (
            <Chip
              key={g}
              active={genders.includes(g)}
              onClick={() => onToggle('gender', g)}
              testId={`shop-filter-gender-${g.toLowerCase()}`}
            >
              {g}
            </Chip>
          ))}
        </div>
      </Section>

      <Section id="notes" title="Notes" count={counts.notes} open={open.notes} onOpenChange={setSection('notes')}>
        <div className="flex flex-wrap gap-1.5">
          {noteOptions.map((n) => (
            <Chip
              key={n}
              active={notes.includes(n)}
              onClick={() => onToggle('note', n)}
              testId={`shop-filter-note-${n.toLowerCase()}`}
            >
              {n}
            </Chip>
          ))}
        </div>
      </Section>
    </div>
  );

  if (variant === 'sheet') {
    // Di dalam Sheet, judul "Filter" sudah ada di SheetHeader -> jangan duplikat header.
    return (
      <div data-testid="shop-filters-sheet-panel">
        {body}
        <div className="mt-4 grid grid-cols-2 gap-2">
          <button
            type="button"
            onClick={onReset}
            className="h-11 rounded-full border border-black/15 cp-mono uppercase text-[10px] tracking-[0.2em] hover:bg-black/5"
          >
            Reset
          </button>
          <button
            type="button"
            onClick={onApply}
            data-testid="shop-apply-filters"
            className="h-11 rounded-full cp-btn-gold cp-mono uppercase text-[10px] tracking-[0.2em]"
          >
            Terapkan
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="cp-glass rounded-[18px] px-3.5 py-2.5" data-testid="shop-filters-panel">
      {header}
      {body}
    </div>
  );
};
