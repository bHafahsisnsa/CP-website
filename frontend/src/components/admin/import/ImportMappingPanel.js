// components/admin/import/ImportMappingPanel.js — editor pemetaan kolom file -> field kanonik.
// Dipisah dari AdminProductImportPage agar tiap file tetap di bawah batas compliance.
import React from 'react';
import { AlertTriangle, Layers, Wand2 } from 'lucide-react';
import { Button } from '../../ui/button';
import { Card, CardContent } from '../../ui/card';
import { Label } from '../../ui/label';
import {
  Select, SelectTrigger, SelectValue, SelectContent, SelectItem,
} from '../../ui/select';
import { ACCENT } from '../adminUi';
import { adminTestIds as T } from '../../../constants/testIds/admin';
import { NONE, CANON, LABEL, GROUPS } from './importConstants';

export const ImportMappingPanel = ({
  mapping, headers, suggested, onSetMap, onApplySuggested,
  missingRequired = [], dimensionMapped = true, partialDims = [],
}) => (
  <Card className="border-border/70" data-testid={T.importMapping}>
    <CardContent className="p-5">
      <div className="flex items-center justify-between mb-4 gap-3 flex-wrap">
        <div>
          <h3 className="text-sm font-semibold text-foreground">Pemetaan Kolom</h3>
          <p className="text-xs text-muted-foreground mt-0.5">
            Cocokkan kolom file Anda ke field produk. Sistem sudah menyarankan otomatis.
          </p>
        </div>
        <Button variant="outline" size="sm" className="gap-2" onClick={() => onApplySuggested(suggested)}>
          <Wand2 className="h-4 w-4" /> Terapkan saran
        </Button>
      </div>

      {missingRequired.length > 0 && (
        <div className="mb-3 flex items-start gap-2 rounded-lg border border-rose-200 bg-rose-50 p-3 text-xs text-rose-700">
          <AlertTriangle className="h-4 w-4 shrink-0 mt-0.5" />
          <span>
            Field wajib belum dipetakan: {missingRequired.map((k) => LABEL[k]).join(', ')}.
            Impor dinonaktifkan sampai semua field wajib terpetakan.
          </span>
        </div>
      )}

      {!dimensionMapped && (
        <div
          className="mb-4 flex items-start gap-2 rounded-lg border border-amber-200 bg-amber-50 p-3 text-xs text-amber-800"
          data-testid={T.importDimensionWarn}
        >
          <Layers className="h-4 w-4 shrink-0 mt-0.5" />
          <span>
            Petakan minimal <span className="font-medium">satu dimensi</span> (pasangan
            Nama + Nilai, mis. Dimensi 1 = &quot;Ukuran&quot;/&quot;50ml&quot;), atau kolom
            &quot;Ukuran ml (lama)&quot;. Wajib ada dimensi ukuran bernilai &gt; 0.
          </span>
        </div>
      )}

      {partialDims.length > 0 && (
        <div
          className="mb-4 flex items-start gap-2 rounded-lg border border-amber-200 bg-amber-50 p-3 text-xs text-amber-800"
          data-testid={T.importPartialDimWarn}
        >
          <AlertTriangle className="h-4 w-4 shrink-0 mt-0.5" />
          <span>
            Dimensi belum lengkap dan akan <span className="font-medium">diabaikan</span>:{' '}
            {partialDims.map((d) => `Dimensi ${d.idx} (butuh "${LABEL[d.missing]}")`).join(', ')}.
            Satu dimensi butuh pasangan Nama + Nilai.
          </span>
        </div>
      )}

      {GROUPS.map((g) => {
        const fields = CANON.filter((c) => c.group === g.id);
        if (fields.length === 0) return null;
        return (
          <div key={g.id} className="mb-5 last:mb-0">
            <div className="flex items-baseline gap-2 mb-2">
              <h4 className="text-xs font-semibold uppercase tracking-wide" style={{ color: ACCENT }}>
                {g.title}
              </h4>
              <span className="text-[11px] text-muted-foreground">{g.hint}</span>
            </div>
            <div className="grid sm:grid-cols-2 xl:grid-cols-3 gap-3">
              {fields.map((c) => {
                const missing = c.req && !mapping[c.key];
                return (
                  <div key={c.key} className="space-y-1">
                    <Label className={`text-xs ${missing ? 'text-rose-600' : 'text-muted-foreground'}`}>
                      {c.label}{c.req && <span className="text-rose-500"> *</span>}
                    </Label>
                    <Select value={mapping[c.key] || NONE} onValueChange={(v) => onSetMap(c.key, v)}>
                      <SelectTrigger
                        className="h-9"
                        data-testid={`admin-import-map-${c.key}`}
                        style={missing ? { borderColor: '#fda4af' } : undefined}
                      >
                        <SelectValue placeholder="— Tidak dipetakan —" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value={NONE}>— Tidak dipetakan —</SelectItem>
                        {headers.map((h) => (
                          <SelectItem key={h} value={h}>{h}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                );
              })}
            </div>
          </div>
        );
      })}
    </CardContent>
  </Card>
);
