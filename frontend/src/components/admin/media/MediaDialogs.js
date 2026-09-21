// components/admin/media/MediaDialogs.js — dialog kecil pendukung Media Manager (E20).
//
// FolderNameDialog  : buat / ubah nama folder
// MoveToFolderDialog: fallback NON-DRAG untuk memindahkan aset/folder
// FromUrlDialog     : unduh gambar dari URL eksternal -> simpan LOKAL
// ConfirmDialog     : konfirmasi aksi destruktif
import React, { useEffect, useMemo, useState } from 'react';
import { FolderInput, Link2, Loader2 } from 'lucide-react';
import { Button } from '../../ui/button';
import { Input } from '../../ui/input';
import { Label } from '../../ui/label';
import {
  Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle,
} from '../../ui/dialog';
import {
  AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent,
  AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle,
} from '../../ui/alert-dialog';
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from '../../ui/select';
import { adminTestIds as T } from '../../../constants/testIds/admin';
import { MEDIA_MAX_MB } from '../../../services/media';

export const FolderNameDialog = ({
  open, onOpenChange, mode = 'create', initialName = '', parentPath = '', onSubmit, busy,
}) => {
  const [name, setName] = useState(initialName);
  useEffect(() => { if (open) setName(initialName); }, [open, initialName]);
  const submit = () => {
    if (!name.trim()) return;
    onSubmit(name.trim());
  };
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md" data-testid={T.mediaFolderDialog}>
        <DialogHeader>
          <DialogTitle>{mode === 'create' ? 'Folder Baru' : 'Ubah Nama Folder'}</DialogTitle>
          <DialogDescription>
            {mode === 'create'
              ? `Folder akan dibuat di ${parentPath || 'tingkat teratas'}. Folder bisa bertingkat tanpa batas.`
              : 'Mengubah nama folder tidak memindahkan atau merusak berkas di dalamnya.'}
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-1.5">
          <Label htmlFor="folder-name">Nama folder</Label>
          <Input
            id="folder-name"
            autoFocus
            value={name}
            onChange={(e) => setName(e.target.value)}
            onKeyDown={(e) => { if (e.key === 'Enter') submit(); }}
            placeholder="mis. Produk Parfum 2026"
            data-testid={T.mediaFolderNameInput}
          />
        </div>
        <DialogFooter>
          <Button variant="secondary" onClick={() => onOpenChange(false)}>Batal</Button>
          <Button onClick={submit} disabled={busy || !name.trim()} data-testid={T.mediaFolderSubmit}>
            {busy ? 'Menyimpan…' : 'Simpan'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

export const MoveToFolderDialog = ({
  open, onOpenChange, folders = [], count = 1, currentFolderId = null, onSubmit, busy,
}) => {
  const [target, setTarget] = useState('__root__');
  useEffect(() => { if (open) setTarget(currentFolderId || '__root__'); }, [open, currentFolderId]);
  const options = useMemo(() => [
    { id: '__root__', name: 'Semua Media (tanpa folder)', depth: 0 },
    ...folders,
  ], [folders]);
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md" data-testid={T.mediaMoveDialog}>
        <DialogHeader>
          <DialogTitle>Pindahkan {count > 1 ? `${count} berkas` : 'berkas'}</DialogTitle>
          <DialogDescription>
            Pilih folder tujuan. URL berkas TIDAK berubah, jadi gambar yang sudah dipakai di
            produk atau konten tetap aman.
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-1.5">
          <Label>Folder tujuan</Label>
          <Select value={target} onValueChange={setTarget}>
            <SelectTrigger data-testid={T.mediaMoveSelect}>
              <SelectValue placeholder="Pilih folder" />
            </SelectTrigger>
            <SelectContent>
              {options.map((f) => (
                <SelectItem key={f.id} value={f.id}>
                  {`${'\u00a0'.repeat(f.depth * 3)}${f.depth ? '↳ ' : ''}${f.name}`}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <DialogFooter>
          <Button variant="secondary" onClick={() => onOpenChange(false)}>Batal</Button>
          <Button
            onClick={() => onSubmit(target === '__root__' ? null : target)}
            disabled={busy}
            className="gap-2"
            data-testid={T.mediaMoveSubmit}
          >
            <FolderInput className="h-4 w-4" /> {busy ? 'Memindahkan…' : 'Pindahkan'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

export const FromUrlDialog = ({ open, onOpenChange, onSubmit, busy, folderPath = '' }) => {
  const [url, setUrl] = useState('');
  const [alt, setAlt] = useState('');
  useEffect(() => { if (open) { setUrl(''); setAlt(''); } }, [open]);
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-lg" data-testid={T.mediaFromUrlDialog}>
        <DialogHeader>
          <DialogTitle>Tambah dari URL</DialogTitle>
          <DialogDescription>
            Gambar akan <strong>diunduh dan disimpan di penyimpanan lokal</strong>
            {folderPath ? ` (folder ${folderPath})` : ''} sehingga tidak akan broken walau
            situs sumbernya mati. Maks {MEDIA_MAX_MB}MB.
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-3">
          <div className="space-y-1.5">
            <Label htmlFor="media-url">URL gambar</Label>
            <Input
              id="media-url"
              autoFocus
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="https://contoh.com/gambar.jpg"
              data-testid={T.mediaFromUrlInput}
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="media-url-alt">Alt text (opsional)</Label>
            <Input
              id="media-url-alt"
              value={alt}
              onChange={(e) => setAlt(e.target.value)}
              placeholder="Deskripsi singkat gambar untuk SEO & aksesibilitas"
            />
          </div>
        </div>
        <DialogFooter>
          <Button variant="secondary" onClick={() => onOpenChange(false)}>Batal</Button>
          <Button
            onClick={() => onSubmit(url.trim(), alt.trim())}
            disabled={busy || !url.trim()}
            className="gap-2"
            data-testid={T.mediaFromUrlSubmit}
          >
            {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : <Link2 className="h-4 w-4" />}
            {busy ? 'Mengunduh…' : 'Unduh & Simpan'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

export const ConfirmDialog = ({
  open, onOpenChange, title, description, confirmLabel = 'Hapus', onConfirm, busy,
  testId = T.mediaConfirmDialog, confirmTestId = T.mediaConfirmAction,
}) => (
  <AlertDialog open={open} onOpenChange={onOpenChange}>
    <AlertDialogContent data-testid={testId}>
      <AlertDialogHeader>
        <AlertDialogTitle>{title}</AlertDialogTitle>
        <AlertDialogDescription>{description}</AlertDialogDescription>
      </AlertDialogHeader>
      <AlertDialogFooter>
        <AlertDialogCancel>Batal</AlertDialogCancel>
        <AlertDialogAction
          onClick={(e) => { e.preventDefault(); onConfirm(); }}
          className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
          data-testid={confirmTestId}
        >
          {busy ? 'Memproses…' : confirmLabel}
        </AlertDialogAction>
      </AlertDialogFooter>
    </AlertDialogContent>
  </AlertDialog>
);
