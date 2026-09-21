import React from 'react';
import { Tag, Truck, Percent, BadgePercent, Check, Loader2, Clock } from 'lucide-react';
import { Button } from '../ui/button';
import { Skeleton } from '../ui/skeleton';
import { fetchVouchers, voucherValueLabel } from '../../services/vouchers';
import { formatIDR } from '../../lib/format';

// Aksen kampanye -> token warna CP (fallback aman).
const THEME = {
  champagne: 'var(--cp-brass)',
  brass: 'var(--cp-brass)',
  'market-blue': 'var(--cp-market-blue)',
  amber: '#b07b3f',
};

const TypeIcon = ({ type }) => {
  if (type === 'free_shipping') return <Truck className="h-4 w-4" />;
  if (type === 'percent') return <Percent className="h-4 w-4" />;
  return <BadgePercent className="h-4 w-4" />;
};

const daysLeft = (iso) => {
  if (!iso) return null;
  const end = new Date(iso).getTime();
  if (Number.isNaN(end)) return null;
  const diff = Math.ceil((end - Date.now()) / (1000 * 60 * 60 * 24));
  return diff > 0 ? diff : null;
};

// Voucher Center — grid kartu voucher publik. Diskon aktual saat "Pakai" dihitung server.
export const VoucherCenter = ({ subtotal = 0, appliedCode = null, onApply, applyingCode = null }) => {
  const [vouchers, setVouchers] = React.useState([]);
  const [state, setState] = React.useState('loading'); // loading | ready | empty | error

  const loadList = React.useCallback(async () => {
    setState('loading');
    try {
      const list = await fetchVouchers();
      setVouchers(list);
      setState(list.length ? 'ready' : 'empty');
    } catch (e) {
      setState('error');
    }
  }, []);

  React.useEffect(() => {
    loadList();
  }, [loadList]);

  if (state === 'loading') {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3" data-testid="voucher-center-loading">
        {[0, 1, 2, 3].map((i) => (
          <Skeleton key={i} className="h-28 rounded-2xl" />
        ))}
      </div>
    );
  }

  if (state === 'error') {
    return (
      <div className="rounded-2xl border border-black/10 bg-white p-6 text-center">
        <div className="text-sm text-black/60 mb-3">Gagal memuat voucher.</div>
        <Button variant="outline" className="rounded-full" onClick={loadList} data-testid="voucher-center-retry">
          Coba lagi
        </Button>
      </div>
    );
  }

  if (state === 'empty') {
    return (
      <div className="rounded-2xl border border-dashed border-black/15 bg-white p-6 text-center text-sm text-black/55" data-testid="voucher-center-empty">
        Belum ada voucher aktif.
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3" data-testid="voucher-center-list">
      {vouchers.map((v) => {
        const accent = THEME[v.campaign?.theme] || 'var(--cp-ink)';
        const eligible = subtotal >= (v.min_spend || 0);
        const isApplied = appliedCode && appliedCode.toUpperCase() === v.code.toUpperCase();
        const isApplying = applyingCode && applyingCode.toUpperCase() === v.code.toUpperCase();
        const dLeft = daysLeft(v.ends_at);
        return (
          <div
            key={v.code}
            data-testid="voucher-card"
            className={`relative rounded-2xl border bg-white overflow-hidden transition-shadow ${
              eligible ? 'border-black/12 hover:shadow-md' : 'border-black/10 opacity-70'
            }`}
          >
            <div className="absolute left-0 top-0 h-full w-1.5" style={{ background: accent }} />
            <div className="p-4 pl-5">
              <div className="flex items-start justify-between gap-2">
                <div className="min-w-0">
                  <div
                    className="inline-flex items-center gap-1.5 cp-mono uppercase text-[10px] tracking-[0.2em] px-2 py-0.5 rounded-full"
                    style={{ background: 'var(--cp-paper-fog)', color: accent }}
                  >
                    <TypeIcon type={v.type} /> {voucherValueLabel(v)}
                  </div>
                  <div className="mt-2 text-sm font-semibold leading-snug truncate">{v.label || v.code}</div>
                  <div className="cp-mono uppercase text-[10px] tracking-[0.2em] text-black/55 mt-1">
                    Kode: {v.code}
                  </div>
                </div>
              </div>

              <div className="mt-3 flex items-center justify-between gap-2">
                <div className="min-w-0">
                  {v.min_spend > 0 ? (
                    eligible ? (
                      <div className="text-[11px] text-black/50">Min. belanja {formatIDR(v.min_spend)}</div>
                    ) : (
                      <div className="text-[11px] text-[color:var(--cp-market-blue)]" data-testid="voucher-card-ineligible-reason">
                        Min. belanja {formatIDR(v.min_spend)}
                      </div>
                    )
                  ) : (
                    <div className="text-[11px] text-black/45">Tanpa min. belanja</div>
                  )}
                  {dLeft !== null && (
                    <div className="mt-1 inline-flex items-center gap-1 cp-mono text-[10px] tracking-[0.15em] text-black/50">
                      <Clock className="h-3 w-3" /> {dLeft} hari lagi
                    </div>
                  )}
                </div>
                <Button
                  size="sm"
                  disabled={!eligible || isApplied || isApplying}
                  onClick={() => onApply && onApply(v.code)}
                  data-testid="voucher-card-apply-button"
                  className="rounded-full h-9 px-4 bg-[color:var(--cp-ink)] text-[color:var(--cp-paper)] hover:bg-black disabled:opacity-50"
                >
                  {isApplying ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : isApplied ? (
                    <>
                      <Check className="h-3.5 w-3.5 mr-1" /> Terpakai
                    </>
                  ) : (
                    <>
                      <Tag className="h-3.5 w-3.5 mr-1" /> Pakai
                    </>
                  )}
                </Button>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
};

export default VoucherCenter;
