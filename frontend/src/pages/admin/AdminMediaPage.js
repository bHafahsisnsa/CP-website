// pages/admin/AdminMediaPage.js — Media Manager (E20).
//
// Pusat kelola berkas gambar untuk produk, konten, kategori, lokasi toko, dan
// pengaturan pembayaran. Semua berkas disimpan di penyimpanan LOKAL server.
//
// Layout master-detail 3 kolom (rail folder | kanvas aset | inspektur detail).
// Di bawah xl inspektur memakai <Sheet>; di mobile rail folder juga <Sheet>.
import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import {
  Copy, FolderInput, FolderTree as FolderTreeIcon, HardDrive, Loader2, RefreshCw,
  AlertTriangle, ShieldCheck, Trash2, X,
} from 'lucide-react';
import { toast } from 'sonner';
import { Badge } from '../../components/ui/badge';
import { Button } from '../../components/ui/button';
import { Card, CardContent } from '../../components/ui/card';
import {
  Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle,
} from '../../components/ui/sheet';
import { EmptyState, MetricCard, PageHeader, ACCENT, ACCENT_SOFT } from '../../components/admin/adminUi';
import { FolderTree, flattenTree } from '../../components/admin/media/FolderTree';
import { MediaToolbar } from '../../components/admin/media/MediaToolbar';
import { AssetGrid, AssetList } from '../../components/admin/media/AssetGrid';
import { AssetDetailsPanel } from '../../components/admin/media/AssetDetailsPanel';
import { Dropzone } from '../../components/admin/media/Dropzone';
import { UploadQueuePanel } from '../../components/admin/media/UploadQueuePanel';
import { useMediaUpload } from '../../components/admin/media/useMediaUpload';
import {
  ConfirmDialog, FolderNameDialog, FromUrlDialog, MoveToFolderDialog,
} from '../../components/admin/media/MediaDialogs';
import { adminTestIds as T } from '../../constants/testIds/admin';
import { formatBytes, resolveMediaUrl } from '../../lib/mediaUrl';
import {
  bulkDeleteAssets, bulkMoveAssets, createFolder, deleteAsset, deleteFolder,
  getFolderTree, getMediaStats, ingestUrl, listAssets, localizeExternalMedia,
  mediaErrorMessage, moveAsset, moveFolder, renameFolder, replaceAsset, updateAsset,
} from '../../services/media';

const PAGE_SIZE = 40;

