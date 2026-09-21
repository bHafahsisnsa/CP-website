// components/admin/import/ImportTierMatrix.js
// Grid matriks harga: BARIS = tier terdeteksi, KOLOM = kombinasi dimensi yang benar-benar
// ada di file (mis. Ukuran x Tipe = 6 kolom). Admin cukup mengisi sel; seluruh baris file
// terisi otomatis oleh importBulkFill.applyBulkFill().
import React from 'react';
import { ArrowRightToLine, Copy } from 'lucide-react';
import { Button } from '../../ui/button';
import { Input } from '../../ui/input';
import { ACCENT, ACCENT_SOFT } from '../adminUi';
import { adminTestIds as T } from '../../../constants/testIds/admin';
import { formatRupiah, parseRupiah } from './importBulkFill';

export const ImportTierMatrix = ({
  tiers = [], combos = [], matrix = {}, onCell, onCopyRow, onSpreadRow, disabled = false,
}) => {
  if (tiers.length === 0 || combos.length === 0) {
    return (
      <div
        className="rounded-lg border border-dashed border-border/70 py-8 px-4 text-center text-sm text-muted-foreground"
        data-testid={T.bulkFillMatrixEmpty}
      >
        Tier atau dimensi belum terdeteksi. Pilih kolom penanda tier di atas, lalu pastikan
        pemetaan dimensi (mis. Ukuran &amp; Tipe) sudah benar.
      </div>
    );
  }
  return (
    <div className="overflow-x-auto rounded-lg border border-border/70 cp-thin-scroll">
      <table className="w-full text-sm border-collapse" data-testid={T.bulkFillMatrix}>
        <thead>
          <tr className="bg-muted/50">
            <th
              className="sticky left-0 z-10 bg-muted/50 px-3 py-2 text-left text-xs font-semibold uppercase tracking-wide whitespace-nowrap border-b border-border/70"
              style={{ color: ACCENT }}
            >
              Tier
            </th>
            {combos.map((c) => (
              <th
                key={c.key}
                className="px-2 py-2 text-right text-[11px] font-semibold whitespace-nowrap border-b border-l border-border/70 text-foreground/80"
              >
                {c.label}
                <div className="font-normal text-[10px] text-muted-foreground">{c.rows} baris</div>
              </th>
            ))}
            <th className="px-2 py-2 border-b border-l border-border/70 w-[86px]" />
          </tr>
        </thead>
        <tbody>
          {tiers.map((t, ti) => {
            const row = matrix[t.label] || {};
            const rowFilled = combos.filter((c) => parseRupiah(row[c.key]) > 0).length;
            return (
              <tr key={t.label} className="hover:bg-muted/20">
                <th
                  scope="row"
                  className="sticky left-0 z-10 bg-card px-3 py-2 text-left whitespace-nowrap border-b border-border/60"
                >
                  <div className="text-xs font-semibold text-foreground font-['Azeret_Mono',monospace]">
                    {t.label}
                  </div>
                  <div className="text-[10px] text-muted-foreground font-normal">
                    {t.products} produk
                    {rowFilled > 0 && rowFilled < combos.length
                      ? ` \u00b7 ${rowFilled}/${combos.length} terisi`
                      : ''}
                  </div>
                </th>
                {combos.map((c, ci) => (
                  <td key={c.key} className="p-1 border-b border-l border-border/60">
                    <Input
                      inputMode="numeric"
                      disabled={disabled}
                      value={formatRupiah(row[c.key])}
                      onChange={(e) => onCell(t.label, c.key, parseRupiah(e.target.value))}
                      placeholder="0"
                      aria-label={`Harga ${t.label} ${c.label}`}
                      className="h-8 text-xs text-right min-w-[92px] font-['Azeret_Mono',monospace]"
                      data-testid={`${T.bulkFillCell}-${ti}-${ci}`}
                    />
                  </td>
                ))}
                <td className="p-1 border-b border-l border-border/60">
                  <div className="flex items-center gap-1 justify-end">
                    <Button
                      type="button" variant="ghost" size="icon" disabled={disabled}
                      className="h-7 w-7" title="Isi seluruh baris ini dari sel pertama"
                      onClick={() => onSpreadRow(t.label)}
                      data-testid={`${T.bulkFillSpreadRow}-${ti}`}
                    >
                      <ArrowRightToLine className="h-3.5 w-3.5" />
                    </Button>
                    <Button
                      type="button" variant="ghost" size="icon"
                      disabled={disabled || ti === 0}
                      className="h-7 w-7" title="Salin nilai dari tier di atasnya"
                      onClick={() => onCopyRow(ti)}
                      data-testid={`${T.bulkFillCopyRow}-${ti}`}
                    >
                      <Copy className="h-3.5 w-3.5" />
                    </Button>
                  </div>
                </td>
              </tr>
            );
          })}
        </tbody>
        <tfoot>
          <tr>
            <td
              colSpan={combos.length + 2}
              className="px-3 py-2 text-[11px] text-muted-foreground"
              style={{ backgroundColor: ACCENT_SOFT }}
            >
              Isi angka rupiah tanpa titik (mis. <span className="font-medium">250000</span>).
              Sel yang dibiarkan 0 tidak mengisi baris mana pun — baris terkait tetap ditandai error.
            </td>
          </tr>
        </tfoot>
      </table>
    </div>
  );
};
