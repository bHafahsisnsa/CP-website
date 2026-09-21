// components/admin/adminUi.js — helper & atom UI bersama Admin (Epic E5). Token serasi storefront.
import React from 'react';
import { Badge } from '../ui/badge';
import { Card, CardContent } from '../ui/card';
import { Skeleton } from '../ui/skeleton';

export const ACCENT = '#B89B6A'; // brass
export const ACCENT_SOFT = 'rgba(184,155,106,0.12)';

// SSOT transisi status order (mirror backend services/orders.LEGAL_TRANSITIONS).
export const LEGAL_TRANSITIONS = {
  pending: ['paid', 'cancelled'],
  paid: ['packed', 'cancelled'],
  packed: ['shipped', 'cancelled'],
  shipped: ['completed'],
  completed: [],
  cancelled: [],
};
export const ORDER_STATUSES = ['pending', 'paid', 'packed', 'shipped', 'completed', 'cancelled'];

export const ORDER_STATUS_META = {
  pending: { label: 'Menunggu', cls: 'bg-amber-100 text-amber-800 border-amber-200' },
  paid: { label: 'Dibayar', cls: 'bg-blue-100 text-blue-800 border-blue-200' },
  packed: { label: 'Dikemas', cls: 'bg-indigo-100 text-indigo-800 border-indigo-200' },
  shipped: { label: 'Dikirim', cls: 'bg-violet-100 text-violet-800 border-violet-200' },
  completed: { label: 'Selesai', cls: 'bg-emerald-100 text-emerald-800 border-emerald-200' },
  cancelled: { label: 'Dibatalkan', cls: 'bg-rose-100 text-rose-800 border-rose-200' },
};
export const REVIEW_STATUS_META = {
  published: { label: 'Tayang', cls: 'bg-emerald-100 text-emerald-800 border-emerald-200' },
  pending: { label: 'Menunggu', cls: 'bg-amber-100 text-amber-800 border-amber-200' },
  hidden: { label: 'Disembunyikan', cls: 'bg-zinc-100 text-zinc-700 border-zinc-200' },
};

export const formatDateTime = (iso) => {
  if (!iso) return '—';
  try {
    return new Date(iso).toLocaleString('id-ID', {
      day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit',
    });
  } catch (e) {
    return String(iso);
  }
};

export const StatusBadge = ({ status }) => {
  const m = ORDER_STATUS_META[status] || { label: status, cls: 'bg-zinc-100 text-zinc-700 border-zinc-200' };
  return <Badge variant="outline" className={`font-medium ${m.cls}`}>{m.label}</Badge>;
};

export const ReviewBadge = ({ status }) => {
  const m = REVIEW_STATUS_META[status] || { label: status, cls: 'bg-zinc-100 text-zinc-700 border-zinc-200' };
  return <Badge variant="outline" className={`font-medium ${m.cls}`}>{m.label}</Badge>;
};

export const PageHeader = ({ title, description, actions, testId }) => (
  <div className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-3 mb-6" data-testid={testId}>
    <div>
      <h1 className="font-[\'DM_Serif_Display\',serif] text-2xl sm:text-3xl text-foreground leading-tight">{title}</h1>
      {description ? <p className="text-sm text-muted-foreground mt-1">{description}</p> : null}
    </div>
    {actions ? <div className="flex items-center gap-2">{actions}</div> : null}
  </div>
);

export const MetricCard = ({ label, value, sub, testId, accent }) => (
  <Card className="border-border/70" data-testid={testId}>
    <CardContent className="p-5">
      <div className="text-[11px] uppercase tracking-[0.14em] text-muted-foreground">{label}</div>
      <div
        className="mt-2 font-[\'Azeret_Mono\',monospace] text-2xl font-semibold text-foreground"
        style={accent ? { color: ACCENT } : undefined}
      >
        {value}
      </div>
      {sub ? <div className="mt-1 text-xs text-muted-foreground">{sub}</div> : null}
    </CardContent>
  </Card>
);

export const EmptyState = ({ title = 'Belum ada data', hint, action }) => (
  <div className="flex flex-col items-center justify-center text-center py-16 px-4">
    <div className="h-12 w-12 rounded-full border border-dashed border-border mb-3" />
    <p className="text-sm font-medium text-foreground">{title}</p>
    {hint ? <p className="text-xs text-muted-foreground mt-1 max-w-sm">{hint}</p> : null}
    {action ? <div className="mt-4">{action}</div> : null}
  </div>
);

export const TableSkeleton = ({ rows = 5, cols = 4 }) => (
  <div className="space-y-2">
    {Array.from({ length: rows }).map((_, r) => (
      <div key={r} className="flex gap-3">
        {Array.from({ length: cols }).map((_, c) => (
          <Skeleton key={c} className="h-9 flex-1" />
        ))}
      </div>
    ))}
  </div>
);
