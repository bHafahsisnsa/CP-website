import React from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { motion } from 'framer-motion';
import { CheckCircle2, ArrowRight, MapPin, Truck, Loader2, Copy, Landmark, Wallet, Banknote } from 'lucide-react';
import { Button } from '../components/ui/button';
import { formatIDR } from '../lib/format';
import { fetchOrder, ORDER_STATUS_LABEL } from '../services/orders';
import PaymentPanel from '../components/shared/PaymentPanel';
import { track } from '../services/analytics';
import { toast } from 'sonner';

function PaymentInstructions({ order }) {
  const grp = order?.payment?.group;
  if (!grp) return null;
  const name = order.payment?.name || '';
  const content = {
    transfer: {
      icon: Landmark,
      title: 'Instruksi Pembayaran — Transfer',
      body: `Silakan transfer sebesar ${formatIDR(order.total)} ke rekening ${name || 'bank kami'}. Setelah transfer, konfirmasi via WhatsApp agar pesanan diproses.`,
    },
    ewallet: {
      icon: Wallet,
      title: 'Instruksi Pembayaran — E-Wallet',
      body: `Lakukan pembayaran ${formatIDR(order.total)} melalui ${name || 'e-wallet'} ke nomor merchant kami, lalu konfirmasi.`,
    },
    cod: {
      icon: Banknote,
      title: 'Bayar di Tempat (COD)',
      body: `Siapkan uang tunai sebesar ${formatIDR(order.total)} (termasuk biaya COD) saat kurir tiba.`,
    },
  }[grp];
  if (!content) return null;
  const Icon = content.icon;
  return (
    <div className="px-6 py-4 border-b border-black/10 bg-[color:var(--cp-market-blue-soft)]/40" data-testid="order-payment-instructions">
      <div className="flex items-start gap-3">
        <Icon className="h-4 w-4 text-[color:var(--cp-market-blue)] mt-0.5" />
        <div>
          <div className="text-sm font-semibold">{content.title}</div>
          <div className="text-xs text-black/70 mt-1 leading-relaxed">{content.body}</div>
        </div>
      </div>
    </div>
  );
}

