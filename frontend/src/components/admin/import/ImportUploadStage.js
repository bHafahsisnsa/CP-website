// components/admin/import/ImportUploadStage.js — tahap 1 wizard: unggah file + unduh template.
import React from 'react';
import { UploadCloud, FileSpreadsheet, FileText, Loader2, Sparkles } from 'lucide-react';
import { Button } from '../../ui/button';
import { Card, CardContent } from '../../ui/card';
import { ACCENT, ACCENT_SOFT } from '../adminUi';
import { adminTestIds as T } from '../../../constants/testIds/admin';

// Contoh file TERISI (statis, tanpa auth) — regenerate: python scripts/make_import_example.py
const EXAMPLE_XLSX = '/templates/contoh-impor-produk-collector-parfum.xlsx';
const EXAMPLE_CSV = '/templates/contoh-impor-produk-collector-parfum.csv';

export const ImportUploadStage = ({
  analyzing, dragOver, setDragOver, onDrop, fileInputRef, onFile, onDownloadTemplate, dlBusy,
}) => (
  <div className="grid lg:grid-cols-3 gap-5">
    <Card className="lg:col-span-2 border-border/70">
      <CardContent className="p-6">
        <div
          data-testid={T.importDropzone}
          onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
          onDragLeave={() => setDragOver(false)}
          onDrop={onDrop}
          onClick={() => fileInputRef.current?.click()}
          className="cursor-pointer rounded-2xl border-2 border-dashed transition-colors grid place-items-center text-center py-16 px-6"
          style={{
            borderColor: dragOver ? ACCENT : 'var(--border, #e5e5e5)',
            backgroundColor: dragOver ? ACCENT_SOFT : 'transparent',
          }}
        >
          <div className="h-14 w-14 rounded-full grid place-items-center mb-4"
            style={{ backgroundColor: ACCENT_SOFT, color: ACCENT }}>
            {analyzing ? <Loader2 className="h-6 w-6 animate-spin" /> : <UploadCloud className="h-6 w-6" />}
          </div>
          <p className="text-sm font-medium text-foreground">
            {analyzing ? 'Membaca file…' : 'Seret & lepas file di sini, atau klik untuk memilih'}
          </p>
          <p className="text-xs text-muted-foreground mt-1">Mendukung .csv, .xlsx (maks 8 MB)</p>
          <input
            ref={fileInputRef}
            data-testid={T.importFileInput}
            type="file"
            accept=".csv,.xlsx,.xlsm"
            className="hidden"
            onChange={(e) => onFile(e.target.files?.[0])}
          />
        </div>
      </CardContent>
    </Card>

    <Card className="border-border/70">
      <CardContent className="p-6">
        <h3 className="text-sm font-semibold text-foreground">Belum punya file?</h3>
        <p className="text-xs text-muted-foreground mt-1 mb-4">
          Unduh template kosong, atau contoh TERISI (produk 2/3/4 dimensi + sheet Panduan &amp; Referensi slug).
        </p>
        <div className="flex flex-col gap-2">
          <Button variant="outline" className="justify-start gap-2" data-testid={T.importTemplateCsv}
            disabled={dlBusy === 'csv'} onClick={() => onDownloadTemplate('csv')}>
            <FileText className="h-4 w-4" /> Template CSV
          </Button>
          <Button variant="outline" className="justify-start gap-2" data-testid={T.importTemplateXlsx}
            disabled={dlBusy === 'xlsx'} onClick={() => onDownloadTemplate('xlsx')}>
            <FileSpreadsheet className="h-4 w-4" /> Template Excel (.xlsx)
          </Button>
          {/* File statis di /public/templates (tanpa auth) — dibuat oleh
              scripts/make_import_example.py, berisi 3 produk contoh + panduan + referensi slug. */}
          <Button asChild variant="outline" className="justify-start gap-2" data-testid={T.importExampleXlsx}>
            <a href={EXAMPLE_XLSX} download>
              <Sparkles className="h-4 w-4" /> Contoh Terisi (.xlsx)
            </a>
          </Button>
          <Button asChild variant="ghost" className="justify-start gap-2 text-xs h-8" data-testid={T.importExampleCsv}>
            <a href={EXAMPLE_CSV} download>
              <FileText className="h-3.5 w-3.5" /> Contoh Terisi (.csv)
            </a>
          </Button>
        </div>
        <div className="mt-5 rounded-lg border border-border/70 p-3 text-xs text-muted-foreground leading-relaxed">
          <span className="font-medium text-foreground">Tips:</span> satu baris = satu varian.
          Baris dengan <span className="font-medium">nama/slug</span> sama akan dikelompokkan menjadi satu produk
          dengan beberapa varian (mis. Konsentrasi × Tipe × Ukuran, sampai 4 dimensi).
        </div>
      </CardContent>
    </Card>
  </div>
);
