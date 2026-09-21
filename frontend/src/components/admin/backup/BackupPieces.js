// components/admin/backup/BackupPieces.js — potongan UI Backup & Restore.
// Dipisah dari AdminBackupPage agar tiap file tetap di bawah batas compliance repo.
import React from 'react';
import { CheckCircle2, ListChecks } from 'lucide-react';
import { Button } from '../../ui/button';
import { Badge } from '../../ui/badge';
import { Checkbox } from '../../ui/checkbox';
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from '../../ui/table';
import { adminTestIds as T } from '../../../constants/testIds/admin';

export const humanSize = (n) => {
  if (!n && n !== 0) return '—';
  if (n < 1024) return `${n} B`;
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`;
  return `${(n / 1024 / 1024).toFixed(2)} MB`;
};

// Baca file backup client-side untuk deteksi koleksi (tanpa upload).
export const readFileCollections = (file) => new Promise((resolve, reject) => {
  const reader = new FileReader();
  reader.onload = () => {
    try {
      const obj = JSON.parse(reader.result);
      let names = [];
      const counts = {};
      const data = obj && typeof obj.data === 'object' && obj.data ? obj.data : obj;
      if (data && typeof data === 'object') {
        names = Object.keys(data).filter((k) => Array.isArray(data[k]));
        names.forEach((n) => { counts[n] = data[n].length; });
      }
      resolve({ meta: obj?.meta || null, names, counts });
    } catch (e) { reject(e); }
  };
  reader.onerror = reject;
  reader.readAsText(file);
});

// ------- Checklist koleksi (reusable) -------
export const CollectionChecklist = ({ items, selected, onToggle, onSelectAll, onClear, countKey = 'count' }) => (
  <div>
    <div className="flex items-center justify-between mb-3">
      <div className="text-xs text-muted-foreground flex items-center gap-1.5">
        <ListChecks className="h-3.5 w-3.5" /> {selected.size} dari {items.length} koleksi dipilih
      </div>
      <div className="flex gap-2">
        <Button type="button" variant="outline" size="sm" onClick={onSelectAll} data-testid={T.backupSelectAll}>Pilih Semua</Button>
        <Button type="button" variant="ghost" size="sm" onClick={onClear} data-testid={T.backupClear}>Kosongkan</Button>
      </div>
    </div>
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2">
      {items.map((it) => {
        const checked = selected.has(it.name);
        return (
          <label
            key={it.name}
            data-testid={`admin-backup-col-${it.name}`}
            className={`flex items-center gap-3 rounded-xl border px-3 py-2.5 cursor-pointer transition-colors ${checked ? 'border-[#B89B6A] bg-[rgba(184,155,106,0.08)]' : 'border-border hover:bg-muted/40'}`}
          >
            <Checkbox checked={checked} onCheckedChange={() => onToggle(it.name)} />
            <div className="min-w-0 flex-1">
              <div className="text-sm font-medium truncate text-foreground">{it.label || it.name}</div>
              <div className="text-[11px] text-muted-foreground font-mono truncate">{it.name}</div>
            </div>
            {countKey && it[countKey] != null ? (
              <Badge variant="outline" className="shrink-0 font-mono text-[11px]">{it[countKey]}</Badge>
            ) : null}
          </label>
        );
      })}
    </div>
  </div>
);

// ------- Laporan hasil restore -------
export const RestoreReport = ({ report }) => {
  if (!report) return null;
  const s = report.summary || {};
  return (
    <div className="mt-5 rounded-xl border border-border overflow-hidden" data-testid={T.restoreReport}>
      <div className="flex items-center gap-2 px-4 py-3 bg-emerald-50 border-b border-emerald-100">
        <CheckCircle2 className="h-4 w-4 text-emerald-600" />
        <span className="text-sm font-medium text-emerald-800">
          Restore selesai · mode <b className="uppercase">{report.mode}</b> · {s.collections} koleksi · {s.written} dokumen ditulis
          {s.errors ? ` · ${s.errors} error` : ''}
        </span>
      </div>
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Koleksi</TableHead>
            <TableHead className="text-right">Di Backup</TableHead>
            <TableHead className="text-right">Dihapus</TableHead>
            <TableHead className="text-right">Ditambah</TableHead>
            <TableHead className="text-right">Diperbarui</TableHead>
            <TableHead className="text-right">Error</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {(report.restored || []).map((r) => (
            <TableRow key={r.collection}>
              <TableCell className="font-medium">{r.label || r.collection}
                <span className="block text-[11px] text-muted-foreground font-mono">{r.collection}</span>
              </TableCell>
              <TableCell className="text-right font-mono text-sm">{r.in_backup}</TableCell>
              <TableCell className="text-right font-mono text-sm">{r.deleted}</TableCell>
              <TableCell className="text-right font-mono text-sm text-emerald-700">{r.inserted}</TableCell>
              <TableCell className="text-right font-mono text-sm text-blue-700">{r.updated}</TableCell>
              <TableCell className="text-right font-mono text-sm">
                {r.errors ? <span className="text-rose-600" title={r.error_detail}>{r.errors}</span> : '0'}
              </TableCell>
            </TableRow>
          ))}
          {report.skipped?.length ? (
            <TableRow>
              <TableCell colSpan={6} className="text-xs text-muted-foreground">
                Dilewati: {report.skipped.join(', ')}
              </TableCell>
            </TableRow>
          ) : null}
        </TableBody>
      </Table>
    </div>
  );
};
