// components/admin/import/ImportResultDialog.js — dialog ringkasan hasil impor.
// Menjelaskan hasil per kategori + PENJELASAN EKSPLISIT untuk baris yang DILEWATI
// (mode "Tambah saja"): produk sudah ada, dan bila statusnya 'archived' ia TIDAK tampil
// di storefront — admin diberi jalan keluar (pakai mode Upsert atau pulihkan dari Produk).
import React from 'react';
import { CheckCircle2, Info, AlertTriangle, EyeOff } from 'lucide-react';
import { Button } from '../../ui/button';
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter,
} from '../../ui/dialog';
import { adminTestIds as T } from '../../../constants/testIds/admin';

const Stat = ({ value, label, tone }) => (
  <div className="rounded-lg border border-border/70 p-3">
    <div className={`text-2xl font-semibold ${tone}`}>{value}</div>
    <div className="text-xs text-muted-foreground">{label}</div>
  </div>
);

export const ImportResultDialog = ({ result, onOpenChange, onImportAnother, onViewProducts }) => {
  const skipped = Number(result?.skipped || 0);
  const skippedDetails = result?.skipped_details || [];
  const skippedArchived = Number(result?.skipped_archived || 0);
  const failedTotal = Number(result?.failed || 0) + Number(result?.row_errors || 0);

  return (
    <Dialog open={!!result} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-md" data-testid={T.importResultDialog}>
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <CheckCircle2 className="h-5 w-5 text-emerald-600" /> Impor Selesai
          </DialogTitle>
          <DialogDescription>Ringkasan hasil impor produk.</DialogDescription>
        </DialogHeader>

        {result && (
          <div className="space-y-3 max-h-[60vh] overflow-y-auto">
            <div className="grid grid-cols-2 gap-3">
              <Stat value={result.created} label="Dibuat" tone="text-emerald-700" />
              <Stat value={result.updated} label="Diperbarui" tone="text-blue-700" />
              <Stat value={result.skipped} label="Dilewati (sudah ada)" tone="text-zinc-600" />
              <Stat value={failedTotal} label="Gagal / baris error" tone="text-rose-700" />
            </div>

            {/* Penjelasan baris yang dilewati — mencegah admin bingung "kok produknya tidak muncul?" */}
            {skipped > 0 && (
              <div
                className="rounded-lg border border-amber-200 bg-amber-50 p-3 space-y-2"
                data-testid={T.importSkippedNote}
              >
                <div className="flex items-start gap-2 text-xs text-amber-900">
                  <Info className="h-4 w-4 shrink-0 mt-0.5" />
                  <span>
                    <span className="font-medium">{skipped} produk dilewati</span> karena slug/nama-nya
                    sudah ada dan mode impor <span className="font-medium">&ldquo;Tambah saja&rdquo;</span> tidak
                    menimpa data. Untuk memperbarui produk yang sudah ada, impor ulang dengan mode{' '}
                    <span className="font-medium">Upsert</span>.
                  </span>
                </div>

                {skippedArchived > 0 && (
                  <div
                    className="flex items-start gap-2 rounded-md border border-rose-200 bg-rose-50 p-2.5 text-xs text-rose-800"
                    data-testid={T.importSkippedArchivedWarn}
                  >
                    <EyeOff className="h-4 w-4 shrink-0 mt-0.5" />
                    <span>
                      <span className="font-medium">{skippedArchived} di antaranya berstatus &ldquo;archived&rdquo;</span>{' '}
                      sehingga <span className="font-medium">TIDAK tampil di storefront</span>. Pulihkan dari
                      halaman Produk, atau impor ulang dengan mode Upsert agar otomatis aktif kembali.
                    </span>
                  </div>
                )}

                {skippedDetails.length > 0 && (
                  <ul className="text-xs text-amber-900 space-y-1 pl-1">
                    {skippedDetails.slice(0, 12).map((s, i) => (
                      <li key={s.slug || i} className="flex items-center gap-2">
                        <span className="truncate">{s.product || s.slug}</span>
                        <span
                          className={`shrink-0 rounded-full border px-1.5 py-0.5 text-[10px] font-medium ${
                            s.status === 'archived'
                              ? 'border-rose-300 bg-rose-100 text-rose-700'
                              : 'border-zinc-300 bg-zinc-100 text-zinc-600'
                          }`}
                        >
                          {s.status === 'archived' ? 'archived' : 'aktif'}
                        </span>
                      </li>
                    ))}
                    {skippedDetails.length > 12 && (
                      <li className="text-amber-800/80">
                        …dan {skippedDetails.length - 12} produk lainnya
                      </li>
                    )}
                  </ul>
                )}
              </div>
            )}

            {(result.errors || []).length > 0 && (
              <div className="rounded-lg border border-rose-200 bg-rose-50 p-3 max-h-40 overflow-y-auto">
                <div className="flex items-center gap-1.5 text-xs font-medium text-rose-700 mb-1">
                  <AlertTriangle className="h-3.5 w-3.5" /> Detail kegagalan:
                </div>
                <ul className="text-xs text-rose-700 list-disc pl-4 space-y-0.5">
                  {result.errors.map((er, idx) => (
                    <li key={idx}>{er.product || er.slug || 'Produk'}: {er.error}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}

        <DialogFooter className="gap-2">
          <Button variant="outline" onClick={onImportAnother}>Impor file lain</Button>
          <Button onClick={onViewProducts}>Lihat Produk</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};
