// components/admin/import/ImportBulkFillPanel.js
// Panel "Isi Harga Massal (Matriks Tier)" untuk wizard impor.
//
// Masalah nyata: file katalog klien sering datang dengan variant_price = 0 di SEMUA baris
// (harga belum ditetapkan) sehingga wizard hanya bisa bilang "6426 error" tanpa jalan keluar.
// Panel ini mendeteksi TIER harga (mis. kolom `tags` berisi "Tier CP02") + kombinasi dimensi
// yang benar-benar ada, lalu admin cukup mengisi matriks kecil (tier x kombinasi).
//
// E12: "Terapkan" mengirim MATRIKS (puluhan angka) ke server (`/session/{id}/fill`) — bukan
// mengunggah ulang 6.426 baris. Pratinjau dampak dihitung dari `cell_rows` yang dilaporkan
// /tiers (jumlah baris per sel), jadi angkanya tetap akurat tanpa menyimpan baris di browser.
// Logika terap SSOT ada di backend services/product_fill.py (cermin importBulkFill.js).
import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { toast } from 'sonner';
import {
  Coins, Loader2, RefreshCw, Wand2, AlertTriangle, Info, CheckCircle2,
} from 'lucide-react';
import { detectImportTiers, importErrorMessage } from '../../../services/admin';
import { Button } from '../../ui/button';
import { Input } from '../../ui/input';
import { Label } from '../../ui/label';
import { Switch } from '../../ui/switch';
import { Card, CardContent } from '../../ui/card';
import {
  Select, SelectTrigger, SelectValue, SelectContent, SelectItem,
} from '../../ui/select';
import { ACCENT } from '../adminUi';
import { adminTestIds as T } from '../../../constants/testIds/admin';
import { Chip } from './ImportPieces';
import { ImportTierMatrix } from './ImportTierMatrix';
import {
  countMatrixCells, numericMatrix, parseRupiah, previewFromCellRows,
} from './importBulkFill';

const STATUS_OPTIONS = [
  { value: 'file', label: 'Ikuti file' },
  { value: 'archived', label: 'Draft — tersembunyi dari toko' },
  { value: 'active', label: 'Aktif — langsung tampil di toko' },
];
const CONC_OPTIONS = [
  { value: 'file', label: 'Ikuti file' },
  { value: 'EDP', label: 'EDP' },
  { value: 'EDT', label: 'EDT' },
];

const nf = (n) => Number(n || 0).toLocaleString('id-ID');
const EMPTY_LIST = [];

