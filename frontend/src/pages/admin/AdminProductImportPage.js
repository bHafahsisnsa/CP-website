// pages/admin/AdminProductImportPage.js — Wizard impor & ekspor produk (Epic E10/E11/E12).
// Alur: Unggah (analyze -> SESI) -> Petakan kolom + Isi Harga Massal + Pratinjau -> Impor.
// Model VARIAN N-DIMENSI (Shopify-style): dimensi via option{i}_name/value; kolom preview DINAMIS.
//
// E12 — SESI IMPOR: baris file TIDAK lagi disimpan di browser dan TIDAK dikirim ulang tiap
// validasi. Dulu katalog 6.426 baris memindahkan ~11,6 MB per validasi sehingga di koneksi
// normal muncul "Gagal memvalidasi baris." (timeout) walau filenya sah. Sekarang: unggah
// SEKALI -> server menyimpan baris -> UI hanya mengirim session_id, matriks harga, atau
// patch sel (payload KB).
import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'sonner';
import {
  FileSpreadsheet, ArrowLeft, RefreshCw, Loader2, Download,
} from 'lucide-react';
import {
  analyzeImport, validateImport, commitImport, downloadTemplate, exportProducts,
  fetchImportRows, patchImportCells, applyImportFill, closeImportSession,
  importErrorMessage,
} from '../../services/admin';
import { PageHeader, ACCENT } from '../../components/admin/adminUi';
import { adminTestIds as T } from '../../constants/testIds/admin';
import { Button } from '../../components/ui/button';
import { Card, CardContent } from '../../components/ui/card';
import {
  NONE, CANON, REQUIRED, DISPLAY_CAP, buildPreviewCols, hasDimensionMapped,
  partialDimensionPairs,
} from '../../components/admin/import/importConstants';
import { effectiveDimensionNames } from '../../components/admin/import/importBulkFill';
import { Stepper, Chip } from '../../components/admin/import/ImportPieces';
import { ImportUploadStage } from '../../components/admin/import/ImportUploadStage';
import { ImportResultDialog } from '../../components/admin/import/ImportResultDialog';
import { ImportStructurePanel } from '../../components/admin/import/ImportStructurePanel';
import { ImportBulkFillPanel } from '../../components/admin/import/ImportBulkFillPanel';
import { ImportMappingPanel } from '../../components/admin/import/ImportMappingPanel';
import { ImportPreviewTable } from '../../components/admin/import/ImportPreviewTable';
import { ImportCommitPanel } from '../../components/admin/import/ImportCommitPanel';

const CANON_KEYS = CANON.map((c) => c.key);
const nf = (n) => Number(n || 0).toLocaleString('id-ID');

