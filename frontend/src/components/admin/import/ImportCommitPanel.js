// components/admin/import/ImportCommitPanel.js — pilih mode impor lalu commit.
import React from 'react';
import { Loader2, PackageCheck } from 'lucide-react';
import { Button } from '../../ui/button';
import { Card, CardContent } from '../../ui/card';
import { RadioGroup, RadioGroupItem } from '../../ui/radio-group';
import { ACCENT, ACCENT_SOFT } from '../adminUi';
import { adminTestIds as T } from '../../../constants/testIds/admin';

const MODES = [
  {
    value: 'add-only', id: 'mode-add', title: 'Tambah saja (aman)',
    desc: 'Buat produk baru. Produk dengan slug/nama yang sudah ada akan dilewati (tidak ditimpa).',
  },
  {
    value: 'upsert', id: 'mode-upsert', title: 'Upsert (perbarui)',
    desc: 'Buat produk baru & perbarui produk yang sudah ada (varian diganti sesuai file).',
  },
];

export const ImportCommitPanel = ({ mode, onMode, summary, canCommit, committing, onCommit }) => (
  <Card className="border-border/70">
    <CardContent className="p-5">
      <h3 className="text-sm font-semibold text-foreground mb-3">Mode Impor</h3>
      <RadioGroup
        value={mode} onValueChange={onMode}
        className="grid sm:grid-cols-2 gap-3" data-testid={T.importModeSelect}
      >
        {MODES.map((m) => (
          <label
            key={m.value} htmlFor={m.id}
            className="flex items-start gap-3 rounded-xl border p-4 cursor-pointer transition-colors"
            style={mode === m.value ? { borderColor: ACCENT, backgroundColor: ACCENT_SOFT } : undefined}
          >
            <RadioGroupItem value={m.value} id={m.id} className="mt-0.5" />
            <div>
              <div className="text-sm font-medium text-foreground">{m.title}</div>
              <div className="text-xs text-muted-foreground mt-0.5">{m.desc}</div>
            </div>
          </label>
        ))}
      </RadioGroup>

      <div className="mt-5 flex items-center justify-between gap-3 flex-wrap">
        <p className="text-xs text-muted-foreground">
          {summary ? (
            <>
              Akan mengimpor <span className="font-medium text-foreground">{summary.products}</span>{' '}
              produk dari <span className="font-medium text-emerald-700">{summary.ok}</span> baris valid
              {summary.error > 0 ? (
                <>, melewati <span className="font-medium text-rose-700">{summary.error}</span> baris error.</>
              ) : '.'}
            </>
          ) : 'Memvalidasi…'}
        </p>
        <Button
          className="gap-2" size="lg" data-testid={T.importCommit}
          disabled={!canCommit} onClick={onCommit}
        >
          {committing ? <Loader2 className="h-4 w-4 animate-spin" /> : <PackageCheck className="h-4 w-4" />}
          {committing ? 'Mengimpor…' : `Impor ${summary ? summary.products : ''} Produk`}
        </Button>
      </div>
    </CardContent>
  </Card>
);
