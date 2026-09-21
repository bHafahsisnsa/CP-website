// components/admin/media/MediaPickerDialog.js — pemilih media serbaguna (E20).
//
// Dipakai di SEMUA tempat yang butuh gambar: editor produk, CMS konten, kategori,
// lokasi toko, dan pengaturan pembayaran. Tiga tab:
//   Pustaka  : jelajah folder + cari + pilih (single/multi)
//   Upload   : seret & lepas / pilih berkas -> langsung masuk folder aktif
//   Dari URL : unduh gambar eksternal -> disimpan LOKAL (anti broken image)
import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { Check, ChevronRight, Loader2, X } from 'lucide-react';
import { toast } from 'sonner';
import { Badge } from '../../ui/badge';
import { Button } from '../../ui/button';
import { Input } from '../../ui/input';
import { Label } from '../../ui/label';
import {
  Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle,
} from '../../ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../ui/tabs';
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from '../../ui/select';
import { SmartImage } from '../../shared/SmartImage';
import { AssetGrid } from './AssetGrid';
import { Dropzone } from './Dropzone';
import { UploadQueuePanel } from './UploadQueuePanel';
import { FolderTree, flattenTree } from './FolderTree';
import { useMediaUpload } from './useMediaUpload';
import { EmptyState, ACCENT } from '../adminUi';
import {
  SORT_OPTIONS, getFolderTree, ingestUrl, listAssets, mediaErrorMessage,
} from '../../../services/media';
import { CHECKER_STYLE, needsCheckerboard } from '../../../lib/mediaUrl';
import { adminTestIds as T } from '../../../constants/testIds/admin';

const PAGE_SIZE = 24;

