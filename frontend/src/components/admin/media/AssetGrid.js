// components/admin/media/AssetGrid.js — grid kartu aset + varian daftar (E20).
import React from 'react';
import {
  Copy, ExternalLink, FolderInput, MoreVertical, Pencil, Trash2,
} from 'lucide-react';
import { Badge } from '../../ui/badge';
import { Checkbox } from '../../ui/checkbox';
import { Skeleton } from '../../ui/skeleton';
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from '../../ui/table';
import {
  DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '../../ui/dropdown-menu';
import { SmartImage } from '../../shared/SmartImage';
import {
  CHECKER_STYLE, formatBytes, mediaTypeBadge, needsCheckerboard,
} from '../../../lib/mediaUrl';
import { ACCENT, ACCENT_SOFT, formatDateTime } from '../adminUi';
import { adminTestIds as T } from '../../../constants/testIds/admin';

const dragPayload = (e, ids) => {
  try {
    e.dataTransfer.setData('application/x-cp-media', JSON.stringify({ type: 'assets', ids }));
    e.dataTransfer.effectAllowed = 'move';
  } catch (_) { /* noop */ }
};

const AssetMenu = ({ asset, onDetails, onCopy, onMove, onDelete, align = 'end' }) => (
  <DropdownMenu>
    <DropdownMenuTrigger asChild>
      <button
        type="button"
        aria-label={`Menu ${asset.filename}`}
        onClick={(e) => e.stopPropagation()}
        className="grid h-7 w-7 place-items-center rounded-md border border-border/70 bg-card/95 text-muted-foreground shadow-sm transition-colors hover:bg-muted hover:text-foreground"
        data-testid={T.mediaTileMenu}
      >
        <MoreVertical className="h-3.5 w-3.5" />
      </button>
    </DropdownMenuTrigger>
    <DropdownMenuContent align={align} className="w-52">
      <DropdownMenuItem onClick={() => onDetails(asset)}>
        <Pencil className="mr-2 h-4 w-4" /> Detail & ubah
      </DropdownMenuItem>
      <DropdownMenuItem onClick={() => onCopy(asset)} data-testid={T.mediaTileCopy}>
        <Copy className="mr-2 h-4 w-4" /> Salin URL
      </DropdownMenuItem>
      {onMove ? (
        <DropdownMenuItem onClick={() => onMove(asset)} data-testid={T.mediaTileMove}>
          <FolderInput className="mr-2 h-4 w-4" /> Pindahkan ke…
        </DropdownMenuItem>
      ) : null}
      <DropdownMenuSeparator />
      <DropdownMenuItem
        onClick={() => onDelete(asset)}
        className="text-rose-600 focus:text-rose-600"
        data-testid={T.mediaTileDelete}
      >
        <Trash2 className="mr-2 h-4 w-4" /> Hapus
      </DropdownMenuItem>
    </DropdownMenuContent>
  </DropdownMenu>
);

export const AssetTile = ({
  asset, selected, focused, onToggleSelect, onOpen, onDetails, onCopy, onMove, onDelete,
  selectedIds, selectable = true, showMenu = true,
}) => {
  const badge = mediaTypeBadge(asset);
  return (
    <div
      className="group relative overflow-hidden rounded-2xl border bg-card shadow-sm transition-shadow duration-150 hover:shadow-md"
      style={{
        borderColor: selected || focused ? ACCENT : 'hsl(var(--border) / 0.7)',
        boxShadow: selected ? `0 0 0 2px ${ACCENT}55` : undefined,
        background: selected ? ACCENT_SOFT : undefined,
      }}
      data-testid={T.mediaTile}
      data-asset-id={asset.id}
      data-selected={selected ? 'true' : undefined}
      draggable
      onDragStart={(e) => dragPayload(e, selected && selectedIds?.length ? selectedIds : [asset.id])}
    >
      <button
        type="button"
        onClick={() => onOpen(asset)}
        onDoubleClick={() => onDetails && onDetails(asset)}
        className="block w-full text-left focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[hsl(var(--ring))]"
        title={asset.filename}
      >
        <span
          className="relative block aspect-[4/3] w-full bg-muted/40"
          style={needsCheckerboard(asset) ? CHECKER_STYLE : undefined}
        >
          <SmartImage
            src={asset.thumb_url || asset.url}
            alt={asset.alt || asset.filename || 'media'}
            className="absolute inset-0 h-full w-full"
            fit="cover"
            showRetry={false}
            fallbackLabel="Tidak ditemukan"
          />
        </span>
        <span className="block px-3 py-2.5">
          <span className="block truncate text-[13px] font-medium text-foreground">
            {asset.filename || 'media'}
          </span>
          <span className="mt-0.5 flex items-center gap-1.5 text-[11px] text-muted-foreground">
            <span className="font-['Azeret_Mono',monospace]">{formatBytes(asset.size)}</span>
            {asset.width ? (
              <>
                <span aria-hidden="true">·</span>
                <span className="font-['Azeret_Mono',monospace]">{asset.width}×{asset.height}</span>
              </>
            ) : null}
          </span>
        </span>
      </button>

      {selectable ? (
        <div
          className={`absolute left-2 top-2 transition-opacity duration-150 ${
            selected ? 'opacity-100' : 'opacity-0 group-hover:opacity-100 focus-within:opacity-100'
          }`}
        >
          <span className="grid h-7 w-7 place-items-center rounded-md border border-border/70 bg-card/95 shadow-sm">
            <Checkbox
              checked={!!selected}
              onCheckedChange={() => onToggleSelect(asset.id)}
              aria-label={`Pilih ${asset.filename}`}
              data-testid={T.mediaTileCheckbox}
            />
          </span>
        </div>
      ) : null}

      {badge ? (
        <Badge
          variant="outline"
          className="pointer-events-none absolute bottom-[52px] left-2 border-border/70 bg-card/95 px-1.5 py-0 text-[9px] font-semibold tracking-wide"
        >
          {badge}
        </Badge>
      ) : null}

      {showMenu ? (
        <div className="absolute right-2 top-2 opacity-0 transition-opacity duration-150 group-hover:opacity-100 focus-within:opacity-100">
          <AssetMenu
            asset={asset}
            onDetails={onDetails}
            onCopy={onCopy}
            onMove={onMove}
            onDelete={onDelete}
          />
        </div>
      ) : null}
    </div>
  );
};

export const AssetGridSkeleton = ({ count = 10 }) => (
  <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 sm:gap-4">
    {Array.from({ length: count }).map((_, i) => (
      <div key={i} className="overflow-hidden rounded-2xl border border-border/70 bg-card">
        <Skeleton className="aspect-[4/3] w-full rounded-none" />
        <div className="space-y-2 p-3">
          <Skeleton className="h-3 w-3/4" />
          <Skeleton className="h-2.5 w-1/2" />
        </div>
      </div>
    ))}
  </div>
);

export const AssetGrid = ({
  items = [], selectedIds = [], focusedId = '', onToggleSelect, onOpen, onDetails,
  onCopy, onMove, onDelete, loading = false, selectable = true, showMenu = true,
  columnsClassName = 'grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5',
}) => {
  if (loading) return <AssetGridSkeleton />;
  return (
    <div className={`grid gap-3 sm:gap-4 ${columnsClassName}`} data-testid={T.mediaGrid}>
      {items.map((a) => (
        <AssetTile
          key={a.id}
          asset={a}
          selected={selectedIds.includes(a.id)}
          focused={focusedId === a.id}
          selectedIds={selectedIds}
          onToggleSelect={onToggleSelect}
          onOpen={onOpen}
          onDetails={onDetails}
          onCopy={onCopy}
          onMove={onMove}
          onDelete={onDelete}
          selectable={selectable}
          showMenu={showMenu}
        />
      ))}
    </div>
  );
};

export const AssetList = ({
  items = [], selectedIds = [], focusedId = '', onToggleSelect, onOpen, onDetails,
  onCopy, onMove, onDelete, loading = false, allSelected = false, onToggleAll,
}) => {
  if (loading) {
    return (
      <div className="space-y-2">
        {Array.from({ length: 8 }).map((_, i) => <Skeleton key={i} className="h-12 w-full" />)}
      </div>
    );
  }
  return (
    <div className="overflow-hidden rounded-2xl border border-border/70 bg-card">
      <Table data-testid={T.mediaList}>
        <TableHeader>
          <TableRow>
            <TableHead className="w-10">
              <Checkbox
                checked={allSelected}
                onCheckedChange={onToggleAll}
                aria-label="Pilih semua di halaman ini"
                data-testid={T.mediaListSelectAll}
              />
            </TableHead>
            <TableHead>Nama</TableHead>
            <TableHead className="hidden sm:table-cell">Tipe</TableHead>
            <TableHead className="hidden sm:table-cell text-right">Ukuran</TableHead>
            <TableHead className="hidden lg:table-cell">Diubah</TableHead>
            <TableHead className="w-12" />
          </TableRow>
        </TableHeader>
        <TableBody>
          {items.map((a) => {
            const selected = selectedIds.includes(a.id);
            return (
              <TableRow
                key={a.id}
                className="cursor-pointer hover:bg-muted/40"
                style={selected ? { background: ACCENT_SOFT } : undefined}
                data-testid={T.mediaListRow}
                data-asset-id={a.id}
                data-selected={selected ? 'true' : undefined}
                draggable
                onDragStart={(e) => dragPayload(e, selected && selectedIds.length ? selectedIds : [a.id])}
                onClick={() => onOpen(a)}
              >
                <TableCell onClick={(e) => e.stopPropagation()}>
                  <Checkbox
                    checked={selected}
                    onCheckedChange={() => onToggleSelect(a.id)}
                    aria-label={`Pilih ${a.filename}`}
                    data-testid={T.mediaListRowCheckbox}
                  />
                </TableCell>
                <TableCell>
                  <div className="flex min-w-0 items-center gap-3">
                    <span
                      className="relative block h-10 w-10 shrink-0 overflow-hidden rounded-lg border border-border/60 bg-muted/40"
                      style={needsCheckerboard(a) ? CHECKER_STYLE : undefined}
                    >
                      <SmartImage
                        src={a.thumb_url || a.url}
                        alt={a.alt || a.filename || 'media'}
                        className="absolute inset-0 h-full w-full"
                        showRetry={false}
                        fallbackLabel=""
                      />
                    </span>
                    <div className="min-w-0">
                      <div className="truncate text-[13px] font-medium text-foreground">{a.filename}</div>
                      {a.alt ? (
                        <div className="truncate text-[11px] text-muted-foreground">{a.alt}</div>
                      ) : null}
                    </div>
                  </div>
                </TableCell>
                <TableCell className="hidden sm:table-cell">
                  <Badge variant="outline" className="text-[10px]">
                    {mediaTypeBadge(a) || (a.mime || '').split('/')[1]?.toUpperCase() || 'FILE'}
                  </Badge>
                </TableCell>
                <TableCell className="hidden sm:table-cell text-right font-['Azeret_Mono',monospace] text-xs">
                  {formatBytes(a.size)}
                </TableCell>
                <TableCell className="hidden lg:table-cell text-xs text-muted-foreground">
                  {formatDateTime(a.updated_at || a.uploaded_at)}
                </TableCell>
                <TableCell onClick={(e) => e.stopPropagation()} className="text-right">
                  <AssetMenu
                    asset={a}
                    onDetails={onDetails}
                    onCopy={onCopy}
                    onMove={onMove}
                    onDelete={onDelete}
                  />
                </TableCell>
              </TableRow>
            );
          })}
        </TableBody>
      </Table>
    </div>
  );
};

export const ExternalHint = () => (
  <span className="inline-flex items-center gap-1 text-[11px] text-muted-foreground">
    <ExternalLink className="h-3 w-3" /> URL eksternal
  </span>
);

export default AssetGrid;
