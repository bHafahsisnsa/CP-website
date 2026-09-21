// pages/admin/AdminAnalyticsPage.js — Dashboard analitik first-party (Epic E7).
// Funnel (page_view→purchase), konversi, & produk paling dilihat. READ-only.
import React, { useCallback, useEffect, useState } from 'react';
import { RefreshCw, TrendingUp, Eye, ShoppingCart } from 'lucide-react';
import { getAnalytics } from '../../services/admin';
import { PageHeader, EmptyState } from '../../components/admin/adminUi';
import { growthTestIds as G } from '../../constants/testIds/growth';
import { Button } from '../../components/ui/button';
import { Card, CardContent } from '../../components/ui/card';
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from '../../components/ui/select';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../../components/ui/table';

const STEP_LABEL = {
  page_view: 'Kunjungan Halaman',
  product_view: 'Lihat Produk',
  add_to_cart: 'Tambah ke Keranjang',
  begin_checkout: 'Mulai Checkout',
  purchase: 'Pembelian',
};
const BAR_COLORS = ['#7c6a58', '#8f7d68', '#a8927a', '#c1ab90', '#5f7d3a'];

const Stat = ({ icon: Icon, label, value, sub }) => (
  <Card className="border-border/70"><CardContent className="p-5">
    <div className="flex items-center gap-2 text-muted-foreground text-xs uppercase tracking-[0.14em]">
      <Icon className="h-4 w-4" /> {label}
    </div>
    <div className="mt-2 text-3xl font-semibold">{value}</div>
    {sub ? <div className="mt-1 text-xs text-muted-foreground">{sub}</div> : null}
  </CardContent></Card>
);

export default function AdminAnalyticsPage() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [range, setRange] = useState('30');

  const load = useCallback(async () => {
    setLoading(true);
    try {
      setData(await getAnalytics(Number(range)));
    } catch (e) {
      setData(null);
    } finally {
      setLoading(false);
    }
  }, [range]);
  useEffect(() => { load(); }, [load]);

  const funnel = data?.funnel || [];
  const maxCount = Math.max(1, ...funnel.map((f) => f.count));
  const totals = data?.totals || { events: 0, orders: 0 };
  const top = data?.top_products || [];

  return (
    <div data-testid={G.analyticsPage}>
      <PageHeader title="Analitik" description="Funnel first-party, konversi, dan produk terpopuler." />

      <div className="flex items-center justify-between gap-3 mb-5">
        <Select value={range} onValueChange={setRange}>
          <SelectTrigger className="w-44" data-testid={G.analyticsRange}><SelectValue /></SelectTrigger>
          <SelectContent>
            <SelectItem value="7">7 hari terakhir</SelectItem>
            <SelectItem value="30">30 hari terakhir</SelectItem>
            <SelectItem value="90">90 hari terakhir</SelectItem>
          </SelectContent>
        </Select>
        <Button variant="outline" onClick={load} className="gap-2" data-testid={G.analyticsRefresh}>
          <RefreshCw className="h-4 w-4" /> Segarkan
        </Button>
      </div>

      <div className="grid sm:grid-cols-3 gap-4 mb-6" data-testid={G.analyticsConversion}>
        <Stat icon={TrendingUp} label="Konversi" value={`${data?.conversion_rate ?? 0}%`} sub="purchase / mulai checkout" />
        <Stat icon={Eye} label="Total Event" value={totals.events} sub={`${range} hari`} />
        <Stat icon={ShoppingCart} label="Total Pesanan" value={totals.orders} sub="seluruh waktu" />
      </div>

      <Card className="border-border/70 mb-6"><CardContent className="p-5">
        <div className="text-sm font-semibold mb-4">Funnel Konversi</div>
        {loading ? (
          <div className="py-6 text-sm text-muted-foreground">Memuat…</div>
        ) : (
          <div className="space-y-3" data-testid={G.analyticsFunnel}>
            {funnel.map((f, i) => (
              <div key={f.step}>
                <div className="flex justify-between text-sm mb-1">
                  <span>{STEP_LABEL[f.step] || f.step}</span>
                  <span className="font-['Azeret_Mono',monospace] text-xs text-muted-foreground">{f.count}</span>
                </div>
                <div className="h-3 rounded-full bg-muted overflow-hidden">
                  <div
                    className="h-full rounded-full transition-all"
                    style={{ width: `${Math.max(3, (f.count / maxCount) * 100)}%`, backgroundColor: BAR_COLORS[i % 5] }}
                  />
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent></Card>

      <Card className="border-border/70"><CardContent className="p-5">
        <div className="text-sm font-semibold mb-4">Produk Paling Dilihat</div>
        {top.length === 0 ? (
          <EmptyState title="Belum ada data produk" hint="Event akan muncul saat pengunjung menjelajah toko." />
        ) : (
          <Table data-testid={G.analyticsTopProducts}>
            <TableHeader><TableRow>
              <TableHead>Produk</TableHead>
              <TableHead className="text-right">Dilihat</TableHead>
              <TableHead className="text-right">Ditambah ke Keranjang</TableHead>
            </TableRow></TableHeader>
            <TableBody>
              {top.map((p) => (
                <TableRow key={p.product_id}>
                  <TableCell className="font-medium">{p.name}</TableCell>
                  <TableCell className="text-right font-['Azeret_Mono',monospace] text-sm">{p.views}</TableCell>
                  <TableCell className="text-right font-['Azeret_Mono',monospace] text-sm">{p.carts}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </CardContent></Card>
    </div>
  );
}