export default function OrderSuccessPage() {
  const [params] = useSearchParams();
  const code = params.get('code') || (() => { try { return localStorage.getItem('cp:lastOrderCode'); } catch (e) { return null; } })();
  const [order, setOrder] = React.useState(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState(null);
  const purchaseTracked = React.useRef(false);

  const reload = React.useCallback(async () => {
    if (!code) return;
    try { setOrder(await fetchOrder(code)); } catch (e) { /* keep current */ }
  }, [code]);

  React.useEffect(() => {
    window.scrollTo({ top: 0 });
    if (code) { try { localStorage.setItem('cp:lastOrderCode', code); } catch (e) {} }
    let active = true;
    (async () => {
      if (!code) { setLoading(false); setError('notfound'); return; }
      try {
        const o = await fetchOrder(code);
        if (active) {
          setOrder(o);
          // Analytics first-party (E7): event purchase sekali, dgn order_code nyata (INV-G1).
          if (!purchaseTracked.current) {
            purchaseTracked.current = true;
            track('purchase', { order_code: o.code, meta: { value: o.total } });
          }
        }
      } catch (e) {
        if (active) setError('notfound');
      } finally {
        if (active) setLoading(false);
      }
    })();
    return () => { active = false; };
  }, [code]);

  const copyCode = () => {
    try { navigator.clipboard.writeText(order.code); toast.success('Nomor pesanan disalin'); } catch (e) {}
  };

  return (
    <div className="cp-container cp-section" data-testid="order-success-page">
      <div className="max-w-2xl mx-auto">
        <motion.div initial={{ scale: 0.8, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }} className="flex items-center justify-center">
          <div className="h-20 w-20 rounded-full bg-[color:var(--cp-market-blue-soft)] flex items-center justify-center">
            <CheckCircle2 className="h-10 w-10 text-[color:var(--cp-market-blue)]" />
          </div>
        </motion.div>

        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.15, duration: 0.6 }} className="text-center mt-6">
          <div className="cp-mono uppercase text-[11px] tracking-[0.22em] text-black/60">Pesanan Berhasil</div>
          <h1 className="cp-headline text-4xl sm:text-5xl mt-2">Terima kasih!</h1>
          <p className="text-sm sm:text-base text-black/70 mt-3 max-w-md mx-auto">
            Pesanan Anda sudah kami terima. Kami akan segera memproses & mengirimkan konfirmasi ke WhatsApp / email Anda.
          </p>
        </motion.div>

        {loading && (
          <div className="mt-10 flex items-center justify-center py-10 text-black/50">
            <Loader2 className="h-5 w-5 animate-spin mr-2" /> Memuat pesanan…
          </div>
        )}

        {!loading && error && (
          <div className="mt-10 rounded-2xl border border-black/10 bg-[color:var(--cp-paper-warm)] p-8 text-center" data-testid="order-success-notfound">
            <div className="text-sm text-black/70">Detail pesanan tidak dapat ditampilkan. Simpan nomor pesanan Anda untuk pengecekan.</div>
            {code && <div className="cp-mono text-lg font-semibold mt-2" data-testid="order-success-code">{code}</div>}
          </div>
        )}

        {!loading && order && (
          <div className="mt-10 rounded-2xl border border-black/10 bg-[color:var(--cp-paper-warm)] overflow-hidden">
            <div className="px-6 py-4 border-b border-black/10 flex flex-wrap items-center justify-between gap-3">
              <div>
                <div className="cp-mono uppercase text-[10px] tracking-[0.22em] text-black/60">Nomor Pesanan</div>
                <button onClick={copyCode} className="cp-mono text-lg font-semibold inline-flex items-center gap-2 hover:text-[color:var(--cp-market-blue)]" data-testid="order-success-code">
                  {order.code} <Copy className="h-3.5 w-3.5 opacity-60" />
                </button>
                <div className="mt-1">
                  <span className="cp-mono uppercase text-[10px] tracking-[0.2em] bg-[color:var(--cp-paper-fog)] px-2 py-0.5 rounded-full" data-testid="order-success-status">
                    {ORDER_STATUS_LABEL[order.status] || order.status}
                  </span>
                </div>
              </div>
              <div className="text-right">
                <div className="cp-mono uppercase text-[10px] tracking-[0.22em] text-black/60">Total Dibayar</div>
                <div className="cp-mono text-lg font-semibold" data-testid="order-success-total">{formatIDR(order.total)}</div>
              </div>
            </div>

            <PaymentInstructions order={order} />

            <PaymentPanel order={order} onRefresh={reload} />

            <div className="px-6 py-4 border-b border-black/10 grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="flex items-start gap-2">
                <MapPin className="h-4 w-4 text-black/60 mt-0.5" />
                <div>
                  <div className="cp-mono uppercase text-[10px] tracking-[0.22em] text-black/60">Dikirim Ke</div>
                  <div className="text-sm font-medium">{order.address?.name}</div>
                  <div className="text-xs text-black/70">{order.address?.street}, {order.address?.city}</div>
                </div>
              </div>
              <div className="flex items-start gap-2">
                <Truck className="h-4 w-4 text-black/60 mt-0.5" />
                <div>
                  <div className="cp-mono uppercase text-[10px] tracking-[0.22em] text-black/60">Metode Kirim</div>
                  <div className="text-sm font-medium">{order.shipping?.name}</div>
                  <div className="text-xs text-black/70">Estimasi {order.shipping?.eta}</div>
                </div>
              </div>
            </div>

            <div className="px-6 py-4">
              <div className="cp-mono uppercase text-[10px] tracking-[0.22em] text-black/60 mb-3">Ringkasan Item</div>
              <div className="space-y-3">
                {order.items.map((it) => (
                  <div key={it.key} className="flex items-center gap-3">
                    <div className="h-12 w-10 rounded-md overflow-hidden bg-[color:var(--cp-paper-fog)] flex-shrink-0">
                      <img src={it.image} alt={it.name} className="h-full w-full object-cover" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="text-sm truncate">{it.name}</div>
                      <div className="cp-mono text-[10px] uppercase tracking-[0.22em] text-black/55">{it.variantLabel || `${it.concentration ? it.concentration + ' · ' : ''}${it.variantType ? it.variantType + ' · ' : ''}${it.volumeMl}ml`} · x{it.quantity}</div>
                    </div>
                    <div className="cp-mono text-sm">{formatIDR(it.unitPrice * it.quantity)}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        <div className="mt-8 flex flex-wrap items-center justify-center gap-3">
          <Link to="/akun">
            <Button variant="outline" className="rounded-full" data-testid="order-success-view-orders">Lihat Pesanan Saya</Button>
          </Link>
          <Link to="/shop">
            <Button className="rounded-full bg-[color:var(--cp-ink)] text-[color:var(--cp-paper)] hover:bg-black" data-testid="order-success-continue-shopping">
              Lanjut Belanja <ArrowRight className="h-4 w-4 ml-2" />
            </Button>
          </Link>
        </div>
      </div>
    </div>
  );
}
