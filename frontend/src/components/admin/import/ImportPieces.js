// components/admin/import/ImportPieces.js — potongan UI kecil untuk wizard impor.
import React from 'react';
import { CheckCircle2 } from 'lucide-react';
import { Badge } from '../../ui/badge';
import { ACCENT, ACCENT_SOFT } from '../adminUi';

export const Stepper = ({ stage }) => {
  const steps = [
    { id: 'upload', n: 1, label: 'Unggah File' },
    { id: 'configure', n: 2, label: 'Petakan & Tinjau' },
    { id: 'configure', n: 3, label: 'Impor' },
  ];
  const activeIdx = stage === 'upload' ? 0 : 1;
  return (
    <div className="flex items-center gap-2 mb-6 flex-wrap">
      {steps.map((s, i) => {
        const done = i < activeIdx;
        const active = i === activeIdx || (stage === 'configure' && i >= 1);
        return (
          <React.Fragment key={s.n}>
            <div className="flex items-center gap-2">
              <div
                className="h-7 w-7 rounded-full grid place-items-center text-xs font-semibold border"
                style={{
                  backgroundColor: active ? ACCENT_SOFT : 'transparent',
                  color: active ? ACCENT : undefined,
                  borderColor: active ? ACCENT : 'var(--border, #e5e5e5)',
                }}
              >
                {done ? <CheckCircle2 className="h-4 w-4" /> : s.n}
              </div>
              <span className={`text-sm ${active ? 'font-medium text-foreground' : 'text-muted-foreground'}`}>{s.label}</span>
            </div>
            {i < steps.length - 1 && <div className="h-px w-8 bg-border" />}
          </React.Fragment>
        );
      })}
    </div>
  );
};

export const Chip = ({ tone = 'default', children }) => {
  const map = {
    default: 'bg-zinc-100 text-zinc-700 border-zinc-200',
    ok: 'bg-emerald-100 text-emerald-800 border-emerald-200',
    error: 'bg-rose-100 text-rose-800 border-rose-200',
    accent: '',
  };
  return (
    <Badge
      variant="outline"
      className={`font-medium ${map[tone] || map.default}`}
      style={tone === 'accent' ? { backgroundColor: ACCENT_SOFT, color: ACCENT, borderColor: ACCENT } : undefined}
    >
      {children}
    </Badge>
  );
};
