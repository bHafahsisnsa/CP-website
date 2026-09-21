// pages/admin/AdminOrdersPage.js — daftar pesanan + filter status (BR-6).
import React, { useEffect, useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'sonner';
import { listOrders } from '../../services/admin';
import { formatIDR } from '../../lib/format';
import {
  PageHeader, TableSkeleton, EmptyState, StatusBadge, formatDateTime, ORDER_STATUSES, ORDER_STATUS_META,
} from '../../components/admin/adminUi';
import { adminTestIds as T } from '../../constants/testIds/admin';
import { Card, CardContent } from '../../components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../../components/ui/table';
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from '../../components/ui/select';
import { Button } from '../../components/ui/button';

export default function AdminOrdersPage() {
  const navigate = useNavigate();
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(true);
  const [status, setStatus] = useState('all');

  const load = useCallback(async () => {
    setLoading(true);
    try { setRows(await listOrders(status === 'all' ? '' : status) || []); }
    catch (e) { toast.error('Gagal memuat pesanan.'); }
    finally { setLoading(false); }
  }, [status]);
  useEffect(() => { load(); }, [load]);

  return (
    <div>
      <PageHeader title="Pesanan" description="Proses & pantau pesanan pelanggan." />
      <Card className="border-border/70"><CardContent className="p-4">
        <div className="flex justify-end mb-4">
          <Select value={status} onValueChange={setStatus}>
            <SelectTrigger className="w-full sm:w-52" data-testid={T.ordersStatusSelect}><SelectValue placeholder="Status" /></SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Semua Status</SelectItem>
              {ORDER_STATUSES.map((s) => <SelectItem key={s} value={s}>{ORDER_STATUS_META[s].label}</SelectItem>)}
            </SelectContent>
          </Select>
        </div>
        {loading ? <TableSkeleton rows={6} cols={5} /> : (
          rows.length === 0 ? <EmptyState title="Belum ada pesanan" /> : (
            <div className="overflow-x-auto">
              <Table data-testid={T.ordersTable}>
                <TableHeader><TableRow>
                  <TableHead>Kode</TableHead><TableHead>Pelanggan</TableHead><TableHead>Tanggal</TableHead>
                  <TableHead>Status</TableHead><TableHead className="text-right">Total</TableHead><TableHead className="w-24" />
                </TableRow></TableHeader>
                <TableBody>
                  {rows.map((o) => (
                    <TableRow key={o.code}>
                      <TableCell className="font-[\'Azeret_Mono\',monospace] text-xs">{o.code}</TableCell>
                      <TableCell className="text-sm">
                        <div className="truncate max-w-[180px]">{o.address?.name || o.customer?.name || '—'}</div>
                        <div className="text-[11px] text-muted-foreground truncate max-w-[180px]">{o.customer_email || o.address?.phone || ''}</div>
                      </TableCell>
                      <TableCell className="text-xs text-muted-foreground">{formatDateTime(o.created_at)}</TableCell>
                      <TableCell><StatusBadge status={o.status} /></TableCell>
                      <TableCell className="text-right font-[\'Azeret_Mono\',monospace] text-sm">{formatIDR(o.total || 0)}</TableCell>
                      <TableCell className="text-right">
                        <Button variant="secondary" size="sm" onClick={() => navigate(`/admin/pesanan/${o.code}`)}>Proses</Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )
        )}
      </CardContent></Card>
    </div>
  );
}
