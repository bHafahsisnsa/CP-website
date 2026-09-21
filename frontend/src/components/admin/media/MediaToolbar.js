// components/admin/media/MediaToolbar.js — toolbar pustaka media (E20).
import React from 'react';
import { FolderPlus, LayoutGrid, Link2, List, Search, Upload, X } from 'lucide-react';
import { Button } from '../../ui/button';
import { Input } from '../../ui/input';
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from '../../ui/select';
import { KIND_OPTIONS, SORT_OPTIONS } from '../../../services/media';
import { ACCENT, ACCENT_SOFT } from '../adminUi';
import { adminTestIds as T } from '../../../constants/testIds/admin';

export const MediaToolbar = ({
  query, onQueryChange, kind, onKindChange, sort, onSortChange,
  view, onViewChange, onUpload, onNewFolder, onFromUrl, recursive, onRecursiveChange,
  showFolderActions = true, className = '',
}) => (
  <div className={`flex flex-col gap-3 ${className}`} data-testid={T.mediaToolbar}>
    <div className="flex flex-wrap items-center gap-2">
      <Button onClick={onUpload} className="gap-2 rounded-lg" data-testid={T.mediaUploadBtn}>
        <Upload className="h-4 w-4" /> Upload
      </Button>
      {onFromUrl ? (
        <Button
          onClick={onFromUrl}
          variant="secondary"
          className="gap-2 rounded-lg"
          data-testid={T.mediaFromUrlBtn}
        >
          <Link2 className="h-4 w-4" /> Dari URL
        </Button>
      ) : null}
      {showFolderActions ? (
        <Button
          onClick={onNewFolder}
          variant="secondary"
          className="gap-2 rounded-lg"
          data-testid={T.mediaNewFolderBtn}
        >
          <FolderPlus className="h-4 w-4" /> Folder Baru
        </Button>
      ) : null}

      <div className="ml-auto flex items-center gap-1 rounded-lg border border-border/70 bg-card p-0.5">
        <button
          type="button"
          aria-label="Tampilan grid"
          onClick={() => onViewChange('grid')}
          className="grid h-8 w-8 place-items-center rounded-md transition-colors"
          style={view === 'grid'
            ? { background: ACCENT_SOFT, color: ACCENT }
            : undefined}
          data-testid={T.mediaViewGrid}
          data-active={view === 'grid' ? 'true' : undefined}
        >
          <LayoutGrid className="h-4 w-4" />
        </button>
        <button
          type="button"
          aria-label="Tampilan daftar"
          onClick={() => onViewChange('list')}
          className="grid h-8 w-8 place-items-center rounded-md transition-colors"
          style={view === 'list'
            ? { background: ACCENT_SOFT, color: ACCENT }
            : undefined}
          data-testid={T.mediaViewList}
          data-active={view === 'list' ? 'true' : undefined}
        >
          <List className="h-4 w-4" />
        </button>
      </div>
    </div>

    <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
      <div className="relative flex-1 min-w-[180px]">
        <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <Input
          value={query}
          onChange={(e) => onQueryChange(e.target.value)}
          placeholder="Cari nama berkas, alt, atau judul…"
          className="h-10 pl-9 pr-9"
          data-testid={T.mediaSearchInput}
        />
        {query ? (
          <button
            type="button"
            aria-label="Bersihkan pencarian"
            onClick={() => onQueryChange('')}
            className="absolute right-2 top-1/2 grid h-6 w-6 -translate-y-1/2 place-items-center rounded-md text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
            data-testid={T.mediaSearchClear}
          >
            <X className="h-3.5 w-3.5" />
          </button>
        ) : null}
      </div>

      <Select value={kind} onValueChange={onKindChange}>
        <SelectTrigger className="h-10 sm:w-[168px]" data-testid={T.mediaTypeFilter}>
          <SelectValue placeholder="Semua tipe" />
        </SelectTrigger>
        <SelectContent>
          {KIND_OPTIONS.map((o) => (
            <SelectItem key={o.value} value={o.value}>{o.label}</SelectItem>
          ))}
        </SelectContent>
      </Select>

      <Select value={sort} onValueChange={onSortChange}>
        <SelectTrigger className="h-10 sm:w-[176px]" data-testid={T.mediaSortSelect}>
          <SelectValue placeholder="Terbaru" />
        </SelectTrigger>
        <SelectContent>
          {SORT_OPTIONS.map((o) => (
            <SelectItem key={o.value} value={o.value}>{o.label}</SelectItem>
          ))}
        </SelectContent>
      </Select>

      {onRecursiveChange ? (
        <label className="flex items-center gap-2 whitespace-nowrap text-xs text-muted-foreground">
          <input
            type="checkbox"
            checked={!!recursive}
            onChange={(e) => onRecursiveChange(e.target.checked)}
            className="h-3.5 w-3.5 rounded border-border accent-[#B89B6A]"
            data-testid={T.mediaRecursiveToggle}
          />
          Termasuk subfolder
        </label>
      ) : null}
    </div>
  </div>
);

export default MediaToolbar;