export const MediaPickerDialog = ({
  open,
  onOpenChange,
  mode = 'single',
  onConfirm,
  title = 'Pilih Media',
  description = 'Pilih gambar dari pustaka, unggah baru, atau ambil dari URL. Semua berkas tersimpan di penyimpanan lokal.',
  initialTab = 'library',
}) => {
  const multi = mode === 'multi';
  const [tab, setTab] = useState(initialTab);
  const [tree, setTree] = useState([]);
  const [root, setRoot] = useState(null);
  const [folderId, setFolderId] = useState('');
  const [items, setItems] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [q, setQ] = useState('');
  const [sort, setSort] = useState('newest');
  const [loading, setLoading] = useState(false);
  const [picked, setPicked] = useState([]);
  const [urlValue, setUrlValue] = useState('');
  const [urlBusy, setUrlBusy] = useState(false);

  const flat = useMemo(() => flattenTree(tree), [tree]);
  const folderPath = folderId
    ? (flat.find((f) => f.id === folderId)?.path || '') : '';

  const loadTree = useCallback(async () => {
    try {
      const t = await getFolderTree();
      setTree(t?.tree || []);
      setRoot(t?.root || null);
    } catch (e) { /* rail opsional */ }
  }, []);

  const loadAssets = useCallback(async () => {
    setLoading(true);
    try {
      const res = await listAssets({
        folderId: folderId || '', q, sort, page, limit: PAGE_SIZE,
        recursive: !!folderId,
      });
      setItems(res.items);
      setTotal(res.total);
    } catch (e) {
      toast.error(mediaErrorMessage(e, 'Gagal memuat pustaka media.'));
    } finally { setLoading(false); }
  }, [folderId, q, sort, page]);

  useEffect(() => {
    if (!open) return;
    setTab(initialTab);
    setPicked([]);
    setPage(1);
    setQ('');
    loadTree();
  }, [open, initialTab, loadTree]);

  useEffect(() => { if (open) loadAssets(); }, [open, loadAssets]);

  // Debounce pencarian.
  const [qInput, setQInput] = useState('');
  useEffect(() => {
    const t = setTimeout(() => { setQ(qInput); setPage(1); }, 320);
    return () => clearTimeout(t);
  }, [qInput]);
  useEffect(() => { if (open) setQInput(''); }, [open]);

  const onUploaded = useCallback((assets) => {
    setPicked((p) => (multi ? [...p, ...assets] : [assets[assets.length - 1]]));
    loadAssets();
    loadTree();
    toast.success(`${assets.length} berkas terunggah.`);
  }, [multi, loadAssets, loadTree]);

  const upload = useMediaUpload({ folderId: folderId || null, onUploaded });

  const toggle = (asset) => {
    setPicked((p) => {
      const exists = p.some((x) => x.id === asset.id);
      if (multi) return exists ? p.filter((x) => x.id !== asset.id) : [...p, asset];
      return exists ? [] : [asset];
    });
  };

  const submitUrl = async () => {
    const u = urlValue.trim();
    if (!u) return;
    setUrlBusy(true);
    try {
      const asset = await ingestUrl(u, { folderId: folderId || null });
      setUrlValue('');
      setPicked((p) => (multi ? [...p, asset] : [asset]));
      toast.success('Gambar diunduh & disimpan lokal.');
      setTab('library');
      loadAssets();
    } catch (e) {
      toast.error(mediaErrorMessage(e, 'Gagal mengunduh dari URL.'));
    } finally { setUrlBusy(false); }
  };

  const confirm = () => {
    if (!picked.length) { toast.error('Belum ada berkas dipilih.'); return; }
    onConfirm(multi ? picked : picked[0]);
    onOpenChange(false);
  };

  const pages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent
        className="flex max-h-[88vh] w-[min(1100px,calc(100vw-1.5rem))] max-w-none flex-col gap-0 overflow-hidden p-0"
        data-testid={T.mediaPickerDialog}
      >
        <DialogHeader className="border-b border-border/70 px-5 py-4">
          <DialogTitle className="font-['DM_Serif_Display',serif] text-xl">{title}</DialogTitle>
          <DialogDescription className="text-xs">{description}</DialogDescription>
        </DialogHeader>

        <Tabs value={tab} onValueChange={setTab} className="flex min-h-0 flex-1 flex-col">
          <div className="border-b border-border/70 px-5 pt-3">
            <TabsList data-testid={T.mediaPickerTabs}>
              <TabsTrigger value="library" data-testid={T.mediaPickerTabLibrary}>Pustaka</TabsTrigger>
              <TabsTrigger value="upload" data-testid={T.mediaPickerTabUpload}>Upload</TabsTrigger>
              <TabsTrigger value="url" data-testid={T.mediaPickerTabUrl}>Dari URL</TabsTrigger>
            </TabsList>
          </div>

          {/* ---------------- PUSTAKA ---------------- */}
          <TabsContent value="library" className="m-0 min-h-0 flex-1 overflow-hidden">
            <div className="flex h-full min-h-0">
              <aside className="hidden w-56 shrink-0 overflow-y-auto border-r border-border/70 bg-muted/30 px-2 py-3 md:block">
                <FolderTree
                  tree={tree}
                  root={root}
                  activeId={folderId}
                  onSelect={(id) => { setFolderId(id); setPage(1); }}
                  onCreateChild={() => {}}
                  onRename={() => {}}
                  onDelete={() => {}}
                  onMoveAssets={() => {}}
                  onMoveFolder={() => {}}
                  compact
                />
              </aside>

              <div className="flex min-h-0 min-w-0 flex-1 flex-col">
                <div className="flex flex-wrap items-center gap-2 border-b border-border/70 px-4 py-3">
                  <Input
                    value={qInput}
                    onChange={(e) => setQInput(e.target.value)}
                    placeholder="Cari berkas…"
                    className="h-9 flex-1 min-w-[160px]"
                    data-testid={T.mediaPickerSearch}
                  />
                  <Select value={sort} onValueChange={(v) => { setSort(v); setPage(1); }}>
                    <SelectTrigger className="h-9 w-[150px]" data-testid={T.mediaPickerSort}>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {SORT_OPTIONS.map((o) => (
                        <SelectItem key={o.value} value={o.value}>{o.label}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <div className="md:hidden">
                    <Select
                      value={folderId || '__root__'}
                      onValueChange={(v) => { setFolderId(v === '__root__' ? '' : v); setPage(1); }}
                    >
                      <SelectTrigger className="h-9 w-[150px]" data-testid={T.mediaPickerFolderSelect}>
                        <SelectValue placeholder="Folder" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="__root__">Semua Media</SelectItem>
                        {flat.map((f) => (
                          <SelectItem key={f.id} value={f.id}>
                            {`${'\u00a0'.repeat(f.depth * 2)}${f.depth ? '↳ ' : ''}${f.name}`}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                <div className="min-h-0 flex-1 overflow-y-auto px-4 py-4">
                  {!loading && !items.length ? (
                    <EmptyState
                      title={q ? 'Tidak ada hasil' : 'Folder ini kosong'}
                      hint={q
                        ? 'Coba kata kunci lain atau pilih folder yang berbeda.'
                        : 'Buka tab Upload untuk menambahkan gambar, atau tab Dari URL.'}
                      action={(
                        <Button variant="secondary" onClick={() => setTab('upload')} className="rounded-lg">
                          Upload gambar
                        </Button>
                      )}
                    />
                  ) : (
                    <AssetGrid
                      items={items}
                      loading={loading}
                      selectedIds={picked.map((p) => p.id)}
                      onToggleSelect={(id) => {
                        const a = items.find((x) => x.id === id);
                        if (a) toggle(a);
                      }}
                      onOpen={toggle}
                      onDetails={toggle}
                      onCopy={() => {}}
                      onDelete={() => {}}
                      showMenu={false}
                      columnsClassName="grid-cols-2 sm:grid-cols-3 lg:grid-cols-4"
                    />
                  )}
                </div>

                {pages > 1 ? (
                  <div className="flex items-center justify-between gap-2 border-t border-border/70 px-4 py-2.5">
                    <span className="text-[11px] text-muted-foreground" data-testid={T.mediaPickerPageInfo}>
                      Halaman {page} dari {pages} · {total} berkas
                    </span>
                    <div className="flex gap-1.5">
                      <Button
                        size="sm"
                        variant="secondary"
                        className="h-7 rounded-md px-2 text-xs"
                        disabled={page <= 1}
                        onClick={() => setPage((p) => Math.max(1, p - 1))}
                        data-testid={T.mediaPickerPrev}
                      >
                        Sebelumnya
                      </Button>
                      <Button
                        size="sm"
                        variant="secondary"
                        className="h-7 rounded-md px-2 text-xs"
                        disabled={page >= pages}
                        onClick={() => setPage((p) => Math.min(pages, p + 1))}
                        data-testid={T.mediaPickerNext}
                      >
                        Berikutnya
                      </Button>
                    </div>
                  </div>
                ) : null}
              </div>
            </div>
          </TabsContent>

          {/* ---------------- UPLOAD ---------------- */}
          <TabsContent value="upload" className="m-0 min-h-0 flex-1 overflow-y-auto px-5 py-4">
            <div className="space-y-3">
              <div className="flex flex-wrap items-center gap-2">
                <Label className="text-xs">Simpan ke folder</Label>
                <Select
                  value={folderId || '__root__'}
                  onValueChange={(v) => setFolderId(v === '__root__' ? '' : v)}
                >
                  <SelectTrigger className="h-9 w-[220px]" data-testid={T.mediaPickerUploadFolder}>
                    <SelectValue placeholder="Semua Media" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="__root__">Semua Media (tanpa folder)</SelectItem>
                    {flat.map((f) => (
                      <SelectItem key={f.id} value={f.id}>
                        {`${'\u00a0'.repeat(f.depth * 2)}${f.depth ? '↳ ' : ''}${f.name}`}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <Dropzone
                onFiles={upload.enqueue}
                busy={upload.busy}
                testId={T.mediaPickerDropzone}
                inputTestId={T.mediaPickerFileInput}
              />
              <UploadQueuePanel
                queue={upload.queue}
                onRetry={upload.retry}
                onRemove={upload.remove}
                onClearDone={upload.clearDone}
              />
            </div>
          </TabsContent>

          {/* ---------------- DARI URL ---------------- */}
          <TabsContent value="url" className="m-0 min-h-0 flex-1 overflow-y-auto px-5 py-4">
            <div className="max-w-xl space-y-3">
              <div className="rounded-xl border border-border/70 bg-muted/40 px-3 py-2.5 text-[11px] leading-relaxed text-muted-foreground">
                Gambar dari URL akan <strong className="text-foreground">diunduh dan disimpan
                di penyimpanan lokal</strong> — bukan hanya ditautkan. Jadi walaupun situs
                sumbernya mati atau memblokir hotlink, gambar Anda tetap tampil.
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="picker-url" className="text-xs">URL gambar</Label>
                <Input
                  id="picker-url"
                  value={urlValue}
                  onChange={(e) => setUrlValue(e.target.value)}
                  onKeyDown={(e) => { if (e.key === 'Enter') submitUrl(); }}
                  placeholder="https://contoh.com/gambar.jpg"
                  data-testid={T.mediaPickerUrlInput}
                />
              </div>
              <Button
                onClick={submitUrl}
                disabled={urlBusy || !urlValue.trim()}
                className="gap-2 rounded-lg"
                data-testid={T.mediaPickerUrlSubmit}
              >
                {urlBusy ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
                {urlBusy ? 'Mengunduh…' : 'Unduh & Simpan'}
              </Button>
            </div>
          </TabsContent>
        </Tabs>

        <DialogFooter className="flex-col items-stretch gap-3 border-t border-border/70 px-5 py-3 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex min-w-0 flex-1 items-center gap-2" data-testid={T.mediaPickerTray}>
            {picked.length ? (
              <>
                <Badge variant="outline" className="shrink-0" style={{ borderColor: ACCENT, color: ACCENT }}>
                  {picked.length} dipilih
                </Badge>
                <div className="flex min-w-0 flex-1 gap-1.5 overflow-x-auto py-0.5">
                  {picked.slice(0, 12).map((p) => (
                    <span
                      key={p.id}
                      className="relative h-10 w-10 shrink-0 overflow-hidden rounded-lg border border-border/70 bg-muted/40"
                      style={needsCheckerboard(p) ? CHECKER_STYLE : undefined}
                      title={p.filename}
                    >
                      <SmartImage
                        src={p.thumb_url || p.url}
                        alt={p.filename}
                        className="absolute inset-0 h-full w-full"
                        showRetry={false}
                        fallbackLabel=""
                      />
                      <button
                        type="button"
                        aria-label={`Buang ${p.filename} dari pilihan`}
                        onClick={() => setPicked((arr) => arr.filter((x) => x.id !== p.id))}
                        className="absolute right-0 top-0 grid h-4 w-4 place-items-center rounded-bl-md bg-black/60 text-white"
                      >
                        <X className="h-2.5 w-2.5" />
                      </button>
                    </span>
                  ))}
                </div>
              </>
            ) : (
              <span className="text-[11px] text-muted-foreground">
                Maks 15MB per berkas · JPG, PNG, WebP, GIF, SVG, AVIF, HEIC
              </span>
            )}
          </div>
          <div className="flex shrink-0 items-center gap-2">
            <Button variant="secondary" onClick={() => onOpenChange(false)} className="rounded-lg">
              Batal
            </Button>
            <Button
              onClick={confirm}
              disabled={!picked.length}
              className="gap-2 rounded-lg"
              data-testid={T.mediaPickerConfirm}
            >
              <Check className="h-4 w-4" />
              {multi ? `Pilih (${picked.length})` : 'Pilih'}
            </Button>
          </div>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

export default MediaPickerDialog;
