// components/admin/media/MediaField.js — kontrol gambar tunggal (E20).
//
// Pengganti input URL telanjang di seluruh admin: pratinjau + "Pilih dari Media",
// "Upload", "Hapus", plus kolom URL manual (tetap didukung, tapi kini bisa
// diunduh ke lokal). Nilai (value) TETAP berupa string URL agar kompatibel dengan
// skema backend yang sudah ada.
import React, { useRef, useState } from 'react';
import { ImagePlus, Loader2, Trash2, Upload } from 'lucide-react';
import { toast } from 'sonner';
import { Button } from '../../ui/button';
import { Input } from '../../ui/input';
import { Label } from '../../ui/label';
import { SmartImage } from '../../shared/SmartImage';
import { MediaPickerDialog } from './MediaPickerDialog';
import {
  MEDIA_ACCEPT, ingestUrl, mediaErrorMessage, uploadAsset,
} from '../../../services/media';
import { validateFile } from './useMediaUpload';
import { CHECKER_STYLE, isLocalMedia } from '../../../lib/mediaUrl';
import { adminTestIds as T } from '../../../constants/testIds/admin';

export const MediaField = ({
  label,
  value = '',
  onChange,
  hint,
  showUrlInput = true,
  folderId = null,
  testId,
  previewClassName = 'h-24 w-24',
  pickerTitle = 'Pilih Gambar',
}) => {
  const [pickerOpen, setPickerOpen] = useState(false);
  const [busy, setBusy] = useState(false);
  const [urlDraft, setUrlDraft] = useState('');
  const fileRef = useRef(null);

  const doUpload = async (file) => {
    if (!file) return;
    const err = validateFile(file);
    if (err) { toast.error(err); return; }
    setBusy(true);
    try {
      const asset = await uploadAsset(file, { folderId });
      onChange(asset.url);
      toast.success('Gambar terunggah & tersimpan lokal.');
    } catch (e) {
      toast.error(mediaErrorMessage(e, 'Gagal mengunggah gambar.'));
    } finally {
      setBusy(false);
      if (fileRef.current) fileRef.current.value = '';
    }
  };

  const doIngest = async () => {
    const u = urlDraft.trim();
    if (!u) return;
    setBusy(true);
    try {
      const asset = await ingestUrl(u, { folderId });
      onChange(asset.url);
      setUrlDraft('');
      toast.success('Gambar diunduh dari URL & disimpan lokal.');
    } catch (e) {
      toast.error(mediaErrorMessage(e, 'Gagal mengunduh dari URL.'));
    } finally { setBusy(false); }
  };

  return (
    <div className="space-y-2" data-testid={testId || T.mediaField}>
      {label ? <Label className="text-xs">{label}</Label> : null}
      <div className="flex items-start gap-3">
        <span
          className={`relative block shrink-0 overflow-hidden rounded-xl border border-border/70 bg-muted/40 ${previewClassName}`}
          style={CHECKER_STYLE}
        >
          {value ? (
            <SmartImage
              src={value}
              alt={label || 'pratinjau gambar'}
              className="absolute inset-0 h-full w-full"
              fit="cover"
              fallbackLabel="Hilang"
              testId={T.mediaFieldPreview}
            />
          ) : (
            <span className="absolute inset-0 grid place-items-center">
              <ImagePlus className="h-5 w-5 text-muted-foreground" aria-hidden="true" />
            </span>
          )}
        </span>

        <div className="min-w-0 flex-1 space-y-2">
          <div className="flex flex-wrap gap-2">
            <Button
              type="button"
              size="sm"
              variant="secondary"
              className="gap-1.5 rounded-lg"
              onClick={() => setPickerOpen(true)}
              data-testid={T.mediaFieldPick}
            >
              <ImagePlus className="h-3.5 w-3.5" /> Pilih dari Media
            </Button>
            <input
              ref={fileRef}
              type="file"
              accept={MEDIA_ACCEPT}
              className="hidden"
              onChange={(e) => doUpload(e.target.files?.[0])}
              data-testid={T.mediaFieldFileInput}
            />
            <Button
              type="button"
              size="sm"
              variant="outline"
              className="gap-1.5 rounded-lg"
              onClick={() => fileRef.current?.click()}
              disabled={busy}
              data-testid={T.mediaFieldUpload}
            >
              {busy ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Upload className="h-3.5 w-3.5" />}
              {busy ? 'Mengunggah…' : 'Upload'}
            </Button>
            {value ? (
              <Button
                type="button"
                size="sm"
                variant="ghost"
                className="gap-1.5 text-muted-foreground"
                onClick={() => onChange('')}
                data-testid={T.mediaFieldClear}
              >
                <Trash2 className="h-3.5 w-3.5" /> Hapus
              </Button>
            ) : null}
          </div>

          {value ? (
            <Input
              readOnly
              value={value}
              onFocus={(e) => e.target.select()}
              className="h-8 font-['Azeret_Mono',monospace] text-[11px]"
              data-testid={T.mediaFieldValue}
            />
          ) : null}

          {showUrlInput ? (
            <div className="flex gap-2">
              <Input
                value={urlDraft}
                onChange={(e) => setUrlDraft(e.target.value)}
                onKeyDown={(e) => { if (e.key === 'Enter') { e.preventDefault(); doIngest(); } }}
                placeholder="atau tempel URL gambar…"
                className="h-8 text-xs"
                data-testid={T.mediaFieldUrlInput}
              />
              <Button
                type="button"
                size="sm"
                variant="secondary"
                className="h-8 shrink-0 rounded-lg text-xs"
                onClick={doIngest}
                disabled={busy || !urlDraft.trim()}
                data-testid={T.mediaFieldUrlSubmit}
              >
                Unduh
              </Button>
            </div>
          ) : null}

          <p className="text-[10px] leading-relaxed text-muted-foreground">
            {hint || 'Gambar disimpan di penyimpanan lokal server. URL eksternal otomatis diunduh agar tidak broken.'}
            {value && !isLocalMedia(value) ? (
              <span className="ml-1 text-amber-700">
                Gambar ini masih menautkan ke situs luar — klik “Unduh” agar disimpan lokal.
              </span>
            ) : null}
          </p>
        </div>
      </div>

      <MediaPickerDialog
        open={pickerOpen}
        onOpenChange={setPickerOpen}
        mode="single"
        title={pickerTitle}
        onConfirm={(asset) => onChange(asset.url)}
      />
    </div>
  );
};

export default MediaField;
