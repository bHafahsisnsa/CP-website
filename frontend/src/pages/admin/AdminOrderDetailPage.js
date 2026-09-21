// pages/admin/AdminOrderDetailPage.js — detail + ubah status via transition (BR-6, INV-M3).
import React, { useEffect, useState, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { toast } from 'sonner';
import { ArrowLeft } from 'lucide-react';
import { getOrder, setOrderStatus } from '../../services/admin';
import { formatIDR } from '../../lib/format';
import {
  PageHeader, StatusBadge, formatDateTime, LEGAL_TRANSITIONS, ORDER_STATUS_META,
} from '../../components/admin/adminUi';
import { adminTestIds as T } from '../../constants/testIds/admin';
import { Button } from '../../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../../components/ui/table';
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from '../../components/ui/select';
import {
  AlertDialog, AlertDialogTrigger, AlertDialogContent, AlertDialogHeader, AlertDialogTitle,
  AlertDialogDescription, AlertDialogFooter, AlertDialogCancel, AlertDialogAction,
} from '../../components/ui/alert-dialog';

const Row = ({ label, value }) => (
  <div className="flex justify-between gap-4 text-sm py-1">
    <span className="text-muted-foreground">{label}</span><span className="text-right">{value}</span>
  </div>
);

export default function AdminOrderDetailPage() {
  const { code } = useParams();
  const navigate = useNavigate();
  const [order, setOrder] = useState(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try { setOrder(await getOrder(code)); }
    catch (e) { toast.error('Pesanan tidak ditemukan.'); navigate('/admin/pesanan'); }
    finally { setLoading(false); }
  }, [code, navigate]);
  useEffect(() => { load(); }, [load]);

  const change = async (to) => {
    setBusy(true);
    try { const updated = await setOrderStatus(code, to); setOrder(updated); toast.success(`Status → ${ORDER_STATUS_META[to]?.label || to}`); }
    catch (e) { toast.error(e?.response?.data?.detail || 'Transisi status tidak diizinkan.'); }
    finally { setBusy(false); }
  };

  if (loading) return <div className="h-64 grid place-items-center text-muted-foreground">Memuat pesanan…</div>;
  if (!order) return null;

  const allowed = LEGAL_TRANSITIONS[order.status] || [];
  const nextOptions = allowed.filter((s) => s !== 'cancelled');
  const canCancel = allowed.includes('cancelled');

  return (
    <div>
      <PageHeader
        title={`Pesanan ${order.code}`}
        description={formatDateTime(order.created_at)}
        actions={<Button variant="secondary" onClick={() => navigate('/admin/pesanan')} className="gap-2"><ArrowLeft className="h-4 w-4" /> Kembali</Button>}
      />

      <div className="grid lg:grid-cols-3 gap-6 items-start">
        <Card className="lg:col-span-2 border-border/70">
          <CardHeader><CardTitle className="text-base">Item</CardTitle></CardHeader>
          <CardContent>
            <Table>
              <TableHeader><TableRow>
                <TableHead>Produk</TableHead><TableHead>Varian</TableHead><TableHead className="text-center">Qty</TableHead>
                <TableHead className="text-right">Harga</TableHead><TableHead className="text-right">Subtotal</TableHead>
              </TableRow></TableHeader>
              <TableBody>
                {(order.items || []).map((it, i) => (
                  <TableRow key={i}>
                    <TableCell className="font-medium">{it.name}</TableCell>
                    <TableCell className="font-[\'Azeret_Mono\',monospace] text-xs">{(it.options && Object.values(it.options).filter(Boolean).join(' / ')) || `${it.variant_type ? `${it.variant_type} · ` : ''}${it.volume_ml}ml`}{it.sku ? ` · ${it.sku}` : ''}</TableCell>
                    <TableCell className="text-center">{it.quantity}</TableCell>
                    <TableCell className="text-right font-[\'Azeret_Mono\',monospace] text-sm">{formatIDR(it.unit_price || 0)}</TableCell>
                    <TableCell className="text-right font-[\'Azeret_Mono\',monospace] text-sm">{formatIDR((it.unit_price || 0) * (it.quantity || 0))}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
            <div className="mt-4 max-w-xs ml-auto">
              <Row label="Subtotal" value={formatIDR(order.subtotal || 0)} />
              <Row label="Ongkir" value={formatIDR(order.shipping_cost || 0)} />
              {order.discount ? <Row label="Diskon" value={`- ${formatIDR(order.discount)}`} /> : null}
              {order.cod_fee ? <Row label="Biaya COD" value={formatIDR(order.cod_fee)} /> : null}
              <div className="border-t border-border mt-1 pt-1 flex justify-between font-semibold">
                <span>Total</span><span className="font-[\'Azeret_Mono\',monospace]">{formatIDR(order.total || 0)}</span>
              </div>
            </div>
          </CardContent>
        </Card>

        <div className="space-y-6">
          <Card className="border-border/70">
            <CardHeader><CardTitle className="text-base">Status & Proses</CardTitle></CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center gap-2"><span className="text-sm text-muted-foreground">Saat ini:</span><StatusBadge status={order.status} /></div>
              <div className="text-xs text-muted-foreground">Pembayaran: {order.payment_status || '—'}</div>
              {nextOptions.length ? (
                <div className="space-y-1.5">
                  <span className="text-xs text-muted-foreground">Ubah status ke</span>
                  <Select onValueChange={change} disabled={busy}>
                    <SelectTrigger data-testid={T.orderStatusSelect}><SelectValue placeholder="Pilih status berikutnya" /></SelectTrigger>
                    <SelectContent>
                      {nextOptions.map((s) => <SelectItem key={s} value={s}>{ORDER_STATUS_META[s]?.label || s}</SelectItem>)}
                    </SelectContent>
                  </Select>
                </div>
              ) : <p className="text-sm text-muted-foreground">Status final — tidak ada transisi lanjutan.</p>}

              {canCancel ? (
                <AlertDialog>
                  <AlertDialogTrigger asChild>
                    <Button variant="outline" className="w-full text-rose-600 border-rose-200" data-testid={T.orderCancel} disabled={busy}>Batalkan Pesanan</Button>
                  </AlertDialogTrigger>
                  <AlertDialogContent>
                    <AlertDialogHeader>
                      <AlertDialogTitle>Batalkan pesanan ini?</AlertDialogTitle>
                      <AlertDialogDescription>Stok akan dikembalikan otomatis. Tindakan ini tidak dapat diurungkan.</AlertDialogDescription>
                    </AlertDialogHeader>
                    <AlertDialogFooter>
                      <AlertDialogCancel>Tidak</AlertDialogCancel>
                      <AlertDialogAction onClick={() => change('cancelled')} className="bg-rose-600 hover:bg-rose-700">Ya, Batalkan</AlertDialogAction>
                    </AlertDialogFooter>
                  </AlertDialogContent>
                </AlertDialog>
              ) : null}
            </CardContent>
          </Card>

          <Card className="border-border/70">
            <CardHeader><CardTitle className="text-base">Pengiriman</CardTitle></CardHeader>
            <CardContent className="text-sm space-y-1">
              <div className="font-medium">{order.address?.name}</div>
              <div className="text-muted-foreground">{order.address?.phone}</div>
              <div className="text-muted-foreground">{order.address?.street}, {order.address?.city}, {order.address?.province} {order.address?.postal}</div>
              <div className="pt-2 text-xs">Kurir: {order.shipping?.name || order.shipping_id || '—'}</div>
              <div className="text-xs">Bayar: {order.payment?.name || order.payment?.method_id || '—'}</div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
