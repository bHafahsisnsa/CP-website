// components/admin/media/AssetDetailsPanel.js — inspektur detail aset (E20).
//
// Berisi: pratinjau besar, info teknis, ubah nama tampilan, alt & judul,
// pindah folder, salin URL, ganti berkas (URL tetap), dan hapus.
import React, { useEffect, useState } from 'react';
import {
  Copy, ExternalLink, FolderInput, ImageUp, Info, Loader2, Save, Trash2, X,
} from 'lucide-react';
import { toast } from 'sonner';
import { Badge } from '../../ui/badge';
import { Button } from '../../ui/button';
import { Input } from '../../ui/input';
import { Label } from '../../ui/label';
import { Separator } from '../../ui/separator';
import { SmartImage } from '../../shared/SmartImage';
import {
  CHECKER_STYLE, formatBytes, mediaTypeBadge, needsCheckerboard, resolveMediaUrl,
} from '../../../lib/mediaUrl';
import { MEDIA_ACCEPT } from '../../../services/media';
import { formatDateTime } from '../adminUi';
import { adminTestIds as T } from '../../../constants/testIds/admin';

const Row = ({ label, value, mono }) => (
  <div className="flex items-baseline justify-between gap-3 py-1">
    <span className="text-[11px] uppercase tracking-[0.12em] text-muted-foreground">{label}</span>
    <span className={`min-w-0 truncate text-right text-xs text-foreground ${mono ? "font-['Azeret_Mono',monospace]" : ''}`}>
      {value || '—'}
    </span>
  </div>
);

