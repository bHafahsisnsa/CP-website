// pages/admin/AdminPaymentsPage.js — Verifikasi bukti bayar (Epic E6).
import React, { useEffect, useState, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { toast } from 'sonner';
import { Check, X, Image as ImageIcon } from 'lucide-react';
import { listPaymentProofs, verifyPaymentProof } from '../../services/admin';
import { formatIDR } from '../../lib/format';
import { PROOF_STATUS_LABEL } from '../../services/orders';
import { PageHeader, TableSkeleton, EmptyState, formatDateTime } from '../../components/admin/adminUi';
import { adminTestIds as T } from '../../constants/testIds/admin';
import { Button } from '../../components/ui/button';
import { Badge } from '../../components/ui/badge';
import { Textarea } from '../../components/ui/textarea';
import { Card, CardContent } from '../../components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../../components/ui/table';
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from '../../components/ui/select';
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter,
} from '../../components/ui/dialog';

const PROOF_CLS = {
  pending: 'bg-amber-100 text-amber-800 border-amber-200',
  verified: 'bg-emerald-100 text-emerald-800 border-emerald-200',
  rejected: 'bg-rose-100 text-rose-800 border-rose-200',
};

export default function AdminPaymentsPage() {
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(true);
  const [status, setStatus] = useState('pending');
  const [busy, setBusy] = useState('');
  const [preview, setPreview] = useState(null);
  const [rejectFor, setRejectFor] = useState(null);
  const [note, setNote] = useState('');

  const load = useCallback(async () => {
    setLoading(true);
    try { setRows(await listPaymentProofs(status === 'all' ? '' : status) || []); }
    catch (e) { toast.error('Gagal memuat bukti bayar.'); }
    finally { setLoading(false); }
  }, [status]);
  useEffect(() => { load(); }, [load]);

  const approve = async (p) => {
    setBusy(p.id);
    try {
      const order = await verifyPaymentProof(p.id, true);
      toast.success(`Pembayaran diverifikasi — pesanan ${order.code} → ${order.payment_status}.`);
      load();
    } catch (e) { toast.error(e?.response?.data?.detail || 'Gagal memverifikasi.'); }
    finally { setBusy(''); }
  };
  const doReject = async () => {
    if (!rejectFor) return;
    setBusy(rejectFor.id);
    try {
      await verifyPaymentProof(rejectFor.id, false, note);
      toast.success('Bukti ditolak.');
      setRejectFor(null); setNote(''); load();
    } catch (e) { toast.error(e?.response?.data?.detail || 'Gagal menolak.'); }
    finally { setBusy(''); }
  };

  return (
    <div>
      <PageHeader title="Verifikasi Pembayaran" description="Tinjau bukti transfer/e-wallet lalu setujui atau tolak." />
      <Card className="border-border/70"><CardContent className="p-4">
        <div className="flex justify-end mb-4">
          <Select value={status} onValueChange={setStatus}>
            <SelectTrigger className="w-full sm:w-52" data-testid={T.paymentsStatusFilter}><SelectValue /></SelectTrigger>
            <SelectContent>
              <SelectItem value="pending">Menunggu Verifikasi</SelectItem>
              <SelectItem value="verified">Terverifikasi</SelectItem>
              <SelectItem value="rejected">Ditolak</SelectItem>
              <SelectItem value="all">Semua</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {loading ? <TableSkeleton rows={6} cols={5} /> : (
          rows.length === 0 ? <EmptyState title="Tidak ada bukti bayar" hint="Bukti dari pelanggan akan muncul di sini." /> : (
            <div className="overflow-x-auto">
              <Table data-testid={T.paymentsTable}>
                <TableHeader><TableRow>
                  <TableHead>Pesanan</TableHead><TableHead className="text-right">Jumlah</TableHead>
                  <TableHead>Referensi</TableHead><TableHead>Tanggal</TableHead>
                  <TableHead>Status</TableHead><TableHead className="text-right">Aksi</TableHead>
                </TableRow></TableHeader>
                <TableBody>
                  {rows.map((p) => (
                    <TableRow key={p.id}>
                      <TableCell className="font-['Azeret_Mono',monospace] text-xs">
                        <Link to={`/admin/pesanan/${p.order_code}`} className="underline">{p.order_code}</Link>
                      </TableCell>
                      <TableCell className="text-right font-['Azeret_Mono',monospace] text-sm">{formatIDR(p.amount)}</TableCell>
                      <TableCell className="text-sm text-muted-foreground">
                        <div className="flex items-center gap-2">
                          {p.ref || '—'}
                          {p.image_url ? (
                            <button type="button" onClick={() => setPreview(p)} className="text-muted-foreground hover:text-foreground" aria-label="Lihat bukti">
                              <ImageIcon className="h-4 w-4" />
                            </button>
                          ) : null}
                        </div>
                      </TableCell>
                      <TableCell className="text-xs text-muted-foreground">{formatDateTime(p.created_at)}</TableCell>
                      <TableCell><Badge variant="outline" className={PROOF_CLS[p.status]}>{PROOF_STATUS_LABEL[p.status] || p.status}</Badge></TableCell>
                      <TableCell className="text-right">
                        {p.status === 'pending' ? (
                          <div className="inline-flex gap-1">
                            <Button size="sm" disabled={busy === p.id} onClick={() => approve(p)} data-testid={T.paymentVerify} className="gap-1">
                              <Check className="h-3.5 w-3.5" /> Setujui
                            </Button>
                            <Button size="sm" variant="outline" disabled={busy === p.id} onClick={() => { setRejectFor(p); setNote(''); }} data-testid={T.paymentReject} className="gap-1 text-rose-600 border-rose-200">
                              <X className="h-3.5 w-3.5" /> Tolak
                            </Button>
                          </div>
                        ) : (
                          <span className="text-xs text-muted-foreground">{p.note || '—'}</span>
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )
        )}
      </CardContent></Card>

      {/* Preview bukti */}
      <Dialog open={!!preview} onOpenChange={(o) => !o && setPreview(null)}>
        <DialogContent>
          <DialogHeader><DialogTitle>Bukti Pembayaran — {preview?.order_code}</DialogTitle></DialogHeader>
          {preview?.image_url ? (
            <img src={preview.image_url} alt="Bukti pembayaran" className="w-full rounded-lg border border-border" />
          ) : <p className="text-sm text-muted-foreground">Tidak ada gambar.</p>}
        </DialogContent>
      </Dialog>

      {/* Dialog tolak + catatan */}
      <Dialog open={!!rejectFor} onOpenChange={(o) => !o && setRejectFor(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Tolak Bukti — {rejectFor?.order_code}</DialogTitle>
            <DialogDescription>
              Tulis alasan penolakan agar pembeli tahu apa yang perlu diperbaiki.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-2">
            <label className="text-sm text-muted-foreground">Catatan (alasan penolakan)</label>
            <Textarea rows={3} value={note} onChange={(e) => setNote(e.target.value)} placeholder="mis. nominal tidak sesuai" />
          </div>
          <DialogFooter>
            <Button variant="secondary" onClick={() => setRejectFor(null)}>Batal</Button>
            <Button className="bg-rose-600 hover:bg-rose-700" onClick={doReject}>Tolak Bukti</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
