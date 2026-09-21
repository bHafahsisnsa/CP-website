// components/admin/import/ImportStructurePanel.js — pratinjau STRUKTUR VARIAN hasil grouping.
// Menampilkan hasil /validate (products[]) sebagai matriks N-dimensi (1–4 dimensi):
// nama dimensi berurutan + nilai unik, jumlah varian, rentang harga, total stok,
// serta tabel varian dengan satu kolom per dimensi. Tujuannya: admin bisa MEMASTIKAN
// file 4 dimensi terbaca benar SEBELUM commit.
import React, { useState } from 'react';
import { Layers, ChevronDown, ChevronRight, AlertTriangle } from 'lucide-react';
import { Card, CardContent } from '../../ui/card';
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from '../../ui/table';
import { Badge } from '../../ui/badge';
import { ACCENT, ACCENT_SOFT } from '../adminUi';
import { adminTestIds as T } from '../../../constants/testIds/admin';

const rupiah = (n) => `Rp ${Number(n || 0).toLocaleString('id-ID')}`;

const priceRange = (variants) => {
  const prices = (variants || []).map((v) => Number(v.price) || 0).filter((p) => p > 0);
  if (prices.length === 0) return '—';
  const lo = Math.min(...prices);
  const hi = Math.max(...prices);
  return lo === hi ? rupiah(lo) : `${rupiah(lo)} – ${rupiah(hi)}`;
};

const totalStock = (variants) =>
  (variants || []).reduce((s, v) => s + (Number(v.stock) || 0), 0);

// Dimensi yang nilainya mengandung angka > 0 dianggap dimensi UKURAN (wajib ada).
const SIZE_RE = /(ukuran|size|ml|volume)/i;
const isSizeDim = (name) => SIZE_RE.test(String(name || ''));

