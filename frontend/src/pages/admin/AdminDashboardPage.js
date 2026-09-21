// pages/admin/AdminDashboardPage.js — ringkasan operasional toko (BR-1).
import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { toast } from 'sonner';
import { getDashboard } from '../../services/admin';
import { formatIDR } from '../../lib/format';
import {
  PageHeader, MetricCard, StatusBadge, formatDateTime, ORDER_STATUS_META, TableSkeleton, EmptyState,
} from '../../components/admin/adminUi';
import { adminTestIds as T } from '../../constants/testIds/admin';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from '../../components/ui/table';
import { Badge } from '../../components/ui/badge';

export default function AdminDashboardPage() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let on = true;
    (async () => {
      try {
        const d = await getDashboard();
        if (on) setData(d);
      } catch (e) {
        toast.error('Gagal memuat dashboard.');
      } finally {
        if (on) setLoading(false);
      }
    })();
    return () => { on = false; };
  }, []);

  const obs = data?.orders_by_status || {};

  return (
    <div data-testid={T.dashboard}>
      <PageHeader title="Dashboard" description="Ringkasan performa toko Collector Parfum." />

      {loading ? (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {Array.from({ length: 4 }).map((_, i) => <Card key={i}><CardContent className="p-5 h-24" /></Card>)}
        </div>
      ) : (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <MetricCard testId={T.metricRevenue} label="Pendapatan" accent
            value={formatIDR(data?.revenue || 0)} sub="Order dibayar/diproses" />
          <MetricCard testId={T.metricOrders} label="Total Pesanan"
            value={data?.total_orders ?? 0} sub={`${obs.pending || 0} menunggu diproses`} />
          <MetricCard testId={T.metricProducts} label="Produk Aktif"
            value={data?.active_products ?? 0} sub={`${data?.archived_products || 0} diarsipkan`} />
          <MetricCard testId={T.metricReviews} label="Ulasan Menunggu"
            value={data?.pending_reviews ?? 0} sub="Perlu moderasi" />
        </div>
      )}

      {/* Orders by status */}
      {!loading && (
        <div className="mt-4 flex flex-wrap gap-2">
          {Object.keys(ORDER_STATUS_META).map((s) => (
            <Badge key={s} variant="outline" className={`font-medium ${ORDER_STATUS_META[s].cls}`}>
              {ORDER_STATUS_META[s].label}: <span className="ml-1 font-[\'Azeret_Mono\',monospace]">{obs[s] || 0}</span>
            </Badge>
          ))}
        </div>
      )}

      <div className="grid lg:grid-cols-3 gap-4 mt-6">
        {/* Recent orders */}
        <Card className="lg:col-span-2 border-border/70">
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle className="text-base">Pesanan Terbaru</CardTitle>
            <Link to="/admin/pesanan" className="text-xs text-muted-foreground underline">Lihat semua</Link>
          </CardHeader>
          <CardContent>
            {loading ? <TableSkeleton rows={5} cols={4} /> : (
              (data?.recent || []).length === 0 ? <EmptyState title="Belum ada pesanan" /> : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Kode</TableHead>
                      <TableHead>Tanggal</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead className="text-right">Total</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {(data?.recent || []).map((o) => (
                      <TableRow key={o.code}>
                        <TableCell className="font-[\'Azeret_Mono\',monospace] text-xs">
                          <Link to={`/admin/pesanan/${o.code}`} className="underline">{o.code}</Link>
                        </TableCell>
                        <TableCell className="text-xs text-muted-foreground">{formatDateTime(o.created_at)}</TableCell>
                        <TableCell><StatusBadge status={o.status} /></TableCell>
                        <TableCell className="text-right font-[\'Azeret_Mono\',monospace] text-sm">{formatIDR(o.total || 0)}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )
            )}
          </CardContent>
        </Card>

        {/* Low stock */}
        <Card className="border-border/70">
          <CardHeader>
            <CardTitle className="text-base">Stok Menipis</CardTitle>
          </CardHeader>
          <CardContent>
            {loading ? <TableSkeleton rows={5} cols={2} /> : (
              (data?.low_stock || []).length === 0 ? (
                <EmptyState title="Stok aman" hint={`Ambang: ${data?.low_stock_threshold ?? 5}`} />
              ) : (
                <div className="space-y-2">
                  {(data?.low_stock || []).map((it, i) => (
                    <div key={i} className="flex items-center justify-between gap-2 text-sm">
                      <div className="min-w-0">
                        <div className="truncate">{it.name}</div>
                        <div className="text-[11px] text-muted-foreground font-[\'Azeret_Mono\',monospace]">{it.ml}ml</div>
                      </div>
                      <Badge variant="outline" className="bg-rose-50 text-rose-700 border-rose-200 font-[\'Azeret_Mono\',monospace]">
                        {it.stock}
                      </Badge>
                    </div>
                  ))}
                </div>
              )
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