export default function AdminMediaPage() {
  // ---------- state data ----------
  const [tree, setTree] = useState([]);
  const [root, setRoot] = useState(null);
  const [folderId, setFolderId] = useState('');
  const [items, setItems] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  // ---------- state UI ----------
  const [qInput, setQInput] = useState('');
  const [q, setQ] = useState('');
  const [kind, setKind] = useState('all');
  const [sort, setSort] = useState('newest');
  const [view, setView] = useState('grid');
  const [recursive, setRecursive] = useState(true);
  const [selected, setSelected] = useState([]);
  const [focused, setFocused] = useState(null);
  const [mobileRail, setMobileRail] = useState(false);
  const [mobileDetails, setMobileDetails] = useState(false);

  // ---------- dialog ----------
  const [folderDialog, setFolderDialog] = useState(null); // {mode, parentId, node}
  const [moveDialog, setMoveDialog] = useState(null);     // {ids} | {folder}
  const [urlDialog, setUrlDialog] = useState(false);
  const [confirm, setConfirm] = useState(null);           // {kind, payload}
  const [dropOverlay, setDropOverlay] = useState(false);
  const dragDepth = useRef(0);
  const dropzoneRef = useRef(null);

  const flat = useMemo(() => flattenTree(tree), [tree]);
  const activeFolder = folderId ? flat.find((f) => f.id === folderId) : null;
  const folderNameOf = (id) => (id ? (flat.find((f) => f.id === id)?.name || '—') : 'Semua Media');

  // ---------- loaders ----------
  const loadTree = useCallback(async () => {
    try {
      const t = await getFolderTree();
      setTree(t?.tree || []);
      setRoot(t?.root || null);
    } catch (e) {
      toast.error(mediaErrorMessage(e, 'Gagal memuat daftar folder.'));
    }
  }, []);

  const loadStats = useCallback(async () => {
    try { setStats(await getMediaStats()); } catch (e) { /* opsional */ }
  }, []);

  const loadAssets = useCallback(async () => {
    setLoading(true);
    try {
      const res = await listAssets({
        folderId: folderId || '',
        q,
        kind: kind === 'all' ? '' : kind,
        sort,
        page,
        limit: PAGE_SIZE,
        recursive: !!folderId && recursive,
      });
      setItems(res.items);
      setTotal(res.total);
    } catch (e) {
      toast.error(mediaErrorMessage(e, 'Gagal memuat pustaka media.'));
      setItems([]);
      setTotal(0);
    } finally { setLoading(false); }
  }, [folderId, q, kind, sort, page, recursive]);

  useEffect(() => { loadTree(); loadStats(); }, [loadTree, loadStats]);
  useEffect(() => { loadAssets(); }, [loadAssets]);
  useEffect(() => {
    const t = setTimeout(() => { setQ(qInput); setPage(1); }, 320);
    return () => clearTimeout(t);
  }, [qInput]);

  const refreshAll = useCallback(async () => {
    await Promise.all([loadAssets(), loadTree(), loadStats()]);
  }, [loadAssets, loadTree, loadStats]);

  // ---------- upload ----------
  const onUploaded = useCallback((assets) => {
    toast.success(`${assets.length} berkas berhasil diunggah.`);
    refreshAll();
    if (assets.length === 1) setFocused(assets[0]);
  }, [refreshAll]);
  const upload = useMediaUpload({ folderId: folderId || null, onUploaded });

  // Overlay drag & drop pada seluruh kanvas.
  useEffect(() => {
    const hasFiles = (e) => Array.from(e.dataTransfer?.types || []).includes('Files');
    const onEnter = (e) => {
      if (!hasFiles(e)) return;
      dragDepth.current += 1;
      setDropOverlay(true);
    };
    const onLeave = () => {
      dragDepth.current = Math.max(0, dragDepth.current - 1);
      if (dragDepth.current === 0) setDropOverlay(false);
    };
    const onOver = (e) => { if (hasFiles(e)) e.preventDefault(); };
    const onDrop = (e) => {
      dragDepth.current = 0;
      setDropOverlay(false);
      if (!hasFiles(e)) return;
      e.preventDefault();
      if (e.dataTransfer.files?.length) upload.enqueue(e.dataTransfer.files);
    };
    window.addEventListener('dragenter', onEnter);
    window.addEventListener('dragleave', onLeave);
    window.addEventListener('dragover', onOver);
    window.addEventListener('drop', onDrop);
    return () => {
      window.removeEventListener('dragenter', onEnter);
      window.removeEventListener('dragleave', onLeave);
      window.removeEventListener('dragover', onOver);
      window.removeEventListener('drop', onDrop);
    };
  }, [upload]);

  // ---------- aksi folder ----------
  const submitFolder = async (name) => {
    setSaving(true);
    try {
      if (folderDialog?.mode === 'rename') {
        await renameFolder(folderDialog.node.id, name);
        toast.success('Nama folder diperbarui.');
      } else {
        const f = await createFolder(name, folderDialog?.parentId || null);
        toast.success(`Folder “${f.name}” dibuat.`);
        setFolderId(f.id);
      }
      setFolderDialog(null);
      await refreshAll();
    } catch (e) {
      toast.error(mediaErrorMessage(e, 'Gagal menyimpan folder.'));
    } finally { setSaving(false); }
  };

  const doDeleteFolder = async (cascade) => {
    const node = confirm?.payload;
    setSaving(true);
    try {
      const res = await deleteFolder(node.id, cascade);
      toast.success(cascade
        ? 'Folder & seluruh isinya dihapus.'
        : `Folder dihapus. ${res.moved_assets || 0} berkas dipindahkan ke folder induk.`);
      if (folderId === node.id) setFolderId('');
      setConfirm(null);
      await refreshAll();
    } catch (e) {
      toast.error(mediaErrorMessage(e, 'Gagal menghapus folder.'));
    } finally { setSaving(false); }
  };

  const doMoveFolder = async (id, parentId) => {
    try {
      await moveFolder(id, parentId);
      toast.success('Folder dipindahkan.');
      await refreshAll();
    } catch (e) {
      toast.error(mediaErrorMessage(e, 'Gagal memindahkan folder.'));
    }
  };

  // ---------- aksi aset ----------
  const toggleSelect = (id) => setSelected((s) => (
    s.includes(id) ? s.filter((x) => x !== id) : [...s, id]
  ));
  const allSelected = items.length > 0 && items.every((i) => selected.includes(i.id));
  const toggleAll = () => setSelected(allSelected ? [] : items.map((i) => i.id));

  const openAsset = (asset) => {
    setFocused(asset);
    if (window.innerWidth < 1280) setMobileDetails(true);
  };

  const copyUrl = async (asset) => {
    const abs = resolveMediaUrl(asset.url);
    try {
      await navigator.clipboard.writeText(abs);
      toast.success('Tautan disalin.');
    } catch (e) {
      toast.error('Tidak bisa menyalin otomatis. Buka detail berkas untuk menyalin manual.');
    }
  };

  const saveAsset = async (patch) => {
    if (!focused) return;
    setSaving(true);
    try {
      const updated = await updateAsset(focused.id, patch);
      setFocused(updated);
      setItems((arr) => arr.map((a) => (a.id === updated.id ? updated : a)));
      toast.success('Perubahan disimpan.');
    } catch (e) {
      toast.error(mediaErrorMessage(e, 'Gagal menyimpan perubahan.'));
    } finally { setSaving(false); }
  };

  const doReplace = async (file) => {
    if (!focused) return;
    try {
      const updated = await replaceAsset(focused.id, file);
      setFocused(updated);
      toast.success('Berkas diganti. URL tetap sama.');
      await loadAssets();
    } catch (e) {
      toast.error(mediaErrorMessage(e, 'Gagal mengganti berkas.'));
    }
  };

  const doDeleteAsset = async () => {
    const asset = confirm?.payload;
    setSaving(true);
    try {
      await deleteAsset(asset.id);
      toast.success('Berkas dihapus.');
      if (focused?.id === asset.id) { setFocused(null); setMobileDetails(false); }
      setSelected((s) => s.filter((x) => x !== asset.id));
      setConfirm(null);
      await refreshAll();
    } catch (e) {
      toast.error(mediaErrorMessage(e, 'Gagal menghapus berkas.'));
    } finally { setSaving(false); }
  };

  const doBulkDelete = async () => {
    setSaving(true);
    try {
      const res = await bulkDeleteAssets(selected);
      toast.success(`${res.count || 0} berkas dihapus.`);
      setSelected([]);
      setFocused(null);
      setConfirm(null);
      await refreshAll();
    } catch (e) {
      toast.error(mediaErrorMessage(e, 'Gagal menghapus berkas terpilih.'));
    } finally { setSaving(false); }
  };

  const doMoveAssets = async (ids, targetFolderId) => {
    try {
      if (ids.length === 1) await moveAsset(ids[0], targetFolderId);
      else await bulkMoveAssets(ids, targetFolderId);
      toast.success(`${ids.length} berkas dipindahkan ke ${folderNameOf(targetFolderId)}.`);
      setMoveDialog(null);
      setSelected([]);
      await refreshAll();
    } catch (e) {
      toast.error(mediaErrorMessage(e, 'Gagal memindahkan berkas.'));
    }
  };

  const submitUrl = async (url, alt) => {
    setSaving(true);
    try {
      const asset = await ingestUrl(url, { folderId: folderId || null, alt });
      toast.success('Gambar diunduh & disimpan di penyimpanan lokal.');
      setUrlDialog(false);
      setFocused(asset);
      await refreshAll();
    } catch (e) {
      toast.error(mediaErrorMessage(e, 'Gagal mengunduh gambar dari URL.'));
    } finally { setSaving(false); }
  };

  // Perbaiki gambar yang masih menautkan ke situs luar: unduh ke lokal lalu
  // perbarui semua referensinya (produk, kategori, CMS, toko, pembayaran).
  const [localizing, setLocalizing] = useState(false);
  const doLocalize = async () => {
    setLocalizing(true);
    setConfirm(null);
    try {
      const res = await localizeExternalMedia();
      if (res.converted) {
        toast.success(
          `${res.converted} gambar eksternal berhasil disimpan lokal · ${res.refs_updated} referensi diperbarui.`,
        );
      } else {
        toast.info('Tidak ada gambar eksternal yang perlu diperbaiki.');
      }
      if (res.failed?.length) {
        toast.error(`${res.failed.length} gambar gagal diunduh (sumber tidak dapat diakses).`);
      }
      await refreshAll();
    } catch (e) {
      toast.error(mediaErrorMessage(e, 'Gagal memperbaiki gambar eksternal.'));
    } finally { setLocalizing(false); }
  };

  const pages = Math.max(1, Math.ceil(total / PAGE_SIZE));
  const rangeFrom = total ? (page - 1) * PAGE_SIZE + 1 : 0;
  const rangeTo = Math.min(total, page * PAGE_SIZE);

  // ---------- render ----------
  const railContent = (
    <FolderTree
      tree={tree}
      root={root}
      activeId={folderId}
      onSelect={(id) => { setFolderId(id); setPage(1); setSelected([]); setMobileRail(false); }}
      onCreateChild={(parentId) => setFolderDialog({ mode: 'create', parentId })}
      onRename={(node) => setFolderDialog({ mode: 'rename', node })}
      onDelete={(node) => setConfirm({ kind: 'folder', payload: node })}
      onMoveAssets={doMoveAssets}
      onMoveFolder={doMoveFolder}
    />
  );

  const assetsArea = (
    <>
      {!loading && !items.length ? (
        <div className="space-y-4">
          <EmptyState
            title={q ? 'Tidak ada hasil' : folderId ? 'Folder ini kosong' : 'Belum ada media'}
            hint={q
              ? 'Coba kata kunci lain atau ubah filter tipe.'
              : 'Seret berkas ke halaman ini, klik Upload, atau tambahkan dari URL. Semua gambar disimpan di penyimpanan lokal server.'}
            action={q ? (
              <Button variant="secondary" className="rounded-lg" onClick={() => setQInput('')}>
                Bersihkan pencarian
              </Button>
            ) : null}
          />
          {!q ? (
            <Dropzone onFiles={upload.enqueue} busy={upload.busy} />
          ) : null}
        </div>
      ) : view === 'grid' ? (
        <AssetGrid
          items={items}
          loading={loading}
          selectedIds={selected}
          focusedId={focused?.id}
          onToggleSelect={toggleSelect}
          onOpen={openAsset}
          onDetails={openAsset}
          onCopy={copyUrl}
          onMove={(a) => setMoveDialog({ ids: [a.id] })}
          onDelete={(a) => setConfirm({ kind: 'asset', payload: a })}
        />
      ) : (
        <AssetList
          items={items}
          loading={loading}
          selectedIds={selected}
          focusedId={focused?.id}
          onToggleSelect={toggleSelect}
          onOpen={openAsset}
          onDetails={openAsset}
          onCopy={copyUrl}
          onMove={(a) => setMoveDialog({ ids: [a.id] })}
          onDelete={(a) => setConfirm({ kind: 'asset', payload: a })}
          allSelected={allSelected}
          onToggleAll={toggleAll}
        />
      )}
    </>
  );

  return (
    <div data-testid={T.mediaPage}>
      <PageHeader
        title="Media"
        description="Kelola gambar untuk produk, konten, kategori, lokasi toko, dan pembayaran. Semua berkas tersimpan di penyimpanan lokal server."
        testId={T.mediaPageHeader}
        actions={(
          <>
            <Button
              variant="secondary"
              className="gap-2 rounded-lg xl:hidden"
              onClick={() => setMobileRail(true)}
              data-testid={T.mediaOpenRail}
            >
              <FolderTreeIcon className="h-4 w-4" /> Folder
            </Button>
            <Button
              variant="secondary"
              className="gap-2 rounded-lg"
              onClick={refreshAll}
              data-testid={T.mediaRefresh}
            >
              <RefreshCw className="h-4 w-4" /> Muat Ulang
            </Button>
          </>
        )}
      />

      {/* ---------- statistik penyimpanan ---------- */}
      <div className="mb-5 grid grid-cols-2 gap-3 lg:grid-cols-4">
        <MetricCard
          label="Jumlah berkas"
          value={stats ? stats.assets : '—'}
          sub={stats ? `${stats.local_assets} berkas lokal` : ' '}
          testId={T.mediaStatFiles}
          accent
        />
        <MetricCard
          label="Total ukuran"
          value={stats ? formatBytes(stats.bytes) : '—'}
          sub={stats ? `di disk: ${formatBytes(stats.disk_bytes)}` : ' '}
          testId={T.mediaStatSize}
        />
        <MetricCard
          label="Folder"
          value={stats ? stats.folders : '—'}
          sub="bertingkat tanpa batas"
          testId={T.mediaStatFolders}
        />
        <MetricCard
          label="Batas upload"
          value={stats ? `${stats.max_mb} MB` : '—'}
          sub={stats?.mirror ? 'cadangan otomatis aktif' : 'cadangan otomatis nonaktif'}
          testId={T.mediaStatLimit}
        />
      </div>

      {/* ---------- peringatan gambar hotlink (penyebab broken image) ---------- */}
      {stats && stats.hotlinked > 0 ? (
        <div
          className="mb-5 flex flex-col gap-3 rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3.5 sm:flex-row sm:items-center sm:justify-between"
          data-testid={T.mediaHotlinkWarning}
        >
          <div className="flex min-w-0 items-start gap-2.5">
            <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-amber-700" aria-hidden="true" />
            <div className="min-w-0">
              <p className="text-sm font-medium text-amber-900">
                {stats.hotlinked} gambar masih menautkan ke situs luar
              </p>
              <p className="mt-0.5 text-xs leading-relaxed text-amber-800">
                Gambar seperti ini bisa jadi <strong>broken</strong> kapan saja bila situs sumbernya
                mati atau memblokir hotlink. Klik perbaiki untuk mengunduh semuanya ke penyimpanan
                lokal — referensi di produk, kategori, konten, lokasi toko, dan pembayaran otomatis
                diperbarui.
              </p>
            </div>
          </div>
          <Button
            className="shrink-0 gap-2 rounded-lg"
            onClick={() => setConfirm({ kind: 'localize' })}
            disabled={localizing}
            data-testid={T.mediaLocalizeBtn}
          >
            {localizing ? <Loader2 className="h-4 w-4 animate-spin" /> : <ShieldCheck className="h-4 w-4" />}
            {localizing ? 'Memperbaiki…' : 'Perbaiki Sekarang'}
          </Button>
        </div>
      ) : null}

      <div className="grid grid-cols-12 gap-4">
        {/* ---------- rail folder (desktop) ---------- */}
        <aside className="hidden xl:col-span-2 xl:block">
          <div className="sticky top-4 overflow-hidden rounded-2xl border border-border/70 bg-card">
            <div className="flex items-center justify-between border-b border-border/70 px-3 py-2.5">
              <span className="text-[10px] font-semibold uppercase tracking-[0.16em] text-muted-foreground">
                Folder
              </span>
              <Button
                size="sm"
                variant="ghost"
                className="h-7 rounded-md px-2 text-xs"
                onClick={() => setFolderDialog({ mode: 'create', parentId: folderId || null })}
                data-testid={T.mediaRailNewFolder}
              >
                + Baru
              </Button>
            </div>
            <div className="max-h-[62vh] overflow-y-auto p-2">{railContent}</div>
          </div>
        </aside>

        {/* ---------- kanvas aset ---------- */}
        <main className="col-span-12 min-w-0 xl:col-span-7">
          <Card className="border-border/70">
            <CardContent className="p-4">
              <div className="mb-3 flex flex-wrap items-center gap-1.5 text-xs text-muted-foreground" data-testid={T.mediaBreadcrumb}>
                <button
                  type="button"
                  className="rounded px-1 py-0.5 transition-colors hover:bg-muted hover:text-foreground"
                  onClick={() => { setFolderId(''); setPage(1); }}
                >
                  Semua Media
                </button>
                {(activeFolder?.path || '').split('/').filter(Boolean).map((seg, i, arr) => (
                  <React.Fragment key={`${seg}-${i}`}>
                    <span aria-hidden="true">/</span>
                    <span className={i === arr.length - 1 ? 'font-medium text-foreground' : ''}>{seg}</span>
                  </React.Fragment>
                ))}
              </div>

              <MediaToolbar
                query={qInput}
                onQueryChange={setQInput}
                kind={kind}
                onKindChange={(v) => { setKind(v); setPage(1); }}
                sort={sort}
                onSortChange={(v) => { setSort(v); setPage(1); }}
                view={view}
                onViewChange={setView}
                onUpload={() => dropzoneRef.current?.pick?.()}
                onNewFolder={() => setFolderDialog({ mode: 'create', parentId: folderId || null })}
                onFromUrl={() => setUrlDialog(true)}
                recursive={recursive}
                onRecursiveChange={folderId ? (v) => { setRecursive(v); setPage(1); } : null}
                className="mb-4"
              />

              {/* Dropzone tipis selalu terlihat (fallback non-drag). */}
              <Dropzone
                onFiles={upload.enqueue}
                busy={upload.busy}
                compact
                className="mb-4"
                title={folderId ? `Seret berkas ke folder “${activeFolder?.name}”` : 'Seret & lepas gambar di sini'}
              />

              <UploadQueuePanel
                queue={upload.queue}
                onRetry={upload.retry}
                onRemove={upload.remove}
                onClearDone={upload.clearDone}
                className="mb-4"
              />

              {assetsArea}

              {total > 0 ? (
                <div className="mt-4 flex flex-wrap items-center justify-between gap-2 border-t border-border/60 pt-3">
                  <span className="text-[11px] text-muted-foreground" data-testid={T.mediaPageInfo}>
                    Menampilkan {rangeFrom}–{rangeTo} dari {total} berkas
                  </span>
                  {pages > 1 ? (
                    <div className="flex gap-1.5">
                      <Button
                        size="sm"
                        variant="secondary"
                        className="h-7 rounded-md px-2 text-xs"
                        disabled={page <= 1}
                        onClick={() => setPage((p) => Math.max(1, p - 1))}
                        data-testid={T.mediaPrevPage}
                      >
                        Sebelumnya
                      </Button>
                      <Button
                        size="sm"
                        variant="secondary"
                        className="h-7 rounded-md px-2 text-xs"
                        disabled={page >= pages}
                        onClick={() => setPage((p) => Math.min(pages, p + 1))}
                        data-testid={T.mediaNextPage}
                      >
                        Berikutnya
                      </Button>
                    </div>
                  ) : null}
                </div>
              ) : null}
            </CardContent>
          </Card>

          {/* ---------- bilah aksi massal ---------- */}
          {selected.length ? (
            <div
              className="sticky bottom-4 z-20 mt-4 flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-border/70 bg-card px-4 py-3 shadow-lg"
              data-testid={T.mediaBulkBar}
            >
              <div className="flex items-center gap-2">
                <Badge variant="outline" style={{ borderColor: ACCENT, color: ACCENT, background: ACCENT_SOFT }}>
                  {selected.length} dipilih
                </Badge>
                <Button
                  size="sm"
                  variant="ghost"
                  className="h-7 rounded-md px-2 text-xs"
                  onClick={toggleAll}
                  data-testid={T.mediaBulkSelectAll}
                >
                  {allSelected ? 'Batal pilih semua' : 'Pilih semua di halaman ini'}
                </Button>
              </div>
              <div className="flex items-center gap-2">
                <Button
                  size="sm"
                  variant="secondary"
                  className="gap-1.5 rounded-lg"
                  onClick={() => setMoveDialog({ ids: selected })}
                  data-testid={T.mediaBulkMove}
                >
                  <FolderInput className="h-3.5 w-3.5" /> Pindahkan
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  className="gap-1.5 rounded-lg border-rose-200 text-rose-600 hover:bg-rose-50"
                  onClick={() => setConfirm({ kind: 'bulk' })}
                  data-testid={T.mediaBulkDelete}
                >
                  <Trash2 className="h-3.5 w-3.5" /> Hapus
                </Button>
                <Button
                  size="sm"
                  variant="ghost"
                  className="gap-1.5"
                  onClick={() => setSelected([])}
                  data-testid={T.mediaBulkClear}
                >
                  <X className="h-3.5 w-3.5" /> Batal
                </Button>
              </div>
            </div>
          ) : null}
        </main>

        {/* ---------- inspektur (desktop xl) ---------- */}
        <aside className="hidden xl:col-span-3 xl:block">
          <div className="sticky top-4 max-h-[calc(100vh-2rem)]">
            <AssetDetailsPanel
              asset={focused}
              folderName={folderNameOf(focused?.folder_id)}
              busy={saving}
              onSave={saveAsset}
              onMove={(a) => setMoveDialog({ ids: [a.id] })}
              onReplace={doReplace}
              onDelete={(a) => setConfirm({ kind: 'asset', payload: a })}
              onClose={() => setFocused(null)}
            />
          </div>
        </aside>
      </div>

      {/* ---------- overlay drag & drop global ---------- */}
      {dropOverlay ? (
        <div
          className="fixed inset-0 z-50 bg-background/75 backdrop-blur-[2px]"
          data-testid={T.mediaDropOverlay}
        >
          <div
            className="mx-auto mt-32 max-w-xl rounded-2xl border-2 border-dashed bg-card p-10 text-center shadow-xl"
            style={{ borderColor: ACCENT }}
          >
            <HardDrive className="mx-auto h-9 w-9" style={{ color: ACCENT }} aria-hidden="true" />
            <p className="mt-3 font-['DM_Serif_Display',serif] text-xl text-foreground">
              Lepaskan untuk mengunggah
            </p>
            <p className="mt-1.5 text-xs text-muted-foreground">
              Berkas akan disimpan di {folderId ? `folder “${activeFolder?.name}”` : 'Semua Media'} ·
              maks {stats?.max_mb || 15}MB per berkas
            </p>
          </div>
        </div>
      ) : null}

      {/* ---------- Sheet: rail folder (mobile/tablet) ---------- */}
      <Sheet open={mobileRail} onOpenChange={setMobileRail}>
        <SheetContent side="left" className="w-[300px] overflow-y-auto p-0">
          <SheetHeader className="border-b border-border/70 px-4 py-3">
            <SheetTitle className="text-base">Folder</SheetTitle>
            <SheetDescription className="text-xs">
              Folder bertingkat untuk merapikan media.
            </SheetDescription>
          </SheetHeader>
          <div className="p-2">
            <Button
              size="sm"
              variant="secondary"
              className="mb-2 w-full rounded-lg"
              onClick={() => { setFolderDialog({ mode: 'create', parentId: folderId || null }); setMobileRail(false); }}
            >
              + Folder Baru
            </Button>
            {railContent}
          </div>
        </SheetContent>
      </Sheet>

      {/* ---------- Sheet: inspektur (mobile/tablet) ---------- */}
      <Sheet
        open={mobileDetails && !!focused}
        onOpenChange={(v) => { setMobileDetails(v); if (!v) setFocused(null); }}
      >
        <SheetContent side="right" className="w-full overflow-y-auto p-0 sm:max-w-md">
          <SheetHeader className="border-b border-border/70 px-4 py-3">
            <SheetTitle className="text-base">Detail Berkas</SheetTitle>
            <SheetDescription className="text-xs">
              Ubah alt text, pindahkan folder, salin URL, atau hapus berkas.
            </SheetDescription>
          </SheetHeader>
          <div className="p-3">
            <AssetDetailsPanel
              asset={focused}
              folderName={folderNameOf(focused?.folder_id)}
              busy={saving}
              onSave={saveAsset}
              onMove={(a) => setMoveDialog({ ids: [a.id] })}
              onReplace={doReplace}
              onDelete={(a) => setConfirm({ kind: 'asset', payload: a })}
              onClose={() => { setMobileDetails(false); setFocused(null); }}
            />
          </div>
        </SheetContent>
      </Sheet>

      {/* ---------- dialog ---------- */}
      <FolderNameDialog
        open={!!folderDialog}
        onOpenChange={(v) => !v && setFolderDialog(null)}
        mode={folderDialog?.mode || 'create'}
        initialName={folderDialog?.node?.name || ''}
        parentPath={folderDialog?.parentId ? folderNameOf(folderDialog.parentId) : ''}
        onSubmit={submitFolder}
        busy={saving}
      />

      <MoveToFolderDialog
        open={!!moveDialog}
        onOpenChange={(v) => !v && setMoveDialog(null)}
        folders={flat}
        count={moveDialog?.ids?.length || 1}
        currentFolderId={folderId || null}
        onSubmit={(target) => doMoveAssets(moveDialog.ids, target)}
        busy={saving}
      />

      <FromUrlDialog
        open={urlDialog}
        onOpenChange={setUrlDialog}
        onSubmit={submitUrl}
        busy={saving}
        folderPath={activeFolder?.name || ''}
      />

      <ConfirmDialog
        open={confirm?.kind === 'asset'}
        onOpenChange={(v) => !v && setConfirm(null)}
        title="Hapus berkas ini?"
        description={`“${confirm?.payload?.filename || ''}” akan dihapus permanen dari penyimpanan lokal. Produk atau konten yang memakainya akan menampilkan placeholder.`}
        confirmLabel="Hapus berkas"
        onConfirm={doDeleteAsset}
        busy={saving}
      />

      <ConfirmDialog
        open={confirm?.kind === 'bulk'}
        onOpenChange={(v) => !v && setConfirm(null)}
        title={`Hapus ${selected.length} berkas?`}
        description="Semua berkas terpilih akan dihapus permanen dari penyimpanan lokal. Tindakan ini tidak bisa dibatalkan."
        confirmLabel="Hapus semua"
        onConfirm={doBulkDelete}
        busy={saving}
      />

      <ConfirmDialog
        open={confirm?.kind === 'localize'}
        onOpenChange={(v) => !v && setConfirm(null)}
        title={`Unduh ${stats?.hotlinked || 0} gambar eksternal ke lokal?`}
        description="Setiap gambar akan diunduh ke penyimpanan lokal server, lalu semua referensinya di produk, kategori, konten situs, lokasi toko, dan metode pembayaran diperbarui otomatis. Proses ini aman dan bisa diulang. Gambar yang sumbernya sudah mati akan dilaporkan sebagai gagal."
        confirmLabel="Unduh & Perbaiki"
        onConfirm={doLocalize}
        busy={localizing}
        testId={T.mediaLocalizeDialog}
        confirmTestId={T.mediaLocalizeConfirm}
      />

      {/* Hapus folder: dua pilihan aman (pindahkan isi) atau cascade. */}
      {confirm?.kind === 'folder' ? (
        <ConfirmFolderDialog
          node={confirm.payload}
          busy={saving}
          onCancel={() => setConfirm(null)}
          onSafe={() => doDeleteFolder(false)}
          onCascade={() => doDeleteFolder(true)}
        />
      ) : null}

      {/* Dropzone tersembunyi untuk tombol Upload di toolbar. */}
      <HiddenPicker ref={dropzoneRef} onFiles={upload.enqueue} />
    </div>
  );
}

