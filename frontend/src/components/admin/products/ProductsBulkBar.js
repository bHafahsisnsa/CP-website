// components/admin/products/ProductsBulkBar.js — bilah aksi massal untuk daftar produk.
// Wajib ada karena impor katalog bisa menghasilkan ribuan produk draft: mengaktifkannya
// satu per satu tidak mungkin. Dua cakupan: produk yang dicentang, ATAU SELURUH hasil filter.
import React from 'react';
import { Archive, CheckCircle2, Loader2, X } from 'lucide-react';
import { Button } from '../../ui/button';
import {
  AlertDialog, AlertDialogTrigger, AlertDialogContent, AlertDialogHeader, AlertDialogTitle,
  AlertDialogDescription, AlertDialogFooter, AlertDialogCancel, AlertDialogAction,
} from '../../ui/alert-dialog';
import { ACCENT, ACCENT_SOFT } from '../adminUi';
import { adminTestIds as T } from '../../../constants/testIds/admin';

const nf = (n) => Number(n || 0).toLocaleString('id-ID');

const ConfirmAction = ({ target, count, onConfirm, busy, testId, children }) => (
  <AlertDialog>
    <AlertDialogTrigger asChild>
      <Button
        size="sm"
        variant={target === 'active' ? 'default' : 'outline'}
        className="gap-2"
        disabled={busy || count === 0}
        data-testid={testId}
      >
        {busy ? <Loader2 className="h-4 w-4 animate-spin" />
          : target === 'active' ? <CheckCircle2 className="h-4 w-4" /> : <Archive className="h-4 w-4" />}
        {children}
      </Button>
    </AlertDialogTrigger>
    <AlertDialogContent>
      <AlertDialogHeader>
        <AlertDialogTitle>
          {target === 'active' ? 'Aktifkan' : 'Arsipkan'} {nf(count)} produk?
        </AlertDialogTitle>
        <AlertDialogDescription>
          {target === 'active'
            ? `${nf(count)} produk akan langsung TAMPIL di storefront. Pastikan harga & datanya sudah benar.`
            : `${nf(count)} produk akan disembunyikan dari storefront. Data tetap tersimpan (aman untuk pesanan lama).`}
        </AlertDialogDescription>
      </AlertDialogHeader>
      <AlertDialogFooter>
        <AlertDialogCancel>Batal</AlertDialogCancel>
        <AlertDialogAction onClick={onConfirm} data-testid={T.productsBulkConfirm}>
          {target === 'active' ? 'Aktifkan sekarang' : 'Arsipkan sekarang'}
        </AlertDialogAction>
      </AlertDialogFooter>
    </AlertDialogContent>
  </AlertDialog>
);

export const ProductsBulkBar = ({
  selectedCount = 0, total = 0, allFilter = false, pageCount = 0,
  busy = false, onSelectAllFilter, onClear, onApply,
}) => {
  const count = allFilter ? total : selectedCount;
  if (count === 0) return null;
  return (
    <div
      className="mb-4 flex flex-wrap items-center gap-3 rounded-xl border p-3"
      style={{ borderColor: ACCENT, backgroundColor: ACCENT_SOFT }}
      data-testid={T.productsBulkBar}
    >
      <span className="text-sm font-medium text-foreground">
        {allFilter
          ? `Semua ${nf(total)} produk hasil filter dipilih`
          : `${nf(selectedCount)} produk dipilih`}
      </span>
      {!allFilter && total > pageCount && (
        <Button
          variant="link" size="sm" className="h-auto p-0 text-xs"
          style={{ color: ACCENT }}
          onClick={onSelectAllFilter}
          data-testid={T.productsBulkSelectAllFilter}
        >
          Pilih semua {nf(total)} hasil filter
        </Button>
      )}
      <div className="flex-1" />
      <ConfirmAction
        target="active" count={count} busy={busy}
        onConfirm={() => onApply('active')} testId={T.productsBulkActivate}
      >
        Aktifkan
      </ConfirmAction>
      <ConfirmAction
        target="archived" count={count} busy={busy}
        onConfirm={() => onApply('archived')} testId={T.productsBulkArchive}
      >
        Arsipkan
      </ConfirmAction>
      <Button
        variant="ghost" size="sm" className="gap-1.5 text-muted-foreground"
        onClick={onClear} data-testid={T.productsBulkClear}
      >
        <X className="h-4 w-4" /> Bersihkan
      </Button>
    </div>
  );
};
