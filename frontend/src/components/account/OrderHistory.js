import React from 'react';
import { Link } from 'react-router-dom';
import { Loader2, XCircle, RefreshCw } from 'lucide-react';
import { fetchOrders, cancelOrder, ORDER_STATUS_LABEL, PAYMENT_STATUS_LABEL, CANCELLABLE } from '../../services/orders';
import { formatIDR } from '../../lib/format';
import { toast } from 'sonner';

const STATUS_CLASS = {
  pending: 'bg-amber-100 text-amber-700',
  paid: 'bg-blue-100 text-blue-700',
  packed: 'bg-indigo-100 text-indigo-700',
  shipped: 'bg-violet-100 text-violet-700',
  completed: 'bg-emerald-100 text-emerald-700',
  cancelled: 'bg-red-100 text-red-600',
};

function OrderCard({ order, onCancel, cancelling }) {
  return (
    <div className="py-4 border-b border-black/10 last:border-0" data-testid="account-order-card">
      <div className="flex flex-wrap items-center gap-4">
        <div className="flex -space-x-3">
          {order.items.slice(0, 3).map((it) => (
            <div key={it.key} className="h-10 w-10 rounded-lg overflow-hidden border-2 border-[color:var(--cp-paper-warm)] bg-[color:var(--cp-paper-fog)]">
              <img src={it.image} alt={it.name} className="h-full w-full object-cover" />
            </div>
          ))}
        </div>
        <div className="flex-1 min-w-0">
          <div className="cp-mono font-semibold" data-testid="account-order-code">{order.code}</div>
          <div className="cp-mono uppercase text-[10px] tracking-[0.22em] text-black/55">
            {order.items.length} item · {new Date(order.created_at).toLocaleDateString('id-ID', { day: '2-digit', month: 'short', year: 'numeric' })}
          </div>
        </div>
        <div className="flex flex-col items-end gap-1">
          <span className={`cp-mono uppercase text-[10px] tracking-[0.2em] px-2 py-0.5 rounded-full ${STATUS_CLASS[order.status] || 'bg-black/10'}`} data-testid="account-order-status">
            {ORDER_STATUS_LABEL[order.status] || order.status}
          </span>
          <div className="cp-mono font-semibold text-sm">{formatIDR(order.total)}</div>
          <div className="cp-mono text-[10px] text-black/50">{PAYMENT_STATUS_LABEL[order.payment_status] || order.payment_status}</div>
        </div>
      </div>
      <div className="flex items-center gap-2 mt-3 pl-1">
        <Link to={`/pesanan-sukses?code=${encodeURIComponent(order.code)}`} className="cp-mono uppercase text-[10px] tracking-[0.22em] text-[color:var(--cp-market-blue)] hover:underline">Lihat detail</Link>
        {CANCELLABLE.has(order.status) && (
          <button onClick={() => onCancel(order.code)} disabled={cancelling === order.code}
            className="ml-auto inline-flex items-center gap-1 cp-mono uppercase text-[10px] tracking-[0.22em] text-red-600 hover:underline disabled:opacity-50" data-testid="account-order-cancel-button">
            {cancelling === order.code ? <Loader2 className="h-3 w-3 animate-spin" /> : <XCircle className="h-3.5 w-3.5" />} Batalkan
          </button>
        )}
      </div>
    </div>
  );
}

export default function OrderHistory() {
  const [orders, setOrders] = React.useState([]);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState(null);
  const [cancelling, setCancelling] = React.useState(null);

  const load = React.useCallback(async () => {
    setLoading(true);
    setError(null);
    try { setOrders(await fetchOrders()); }
    catch (e) { setError('Gagal memuat pesanan.'); }
    finally { setLoading(false); }
  }, []);

  React.useEffect(() => { load(); }, [load]);

  const handleCancel = async (code) => {
    setCancelling(code);
    try {
      await cancelOrder(code);
      toast.success('Pesanan dibatalkan', { description: `${code} — stok dikembalikan` });
      await load();
    } catch (e) {
      toast.error(e?.response?.data?.detail || 'Gagal membatalkan pesanan');
    } finally { setCancelling(null); }
  };

  return (
    <div className="rounded-2xl border border-black/10 bg-[color:var(--cp-paper-warm)] p-6" data-testid="account-orders-card">
      <div className="flex items-center justify-between mb-4">
        <div className="cp-mono uppercase text-[11px] tracking-[0.22em]">Riwayat Pesanan</div>
        <button onClick={load} className="inline-flex items-center gap-1 text-xs text-black/50 hover:text-black" data-testid="account-orders-refresh">
          <RefreshCw className="h-3.5 w-3.5" /> Segarkan
        </button>
      </div>
      {loading ? (
        <div className="py-10 flex items-center justify-center text-black/50"><Loader2 className="h-5 w-5 animate-spin mr-2" /> Memuat pesanan…</div>
      ) : error ? (
        <div className="py-10 text-center text-sm text-red-600">{error} <button onClick={load} className="underline">Coba lagi</button></div>
      ) : orders.length === 0 ? (
        <div className="py-10 text-center text-sm text-black/60" data-testid="account-orders-empty">Belum ada pesanan. <Link to="/shop" className="underline">Mulai belanja</Link>.</div>
      ) : (
        <div>{orders.map((o) => <OrderCard key={o.code} order={o} onCancel={handleCancel} cancelling={cancelling} />)}</div>
      )}
    </div>
  );
}