export const ImportBulkFillPanel = ({
  sessionId = null, mapping = {}, headers = [], summary = null, total = 0,
  onApplySpec, onTiers, busy = false,
}) => {
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState(null);
  const [tierColumn, setTierColumn] = useState('');
  const [tab, setTab] = useState('price');
  const [matrixPrice, setMatrixPrice] = useState({});
  const [matrixCompare, setMatrixCompare] = useState({});
  const [quick, setQuick] = useState('');
  const [stockEnabled, setStockEnabled] = useState(true);
  const [stockValue, setStockValue] = useState('0');
  const [statusMode, setStatusMode] = useState('archived');
  const [concMode, setConcMode] = useState('file');
  const [overwritePrice, setOverwritePrice] = useState(false);
  const onTiersRef = useRef(onTiers);
  onTiersRef.current = onTiers;

  // Kunci pemetaan yang mempengaruhi struktur matriks (dimensi + harga + tag).
  const mappingKey = useMemo(() => JSON.stringify([
    mapping.option1_name, mapping.option1_value, mapping.option2_name, mapping.option2_value,
    mapping.option3_name, mapping.option3_value, mapping.option4_name, mapping.option4_value,
    mapping.variant_price, mapping.variant_compare_at_price, mapping.tags,
  ]), [mapping]);

  const detect = useCallback(async (col) => {
    if (!sessionId) return;
    setLoading(true);
    try {
      const res = await detectImportTiers({ sessionId, mapping, tierColumn: col || null });
      setData(res);
      setTierColumn(res.tier_column || '');
      if (onTiersRef.current) onTiersRef.current(res);
    } catch (e) {
      toast.error(importErrorMessage(e, 'Gagal mendeteksi tier harga.'));
    } finally {
      setLoading(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sessionId, mappingKey]);

  // Deteksi otomatis saat file/pemetaan dimensi berubah (bukan tiap ketikan sel).
  useEffect(() => {
    if (!sessionId) { setData(null); return; }
    detect(null);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sessionId, mappingKey]);

  const tiers = useMemo(() => data?.tiers || EMPTY_LIST, [data]);
  const combos = useMemo(() => data?.combos || EMPTY_LIST, [data]);
  const dims = useMemo(() => data?.dimensions || EMPTY_LIST, [data]);
  const dimOrder = useMemo(() => dims.map((d) => d.name), [dims]);
  const candidates = data?.tier_column_candidates || EMPTY_LIST;
  const activeMatrix = tab === 'price' ? matrixPrice : matrixCompare;
  const setActiveMatrix = tab === 'price' ? setMatrixPrice : setMatrixCompare;
  const compareMapped = Boolean(mapping.variant_compare_at_price);

  const preview = useMemo(
    () => previewFromCellRows(data?.cell_rows, matrixPrice, overwritePrice),
    [data, matrixPrice, overwritePrice],
  );
  const noTierRows = data?.summary?.rows_without_tier || 0;
  const priceCells = countMatrixCells(matrixPrice);
  const compareCells = countMatrixCells(matrixCompare);

  // Harga coret WAJIB > harga jual (validator backend menolak bila tidak).
  const badCompare = useMemo(() => {
    if (compareCells === 0) return 0;
    let bad = 0;
    tiers.forEach((t) => {
      combos.forEach((c) => {
        const cap = parseRupiah((matrixCompare[t.label] || {})[c.key]);
        const p = parseRupiah((matrixPrice[t.label] || {})[c.key]);
        if (cap > 0 && cap <= p) bad += 1;
      });
    });
    return bad;
  }, [matrixCompare, matrixPrice, tiers, combos, compareCells]);

  const setCell = (tier, comboKey, value) =>
    setActiveMatrix((prev) => ({ ...prev, [tier]: { ...(prev[tier] || {}), [comboKey]: value } }));

  const spreadRow = (tier) => setActiveMatrix((prev) => {
    const row = prev[tier] || {};
    const first = combos.map((c) => parseRupiah(row[c.key])).find((v) => v > 0) || 0;
    if (!first) {
      toast.info('Isi salah satu sel di baris ini dulu, lalu tekan tombol sebar.');
      return prev;
    }
    const next = {};
    combos.forEach((c) => { next[c.key] = first; });
    return { ...prev, [tier]: next };
  });

  const copyRow = (tierIdx) => setActiveMatrix((prev) => {
    const from = tiers[tierIdx - 1]; const to = tiers[tierIdx];
    if (!from || !to) return prev;
    return { ...prev, [to.label]: { ...(prev[from.label] || {}) } };
  });

  const fillEmptyCells = () => {
    const v = parseRupiah(quick);
    if (v <= 0) { toast.error('Masukkan angka harga lebih dari 0.'); return; }
    setActiveMatrix((prev) => {
      const next = { ...prev };
      tiers.forEach((t) => {
        const row = { ...(next[t.label] || {}) };
        combos.forEach((c) => { if (parseRupiah(row[c.key]) <= 0) row[c.key] = v; });
        next[t.label] = row;
      });
      return next;
    });
    toast.success(`Semua sel kosong diisi Rp ${nf(v)}.`);
  };

  const resetMatrix = () => { setActiveMatrix({}); toast.info('Matriks dikosongkan.'); };

  const doApply = async () => {
    if (badCompare > 0) {
      toast.error(`${badCompare} sel harga coret tidak lebih besar dari harga jual.`);
      return;
    }
    if (priceCells === 0 && !stockEnabled && statusMode === 'file' && concMode === 'file') {
      toast.error('Tidak ada yang bisa diterapkan. Isi matriks harga terlebih dahulu.');
      return;
    }
    const spec = {
      mapping,
      tier_column: tierColumn || null,
      dim_order: dimOrder,
      matrix_price: numericMatrix(matrixPrice),
      matrix_compare: compareMapped ? numericMatrix(matrixCompare) : {},
      overwrite_price: overwritePrice,
      stock: stockEnabled ? String(Math.max(0, parseRupiah(stockValue))) : null,
      status: statusMode,
      concentration: concMode,
    };
    const stats = await onApplySpec?.(spec);
    if (!stats) return;
    const bits = [];
    if (stats.price_filled) bits.push(`${nf(stats.price_filled)} harga`);
    if (stats.compare_filled) bits.push(`${nf(stats.compare_filled)} harga coret`);
    if (stats.forced) bits.push(`${nf(stats.forced)} nilai dipaksa`);
    if (stats.filled_if_empty) bits.push(`${nf(stats.filled_if_empty)} sel kosong`);
    if (bits.length === 0) {
      toast.error('Tidak ada baris yang cocok dengan matriks. Periksa kolom tier & dimensi.');
      return;
    }
    toast.success(`Diterapkan: ${bits.join(' · ')}.`);
  };

  const missingPrice = summary ? summary.error : 0;
  const canApply = !busy && !loading && Boolean(sessionId)
    && (priceCells > 0 || stockEnabled || statusMode !== 'file' || concMode !== 'file');

  return (
    <Card className="border-border/70" data-testid={T.bulkFillPanel}>
      <CardContent className="p-5">
        <div className="flex items-start justify-between gap-3 flex-wrap mb-4">
          <div className="flex items-start gap-2">
            <Coins className="h-4 w-4 mt-0.5 shrink-0" style={{ color: ACCENT }} />
            <div>
              <h3 className="text-sm font-semibold text-foreground">Isi Harga Massal (Matriks Tier)</h3>
              <p className="text-xs text-muted-foreground mt-0.5 max-w-2xl">
                Untuk katalog besar yang belum berharga. Sistem mendeteksi penanda tier di file
                Anda, lalu Anda cukup mengisi harga per <span className="font-medium">tier × kombinasi
                varian</span> — seluruh baris terisi sekali klik.
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2 flex-wrap">
            {loading && <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />}
            <Chip tone="accent">{tiers.length} tier</Chip>
            <Chip>{combos.length} kombinasi</Chip>
            <Chip tone={priceCells > 0 ? 'ok' : 'default'}>
              {priceCells}/{tiers.length * combos.length} sel terisi
            </Chip>
            <Button
              type="button" variant="ghost" size="sm" className="gap-2"
              disabled={loading || !sessionId}
              onClick={() => detect(tierColumn || null)}
              data-testid={T.bulkFillRedetect}
            >
              <RefreshCw className="h-4 w-4" /> Deteksi ulang
            </Button>
          </div>
        </div>

        {missingPrice > 0 && (
          <div
            className="mb-4 flex items-start gap-2 rounded-lg border border-amber-200 bg-amber-50 p-3 text-xs text-amber-800"
            data-testid={T.bulkFillMissingPriceAlert}
          >
            <AlertTriangle className="h-4 w-4 shrink-0 mt-0.5" />
            <span>
              <span className="font-medium">{nf(missingPrice)} baris</span> masih bermasalah —
              umumnya karena harga di file masih 0. Isi matriks di bawah, klik
              <span className="font-medium"> Terapkan</span>, lalu error akan hilang sendiri.
            </span>
          </div>
        )}

        {/* Kolom penanda tier */}
        <div className="grid sm:grid-cols-2 xl:grid-cols-3 gap-3 mb-4">
          <div className="space-y-1">
            <Label className="text-xs text-muted-foreground">Kolom penanda tier</Label>
            <Select
              value={tierColumn || '__none__'}
              onValueChange={(v) => { const c = v === '__none__' ? '' : v; setTierColumn(c); detect(c || null); }}
            >
              <SelectTrigger className="h-9" data-testid={T.bulkFillTierColumn}>
                <SelectValue placeholder="— Pilih kolom —" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="__none__">— Tidak ada tier —</SelectItem>
                {headers.map((h) => {
                  const cand = candidates.find((c) => c.column === h);
                  return (
                    <SelectItem key={h} value={h}>
                      {h}{cand ? ` · ${cand.tiers} tier` : ''}
                    </SelectItem>
                  );
                })}
              </SelectContent>
            </Select>
            <p className="text-[11px] text-muted-foreground">
              {candidates.length > 0
                ? `Terdeteksi otomatis: ${candidates.map((c) => c.column).join(', ')}`
                : 'Tidak ada kolom yang berisi pola tier (mis. "Tier CP01").'}
            </p>
          </div>
          <div className="space-y-1">
            <Label className="text-xs text-muted-foreground">Dimensi varian terdeteksi</Label>
            <div className="min-h-9 flex flex-wrap items-center gap-1.5 rounded-md border border-border/70 px-3 py-2">
              {dims.length === 0 ? (
                <span className="text-xs text-muted-foreground italic">belum terdeteksi</span>
              ) : dims.map((d, i) => (
                <React.Fragment key={d.name}>
                  {i > 0 && <span className="text-foreground/40 text-xs">×</span>}
                  <span className="text-xs text-foreground/80">
                    {d.name}<span className="text-muted-foreground">({d.values.length})</span>
                  </span>
                </React.Fragment>
              ))}
            </div>
            <p className="text-[11px] text-muted-foreground">
              {data?.summary
                ? `${nf(data.summary.products)} produk · ${nf(data.summary.rows)} baris`
                : '—'}
            </p>
          </div>
          <div className="space-y-1">
            <Label className="text-xs text-muted-foreground">Isi cepat semua sel kosong</Label>
            <div className="flex items-center gap-2">
              <Input
                inputMode="numeric" placeholder="mis. 250000"
                value={quick} onChange={(e) => setQuick(e.target.value)}
                className="h-9 text-xs" data-testid={T.bulkFillQuickValue}
              />
              <Button
                type="button" variant="outline" size="sm" className="gap-2 h-9 shrink-0"
                disabled={tiers.length === 0 || combos.length === 0}
                onClick={fillEmptyCells} data-testid={T.bulkFillQuickApply}
              >
                <Wand2 className="h-4 w-4" /> Isi
              </Button>
            </div>
            <p className="text-[11px] text-muted-foreground">
              Berguna sebagai titik awal, lalu sesuaikan per tier.
            </p>
          </div>
        </div>

        {/* Tab Harga / Harga Coret */}
        <div className="flex items-center gap-2 mb-2 flex-wrap">
          <Button
            type="button" size="sm" variant={tab === 'price' ? 'default' : 'outline'}
            onClick={() => setTab('price')} data-testid={T.bulkFillTabPrice}
          >
            Harga Jual
          </Button>
          <Button
            type="button" size="sm" variant={tab === 'compare' ? 'default' : 'outline'}
            disabled={!compareMapped} onClick={() => setTab('compare')}
            title={compareMapped ? undefined : 'Kolom Harga Coret belum dipetakan'}
            data-testid={T.bulkFillTabCompare}
          >
            Harga Coret (opsional){compareCells > 0 ? ` · ${compareCells}` : ''}
          </Button>
          <div className="flex-1" />
          <Button
            type="button" size="sm" variant="ghost" className="text-muted-foreground"
            onClick={resetMatrix} data-testid={T.bulkFillReset}
          >
            Kosongkan matriks {tab === 'price' ? 'harga' : 'harga coret'}
          </Button>
        </div>

        <ImportTierMatrix
          tiers={tiers} combos={combos} matrix={activeMatrix}
          onCell={setCell} onCopyRow={copyRow} onSpreadRow={spreadRow}
          disabled={busy || loading}
        />

        {badCompare > 0 && (
          <div
            className="mt-3 flex items-start gap-2 rounded-lg border border-rose-200 bg-rose-50 p-3 text-xs text-rose-700"
            data-testid={T.bulkFillCompareWarn}
          >
            <AlertTriangle className="h-4 w-4 shrink-0 mt-0.5" />
            <span>
              {badCompare} sel <span className="font-medium">Harga Coret</span> tidak lebih besar
              dari Harga Jual. Perbaiki dulu — validator akan menolak baris tersebut.
            </span>
          </div>
        )}

        {noTierRows > 0 && (
          <div
            className="mt-3 flex items-start gap-2 rounded-lg border border-amber-200 bg-amber-50 p-3 text-xs text-amber-800"
            data-testid={T.bulkFillNoTierWarn}
          >
            <AlertTriangle className="h-4 w-4 shrink-0 mt-0.5" />
            <span>
              {nf(noTierRows)} baris tidak punya penanda tier sehingga
              <span className="font-medium"> tidak akan terisi</span>. Isi harganya manual di
              tabel pratinjau, atau lengkapi kolom tier di file.
            </span>
          </div>
        )}

        {/* Nilai kolom lain */}
        <div className="mt-5 rounded-xl border border-border/70 p-4">
          <h4 className="text-xs font-semibold uppercase tracking-wide mb-3" style={{ color: ACCENT }}>
            Nilai Kolom Lain (berlaku untuk semua baris)
          </h4>
          <div className="grid sm:grid-cols-2 xl:grid-cols-4 gap-4">
            <div className="space-y-1.5">
              <Label className="text-xs text-muted-foreground">Stok awal</Label>
              <div className="flex items-center gap-2">
                <Switch
                  checked={stockEnabled} onCheckedChange={setStockEnabled}
                  data-testid={T.bulkFillStockToggle} aria-label="Paksa stok awal"
                />
                <Input
                  inputMode="numeric" value={stockValue} disabled={!stockEnabled}
                  onChange={(e) => setStockValue(e.target.value)}
                  className="h-9 text-xs" data-testid={T.bulkFillStock}
                />
              </div>
              <p className="text-[11px] text-muted-foreground">Menimpa kolom stok di file.</p>
            </div>
            <div className="space-y-1.5">
              <Label className="text-xs text-muted-foreground">Status produk</Label>
              <Select value={statusMode} onValueChange={setStatusMode}>
                <SelectTrigger className="h-9" data-testid={T.bulkFillStatus}>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {STATUS_OPTIONS.map((o) => (
                    <SelectItem key={o.value} value={o.value}>{o.label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <p className="text-[11px] text-muted-foreground">
                Draft aman untuk katalog baru — cek dulu, aktifkan massal dari halaman Produk.
              </p>
            </div>
            <div className="space-y-1.5">
              <Label className="text-xs text-muted-foreground">Konsentrasi</Label>
              <Select value={concMode} onValueChange={setConcMode}>
                <SelectTrigger className="h-9" data-testid={T.bulkFillConcentration}>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {CONC_OPTIONS.map((o) => (
                    <SelectItem key={o.value} value={o.value}>{o.label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <p className="text-[11px] text-muted-foreground">Hanya mengisi sel yang kosong.</p>
            </div>
            <div className="space-y-1.5">
              <Label className="text-xs text-muted-foreground">Harga yang sudah terisi</Label>
              <div className="flex items-center gap-2 h-9">
                <Switch
                  checked={overwritePrice} onCheckedChange={setOverwritePrice}
                  data-testid={T.bulkFillOverwrite} aria-label="Timpa harga yang sudah terisi"
                />
                <span className="text-xs text-foreground/80">
                  {overwritePrice ? 'Timpa semua' : 'Jangan ditimpa'}
                </span>
              </div>
              <p className="text-[11px] text-muted-foreground">
                Default: hanya baris berharga 0 yang diisi.
              </p>
            </div>
          </div>
        </div>

        {/* Ringkasan + terapkan */}
        <div className="mt-4 flex items-center justify-between gap-3 flex-wrap">
          <p className="text-xs text-muted-foreground flex items-start gap-1.5" data-testid={T.bulkFillPreview}>
            <Info className="h-3.5 w-3.5 mt-0.5 shrink-0" />
            <span>
              Akan mengisi <span className="font-medium text-foreground">{nf(preview.willFill)}</span> harga
              {preview.rowsWithoutCell > 0 && (
                <> · <span className="font-medium text-amber-700">{nf(preview.rowsWithoutCell)}</span> baris belum punya sel harga</>
              )}
              {statusMode !== 'file' && <> · status → <span className="font-medium text-foreground">{statusMode === 'archived' ? 'draft' : 'aktif'}</span></>}
              {stockEnabled && <> · stok → <span className="font-medium text-foreground">{parseRupiah(stockValue)}</span></>}
            </span>
          </p>
          <Button
            type="button" className="gap-2" disabled={!canApply}
            onClick={doApply} data-testid={T.bulkFillApply}
          >
            {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : <CheckCircle2 className="h-4 w-4" />}
            Terapkan ke {nf(total)} baris
          </Button>
        </div>
      </CardContent>
    </Card>
  );
};