export default function AdminProductImportPage() {
  const navigate = useNavigate();
  const fileInputRef = useRef(null);
  const cellQueue = useRef([]);
  const cellTimer = useRef(null);

  const [stage, setStage] = useState('upload');
  const [sessionId, setSessionId] = useState(null);
  const [fileName, setFileName] = useState('');
  const [total, setTotal] = useState(0);
  const [headers, setHeaders] = useState([]);
  const [mapping, setMapping] = useState({});
  const [suggested, setSuggested] = useState({});

  const [items, setItems] = useState([]);           // [{index, data}] jendela pratinjau
  const [reportMap, setReportMap] = useState({});   // index baris -> laporan validasi
  const [errorRows, setErrorRows] = useState([]);   // indeks baris bermasalah
  const [summary, setSummary] = useState(null);
  const [grouped, setGrouped] = useState([]);       // contoh produk hasil grouping
  const [productsTotal, setProductsTotal] = useState(0);
  const [tiersData, setTiersData] = useState(null);

  const [analyzing, setAnalyzing] = useState(false);
  const [validating, setValidating] = useState(false);
  const [committing, setCommitting] = useState(false);
  const [filling, setFilling] = useState(false);
  const [dragOver, setDragOver] = useState(false);
  const [showErrorsOnly, setShowErrorsOnly] = useState(false);
  const [revalidateKey, setRevalidateKey] = useState(0);

  const [mode, setMode] = useState('add-only');
  const [result, setResult] = useState(null);
  const [dlBusy, setDlBusy] = useState('');
  const [expBusy, setExpBusy] = useState('');

  const clearState = () => {
    setStage('upload');
    setSessionId(null); setFileName(''); setTotal(0); setHeaders([]);
    setMapping({}); setSuggested({}); setItems([]); setReportMap({});
    setErrorRows([]); setSummary(null); setGrouped([]); setProductsTotal(0);
    setTiersData(null); setShowErrorsOnly(false); setResult(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const reset = () => {
    if (sessionId) closeImportSession(sessionId).catch(() => {});
    clearState();
  };

  const handleFile = useCallback(async (file) => {
    if (!file) return;
    const name = (file.name || '').toLowerCase();
    if (!(name.endsWith('.csv') || name.endsWith('.xlsx') || name.endsWith('.xlsm'))) {
      toast.error('Format tidak didukung. Gunakan .csv atau .xlsx');
      return;
    }
    setAnalyzing(true);
    try {
      const data = await analyzeImport(file);
      setSessionId(data.session_id || null);
      setFileName(file.name);
      setTotal(data.total || 0);
      setHeaders(data.headers || []);
      const sm = data.suggested_mapping || {};
      setSuggested(sm);
      setMapping(sm);
      setItems(data.preview_rows || []);
      setReportMap({}); setErrorRows([]); setSummary(null);
      setGrouped([]); setProductsTotal(0); setTiersData(null);
      setShowErrorsOnly(false);
      setStage('configure');
      toast.success(`${nf(data.total || 0)} baris terbaca dari ${file.name}`);
    } catch (e) {
      toast.error(importErrorMessage(e, 'Gagal membaca file.'));
    } finally {
      setAnalyzing(false);
    }
  }, []);

  const onDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    const f = e.dataTransfer?.files?.[0];
    if (f) handleFile(f);
  };

  // Ambil jendela baris dari SESI (berurutan, atau hanya baris bermasalah).
  const loadWindow = useCallback(async (errorsOnly, errIdx) => {
    if (!sessionId) return;
    try {
      const indexes = errorsOnly ? (errIdx || []).slice(0, DISPLAY_CAP) : null;
      if (errorsOnly && indexes.length === 0) { setItems([]); return; }
      const res = await fetchImportRows(sessionId, { offset: 0, limit: DISPLAY_CAP, indexes });
      setItems(res.rows || []);
    } catch (e) {
      toast.error(importErrorMessage(e, 'Gagal memuat baris pratinjau.'));
    }
  }, [sessionId]);

  // Validasi (debounced) — hanya mengirim session_id + pemetaan, bukan 6.426 baris.
  useEffect(() => {
    if (stage !== 'configure' || !sessionId) return undefined;
    let alive = true;
    const t = setTimeout(async () => {
      setValidating(true);
      try {
        const res = await validateImport({ sessionId, mapping });
        if (!alive) return;
        setSummary(res.summary || null);
        setGrouped(res.products_head || res.products || []);
        setProductsTotal(res.products_total ?? (res.products || []).length);
        const map = {};
        [...(res.reports_head || []), ...(res.error_reports || [])].forEach((r) => {
          if (r && r.row) map[r.row - 1] = r;
        });
        setReportMap(map);
        const errIdx = (res.error_reports || []).map((r) => r.row - 1);
        setErrorRows(errIdx);
        if (showErrorsOnly) loadWindow(true, errIdx);
      } catch (e) {
        if (alive) toast.error(importErrorMessage(e, 'Gagal memvalidasi baris.'));
      } finally {
        if (alive) setValidating(false);
      }
    }, 450);
    return () => { alive = false; clearTimeout(t); };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sessionId, mapping, stage, revalidateKey]);

  const setMap = (canon, headerVal) =>
    setMapping((prev) => ({ ...prev, [canon]: headerVal === NONE ? null : headerVal }));

  const applySuggested = (sm) => setMapping(sm);

  // Edit sel: perbarui tampilan langsung, kirim patch KECIL ke sesi (debounced).
  const updateCell = (rowIdx, header, value) => {
    setItems((prev) => prev.map((it) => (it.index === rowIdx
      ? { ...it, data: { ...it.data, [header]: value } } : it)));
    cellQueue.current = [...cellQueue.current.filter(
      (c) => !(c.row === rowIdx && c.header === header),
    ), { row: rowIdx, header, value }];
    if (cellTimer.current) clearTimeout(cellTimer.current);
    cellTimer.current = setTimeout(async () => {
      const batch = cellQueue.current;
      cellQueue.current = [];
      if (!sessionId || batch.length === 0) return;
      try {
        await patchImportCells(sessionId, batch);
        setRevalidateKey((k) => k + 1);
      } catch (e) {
        toast.error(importErrorMessage(e, 'Gagal menyimpan perubahan sel.'));
      }
    }, 700);
  };

  const toggleErrorsOnly = () => {
    const next = !showErrorsOnly;
    setShowErrorsOnly(next);
    loadWindow(next, errorRows);
  };

  const doDownloadTemplate = async (format) => {
    setDlBusy(format);
    try {
      await downloadTemplate(format);
      toast.success(`Template ${format.toUpperCase()} diunduh.`);
    } catch (e) {
      toast.error('Gagal mengunduh template.');
    } finally {
      setDlBusy('');
    }
  };

  const doExport = async (format) => {
    setExpBusy(format);
    try {
      await exportProducts(format);
      toast.success(`Ekspor produk ${format.toUpperCase()} diunduh.`);
    } catch (e) {
      toast.error('Gagal mengekspor produk.');
    } finally {
      setExpBusy('');
    }
  };

  // Kolom preview DINAMIS (mengikuti dimensi yang terpetakan).
  const previewCols = useMemo(() => buildPreviewCols(mapping), [mapping]);
  const dimensionMapped = useMemo(() => hasDimensionMapped(mapping), [mapping]);
  const partialDims = useMemo(() => partialDimensionPairs(mapping), [mapping]);
  // Dimensi EFEKTIF dihitung SERVER atas SEMUA baris (via /tiers); fallback ke jendela
  // pratinjau. Dulu chip memakai jumlah pasangan terpetakan sehingga file 2 dimensi
  // tertulis "4 dimensi".
  const effDims = useMemo(() => {
    const fromTiers = (tiersData?.dimensions || []).map((d) => d.name);
    if (fromTiers.length) return fromTiers;
    return effectiveDimensionNames(items.map((it) => it.data), mapping);
  }, [tiersData, items, mapping]);

  const missingRequired = REQUIRED.filter((k) => !mapping[k]);
  const canCommit = missingRequired.length === 0 && dimensionMapped
    && summary && summary.ok > 0 && !committing && !validating && !filling;

  const doCommit = async () => {
    if (!canCommit) return;
    setCommitting(true);
    try {
      const res = await commitImport({ sessionId, mapping, mode });
      setResult(res);
      toast.success(`Impor selesai — ${res.created} dibuat, ${res.updated} diperbarui.`);
    } catch (e) {
      toast.error(importErrorMessage(e, 'Gagal mengimpor produk.'));
    } finally {
      setCommitting(false);
    }
  };

  // Isi harga massal: kirim MATRIKS (puluhan angka) — server yang menyentuh 6.426 baris.
  const applyFill = async (spec) => {
    if (!sessionId) return null;
    setFilling(true);
    try {
      const res = await applyImportFill(sessionId, spec);
      setShowErrorsOnly(false);
      await loadWindow(false, []);
      setRevalidateKey((k) => k + 1);
      return res.stats || {};
    } catch (e) {
      toast.error(importErrorMessage(e, 'Gagal menerapkan harga massal.'));
      return null;
    } finally {
      setFilling(false);
    }
  };

  const bulkMapping = useMemo(
    () => Object.fromEntries(CANON_KEYS.map((k) => [k, mapping[k] || null])),
    [mapping],
  );

  return (
    <div data-testid={T.importPage}>
      <PageHeader
        title="Impor / Ekspor Produk"
        description="Impor katalog dari CSV/Excel dengan pemetaan kolom cerdas (varian N-dimensi), isi harga massal per tier, pratinjau, dan mode aman."
        actions={(
          <div className="flex items-center gap-2 flex-wrap justify-end">
            <Button
              variant="outline" className="gap-2" data-testid={T.importExportCsv}
              disabled={expBusy === 'csv'} onClick={() => doExport('csv')}
            >
              {expBusy === 'csv' ? <Loader2 className="h-4 w-4 animate-spin" /> : <Download className="h-4 w-4" />}
              Ekspor CSV
            </Button>
            <Button
              variant="outline" className="gap-2" data-testid={T.importExportXlsx}
              disabled={expBusy === 'xlsx'} onClick={() => doExport('xlsx')}
            >
              {expBusy === 'xlsx' ? <Loader2 className="h-4 w-4 animate-spin" /> : <FileSpreadsheet className="h-4 w-4" />}
              Ekspor Excel
            </Button>
            <Button variant="outline" className="gap-2" onClick={() => navigate('/admin/produk')}>
              <ArrowLeft className="h-4 w-4" /> Kembali ke Produk
            </Button>
          </div>
        )}
      />

      <Stepper stage={stage} />

      {stage === 'upload' && (
        <ImportUploadStage
          analyzing={analyzing}
          dragOver={dragOver}
          setDragOver={setDragOver}
          onDrop={onDrop}
          fileInputRef={fileInputRef}
          onFile={handleFile}
          onDownloadTemplate={doDownloadTemplate}
          dlBusy={dlBusy}
        />
      )}

      {stage === 'configure' && (
        <div className="space-y-5">
          {/* File info + summary bar */}
          <Card className="border-border/70">
            <CardContent className="p-4 flex flex-col md:flex-row md:items-center gap-3 justify-between">
              <div className="flex items-center gap-3 min-w-0">
                <FileSpreadsheet className="h-5 w-5 shrink-0" style={{ color: ACCENT }} />
                <div className="min-w-0">
                  <div className="text-sm font-medium truncate">{fileName}</div>
                  <div className="text-xs text-muted-foreground">
                    {nf(total)} baris • {headers.length} kolom terdeteksi
                  </div>
                </div>
              </div>
              <div className="flex items-center gap-2 flex-wrap" data-testid={T.importSummary}>
                {(validating || filling) && <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />}
                <Chip tone="accent">{nf(total)} baris</Chip>
                <span data-testid={T.importDimensionChip}>
                  <Chip tone={dimensionMapped ? 'ok' : 'error'}>
                    {effDims.length > 0
                      ? `${effDims.length} dimensi (${effDims.join(' × ')})`
                      : 'dimensi belum dipetakan'}
                  </Chip>
                </span>
                <Chip tone="ok">{summary ? nf(summary.ok) : 0} valid</Chip>
                <Chip tone="error">{summary ? nf(summary.error) : 0} error</Chip>
                <Chip>{summary ? nf(summary.products) : 0} produk</Chip>
                <Button variant="ghost" size="sm" className="gap-2" data-testid={T.importReset} onClick={reset}>
                  <RefreshCw className="h-4 w-4" /> Ganti file
                </Button>
              </div>
            </CardContent>
          </Card>

          <ImportMappingPanel
            mapping={mapping}
            headers={headers}
            suggested={suggested}
            onSetMap={setMap}
            onApplySuggested={applySuggested}
            missingRequired={missingRequired}
            dimensionMapped={dimensionMapped}
            partialDims={partialDims}
          />

          {/* Isi harga massal per TIER (untuk katalog besar yang belum berharga) */}
          <ImportBulkFillPanel
            sessionId={sessionId}
            mapping={bulkMapping}
            headers={headers}
            summary={summary}
            total={total}
            onApplySpec={applyFill}
            onTiers={setTiersData}
            busy={validating || committing || filling}
          />

          {/* Struktur varian N-dimensi hasil grouping (verifikasi sebelum commit) */}
          <ImportStructurePanel products={grouped} validating={validating} />

          <ImportPreviewTable
            items={items}
            reportMap={reportMap}
            mapping={mapping}
            previewCols={previewCols}
            summary={summary}
            total={total}
            errorCount={errorRows.length}
            productsTotal={productsTotal}
            showErrorsOnly={showErrorsOnly}
            onToggleErrorsOnly={toggleErrorsOnly}
            onUpdateCell={updateCell}
          />

          <ImportCommitPanel
            mode={mode}
            onMode={setMode}
            summary={summary}
            canCommit={canCommit}
            committing={committing}
            onCommit={doCommit}
          />
        </div>
      )}

      <ImportResultDialog
        result={result}
        onOpenChange={(o) => { if (!o) setResult(null); }}
        onImportAnother={() => { setResult(null); reset(); }}
        onViewProducts={() => navigate('/admin/produk')}
      />
    </div>
  );
}
