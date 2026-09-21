// components/shared/PaymentPanel.js — panel pembayaran pelanggan (Epic E6).
// Badge status bayar + timeline status pesanan + form unggah bukti (transfer/e-wallet) + daftar bukti.
import React, { useEffect, useState, useCallback, useRef } from 'react';
import { toast } from 'sonner';
import { Loader2, UploadCloud, CheckCircle2, Clock, XCircle } from 'lucide-react';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { SmartImage } from './SmartImage';
import { formatIDR } from '../../lib/format';
import { useAuth } from '../../store/AuthContext';
import {
  submitPaymentProof, fetchPaymentProofs, uploadPaymentProofImage,
  PAYMENT_STATUS_LABEL, PROOF_STATUS_LABEL, ORDER_STATUS_LABEL,
} from '../../services/orders';

const FLOW = ['pending', 'paid', 'packed', 'shipped', 'completed'];
const PS_CLS = {
  belum_bayar: 'bg-amber-100 text-amber-800',
  dp: 'bg-blue-100 text-blue-800',
  lunas: 'bg-emerald-100 text-emerald-800',
};
const PROOF_ICON = { pending: Clock, verified: CheckCircle2, rejected: XCircle };
const PROOF_CLS = { pending: 'text-amber-600', verified: 'text-emerald-600', rejected: 'text-rose-600' };

function Timeline({ status }) {
  if (status === 'cancelled') {
    return <div className="text-xs text-rose-600 font-medium">Pesanan dibatalkan.</div>;
  }
  const idx = FLOW.indexOf(status);
  return (
    <div className="flex items-center gap-1" data-testid="order-status-timeline">
      {FLOW.map((s, i) => (
        <React.Fragment key={s}>
          <div className="flex flex-col items-center">
            <div className={`h-2.5 w-2.5 rounded-full ${i <= idx ? 'bg-[color:var(--cp-market-blue)]' : 'bg-black/15'}`} />
            <span className={`mt-1 text-[9px] uppercase tracking-[0.08em] ${i <= idx ? 'text-black/70' : 'text-black/35'}`}>
              {ORDER_STATUS_LABEL[s].split(' ')[0]}
            </span>
          </div>
          {i < FLOW.length - 1 && <div className={`h-0.5 flex-1 ${i < idx ? 'bg-[color:var(--cp-market-blue)]' : 'bg-black/15'}`} />}
        </React.Fragment>
      ))}
    </div>
  );
}

