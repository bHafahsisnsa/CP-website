// pages/admin/AdminBackupPage.js — Backup & Restore data (admin-only).
// Fitur: pilih koleksi, unduh/ simpan backup (server), restore (upload/server) mode combine|overwrite.
import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { toast } from 'sonner';
import {
  DatabaseBackup, Download, Save, UploadCloud, RotateCcw, Trash2, AlertTriangle,
  Server, FileJson, Loader2, CheckCircle2, RefreshCw, ListChecks,
} from 'lucide-react';
import {
  listBackupCollections, exportBackup, createServerBackup, listServerBackups,
  downloadServerBackup, restoreServerBackup, deleteServerBackup, restoreFromFile,
} from '../../services/backup';
import { PageHeader, EmptyState, formatDateTime } from '../../components/admin/adminUi';
import { adminTestIds as T } from '../../constants/testIds/admin';
import {
  humanSize, readFileCollections, CollectionChecklist, RestoreReport,
} from '../../components/admin/backup/BackupPieces';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Textarea } from '../../components/ui/textarea';
import { Label } from '../../components/ui/label';
import { Badge } from '../../components/ui/badge';
import { Checkbox } from '../../components/ui/checkbox';
import { RadioGroup, RadioGroupItem } from '../../components/ui/radio-group';
import { Card, CardContent } from '../../components/ui/card';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '../../components/ui/tabs';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../../components/ui/table';
import {
  AlertDialog, AlertDialogContent, AlertDialogHeader, AlertDialogTitle, AlertDialogDescription,
  AlertDialogFooter, AlertDialogCancel, AlertDialogAction,
} from '../../components/ui/alert-dialog';


