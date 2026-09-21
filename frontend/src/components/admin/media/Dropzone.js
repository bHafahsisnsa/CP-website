// components/admin/media/Dropzone.js — area seret & lepas berkas (E20).
//
// Selalu menyediakan tombol "Pilih Berkas" (fallback non-drag / aksesibilitas).
import React, { useCallback, useRef, useState } from 'react';
import { UploadCloud } from 'lucide-react';
import { Button } from '../../ui/button';
import { MEDIA_ACCEPT, MEDIA_MAX_MB } from '../../../services/media';
import { ACCENT } from '../adminUi';
import { adminTestIds as T } from '../../../constants/testIds/admin';

export const Dropzone = ({
  onFiles,
  compact = false,
  busy = false,
  className = '',
  testId = T.mediaDropzone,
  inputTestId = T.mediaFileInput,
  title = 'Seret & lepas gambar di sini',
  hint = `Maks ${MEDIA_MAX_MB}MB per berkas · JPG, PNG, WebP, GIF, SVG, AVIF, HEIC`,
}) => {
  const inputRef = useRef(null);
  const [over, setOver] = useState(false);

  const pick = useCallback(() => inputRef.current?.click(), []);
  const handleFiles = useCallback((files) => {
    if (files && files.length) onFiles(files);
    if (inputRef.current) inputRef.current.value = '';
  }, [onFiles]);

  return (
    <div
      className={`rounded-2xl border-2 border-dashed bg-card text-center transition-colors duration-150 ${
        compact ? 'px-4 py-5' : 'px-6 py-10'
      } ${className}`}
      style={{
        borderColor: over ? ACCENT : 'hsl(var(--border))',
        background: over ? 'rgba(184,155,106,0.08)' : undefined,
      }}
      onDragOver={(e) => { e.preventDefault(); setOver(true); }}
      onDragEnter={(e) => { e.preventDefault(); setOver(true); }}
      onDragLeave={() => setOver(false)}
      onDrop={(e) => {
        e.preventDefault();
        setOver(false);
        handleFiles(e.dataTransfer?.files);
      }}
      data-testid={testId}
      data-drag-over={over ? 'true' : undefined}
    >
      <input
        ref={inputRef}
        type="file"
        multiple
        accept={MEDIA_ACCEPT}
        className="hidden"
        onChange={(e) => handleFiles(e.target.files)}
        data-testid={inputTestId}
      />
      <UploadCloud
        className={`mx-auto ${compact ? 'h-6 w-6' : 'h-9 w-9'}`}
        style={{ color: ACCENT }}
        aria-hidden="true"
      />
      <p className={`mt-2 font-medium text-foreground ${compact ? 'text-xs' : 'text-sm'}`}>{title}</p>
      <p className="mt-1 text-[11px] leading-relaxed text-muted-foreground">{hint}</p>
      <Button
        type="button"
        variant="secondary"
        size={compact ? 'sm' : 'default'}
        className="mt-3 rounded-lg"
        onClick={pick}
        disabled={busy}
        data-testid={T.mediaDropzonePick}
      >
        {busy ? 'Mengunggah…' : 'Pilih Berkas'}
      </Button>
    </div>
  );
};

export default Dropzone;
