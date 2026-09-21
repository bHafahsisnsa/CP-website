// components/admin/media/FolderTree.js — rail folder bertingkat (E20).
//
// Fitur: expand/collapse, hitung aset, buat/rename/hapus, drop-target untuk
// memindahkan aset & folder (drag&drop) DENGAN fallback menu non-drag.
//
// CATATAN IMPLEMENTASI: tree dirender sebagai DAFTAR RATA (flat) hasil traversal,
// BUKAN komponen JSX yang memanggil dirinya sendiri. Pola rekursif-JSX membuat
// instrumentasi Babel dev (visual-edits) meledak "Maximum call stack size exceeded".
import React, { useMemo, useState } from 'react';
import {
  ChevronRight, Folder, FolderOpen, FolderPlus, Images, MoreVertical, Pencil, Trash2,
} from 'lucide-react';
import { Badge } from '../../ui/badge';
import { Button } from '../../ui/button';
import {
  DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '../../ui/dropdown-menu';
import { ACCENT, ACCENT_SOFT } from '../adminUi';
import { adminTestIds as T } from '../../../constants/testIds/admin';

const ROW_BASE = 'group/row flex w-full items-center gap-1.5 rounded-lg pr-1.5 h-9 text-sm '
  + 'transition-colors duration-150 focus-visible:outline-none focus-visible:ring-2 '
  + 'focus-visible:ring-[hsl(var(--ring))]';

/** Ratakan tree menjadi daftar (untuk <Select> pindah folder — fallback non-drag). */
export const flattenTree = (tree, depth, acc) => {
  const nodes = tree || [];
  const out = acc || [];
  const d = depth || 0;
  for (let i = 0; i < nodes.length; i += 1) {
    const n = nodes[i];
    out.push({ id: n.id, name: n.name, depth: d, path: n.path });
    flattenTree(n.children, d + 1, out);
  }
  return out;
};

/** Daftar baris yang TERLIHAT (menghormati state expand). Iteratif, tanpa rekursi JSX. */
const visibleRows = (tree, expandedMap) => {
  const rows = [];
  const stack = [];
  const src = tree || [];
  for (let i = src.length - 1; i >= 0; i -= 1) stack.push({ node: src[i], depth: 0 });
  while (stack.length) {
    const { node, depth } = stack.pop();
    const kids = node.children || [];
    rows.push({ node, depth, hasKids: kids.length > 0 });
    if (expandedMap[node.id] && kids.length) {
      for (let i = kids.length - 1; i >= 0; i -= 1) stack.push({ node: kids[i], depth: depth + 1 });
    }
  }
  return rows;
};

export const FolderTree = ({
  tree = [],
  root = null,
  activeId = '',
  onSelect,
  onCreateChild,
  onRename,
  onDelete,
  onMoveAssets,
  onMoveFolder,
  compact = false,
}) => {
  const [expanded, setExpanded] = useState({});
  const [dragOverId, setDragOverId] = useState(null);

  // Buka otomatis jalur menuju folder aktif.
  const autoOpen = useMemo(() => {
    const acc = {};
    const stack = [];
    (tree || []).forEach((n) => stack.push({ node: n, chain: [] }));
    while (stack.length) {
      const { node, chain } = stack.pop();
      if (node.id === activeId) chain.forEach((id) => { acc[id] = true; });
      (node.children || []).forEach((c) => stack.push({ node: c, chain: [...chain, node.id] }));
    }
    return acc;
  }, [tree, activeId]);

  const eff = useMemo(() => ({ ...autoOpen, ...expanded }), [autoOpen, expanded]);
  const toggle = (id) => setExpanded((e) => ({ ...e, [id]: !eff[id] }));
  const rows = useMemo(() => visibleRows(tree, eff), [tree, eff]);

  const readPayload = (e) => {
    try {
      const raw = e.dataTransfer.getData('application/x-cp-media');
      return raw ? JSON.parse(raw) : null;
    } catch (err) { return null; }
  };

  const dragOver = (e, key) => {
    if (!e.dataTransfer) return;
    const types = Array.from(e.dataTransfer.types || []);
    if (!types.includes('application/x-cp-media')) return;
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
    setDragOverId(key);
  };
  const dragLeave = (key) => setDragOverId((cur) => (cur === key ? null : cur));
  const handleDrop = (e, targetId) => {
    const payload = readPayload(e);
    setDragOverId(null);
    if (!payload) return;
    e.preventDefault();
    if (payload.type === 'assets' && payload.ids && payload.ids.length) {
      onMoveAssets(payload.ids, targetId);
    }
    if (payload.type === 'folder' && payload.id && payload.id !== targetId) {
      onMoveFolder(payload.id, targetId);
    }
  };
  const folderDragStart = (e, id) => {
    try {
      e.dataTransfer.setData('application/x-cp-media', JSON.stringify({ type: 'folder', id }));
      e.dataTransfer.effectAllowed = 'move';
    } catch (err) { /* noop */ }
  };

  const rootActive = !activeId;

  return (
    <div className="flex flex-col" data-testid={T.mediaFolderRail}>
      {/* ---- Semua Media (root) ---- */}
      <div
        className={ROW_BASE}
        style={{
          paddingLeft: 6,
          background: dragOverId === '__root__' || rootActive ? ACCENT_SOFT : undefined,
          boxShadow: dragOverId === '__root__' ? `inset 0 0 0 2px ${ACCENT}66` : undefined,
        }}
        onDragOver={(e) => dragOver(e, '__root__')}
        onDragLeave={() => dragLeave('__root__')}
        onDrop={(e) => handleDrop(e, null)}
        data-testid={T.mediaFolderRowAll}
      >
        <span className="h-5 w-5" />
        <button
          type="button"
          onClick={() => onSelect('')}
          className="flex min-w-0 flex-1 items-center gap-2 py-1 text-left"
        >
          <Images className="h-4 w-4 shrink-0" style={{ color: rootActive ? ACCENT : undefined }} />
          <span className={`truncate ${rootActive ? 'font-medium text-foreground' : 'text-foreground/85'}`}>
            Semua Media
          </span>
        </button>
        <Badge variant="secondary" className="shrink-0 rounded-full px-1.5 py-0 text-[10px] font-normal tabular-nums">
          {(root && root.total_count) || 0}
        </Badge>
      </div>

      {/* ---- Folder ---- */}
      {rows.length === 0 ? (
        <div className="px-2 py-6 text-center">
          <p className="text-xs font-medium text-foreground">Belum ada folder</p>
          <p className="mt-1 text-[11px] leading-relaxed text-muted-foreground">
            Buat folder untuk merapikan media. Folder bisa bertingkat tanpa batas.
          </p>
          {!compact ? (
            <Button
              size="sm"
              variant="secondary"
              className="mt-3 gap-1.5 rounded-lg"
              onClick={() => onCreateChild(null)}
            >
              <FolderPlus className="h-3.5 w-3.5" /> Folder Baru
            </Button>
          ) : null}
        </div>
      ) : rows.map(({ node, depth, hasKids }) => {
        const isActive = activeId === node.id;
        const isOpen = !!eff[node.id];
        const isDropTarget = dragOverId === node.id;
        return (
          <div
            key={node.id}
            className={ROW_BASE}
            style={{
              paddingLeft: 6 + depth * 14,
              background: isDropTarget || isActive ? ACCENT_SOFT : undefined,
              boxShadow: isDropTarget ? `inset 0 0 0 2px ${ACCENT}66` : undefined,
            }}
            data-testid={T.mediaFolderRow}
            data-folder-id={node.id}
            data-folder-depth={depth}
            data-active={isActive ? 'true' : undefined}
            draggable={!compact}
            onDragStart={(e) => { if (!compact) folderDragStart(e, node.id); }}
            onDragOver={(e) => dragOver(e, node.id)}
            onDragLeave={() => dragLeave(node.id)}
            onDrop={(e) => handleDrop(e, node.id)}
          >
            <button
              type="button"
              aria-label={isOpen ? `Tutup folder ${node.name}` : `Buka folder ${node.name}`}
              onClick={(e) => { e.stopPropagation(); toggle(node.id); }}
              className={`grid h-5 w-5 shrink-0 place-items-center rounded transition-colors ${
                hasKids ? 'hover:bg-muted' : 'pointer-events-none opacity-0'
              }`}
              tabIndex={hasKids ? 0 : -1}
            >
              <ChevronRight
                className={`h-3.5 w-3.5 text-muted-foreground transition-transform duration-150 ${
                  isOpen ? 'rotate-90' : ''
                }`}
              />
            </button>

            <button
              type="button"
              onClick={() => onSelect(node.id)}
              className="flex min-w-0 flex-1 items-center gap-2 py-1 text-left"
              title={node.path}
            >
              {isOpen && hasKids
                ? <FolderOpen className="h-4 w-4 shrink-0" style={{ color: ACCENT }} />
                : <Folder className="h-4 w-4 shrink-0" style={{ color: isActive ? ACCENT : undefined }} />}
              <span className={`truncate ${isActive ? 'font-medium text-foreground' : 'text-foreground/85'}`}>
                {node.name}
              </span>
            </button>

            <Badge
              variant="secondary"
              className="shrink-0 rounded-full px-1.5 py-0 text-[10px] font-normal tabular-nums"
            >
              {node.total_count != null ? node.total_count : (node.asset_count || 0)}
            </Badge>

            {!compact ? (
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <button
                    type="button"
                    aria-label={`Menu folder ${node.name}`}
                    className="grid h-6 w-6 shrink-0 place-items-center rounded-md text-muted-foreground opacity-0 transition-opacity hover:bg-muted hover:text-foreground focus:opacity-100 group-hover/row:opacity-100"
                    data-testid={T.mediaFolderMenu}
                  >
                    <MoreVertical className="h-3.5 w-3.5" />
                  </button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end" className="w-52">
                  <DropdownMenuItem onClick={() => onCreateChild(node.id)}>
                    <FolderPlus className="mr-2 h-4 w-4" /> Buat subfolder
                  </DropdownMenuItem>
                  <DropdownMenuItem onClick={() => onRename(node)} data-testid={T.mediaFolderRename}>
                    <Pencil className="mr-2 h-4 w-4" /> Ubah nama
                  </DropdownMenuItem>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem
                    onClick={() => onDelete(node)}
                    className="text-rose-600 focus:text-rose-600"
                    data-testid={T.mediaFolderDelete}
                  >
                    <Trash2 className="mr-2 h-4 w-4" /> Hapus folder
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            ) : null}
          </div>
        );
      })}
    </div>
  );
};

export default FolderTree;