// Tombol "Upload" pada toolbar memicu input berkas tersembunyi ini.
const HiddenPicker = React.forwardRef(({ onFiles }, ref) => {
  const inputRef = useRef(null);
  React.useImperativeHandle(ref, () => ({ pick: () => inputRef.current?.click() }));
  return (
    <input
      ref={inputRef}
      type="file"
      multiple
      accept="image/*"
      className="hidden"
      onChange={(e) => {
        if (e.target.files?.length) onFiles(e.target.files);
        e.target.value = '';
      }}
      data-testid={T.mediaToolbarFileInput}
    />
  );
});

const ConfirmFolderDialog = ({ node, onCancel, onSafe, onCascade, busy }) => (
  <Sheet open onOpenChange={(v) => !v && onCancel()}>
    <SheetContent side="right" className="w-full sm:max-w-md">
      <SheetHeader>
        <SheetTitle className="text-base">Hapus folder “{node?.name}”?</SheetTitle>
        <SheetDescription className="text-xs">
          Pilih cara menghapus. Opsi aman TIDAK menghapus berkas apa pun.
        </SheetDescription>
      </SheetHeader>
      <div className="mt-5 space-y-3" data-testid={T.mediaFolderDeleteDialog}>
        <button
          type="button"
          onClick={onSafe}
          disabled={busy}
          className="w-full rounded-xl border border-border/70 bg-card p-4 text-left transition-colors hover:bg-muted/60"
          data-testid={T.mediaFolderDeleteSafe}
        >
          <div className="flex items-center gap-2 text-sm font-medium text-foreground">
            <FolderInput className="h-4 w-4" style={{ color: ACCENT }} /> Pindahkan isi ke folder induk
          </div>
          <p className="mt-1 text-xs leading-relaxed text-muted-foreground">
            Disarankan. Folder dihapus, tetapi semua berkas & subfolder di dalamnya dipindahkan
            ke induknya — tidak ada gambar yang hilang.
          </p>
        </button>
        <button
          type="button"
          onClick={onCascade}
          disabled={busy}
          className="w-full rounded-xl border border-rose-200 bg-rose-50/60 p-4 text-left transition-colors hover:bg-rose-50"
          data-testid={T.mediaFolderDeleteCascade}
        >
          <div className="flex items-center gap-2 text-sm font-medium text-rose-700">
            <Trash2 className="h-4 w-4" /> Hapus folder & semua isinya
          </div>
          <p className="mt-1 text-xs leading-relaxed text-rose-700/80">
            Permanen. Seluruh berkas dan subfolder di dalamnya akan dihapus dari penyimpanan.
          </p>
        </button>
        <Button variant="secondary" className="w-full rounded-lg" onClick={onCancel}>
          {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : null} Batal
        </Button>
        <p className="flex items-center gap-1.5 text-[10px] text-muted-foreground">
          <Copy className="h-3 w-3" /> Tip: gunakan “Pindahkan” pada berkas jika hanya ingin merapikan.
        </p>
      </div>
    </SheetContent>
  </Sheet>
);