const ProductBlock = ({ product, index, defaultOpen }) => {
  const [open, setOpen] = useState(!!defaultOpen);
  const options = product.options || [];
  const variants = product.variants || [];
  const dims = options.length;
  const hasSize = options.some((o) => isSizeDim(o.name));

  return (
    <div
      className="rounded-xl border border-border/70 overflow-hidden bg-card"
      data-testid={`${T.importStructureProduct}-${index}`}
    >
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="w-full flex items-start gap-3 p-4 text-left hover:bg-muted/40 transition-colors"
        data-testid={`${T.importStructureToggle}-${index}`}
      >
        {open
          ? <ChevronDown className="h-4 w-4 mt-1 shrink-0 text-muted-foreground" />
          : <ChevronRight className="h-4 w-4 mt-1 shrink-0 text-muted-foreground" />}
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-sm font-semibold text-foreground truncate">
              {product.name || '(tanpa nama)'}
            </span>
            <Badge
              variant="outline"
              className="font-medium"
              style={{ backgroundColor: ACCENT_SOFT, color: ACCENT, borderColor: ACCENT }}
              data-testid={`${T.importStructureDims}-${index}`}
            >
              {dims} dimensi
            </Badge>
            <Badge variant="outline" className="font-medium bg-zinc-100 text-zinc-700 border-zinc-200">
              {variants.length} varian
            </Badge>
            {!hasSize && (
              <Badge variant="outline" className="font-medium bg-amber-100 text-amber-800 border-amber-200">
                <AlertTriangle className="h-3 w-3 mr-1" /> tanpa dimensi ukuran
              </Badge>
            )}
          </div>
          {/* Rantai dimensi berurutan: Konsentrasi x Tipe x Ukuran */}
          <div className="mt-1.5 text-xs text-muted-foreground">
            {dims === 0 ? (
              <span className="italic">Belum ada dimensi terdeteksi.</span>
            ) : (
              <span className="font-['Azeret_Mono',monospace]">
                {options.map((o, i) => (
                  <React.Fragment key={o.name || i}>
                    {i > 0 && <span className="mx-1.5 text-foreground/40">×</span>}
                    <span className="text-foreground/80">{o.name}</span>
                    <span className="text-muted-foreground">({(o.values || []).length})</span>
                  </React.Fragment>
                ))}
              </span>
            )}
          </div>
          <div className="mt-1 text-xs text-muted-foreground">
            {priceRange(variants)} · total stok {totalStock(variants)}
            {product.category ? ` · kategori ${product.category}` : ''}
          </div>
        </div>
      </button>

      {open && (
        <div className="border-t border-border/70">
          {/* Nilai tiap dimensi */}
          {dims > 0 && (
            <div className="p-4 pb-2 grid sm:grid-cols-2 xl:grid-cols-4 gap-3">
              {options.map((o, i) => (
                <div key={o.name || i} className="rounded-lg border border-border/60 p-3">
                  <div className="text-[11px] uppercase tracking-wide font-semibold" style={{ color: ACCENT }}>
                    Dimensi {i + 1} — {o.name}
                  </div>
                  <div className="mt-1.5 flex flex-wrap gap-1">
                    {(o.values || []).map((val) => (
                      <span
                        key={val}
                        className="inline-flex rounded-full border border-border/70 bg-muted/50 px-2 py-0.5 text-[11px] text-foreground/80"
                      >
                        {val}
                      </span>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Matriks varian — satu kolom per dimensi */}
          <div className="px-4 pb-4">
            <div className="overflow-x-auto rounded-lg border border-border/70">
              <Table data-testid={`${T.importStructureTable}-${index}`}>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-10">#</TableHead>
                    {options.map((o, i) => (
                      <TableHead key={o.name || i} className="whitespace-nowrap">{o.name}</TableHead>
                    ))}
                    <TableHead className="whitespace-nowrap text-right">Harga</TableHead>
                    <TableHead className="whitespace-nowrap text-right">Harga Coret</TableHead>
                    <TableHead className="whitespace-nowrap text-right">Stok</TableHead>
                    <TableHead className="whitespace-nowrap">SKU</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {variants.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={options.length + 5} className="text-center text-sm text-muted-foreground py-8">
                        Belum ada varian valid.
                      </TableCell>
                    </TableRow>
                  ) : variants.map((v, vi) => (
                    <TableRow key={v.sku || vi}>
                      <TableCell className="text-xs text-muted-foreground">{vi + 1}</TableCell>
                      {options.map((o, i) => (
                        <TableCell key={o.name || i} className="text-xs whitespace-nowrap">
                          {(v.options || {})[o.name] || <span className="text-muted-foreground/60 italic">—</span>}
                        </TableCell>
                      ))}
                      <TableCell className="text-xs text-right whitespace-nowrap">{rupiah(v.price)}</TableCell>
                      <TableCell className="text-xs text-right whitespace-nowrap text-muted-foreground">
                        {v.compare_at_price ? rupiah(v.compare_at_price) : '—'}
                      </TableCell>
                      <TableCell className="text-xs text-right">{Number(v.stock) || 0}</TableCell>
                      <TableCell className="text-xs font-['Azeret_Mono',monospace] text-muted-foreground">
                        {v.sku || <span className="italic">otomatis</span>}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

/**
 * Panel struktur varian hasil grouping.
 * @param {Array} products hasil /validate -> products[]
 * @param {boolean} validating sedang memvalidasi (tampilkan hint)
 */
export const ImportStructurePanel = ({ products = [], validating = false }) => (
  <Card className="border-border/70" data-testid={T.importStructurePanel}>
    <CardContent className="p-4">
      <div className="flex items-start justify-between mb-3 gap-3 flex-wrap">
        <div className="flex items-start gap-2">
          <Layers className="h-4 w-4 mt-0.5 shrink-0" style={{ color: ACCENT }} />
          <div>
            <h3 className="text-sm font-semibold text-foreground">Struktur Varian Terdeteksi</h3>
            <p className="text-xs text-muted-foreground mt-0.5">
              Hasil pengelompokan baris menjadi produk multivarian (1–4 dimensi). Pastikan nama &amp;
              urutan dimensi sudah benar sebelum mengimpor.
            </p>
          </div>
        </div>
        <Badge
          variant="outline"
          className="font-medium"
          style={{ backgroundColor: ACCENT_SOFT, color: ACCENT, borderColor: ACCENT }}
        >
          {products.length} produk
        </Badge>
      </div>

      {products.length === 0 ? (
        <div className="rounded-lg border border-dashed border-border/70 py-8 text-center text-sm text-muted-foreground">
          {validating
            ? 'Memvalidasi struktur varian…'
            : 'Belum ada produk valid. Lengkapi pemetaan kolom (termasuk minimal satu dimensi ukuran).'}
        </div>
      ) : (
        <div className="space-y-3">
          {products.map((p, i) => (
            <ProductBlock
              key={p.slug || p.name || i}
              product={p}
              index={i}
              defaultOpen={products.length <= 2}
            />
          ))}
        </div>
      )}
    </CardContent>
  </Card>
);