export default function PaymentPanel({ order, onRefresh }) {
  const { isAuthenticated } = useAuth();
  const grp = order?.payment?.group;
  const isTransfer = grp === 'transfer' || grp === 'ewallet';
  const terminal = ['completed', 'cancelled'].includes(order?.status);
  const paid = Number(order?.paid_amount || 0);
  const remaining = Math.max(0, Number(order?.total || 0) - paid);
  const ps = order?.payment_status || 'belum_bayar';

  const [proofs, setProofs] = useState([]);
  const [amount, setAmount] = useState(remaining || order?.total || 0);
  const [ref, setRef] = useState('');
  const [imageUrl, setImageUrl] = useState('');
  const [uploadingProof, setUploadingProof] = useState(false);
  const [proofPct, setProofPct] = useState(0);
  const proofFileRef = useRef(null);
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(false);

  const uploadProof = async (file) => {
    if (!file) return;
    if (file.size > 15 * 1024 * 1024) {
      toast.error('Ukuran foto melebihi 15MB.');
      return;
    }
    setUploadingProof(true);
    setProofPct(0);
    try {
      const res = await uploadPaymentProofImage(order.code, file, setProofPct);
      setImageUrl(res.url);
      toast.success('Foto bukti terunggah.');
    } catch (err) {
      toast.error(err?.response?.data?.detail || 'Gagal mengunggah foto bukti.');
    } finally {
      setUploadingProof(false);
      setProofPct(0);
      if (proofFileRef.current) proofFileRef.current.value = '';
    }
  };

  const load = useCallback(async () => {
    if (!isAuthenticated || !isTransfer) return;
    setLoading(true);
    try { setProofs(await fetchPaymentProofs(order.code)); }
    catch (e) { /* guest / non-owner: abaikan */ }
    finally { setLoading(false); }
  }, [isAuthenticated, isTransfer, order?.code]);
  useEffect(() => { load(); }, [load]);
  useEffect(() => { setAmount(remaining || order?.total || 0); }, [remaining, order?.total]);

  const submit = async (e) => {
    e.preventDefault();
    if (!(Number(amount) > 0)) { toast.error('Jumlah harus lebih dari 0.'); return; }
    setBusy(true);
    try {
      await submitPaymentProof(order.code, { amount, ref, image_url: imageUrl });
      toast.success('Bukti pembayaran terkirim. Menunggu verifikasi admin.');
      setRef(''); setImageUrl('');
      await load();
      if (onRefresh) onRefresh();
    } catch (err) {
      toast.error(err?.response?.data?.detail || 'Gagal mengirim bukti.');
    } finally { setBusy(false); }
  };

  return (
    <div className="px-6 py-4 border-b border-black/10" data-testid="order-payment-panel">
      <div className="flex flex-wrap items-center justify-between gap-2 mb-3">
        <div className="cp-mono uppercase text-[10px] tracking-[0.22em] text-black/60">Status Pembayaran</div>
        <span className={`cp-mono text-[10px] uppercase tracking-[0.16em] px-2.5 py-1 rounded-full ${PS_CLS[ps] || 'bg-black/10 text-black/70'}`} data-testid="order-payment-status-badge">
          {PAYMENT_STATUS_LABEL[ps] || ps}
          {ps === 'dp' ? ` · ${formatIDR(paid)}/${formatIDR(order.total)}` : ''}
        </span>
      </div>

      <Timeline status={order.status} />

      {/* Form unggah bukti — transfer/e-wallet, belum lunas, belum final, wajib login */}
      {isTransfer && !terminal && ps !== 'lunas' && (
        isAuthenticated ? (
          <form onSubmit={submit} className="mt-4 rounded-xl border border-black/10 bg-white/60 p-4 space-y-3" data-testid="order-proof-form">
            <div className="text-sm font-semibold flex items-center gap-2"><UploadCloud className="h-4 w-4" /> Konfirmasi Pembayaran</div>
            <div className="grid sm:grid-cols-2 gap-2">
              <div>
                <label className="text-[11px] text-black/60">Jumlah Transfer</label>
                <Input type="number" value={amount} onChange={(e) => setAmount(e.target.value)} data-testid="order-proof-amount" />
              </div>
              <div>
                <label className="text-[11px] text-black/60">No. Referensi (opsional)</label>
                <Input value={ref} onChange={(e) => setRef(e.target.value)} placeholder="mis. TRX-98213" data-testid="order-proof-ref" />
              </div>
            </div>
            <div>
              <label className="text-[11px] text-black/60">Foto Bukti / Screenshot (opsional)</label>
              <div className="mt-1 flex flex-wrap items-center gap-2">
                <input
                  ref={proofFileRef}
                  type="file"
                  accept="image/*"
                  className="hidden"
                  onChange={(e) => uploadProof(e.target.files?.[0])}
                  data-testid="order-proof-file-input"
                />
                <Button
                  type="button"
                  variant="secondary"
                  className="rounded-full gap-2"
                  onClick={() => proofFileRef.current?.click()}
                  disabled={uploadingProof}
                  data-testid="order-proof-upload"
                >
                  {uploadingProof
                    ? <><Loader2 className="h-4 w-4 animate-spin" /> Mengunggah {proofPct}%</>
                    : <><UploadCloud className="h-4 w-4" /> Upload Foto Bukti</>}
                </Button>
                {imageUrl ? (
                  <span className="relative h-12 w-12 overflow-hidden rounded-lg border border-black/15">
                    <SmartImage
                      src={imageUrl}
                      alt="Pratinjau bukti bayar"
                      className="absolute inset-0 h-full w-full"
                      showRetry={false}
                      fallbackLabel=""
                    />
                  </span>
                ) : null}
                {imageUrl ? (
                  <button
                    type="button"
                    onClick={() => setImageUrl('')}
                    className="text-[11px] underline text-black/50"
                    data-testid="order-proof-image-clear"
                  >
                    Hapus foto
                  </button>
                ) : null}
              </div>
              <Input
                value={imageUrl}
                onChange={(e) => setImageUrl(e.target.value)}
                placeholder="atau tempel URL gambar bukti"
                className="mt-2"
                data-testid="order-proof-image"
              />
            </div>
            <Button type="submit" disabled={busy} className="rounded-full bg-[color:var(--cp-ink)] text-[color:var(--cp-paper)] hover:bg-black" data-testid="order-proof-submit">
              {busy ? <><Loader2 className="h-4 w-4 mr-2 animate-spin" /> Mengirim…</> : 'Kirim Bukti'}
            </Button>
          </form>
        ) : (
          <div className="mt-4 text-xs text-black/60">Masuk ke akun Anda untuk mengunggah bukti pembayaran, atau konfirmasi via WhatsApp.</div>
        )
      )}

      {/* Daftar bukti */}
      {isAuthenticated && isTransfer && (proofs.length > 0 || loading) && (
        <div className="mt-4">
          <div className="cp-mono uppercase text-[10px] tracking-[0.22em] text-black/60 mb-2">Riwayat Bukti</div>
          {loading ? (
            <div className="text-xs text-black/50 flex items-center gap-2"><Loader2 className="h-3.5 w-3.5 animate-spin" /> Memuat…</div>
          ) : (
            <div className="space-y-2" data-testid="order-proof-list">
              {proofs.map((p) => {
                const Icon = PROOF_ICON[p.status] || Clock;
                return (
                  <div key={p.id} className="flex items-center justify-between gap-3 text-sm rounded-lg border border-black/10 px-3 py-2">
                    <div className="flex items-center gap-2 min-w-0">
                      <Icon className={`h-4 w-4 ${PROOF_CLS[p.status] || 'text-black/50'}`} />
                      {p.image_url ? (
                        <a
                          href={p.image_url.startsWith('/') ? `${process.env.REACT_APP_BACKEND_URL || ''}${p.image_url}` : p.image_url}
                          target="_blank"
                          rel="noreferrer"
                          className="relative h-9 w-9 shrink-0 overflow-hidden rounded-md border border-black/15"
                          data-testid="order-proof-thumb"
                        >
                          <SmartImage
                            src={p.image_url}
                            alt="Bukti bayar"
                            className="absolute inset-0 h-full w-full"
                            showRetry={false}
                            fallbackLabel=""
                          />
                        </a>
                      ) : null}
                      <span className="cp-mono">{formatIDR(p.amount)}</span>
                      {p.ref ? <span className="text-xs text-black/50 truncate">· {p.ref}</span> : null}
                    </div>
                    <span className={`text-[11px] font-medium ${PROOF_CLS[p.status] || ''}`}>{PROOF_STATUS_LABEL[p.status] || p.status}</span>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
