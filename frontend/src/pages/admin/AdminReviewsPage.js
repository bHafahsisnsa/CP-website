// pages/admin/AdminReviewsPage.js — moderasi ulasan (BR-5).
import React, { useEffect, useState, useCallback } from 'react';
import { toast } from 'sonner';
import { Star } from 'lucide-react';
import { listReviews, setReviewStatus } from '../../services/admin';
import {
  PageHeader, TableSkeleton, EmptyState, ReviewBadge, formatDateTime,
} from '../../components/admin/adminUi';
import { adminTestIds as T } from '../../constants/testIds/admin';
import { Card, CardContent } from '../../components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../../components/ui/table';
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from '../../components/ui/select';
import { Button } from '../../components/ui/button';

const Stars = ({ n = 0 }) => (
  <span className="inline-flex">{Array.from({ length: 5 }).map((_, i) => (
    <Star key={i} className={`h-3.5 w-3.5 ${i < n ? 'fill-amber-400 text-amber-400' : 'text-zinc-300'}`} />
  ))}</span>
);

export default function AdminReviewsPage() {
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(true);
  const [status, setStatus] = useState('all');
  const [busy, setBusy] = useState('');

  const load = useCallback(async () => {
    setLoading(true);
    try { setRows(await listReviews(status === 'all' ? '' : status) || []); }
    catch (e) { toast.error('Gagal memuat ulasan.'); }
    finally { setLoading(false); }
  }, [status]);
  useEffect(() => { load(); }, [load]);

  const moderate = async (r, to) => {
    setBusy(r.id);
    try { await setReviewStatus(r.id, to); toast.success('Status ulasan diperbarui.'); load(); }
    catch (e) { toast.error('Gagal memperbarui ulasan.'); }
    finally { setBusy(''); }
  };

  return (
    <div>
      <PageHeader title="Ulasan" description="Moderasi ulasan pelanggan (memengaruhi rating produk)." />
      <Card className="border-border/70"><CardContent className="p-4">
        <div className="flex justify-end mb-4">
          <Select value={status} onValueChange={setStatus}>
            <SelectTrigger className="w-full sm:w-52" data-testid="admin-reviews-status-filter"><SelectValue /></SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Semua</SelectItem>
              <SelectItem value="pending">Menunggu</SelectItem>
              <SelectItem value="published">Tayang</SelectItem>
              <SelectItem value="hidden">Disembunyikan</SelectItem>
            </SelectContent>
          </Select>
        </div>
        {loading ? <TableSkeleton rows={6} cols={5} /> : (
          rows.length === 0 ? <EmptyState title="Belum ada ulasan" /> : (
            <div className="overflow-x-auto">
              <Table data-testid={T.reviewsTable}>
                <TableHeader><TableRow>
                  <TableHead>Pengguna</TableHead><TableHead>Rating</TableHead><TableHead>Ulasan</TableHead>
                  <TableHead>Status</TableHead><TableHead className="text-right">Aksi</TableHead>
                </TableRow></TableHeader>
                <TableBody>
                  {rows.map((r) => (
                    <TableRow key={r.id}>
                      <TableCell className="text-sm">
                        <div className="font-medium">{r.user_name || r.name || 'Anonim'}</div>
                        <div className="text-[11px] text-muted-foreground">{formatDateTime(r.created_at)}</div>
                      </TableCell>
                      <TableCell><Stars n={r.rating || 0} /></TableCell>
                      <TableCell className="text-sm max-w-[280px]"><div className="line-clamp-2">{r.comment || r.body || '—'}</div></TableCell>
                      <TableCell><ReviewBadge status={r.status} /></TableCell>
                      <TableCell className="text-right">
                        <div className="inline-flex gap-1">
                          {r.status !== 'published' && <Button size="sm" variant="secondary" disabled={busy === r.id} onClick={() => moderate(r, 'published')}>Tayangkan</Button>}
                          {r.status !== 'hidden' && <Button size="sm" variant="outline" disabled={busy === r.id} onClick={() => moderate(r, 'hidden')}>Sembunyikan</Button>}
                        </div>
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
