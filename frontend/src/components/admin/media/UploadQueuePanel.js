// components/admin/media/UploadQueuePanel.js — antrean upload + progress per berkas (E20).
import React from 'react';
import { AlertCircle, CheckCircle2, Loader2, RefreshCw, X } from 'lucide-react';
import { Badge } from '../../ui/badge';
import { Button } from '../../ui/button';
import { Progress } from '../../ui/progress';
import { formatBytes } from '../../../lib/mediaUrl';
import { adminTestIds as T } from '../../../constants/testIds/admin';

const STATUS = {
  queued: { label: 'Menunggu', cls: 'bg-zinc-100 text-zinc-700 border-zinc-200' },
  uploading: { label: 'Mengunggah', cls: 'bg-blue-100 text-blue-800 border-blue-200' },
  done: { label: 'Selesai', cls: 'bg-emerald-100 text-emerald-800 border-emerald-200' },
  error: { label: 'Gagal', cls: 'bg-rose-100 text-rose-800 border-rose-200' },
};

export const UploadQueuePanel = ({ queue = [], onRetry, onRemove, onClearDone, className = '' }) => {
  if (!queue.length) return null;
  const doneCount = queue.filter((q) => q.status === 'done').length;

  return (
    <div
      className={`rounded-2xl border border-border/70 bg-card shadow-sm ${className}`}
      data-testid={T.mediaUploadQueue}
    >
      <div className="flex items-center justify-between gap-2 border-b border-border/70 px-4 py-2.5">
        <div className="text-[10px] font-semibold uppercase tracking-[0.16em] text-muted-foreground">
          Antrean Upload ({queue.length})
        </div>
        {doneCount ? (
          <Button
            size="sm"
            variant="ghost"
            className="h-7 rounded-md px-2 text-xs"
            onClick={onClearDone}
            data-testid={T.mediaUploadQueueClear}
          >
            Bersihkan selesai
          </Button>
        ) : null}
      </div>
      <div className="max-h-64 divide-y divide-border/60 overflow-y-auto">
        {queue.map((it) => {
          const meta = STATUS[it.status] || STATUS.queued;
          return (
            <div key={it.id} className="px-4 py-2.5" data-testid={T.mediaUploadQueueRow}>
              <div className="flex items-center gap-2">
                {it.status === 'uploading' ? <Loader2 className="h-3.5 w-3.5 shrink-0 animate-spin text-muted-foreground" /> : null}
                {it.status === 'done' ? <CheckCircle2 className="h-3.5 w-3.5 shrink-0 text-emerald-600" /> : null}
                {it.status === 'error' ? <AlertCircle className="h-3.5 w-3.5 shrink-0 text-rose-600" /> : null}
                <span className="min-w-0 flex-1 truncate text-xs font-medium text-foreground" title={it.name}>
                  {it.name}
                </span>
                <span className="shrink-0 font-['Azeret_Mono',monospace] text-[10px] text-muted-foreground">
                  {formatBytes(it.size)}
                </span>
                <Badge variant="outline" className={`shrink-0 text-[10px] ${meta.cls}`}>{meta.label}</Badge>
                {it.status === 'error' ? (
                  <button
                    type="button"
                    onClick={() => onRetry && onRetry(it.id)}
                    aria-label="Coba lagi"
                    className="grid h-6 w-6 shrink-0 place-items-center rounded-md text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
                    data-testid={T.mediaUploadQueueRetry}
                  >
                    <RefreshCw className="h-3.5 w-3.5" />
                  </button>
                ) : null}
                <button
                  type="button"
                  onClick={() => onRemove && onRemove(it.id)}
                  aria-label="Buang dari antrean"
                  className="grid h-6 w-6 shrink-0 place-items-center rounded-md text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
                >
                  <X className="h-3.5 w-3.5" />
                </button>
              </div>
              {it.status === 'uploading' || it.status === 'queued' ? (
                <Progress value={it.progress} className="mt-2 h-1.5" />
              ) : null}
              {it.error ? (
                <p className="mt-1.5 text-[11px] leading-snug text-rose-600">{it.error}</p>
              ) : null}
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default UploadQueuePanel;