export const AssetDetailsPanel = ({
  asset, onSave, onMove, onReplace, onDelete, onClose, folderName, busy,
}) => {
  const [filename, setFilename] = useState('');
  const [alt, setAlt] = useState('');
  const [title, setTitle] = useState('');
  const [replacing, setReplacing] = useState(false);
  const fileRef = React.useRef(null);

  useEffect(() => {
    setFilename(asset?.filename || '');
    setAlt(asset?.alt || '');
    setTitle(asset?.title || '');
  }, [asset?.id, asset?.filename, asset?.alt, asset?.title]);

  if (!asset) {
    return (
      <div
        className="flex h-full flex-col items-center justify-center gap-2 rounded-2xl border border-border/70 bg-card px-6 py-14 text-center"
        data-testid={T.mediaDetailsEmpty}
      >
        <Info className="h-5 w-5 text-muted-foreground" aria-hidden="true" />
        <p className="text-sm font-medium text-foreground">Belum ada berkas dipilih</p>
        <p className="text-xs leading-relaxed text-muted-foreground">
          Klik salah satu berkas untuk melihat detail, mengubah alt text, memindahkan folder,
          atau menyalin URL-nya.
        </p>
      </div>
    );
  }

  const dirty = filename !== (asset.filename || '')
    || alt !== (asset.alt || '')
    || title !== (asset.title || '');

  const copyUrl = async () => {
    const abs = resolveMediaUrl(asset.url);
    try {
      await navigator.clipboard.writeText(abs);
      toast.success('Tautan disalin.');
    } catch (e) {
      // Fallback bila clipboard API diblokir browser.
      const ta = document.createElement('textarea');
      ta.value = abs;
      document.body.appendChild(ta);
      ta.select();
      try { document.execCommand('copy'); toast.success('Tautan disalin.'); }
      catch (_) { toast.error('Tidak bisa menyalin. Salin manual dari kolom URL.'); }
      ta.remove();
    }
  };

  const doReplace = async (file) => {
    if (!file) return;
    setReplacing(true);
    try { await onReplace(file); } finally {
      setReplacing(false);
      if (fileRef.current) fileRef.current.value = '';
    }
  };

  const badge = mediaTypeBadge(asset);

  return (
    <div
      className="flex h-full flex-col overflow-hidden rounded-2xl border border-border/70 bg-card shadow-sm"
      data-testid={T.mediaDetailsPanel}
    >
      <div className="flex items-center justify-between gap-2 border-b border-border/70 px-4 py-2.5">
        <span className="text-[10px] font-semibold uppercase tracking-[0.16em] text-muted-foreground">
          Detail Berkas
        </span>
        {onClose ? (
          <button
            type="button"
            onClick={onClose}
            aria-label="Tutup panel detail"
            className="grid h-7 w-7 place-items-center rounded-md text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
            data-testid={T.mediaDetailsClose}
          >
            <X className="h-4 w-4" />
          </button>
        ) : null}
      </div>

      <div className="min-h-0 flex-1 overflow-y-auto px-4 py-4">
        <div
          className="relative block aspect-[4/3] w-full overflow-hidden rounded-xl border border-border/60 bg-muted/40"
          style={needsCheckerboard(asset) ? CHECKER_STYLE : undefined}
        >
          <SmartImage
            src={asset.medium_url || asset.url}
            alt={asset.alt || asset.filename || 'media'}
            className="absolute inset-0 h-full w-full"
            fit="contain"
            testId={T.mediaDetailsPreview}
          />
          {badge ? (
            <Badge
              variant="outline"
              className="absolute left-2 top-2 border-border/70 bg-card/95 px-1.5 py-0 text-[9px] font-semibold"
            >
              {badge}
            </Badge>
          ) : null}
        </div>

        <div className="mt-3 flex flex-wrap gap-2">
          <Button
            size="sm"
            variant="secondary"
            className="gap-1.5 rounded-lg"
            onClick={copyUrl}
            data-testid={T.mediaDetailsCopyUrl}
          >
            <Copy className="h-3.5 w-3.5" /> Salin URL
          </Button>
          <Button
            size="sm"
            variant="secondary"
            className="gap-1.5 rounded-lg"
            asChild
          >
            <a
              href={resolveMediaUrl(asset.url)}
              target="_blank"
              rel="noreferrer"
              data-testid={T.mediaDetailsOpen}
            >
              <ExternalLink className="h-3.5 w-3.5" /> Buka
            </a>
          </Button>
          {onMove ? (
            <Button
              size="sm"
              variant="secondary"
              className="gap-1.5 rounded-lg"
              onClick={() => onMove(asset)}
              data-testid={T.mediaDetailsMove}
            >
              <FolderInput className="h-3.5 w-3.5" /> Pindahkan
            </Button>
          ) : null}
        </div>

        <div className="mt-4 rounded-xl border border-border/70 bg-muted/40 px-3 py-2">
          <Row label="Folder" value={folderName || 'Semua Media'} />
          <Row label="Tipe" value={asset.mime} mono />
          <Row label="Ukuran" value={formatBytes(asset.size)} mono />
          <Row
            label="Dimensi"
            value={asset.width ? `${asset.width} × ${asset.height} px` : '—'}
            mono
          />
          <Row label="Diunggah" value={formatDateTime(asset.uploaded_at)} />
          <Row label="Diubah" value={formatDateTime(asset.updated_at)} />
          <Row label="Sumber" value={asset.source === 'external' ? 'URL eksternal (hotlink)' : asset.source === 'url' ? 'Diunduh dari URL' : 'Upload lokal'} />
        </div>

        <div className="mt-4 space-y-3">
          <div className="space-y-1.5">
            <Label htmlFor="asset-url" className="text-xs">URL (untuk ditempel manual)</Label>
            <Input
              id="asset-url"
              readOnly
              value={asset.url || ''}
              onFocus={(e) => e.target.select()}
              className="h-9 font-['Azeret_Mono',monospace] text-[11px]"
              data-testid={T.mediaDetailsUrl}
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="asset-filename" className="text-xs">Nama tampilan</Label>
            <Input
              id="asset-filename"
              value={filename}
              onChange={(e) => setFilename(e.target.value)}
              className="h-9"
              data-testid={T.mediaDetailsRename}
            />
            <p className="text-[10px] leading-relaxed text-muted-foreground">
              Mengubah nama tampilan TIDAK mengubah URL, jadi gambar yang sudah dipakai tetap aman.
            </p>
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="asset-alt" className="text-xs">Alt text (SEO & aksesibilitas)</Label>
            <Input
              id="asset-alt"
              value={alt}
              onChange={(e) => setAlt(e.target.value)}
              placeholder="mis. Botol parfum amber di atas kain gelap"
              className="h-9"
              data-testid={T.mediaDetailsAlt}
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="asset-title" className="text-xs">Judul (opsional)</Label>
            <Input
              id="asset-title"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="h-9"
              data-testid={T.mediaDetailsTitle}
            />
          </div>
          <Button
            onClick={() => onSave({ filename, alt, title })}
            disabled={!dirty || busy}
            className="w-full gap-2 rounded-lg"
            data-testid={T.mediaDetailsSave}
          >
            {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
            {busy ? 'Menyimpan…' : 'Simpan Perubahan'}
          </Button>
        </div>

        {asset.stored_path ? (
          <>
            <Separator className="my-4" />
            <div className="space-y-1.5">
              <Label className="text-xs">Ganti berkas</Label>
              <p className="text-[10px] leading-relaxed text-muted-foreground">
                Unggah gambar baru untuk MENGGANTI isi berkas ini. URL tetap sama sehingga
                semua produk/konten yang memakainya otomatis ikut terbarui.
              </p>
              <input
                ref={fileRef}
                type="file"
                accept={MEDIA_ACCEPT}
                className="hidden"
                onChange={(e) => doReplace(e.target.files?.[0])}
                data-testid={T.mediaDetailsReplaceInput}
              />
              <Button
                variant="secondary"
                className="w-full gap-2 rounded-lg"
                onClick={() => fileRef.current?.click()}
                disabled={replacing}
                data-testid={T.mediaDetailsReplace}
              >
                {replacing ? <Loader2 className="h-4 w-4 animate-spin" /> : <ImageUp className="h-4 w-4" />}
                {replacing ? 'Mengganti…' : 'Pilih berkas pengganti'}
              </Button>
            </div>
          </>
        ) : null}

        <Separator className="my-4" />
        <Button
          variant="outline"
          className="w-full gap-2 rounded-lg border-rose-200 text-rose-600 hover:bg-rose-50 hover:text-rose-700"
          onClick={() => onDelete(asset)}
          data-testid={T.mediaDetailsDelete}
        >
          <Trash2 className="h-4 w-4" /> Hapus Berkas
        </Button>
      </div>
    </div>
  );
};

export default AssetDetailsPanel;