export default function AdminBackupPage() {
  const [tab, setTab] = useState('buat');
  const [collections, setCollections] = useState([]);
  const [loading, setLoading] = useState(true);

  // Buat backup
  const [selBackup, setSelBackup] = useState(new Set());
  const [note, setNote] = useState('');
  const [busyDownload, setBusyDownload] = useState(false);
  const [busySave, setBusySave] = useState(false);

  // Restore
  const [source, setSource] = useState('upload'); // 'upload' | 'server'
  const [file, setFile] = useState(null);
  const [fileInfo, setFileInfo] = useState(null); // {meta, names, counts}
  const [pickedServer, setPickedServer] = useState(null); // backup obj
  const [mode, setMode] = useState('combine');
  const [selRestore, setSelRestore] = useState(new Set());
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [busyRestore, setBusyRestore] = useState(false);
  const [report, setReport] = useState(null);

  // Server history
  const [servers, setServers] = useState([]);
  const [loadingServers, setLoadingServers] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState(null);

  const labelMap = useMemo(() => {
    const m = {};
    collections.forEach((c) => { m[c.name] = c.label; });
    return m;
  }, [collections]);

  const loadCollections = useCallback(() => {
    setLoading(true);
    listBackupCollections()
      .then((rows) => {
        setCollections(rows || []);
        setSelBackup(new Set((rows || []).map((r) => r.name)));
      })
      .catch(() => toast.error('Gagal memuat daftar koleksi.'))
      .finally(() => setLoading(false));
  }, []);

  const loadServers = useCallback(() => {
    setLoadingServers(true);
    listServerBackups()
      .then((rows) => setServers(rows || []))
      .catch(() => toast.error('Gagal memuat riwayat backup server.'))
      .finally(() => setLoadingServers(false));
  }, []);

  useEffect(() => { loadCollections(); loadServers(); }, [loadCollections, loadServers]);

  // ------- Buat backup handlers -------
  const toggleBackup = (name) => setSelBackup((prev) => {
    const s = new Set(prev); s.has(name) ? s.delete(name) : s.add(name); return s;
  });
  const selectAllBackup = () => setSelBackup(new Set(collections.map((c) => c.name)));
  const clearBackup = () => setSelBackup(new Set());

  const doDownload = async () => {
    if (selBackup.size === 0) { toast.error('Pilih minimal satu koleksi.'); return; }
    setBusyDownload(true);
    try {
      await exportBackup([...selBackup]);
      toast.success('Backup diunduh.');
    } catch (e) {
      toast.error(e?.response?.data?.detail || 'Gagal mengunduh backup.');
    } finally { setBusyDownload(false); }
  };

  const doSaveServer = async () => {
    if (selBackup.size === 0) { toast.error('Pilih minimal satu koleksi.'); return; }
    setBusySave(true);
    try {
      await createServerBackup([...selBackup], note.trim());
      toast.success('Backup tersimpan di server.');
      setNote('');
      loadServers();
    } catch (e) {
      toast.error(e?.response?.data?.detail || 'Gagal menyimpan backup.');
    } finally { setBusySave(false); }
  };

  // ------- Restore handlers -------
  const onFileChange = async (e) => {
    const f = e.target.files?.[0];
    setReport(null);
    if (!f) { setFile(null); setFileInfo(null); return; }
    setFile(f);
    try {
      const info = await readFileCollections(f);
      if (!info.names.length) { toast.error('File tidak berisi koleksi yang dikenali.'); setFileInfo(null); return; }
      setFileInfo(info);
      setSelRestore(new Set(info.names));
    } catch (err) {
      toast.error('File JSON tidak valid.');
      setFileInfo(null);
    }
  };

  const restoreItems = useMemo(() => {
    if (source === 'upload' && fileInfo) {
      return fileInfo.names.map((n) => ({ name: n, label: labelMap[n] || n, count: fileInfo.counts[n] }));
    }
    if (source === 'server' && pickedServer) {
      return (pickedServer.collections || []).map((n) => ({
        name: n, label: labelMap[n] || n, count: pickedServer.counts?.[n],
      }));
    }
    return [];
  }, [source, fileInfo, pickedServer, labelMap]);

  const toggleRestore = (name) => setSelRestore((prev) => {
    const s = new Set(prev); s.has(name) ? s.delete(name) : s.add(name); return s;
  });
  const selectAllRestore = () => setSelRestore(new Set(restoreItems.map((i) => i.name)));
  const clearRestore = () => setSelRestore(new Set());

  const canRestore = restoreItems.length > 0 && selRestore.size > 0;

  const runRestore = async () => {
    setConfirmOpen(false);
    setBusyRestore(true);
    setReport(null);
    try {
      const colls = [...selRestore];
      let res;
      if (source === 'upload') {
        res = await restoreFromFile(file, mode, colls);
      } else {
        res = await restoreServerBackup(pickedServer.id, mode, colls);
      }
      setReport(res);
      const s = res.summary || {};
      if (s.errors) toast.warning(`Restore selesai dengan ${s.errors} error. Cek laporan.`);
      else toast.success(`Restore selesai — ${s.written} dokumen ditulis.`);
      loadCollections();
    } catch (e) {
      toast.error(e?.response?.data?.detail || 'Gagal melakukan restore.');
    } finally { setBusyRestore(false); }
  };

  // ------- Server history handlers -------
  const doDownloadServer = async (b) => {
    try { await downloadServerBackup(b.id, b.filename); toast.success('Backup diunduh.'); }
    catch (e) { toast.error('Gagal mengunduh.'); }
  };
  const pickServerForRestore = (b) => {
    setSource('server');
    setPickedServer(b);
    setSelRestore(new Set(b.collections || []));
    setReport(null);
    setTab('restore');
  };
  const doDeleteServer = async () => {
    if (!deleteTarget) return;
    try {
      await deleteServerBackup(deleteTarget.id);
      toast.success('Backup dihapus.');
      if (pickedServer?.id === deleteTarget.id) setPickedServer(null);
      loadServers();
    } catch (e) { toast.error('Gagal menghapus.'); }
    finally { setDeleteTarget(null); }
  };

  return (
    <div data-testid={T.backupPage}>
      <PageHeader
        title="Backup & Restore"
        description="Ekspor data ke file JSON atau simpan di server, lalu pulihkan dengan mode Overwrite atau Combine."
      />

      <div className="mb-5 flex items-start gap-2 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
        <AlertTriangle className="h-4 w-4 mt-0.5 shrink-0" />
        <p>
          Restore mengubah data secara langsung. <b>Overwrite</b> mengosongkan koleksi lalu menggantinya penuh dari backup.
          <b> Combine</b> menimpa dokumen ber-ID sama (data backup menang) dan menambah yang baru. Sesi login tidak ikut dipulihkan.
        </p>
      </div>

      <Card className="border-border/70">
        <CardContent className="p-4">
          <Tabs value={tab} onValueChange={setTab}>
            <TabsList className="flex flex-wrap h-auto">
              <TabsTrigger value="buat" className="gap-1.5"><DatabaseBackup className="h-4 w-4" /> Buat Backup</TabsTrigger>
              <TabsTrigger value="restore" className="gap-1.5"><RotateCcw className="h-4 w-4" /> Restore</TabsTrigger>
              <TabsTrigger value="riwayat" className="gap-1.5"><Server className="h-4 w-4" /> Riwayat Server</TabsTrigger>
            </TabsList>

            {/* ============ Tab: Buat Backup ============ */}
            <TabsContent value="buat" className="pt-5">
              {loading ? (
                <div className="py-10 text-center text-sm text-muted-foreground">Memuat koleksi…</div>
              ) : collections.length === 0 ? (
                <EmptyState title="Tidak ada koleksi" />
              ) : (
                <div className="space-y-5">
                  <CollectionChecklist
                    items={collections}
                    selected={selBackup}
                    onToggle={toggleBackup}
                    onSelectAll={selectAllBackup}
                    onClear={clearBackup}
                  />
                  <div className="space-y-1.5 max-w-xl">
                    <Label className="text-xs text-muted-foreground">Catatan (opsional — untuk backup server)</Label>
                    <Textarea
                      value={note} onChange={(e) => setNote(e.target.value)}
                      placeholder="mis. Sebelum impor produk massal"
                      rows={2} data-testid={T.backupNote}
                    />
                  </div>
                  <div className="flex flex-wrap gap-3">
                    <Button onClick={doDownload} disabled={busyDownload || selBackup.size === 0} className="gap-2" data-testid={T.backupDownload}>
                      {busyDownload ? <Loader2 className="h-4 w-4 animate-spin" /> : <Download className="h-4 w-4" />}
                      Unduh File Backup (.json)
                    </Button>
                    <Button onClick={doSaveServer} disabled={busySave || selBackup.size === 0} variant="secondary" className="gap-2" data-testid={T.backupSaveServer}>
                      {busySave ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
                      Simpan Backup ke Server
                    </Button>
                  </div>
                </div>
              )}
            </TabsContent>

            {/* ============ Tab: Restore ============ */}
            <TabsContent value="restore" className="pt-5">
              <div className="space-y-6">
                {/* Sumber */}
                <div>
                  <div className="text-sm font-semibold mb-3">1. Sumber Backup</div>
                  <RadioGroup value={source} onValueChange={(v) => { setSource(v); setReport(null); }} className="flex flex-col sm:flex-row gap-3">
                    <label className={`flex-1 flex items-start gap-3 rounded-xl border px-4 py-3 cursor-pointer ${source === 'upload' ? 'border-[#B89B6A] bg-[rgba(184,155,106,0.08)]' : 'border-border'}`}>
                      <RadioGroupItem value="upload" className="mt-0.5" data-testid={T.restoreSourceUpload} />
                      <div>
                        <div className="text-sm font-medium flex items-center gap-1.5"><UploadCloud className="h-4 w-4" /> Unggah File</div>
                        <div className="text-xs text-muted-foreground">Pilih file backup .json dari komputer.</div>
                      </div>
                    </label>
                    <label className={`flex-1 flex items-start gap-3 rounded-xl border px-4 py-3 cursor-pointer ${source === 'server' ? 'border-[#B89B6A] bg-[rgba(184,155,106,0.08)]' : 'border-border'}`}>
                      <RadioGroupItem value="server" className="mt-0.5" data-testid={T.restoreSourceServer} />
                      <div>
                        <div className="text-sm font-medium flex items-center gap-1.5"><Server className="h-4 w-4" /> Dari Server</div>
                        <div className="text-xs text-muted-foreground">Pakai backup yang tersimpan di server.</div>
                      </div>
                    </label>
                  </RadioGroup>

                  {source === 'upload' ? (
                    <div className="mt-3">
                      <Input type="file" accept=".json,application/json" onChange={onFileChange} data-testid={T.restoreFileInput} className="max-w-md" />
                      {fileInfo?.meta ? (
                        <p className="mt-2 text-xs text-muted-foreground">
                          Backup dibuat {formatDateTime(fileInfo.meta.created_at)} · DB {fileInfo.meta.db_name || '—'}
                        </p>
                      ) : null}
                    </div>
                  ) : (
                    <div className="mt-3">
                      {servers.length === 0 ? (
                        <p className="text-sm text-muted-foreground">Belum ada backup di server. Buat di tab "Buat Backup".</p>
                      ) : (
                        <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
                          {servers.map((b) => (
                            <button
                              key={b.id} type="button" onClick={() => { setPickedServer(b); setSelRestore(new Set(b.collections || [])); setReport(null); }}
                              className={`text-left rounded-xl border px-3 py-2.5 transition-colors ${pickedServer?.id === b.id ? 'border-[#B89B6A] bg-[rgba(184,155,106,0.08)]' : 'border-border hover:bg-muted/40'}`}
                            >
                              <div className="text-xs font-medium flex items-center gap-1.5"><FileJson className="h-3.5 w-3.5" /> {formatDateTime(b.created_at)}</div>
                              <div className="text-[11px] text-muted-foreground mt-1">{(b.collections || []).length} koleksi · {humanSize(b.size)}</div>
                              {b.note ? <div className="text-[11px] text-muted-foreground truncate mt-0.5 italic">"{b.note}"</div> : null}
                            </button>
                          ))}
                        </div>
                      )}
                    </div>
                  )}
                </div>

                {/* Koleksi yang dipulihkan */}
                {restoreItems.length > 0 ? (
                  <div>
                    <div className="text-sm font-semibold mb-3">2. Koleksi yang Dipulihkan</div>
                    <CollectionChecklist
                      items={restoreItems}
                      selected={selRestore}
                      onToggle={toggleRestore}
                      onSelectAll={selectAllRestore}
                      onClear={clearRestore}
                    />
                  </div>
                ) : null}

                {/* Mode */}
                {restoreItems.length > 0 ? (
                  <div>
                    <div className="text-sm font-semibold mb-3">3. Mode Restore</div>
                    <RadioGroup value={mode} onValueChange={setMode} className="flex flex-col sm:flex-row gap-3">
                      <label className={`flex-1 flex items-start gap-3 rounded-xl border px-4 py-3 cursor-pointer ${mode === 'combine' ? 'border-[#B89B6A] bg-[rgba(184,155,106,0.08)]' : 'border-border'}`}>
                        <RadioGroupItem value="combine" className="mt-0.5" data-testid={T.restoreModeCombine} />
                        <div>
                          <div className="text-sm font-medium">Combine (gabung)</div>
                          <div className="text-xs text-muted-foreground">Menimpa dokumen ber-ID sama (data backup menang) & menambah yang baru. Data lain tetap.</div>
                        </div>
                      </label>
                      <label className={`flex-1 flex items-start gap-3 rounded-xl border px-4 py-3 cursor-pointer ${mode === 'overwrite' ? 'border-rose-300 bg-rose-50' : 'border-border'}`}>
                        <RadioGroupItem value="overwrite" className="mt-0.5" data-testid={T.restoreModeOverwrite} />
                        <div>
                          <div className="text-sm font-medium text-rose-700">Overwrite (timpa penuh)</div>
                          <div className="text-xs text-muted-foreground">Mengosongkan koleksi terpilih lalu mengisi penuh dari backup. Data yang tidak ada di backup akan hilang.</div>
                        </div>
                      </label>
                    </RadioGroup>
                  </div>
                ) : null}

                <div>
                  <Button
                    onClick={() => setConfirmOpen(true)}
                    disabled={!canRestore || busyRestore}
                    className="gap-2"
                    data-testid={T.restoreRun}
                  >
                    {busyRestore ? <Loader2 className="h-4 w-4 animate-spin" /> : <RotateCcw className="h-4 w-4" />}
                    Jalankan Restore
                  </Button>
                </div>

                <RestoreReport report={report} />
              </div>
            </TabsContent>

            {/* ============ Tab: Riwayat Server ============ */}
            <TabsContent value="riwayat" className="pt-5">
              <div className="flex justify-end mb-3">
                <Button variant="outline" size="sm" onClick={loadServers} className="gap-2" disabled={loadingServers}>
                  <RefreshCw className={`h-4 w-4 ${loadingServers ? 'animate-spin' : ''}`} /> Segarkan
                </Button>
              </div>
              {servers.length === 0 ? (
                <EmptyState title="Belum ada backup di server" hint="Buat backup dari tab 'Buat Backup' lalu pilih 'Simpan Backup ke Server'." />
              ) : (
                <Table data-testid={T.serverBackupTable}>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Dibuat</TableHead>
                      <TableHead>Koleksi</TableHead>
                      <TableHead className="text-right">Ukuran</TableHead>
                      <TableHead>Catatan</TableHead>
                      <TableHead className="w-40 text-right">Aksi</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {servers.map((b) => (
                      <TableRow key={b.id}>
                        <TableCell className="text-sm">{formatDateTime(b.created_at)}</TableCell>
                        <TableCell>
                          <div className="flex flex-wrap gap-1 max-w-md">
                            {(b.collections || []).slice(0, 6).map((c) => (
                              <Badge key={c} variant="outline" className="text-[10px] font-mono">{c}</Badge>
                            ))}
                            {(b.collections || []).length > 6 ? (
                              <Badge variant="outline" className="text-[10px]">+{b.collections.length - 6}</Badge>
                            ) : null}
                          </div>
                        </TableCell>
                        <TableCell className="text-right font-mono text-sm">{humanSize(b.size)}</TableCell>
                        <TableCell className="text-xs text-muted-foreground max-w-[180px] truncate italic">{b.note || '—'}</TableCell>
                        <TableCell className="text-right">
                          <div className="flex justify-end gap-1">
                            <Button variant="ghost" size="icon" onClick={() => doDownloadServer(b)} aria-label="Unduh" title="Unduh"><Download className="h-4 w-4" /></Button>
                            <Button variant="ghost" size="icon" onClick={() => pickServerForRestore(b)} aria-label="Restore" title="Restore"><RotateCcw className="h-4 w-4 text-[#B89B6A]" /></Button>
                            <Button variant="ghost" size="icon" onClick={() => setDeleteTarget(b)} aria-label="Hapus" title="Hapus"><Trash2 className="h-4 w-4 text-rose-600" /></Button>
                          </div>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>

      {/* Konfirmasi restore */}
      <AlertDialog open={confirmOpen} onOpenChange={setConfirmOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle className="flex items-center gap-2">
              <AlertTriangle className={`h-5 w-5 ${mode === 'overwrite' ? 'text-rose-600' : 'text-amber-500'}`} />
              Konfirmasi Restore
            </AlertDialogTitle>
            <AlertDialogDescription>
              Anda akan memulihkan <b>{selRestore.size}</b> koleksi dengan mode <b className="uppercase">{mode}</b>.
              {mode === 'overwrite'
                ? ' Koleksi terpilih akan DIKOSONGKAN lalu diisi penuh dari backup. Tindakan ini tidak dapat dibatalkan.'
                : ' Dokumen dengan ID sama akan ditimpa oleh data backup, dokumen baru ditambahkan.'}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Batal</AlertDialogCancel>
            <AlertDialogAction
              onClick={runRestore}
              data-testid={T.restoreConfirm}
              className={mode === 'overwrite' ? 'bg-rose-600 hover:bg-rose-700' : ''}
            >
              Ya, Jalankan Restore
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Konfirmasi hapus backup server */}
      <AlertDialog open={!!deleteTarget} onOpenChange={(o) => !o && setDeleteTarget(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Hapus backup?</AlertDialogTitle>
            <AlertDialogDescription>
              Backup {deleteTarget ? formatDateTime(deleteTarget.created_at) : ''} akan dihapus permanen dari server.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Batal</AlertDialogCancel>
            <AlertDialogAction onClick={doDeleteServer} className="bg-rose-600 hover:bg-rose-700">Hapus</AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
