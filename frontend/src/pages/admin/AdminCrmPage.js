// pages/admin/AdminCrmPage.js — Segmentasi CRM diturunkan dari orders (Epic E7).
// Segmen: prospek/new/repeat/high_value/dormant. Ekspor CSV per tampilan. READ-only.
import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { Download, Users } from 'lucide-react';
import { toast } from 'sonner';
import { getCrmSegments } from '../../services/admin';
import { formatIDR } from '../../lib/format';
import { PageHeader, EmptyState, formatDateTime } from '../../components/admin/adminUi';
import { growthTestIds as G } from '../../constants/testIds/growth';
import { Button } from '../../components/ui/button';
import { Badge } from '../../components/ui/badge';
import { Card, CardContent } from '../../components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../../components/ui/table';
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from '../../components/ui/select';

const SEG_LABEL = {
  prospek: 'Prospek', new: 'Baru', repeat: 'Berulang', high_value: 'Bernilai Tinggi', dormant: 'Dorman',
};
const SEG_CLS = {
  prospek: 'bg-zinc-100 text-zinc-700 border-zinc-200',
  new: 'bg-sky-100 text-sky-800 border-sky-200',
  repeat: 'bg-emerald-100 text-emerald-800 border-emerald-200',
  high_value: 'bg-amber-100 text-amber-800 border-amber-200',
  dormant: 'bg-rose-100 text-rose-800 border-rose-200',
};

export default function AdminCrmPage() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [seg, setSeg] = useState('all');

  const load = useCallback(async () => {
    setLoading(true);
    try {
      setData(await getCrmSegments(seg === 'all' ? '' : seg));
    } catch (e) {
      setData(null);
      toast.error('Gagal memuat CRM.');
    } finally {
      setLoading(false);
    }
  }, [seg]);
  useEffect(() => { load(); }, [load]);

  const rows = data?.rows || [];
  const segments = data?.segments;
  const cards = useMemo(
    () => {
      const counts = segments || {};
      return ['prospek', 'new', 'repeat', 'high_value', 'dormant'].map((k) => ({ k, n: counts[k] || 0 }));
    },
    [segments]
  );

  const exportCsv = () => {
    if (!rows.length) { toast.error('Tidak ada data untuk diekspor.'); return; }
    const head = ['Nama', 'Email', 'Segmen', 'Jumlah Order', 'LTV', 'Order Terakhir'];
    const lines = rows.map((r) => [
      r.name || '', r.email || '', SEG_LABEL[r.segment] || r.segment,
      r.orders, r.ltv, r.last_order || '',
    ].map((v) => `"${String(v).replace(/"/g, '""')}"`).join(','));
    const csv = [head.join(','), ...lines].join('\n');
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = `crm-${seg}-${Date.now()}.csv`;
    a.click();
    URL.revokeObjectURL(a.href);
    toast.success('CSV diekspor.');
  };

  return (
    <div data-testid={G.crmPage}>
      <PageHeader title="CRM & Segmen" description="Segmentasi pelanggan diturunkan dari riwayat pesanan." />

      <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 mb-6">
        {cards.map((c) => (
          <Card key={c.k} className="border-border/70"><CardContent className="p-4">
            <div className="text-[11px] uppercase tracking-[0.14em] text-muted-foreground">{SEG_LABEL[c.k]}</div>
            <div className="mt-1 text-2xl font-semibold">{c.n}</div>
          </CardContent></Card>
        ))}
      </div>

      <div className="flex items-center justify-between gap-3 mb-4">
        <Select value={seg} onValueChange={setSeg}>
          <SelectTrigger className="w-52" data-testid={G.crmSegmentFilter}><SelectValue /></SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Semua Segmen</SelectItem>
            <SelectItem value="prospek">Prospek</SelectItem>
            <SelectItem value="new">Baru</SelectItem>
            <SelectItem value="repeat">Berulang</SelectItem>
            <SelectItem value="high_value">Bernilai Tinggi</SelectItem>
            <SelectItem value="dormant">Dorman</SelectItem>
          </SelectContent>
        </Select>
        <Button variant="outline" onClick={exportCsv} className="gap-2" data-testid={G.crmExport}>
          <Download className="h-4 w-4" /> Ekspor CSV
        </Button>
      </div>

      <Card className="border-border/70"><CardContent className="p-4">
        {loading ? (
          <div className="py-8 text-sm text-muted-foreground">Memuat…</div>
        ) : rows.length === 0 ? (
          <EmptyState title="Belum ada pelanggan" hint="Pelanggan akan tersegmentasi otomatis dari pesanan." />
        ) : (
          <div className="overflow-x-auto">
            <Table data-testid={G.crmTable}>
              <TableHeader><TableRow>
                <TableHead>Pelanggan</TableHead><TableHead>Segmen</TableHead>
                <TableHead className="text-right">Order</TableHead>
                <TableHead className="text-right">LTV</TableHead>
                <TableHead>Order Terakhir</TableHead>
              </TableRow></TableHeader>
              <TableBody>
                {rows.map((r) => (
                  <TableRow key={r.user_id}>
                    <TableCell>
                      <div className="font-medium truncate max-w-[260px]" title={r.name || ''}>{r.name || '—'}</div>
                      <div className="text-xs text-muted-foreground truncate max-w-[260px]" title={r.email || ''}>{r.email}</div>
                    </TableCell>
                    <TableCell><Badge variant="outline" className={SEG_CLS[r.segment]}>{SEG_LABEL[r.segment] || r.segment}</Badge></TableCell>
                    <TableCell className="text-right font-['Azeret_Mono',monospace] text-sm">{r.orders}</TableCell>
                    <TableCell className="text-right font-['Azeret_Mono',monospace] text-sm">{formatIDR(r.ltv)}</TableCell>
                    <TableCell className="text-xs text-muted-foreground">{r.last_order ? formatDateTime(r.last_order) : '—'}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        )}
      </CardContent></Card>
    </div>
  );
}
