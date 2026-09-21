// components/admin/import/ImportPreviewTable.js — pratinjau baris yang BISA DIEDIT.
// Kolom mengikuti pemetaan aktif (dinamis, maks 4 dimensi).
//
// E12: baris TIDAK lagi disimpan seluruhnya di browser. Komponen menerima `items`
// ([{index, data}]) yaitu JENDELA baris dari sesi server + `reportMap` (index -> laporan).
// Mode "Hanya error" mengambil baris bermasalah dari server, jadi admin tetap bisa
// memperbaiki baris ke-6.000 tanpa memuat 6.426 baris ke memori.
import React from 'react';
import { AlertTriangle, CheckCircle2, Filter, Loader2 } from 'lucide-react';
import { Button } from '../../ui/button';
import { Card, CardContent } from '../../ui/card';
import { Input } from '../../ui/input';
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from '../../ui/table';
import { adminTestIds as T } from '../../../constants/testIds/admin';
import { DISPLAY_CAP, LABEL, REQUIRED } from './importConstants';

const nf = (n) => Number(n || 0).toLocaleString('id-ID');

export const ImportPreviewTable = ({
  items = [], reportMap = {}, mapping, previewCols, summary, total = 0,
  errorCount = 0, showErrorsOnly, onToggleErrorsOnly, onUpdateCell, loading = false,
}) => {
  const shown = items.length;
  const scope = showErrorsOnly ? errorCount : total;

  return (
    <Card className="border-border/70">
      <CardContent className="p-4">
        <div className="flex items-center justify-between mb-3 gap-3 flex-wrap">
          <div>
            <h3 className="text-sm font-semibold text-foreground">Pratinjau Baris (bisa diedit)</h3>
            <p className="text-xs text-muted-foreground mt-0.5">
              Satu baris = satu varian. Kolom mengikuti dimensi yang terpetakan (maks 4 dimensi).
              Baris dengan nama/slug sama = satu produk multivarian.
            </p>
          </div>
          <div className="flex items-center gap-3">
            {loading && <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />}
            {scope > shown && (
              <span className="text-xs text-muted-foreground">
                Menampilkan {nf(shown)} dari {nf(scope)} baris
              </span>
            )}
            <Button
              variant={showErrorsOnly ? 'default' : 'outline'}
              size="sm" className="gap-2"
              onClick={onToggleErrorsOnly}
              data-testid={T.importErrorsOnly}
            >
              <Filter className="h-4 w-4" /> {showErrorsOnly ? 'Tampilkan semua' : 'Hanya error'}
            </Button>
          </div>
        </div>

        <div className="overflow-x-auto rounded-lg border border-border/70">
          <Table data-testid={T.importPreviewTable}>
            <TableHeader>
              <TableRow>
                <TableHead className="w-12">#</TableHead>
                <TableHead className="w-24">Status</TableHead>
                {previewCols.map((col) => (
                  <TableHead key={col} className="whitespace-nowrap">
                    {LABEL[col] || col}{REQUIRED.includes(col) && <span className="text-rose-500"> *</span>}
                  </TableHead>
                ))}
              </TableRow>
            </TableHeader>
            <TableBody>
              {shown === 0 ? (
                <TableRow>
                  <TableCell colSpan={previewCols.length + 2} className="text-center text-sm text-muted-foreground py-10">
                    {showErrorsOnly ? 'Tidak ada baris bermasalah.' : 'Tidak ada baris.'}
                  </TableCell>
                </TableRow>
              ) : items.slice(0, DISPLAY_CAP).map(({ index: i, data: r }) => {
                const rep = reportMap[i];
                const isErr = rep && rep.status === 'error';
                return (
                  <TableRow
                    key={i}
                    className={isErr ? 'bg-rose-50/60' : ''}
                    style={isErr ? { boxShadow: 'inset 3px 0 0 #f43f5e' } : undefined}
                  >
                    <TableCell className="text-xs text-muted-foreground">{i + 1}</TableCell>
                    <TableCell>
                      {!rep ? (
                        <span className="text-xs text-muted-foreground">…</span>
                      ) : isErr ? (
                        <span
                          className="inline-flex items-center gap-1 text-xs text-rose-700 cursor-help"
                          title={(rep.errors || []).join(' • ')}
                        >
                          <AlertTriangle className="h-3.5 w-3.5" /> {(rep.errors || []).length} isu
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 text-xs text-emerald-700">
                          <CheckCircle2 className="h-3.5 w-3.5" /> OK
                        </span>
                      )}
                    </TableCell>
                    {previewCols.map((col) => {
                      const header = mapping[col];
                      if (!header) {
                        return (
                          <TableCell key={col} className="text-xs text-muted-foreground/60 italic">—</TableCell>
                        );
                      }
                      return (
                        <TableCell key={col} className="p-1.5">
                          <Input
                            value={r?.[header] ?? ''}
                            onChange={(e) => onUpdateCell(i, header, e.target.value)}
                            className="h-8 text-xs min-w-[110px]"
                            data-testid={`admin-import-cell-${i}-${col}`}
                          />
                        </TableCell>
                      );
                    })}
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </div>

        {summary && summary.error > 0 && !showErrorsOnly && (
          <p className="mt-3 text-xs text-muted-foreground">
            {nf(summary.error)} baris memiliki masalah. Klik <span className="font-medium">Hanya error</span>{' '}
            untuk memperbaikinya. Baris error akan otomatis dilewati saat impor.
          </p>
        )}
      </CardContent>
    </Card>
  );
};
