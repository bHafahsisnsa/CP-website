// components/admin/ContentForm.js — form generik berbasis skema (Epic E9 CMS).
// Merender field: text, textarea, image (Media Manager picker + upload + URL + preview),
// list (drag-and-drop reorder + string), repeater (drag-and-drop reorder + sub-field).
// Controlled: onChange(nextValue) mengembalikan objek penuh.
import React, { useState } from 'react';
import { Plus, Trash2, GripVertical, Images, Pencil } from 'lucide-react';
import { Input } from '../ui/input';
import { Textarea } from '../ui/textarea';
import { Button } from '../ui/button';
import { Label } from '../ui/label';
import { Switch } from '../ui/switch';
import { MediaField } from './media/MediaField';
import { MediaPickerDialog } from './media/MediaPickerDialog';
import { SmartImage } from '../shared/SmartImage';

// ============================== IMAGE FIELD ==============================
// E20: memakai <MediaField> — pilih dari Media Manager, upload, atau URL (diunduh lokal).
const ImageField = ({ field, value, onChange }) => (
  <div data-testid={`cms-field-${field.name}`}>
    <MediaField
      value={value ?? ''}
      onChange={onChange}
      testId={`cms-image-field-${field.name}`}
      pickerTitle={`Pilih Gambar — ${field.label || field.name}`}
      hint="Pilih dari Media Manager, unggah dari perangkat, atau tempel URL (otomatis diunduh ke penyimpanan lokal)."
    />
  </div>
);

// ============================== TOGGLE / SELECT ==============================
const ToggleField = ({ field, value, onChange }) => (
  <label className="flex items-center gap-3 cursor-pointer select-none" data-testid={`cms-field-${field.name}`}>
    <Switch checked={!!value} onCheckedChange={onChange} data-testid={`cms-toggle-${field.name}`} />
    <span className="text-sm text-muted-foreground">{value ? 'Ya' : 'Tidak'}</span>
  </label>
);

const SelectField = ({ field, value, onChange }) => (
  <select
    value={value ?? ''}
    onChange={(e) => onChange(e.target.value)}
    className="h-9 w-full rounded-md border border-input bg-background px-3 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
    data-testid={`cms-field-${field.name}`}
  >
    {(field.options || []).map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
  </select>
);

// ============================== GALLERY FIELD ==============================
// Multi-gambar dari Media Manager: grid thumbnail + caption/tautan + drag reorder.
const GalleryField = ({ field, value, onChange }) => {
  const arr = Array.isArray(value) ? value : [];
  const [pickerOpen, setPickerOpen] = useState(false);
  const [editing, setEditing] = useState(null);
  const upd = (i, k, v) => onChange(arr.map((row, idx) => (idx === i ? { ...row, [k]: v } : row)));
  const del = (i) => onChange(arr.filter((_, idx) => idx !== i));
  const { handlers, dragIdx } = useDnd((from, to) => onChange(reorderArr(arr, from, to)));
  const addAssets = (assets) => {
    const list = Array.isArray(assets) ? assets : [assets];
    const fresh = list.filter((a) => a?.url && !arr.some((r) => r.image === a.url))
      .map((a) => ({ image: a.url, caption: a.alt || a.title || '', to: '' }));
    if (fresh.length) onChange([...arr, ...fresh]);
  };
  return (
    <div className="space-y-3" data-testid={`cms-gallery-${field.name}`}>
      {arr.length === 0 ? (
        <button
          type="button"
          onClick={() => setPickerOpen(true)}
          className="w-full rounded-xl border-2 border-dashed border-border/80 py-8 grid place-items-center gap-2 text-muted-foreground hover:border-primary/50 hover:text-foreground transition-colors"
          data-testid={`cms-gallery-empty-${field.name}`}
        >
          <Images className="h-6 w-6" />
          <span className="text-sm">Belum ada foto — klik untuk memilih dari Media</span>
        </button>
      ) : (
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
          {arr.map((row, i) => {
            const h = handlers(i);
            return (
              <div
                key={`${row.image}-${i}`}
                draggable
                onDragStart={h.onDragStart}
                onDragOver={h.onDragOver}
                onDrop={h.onDrop}
                onDragLeave={h.onDragLeave}
                onDragEnd={h.onDragEnd}
                className={`group relative rounded-lg overflow-hidden border border-border/70 bg-muted/30 cursor-grab active:cursor-grabbing transition-all ${dragIdx === i ? 'opacity-40' : ''} ${h['data-drop-target'] ? 'ring-2 ring-primary/50' : ''}`}
                data-testid={`cms-gallery-item-${field.name}-${i}`}
              >
                <SmartImage src={row.image} alt={row.caption} className="aspect-square" imgClassName="h-full w-full object-cover" showRetry={false} />
                <div className="absolute top-1 left-1 rounded bg-black/60 text-white text-[10px] px-1.5 py-0.5 font-mono">{i + 1}</div>
                <div className="absolute inset-x-0 bottom-0 p-1.5 flex items-center justify-between gap-1 bg-gradient-to-t from-black/70 to-transparent opacity-0 group-hover:opacity-100 transition-opacity">
                  <button type="button" onClick={() => setEditing(editing === i ? null : i)} className="rounded bg-white/90 text-black p-1 hover:bg-white" title="Caption & tautan" data-testid={`cms-gallery-edit-${field.name}-${i}`}>
                    <Pencil className="h-3 w-3" />
                  </button>
                  <button type="button" onClick={() => del(i)} className="rounded bg-white/90 text-destructive p-1 hover:bg-white" title="Hapus" data-testid={`cms-gallery-del-${field.name}-${i}`}>
                    <Trash2 className="h-3 w-3" />
                  </button>
                </div>
                {row.caption ? <div className="absolute inset-x-0 bottom-0 px-1.5 py-1 text-[10px] text-white bg-black/50 truncate group-hover:opacity-0 transition-opacity">{row.caption}</div> : null}
              </div>
            );
          })}
          <button
            type="button"
            onClick={() => setPickerOpen(true)}
            className="aspect-square rounded-lg border-2 border-dashed border-border/80 grid place-items-center text-muted-foreground hover:border-primary/50 hover:text-foreground transition-colors"
            title="Tambah foto"
            data-testid={`cms-gallery-add-${field.name}`}
          >
            <Plus className="h-5 w-5" />
          </button>
        </div>
      )}
      {editing != null && arr[editing] ? (
        <div className="rounded-lg border border-border/70 p-3 bg-muted/30 grid sm:grid-cols-2 gap-3">
          <div>
            <Label className="text-xs mb-1 block">Caption foto #{editing + 1}</Label>
            <Input value={arr[editing].caption ?? ''} onChange={(e) => upd(editing, 'caption', e.target.value)} data-testid={`cms-gallery-caption-${field.name}`} />
          </div>
          <div>
            <Label className="text-xs mb-1 block">Tautan saat diklik (opsional)</Label>
            <Input value={arr[editing].to ?? ''} onChange={(e) => upd(editing, 'to', e.target.value)} placeholder="/shop atau https://…" data-testid={`cms-gallery-to-${field.name}`} />
          </div>
        </div>
      ) : null}
      <div className="flex items-center justify-between text-xs text-muted-foreground">
        <span>{arr.length} foto · geser untuk mengurutkan</span>
        <Button type="button" variant="outline" size="sm" onClick={() => setPickerOpen(true)} className="gap-1" data-testid={`cms-gallery-pick-${field.name}`}>
          <Images className="h-3.5 w-3.5" /> Pilih dari Media
        </Button>
      </div>
      <MediaPickerDialog
        open={pickerOpen}
        onOpenChange={setPickerOpen}
        mode="multi"
        title={`Pilih Foto — ${field.label || field.name}`}
        onConfirm={addAssets}
      />
    </div>
  );
};

// ============================== SCALAR FIELD ==============================
const Scalar = ({ field, value, onChange }) => {
  if (field.type === 'toggle') return <ToggleField field={field} value={value} onChange={onChange} />;
  if (field.type === 'select') return <SelectField field={field} value={value} onChange={onChange} />;
  if (field.type === 'textarea') {
    return (
      <Textarea
        rows={3}
        value={value ?? ''}
        onChange={(e) => onChange(e.target.value)}
        data-testid={`cms-field-${field.name}`}
      />
    );
  }
  if (field.type === 'image') {
    return <ImageField field={field} value={value} onChange={onChange} />;
  }
  return (
    <Input
      value={value ?? ''}
      onChange={(e) => onChange(e.target.value)}
      data-testid={`cms-field-${field.name}`}
    />
  );
};

// ============================== DND HELPER ==============================
// HTML5 native DnD hook: dragIndex + dropIndex sederhana; onReorder(from, to).
const useDnd = (onReorder) => {
  const [dragIdx, setDragIdx] = useState(null);
  const [overIdx, setOverIdx] = useState(null);
  const handlers = (i) => ({
    draggable: true,
    onDragStart: (e) => { setDragIdx(i); try { e.dataTransfer.effectAllowed = 'move'; } catch (_) {} },
    onDragOver: (e) => { e.preventDefault(); setOverIdx(i); try { e.dataTransfer.dropEffect = 'move'; } catch (_) {} },
    onDragLeave: () => { if (overIdx === i) setOverIdx(null); },
    onDrop: (e) => {
      e.preventDefault();
      if (dragIdx != null && dragIdx !== i) onReorder(dragIdx, i);
      setDragIdx(null); setOverIdx(null);
    },
    onDragEnd: () => { setDragIdx(null); setOverIdx(null); },
    'data-drop-target': overIdx === i && dragIdx != null ? 'true' : undefined,
    'data-drag-source': dragIdx === i ? 'true' : undefined,
  });
  return { handlers, dragIdx, overIdx };
};

const reorderArr = (arr, from, to) => {
  const next = [...arr];
  const [it] = next.splice(from, 1);
  next.splice(to, 0, it);
  return next;
};

// ============================== LIST FIELD ==============================
const ListField = ({ field, value, onChange }) => {
  const arr = Array.isArray(value) ? value : [];
  const upd = (i, v) => onChange(arr.map((x, idx) => (idx === i ? v : x)));
  const del = (i) => onChange(arr.filter((_, idx) => idx !== i));
  const add = () => onChange([...arr, '']);
  const { handlers, dragIdx } = useDnd((from, to) => onChange(reorderArr(arr, from, to)));
  return (
    <div className="space-y-2">
      {arr.map((v, i) => {
        const h = handlers(i);
        const isDragging = dragIdx === i;
        return (
          <div
            key={i}
            className={`flex items-center gap-2 rounded-md ${isDragging ? 'opacity-40' : ''} ${h['data-drop-target'] ? 'ring-2 ring-primary/40' : ''}`}
            onDragOver={h.onDragOver}
            onDrop={h.onDrop}
            onDragLeave={h.onDragLeave}
            onDragEnd={h.onDragEnd}
          >
            <button
              type="button"
              draggable={h.draggable}
              onDragStart={h.onDragStart}
              onDragEnd={h.onDragEnd}
              className="cursor-grab active:cursor-grabbing p-1 text-muted-foreground hover:text-foreground"
              aria-label="Geser untuk atur ulang"
              data-testid={`cms-list-drag-${field.name}-${i}`}
            >
              <GripVertical className="h-4 w-4" />
            </button>
            <Input value={v ?? ''} onChange={(e) => upd(i, e.target.value)} data-testid={`cms-list-${field.name}-${i}`} />
            <Button type="button" variant="ghost" size="icon" onClick={() => del(i)} aria-label="Hapus">
              <Trash2 className="h-4 w-4 text-destructive" />
            </Button>
          </div>
        );
      })}
      <Button type="button" variant="outline" size="sm" onClick={add} className="gap-1" data-testid={`cms-list-add-${field.name}`}>
        <Plus className="h-3.5 w-3.5" /> Tambah
      </Button>
    </div>
  );
};

// ============================== REPEATER FIELD ==============================
const RepeaterField = ({ field, value, onChange }) => {
  const arr = Array.isArray(value) ? value : [];
  const updRow = (i, key, v) => onChange(arr.map((row, idx) => (idx === i ? { ...row, [key]: v } : row)));
  const del = (i) => onChange(arr.filter((_, idx) => idx !== i));
  const add = () => onChange([...arr, Object.fromEntries(field.item.map((f) => [f.name, f.type === 'toggle' ? true : '']))]);
  const { handlers, dragIdx } = useDnd((from, to) => onChange(reorderArr(arr, from, to)));
  // Baris ringkas bila semua sub-field select/toggle (mis. Tata Letak Beranda).
  const compact = field.item.every((f) => f.type === 'select' || f.type === 'toggle');
  if (compact) {
    return (
      <div className="space-y-1.5">
        {arr.map((row, i) => {
          const h = handlers(i);
          return (
            <div
              key={i}
              className={`flex items-center gap-2 rounded-lg border border-border/70 bg-muted/30 px-2 py-1.5 transition-all ${dragIdx === i ? 'opacity-40 border-dashed' : ''} ${h['data-drop-target'] ? 'ring-2 ring-primary/40 border-primary/50' : ''}`}
              onDragOver={h.onDragOver} onDrop={h.onDrop} onDragLeave={h.onDragLeave} onDragEnd={h.onDragEnd}
              data-testid={`cms-rep-row-${field.name}-${i}`}
            >
              <button type="button" draggable={h.draggable} onDragStart={h.onDragStart} onDragEnd={h.onDragEnd}
                className="cursor-grab active:cursor-grabbing p-1 text-muted-foreground hover:text-foreground" aria-label="Geser untuk atur ulang"
                data-testid={`cms-rep-drag-${field.name}-${i}`}>
                <GripVertical className="h-4 w-4" />
              </button>
              <span className="w-6 text-center text-[11px] font-mono text-muted-foreground">{i + 1}</span>
              {field.item.map((sf) => (
                <div key={sf.name} className={sf.type === 'select' ? 'flex-1 min-w-0' : 'shrink-0'} title={sf.label}>
                  <Scalar field={{ ...sf, name: `${sf.name}-${i}` }} value={row?.[sf.name]} onChange={(v) => updRow(i, sf.name, v)} />
                </div>
              ))}
              <Button type="button" variant="ghost" size="icon" className="h-8 w-8" onClick={() => del(i)} aria-label="Hapus item">
                <Trash2 className="h-4 w-4 text-destructive" />
              </Button>
            </div>
          );
        })}
        <Button type="button" variant="outline" size="sm" onClick={add} className="gap-1" data-testid={`cms-rep-add-${field.name}`}>
          <Plus className="h-3.5 w-3.5" /> Tambah Item
        </Button>
      </div>
    );
  }
  return (
    <div className="space-y-3">
      {arr.map((row, i) => {
        const h = handlers(i);
        const isDragging = dragIdx === i;
        return (
          <div
            key={i}
            className={`rounded-lg border border-border/70 p-3 bg-muted/30 transition-all ${isDragging ? 'opacity-40 border-dashed' : ''} ${h['data-drop-target'] ? 'ring-2 ring-primary/40 border-primary/50' : ''}`}
            onDragOver={h.onDragOver}
            onDrop={h.onDrop}
            onDragLeave={h.onDragLeave}
            onDragEnd={h.onDragEnd}
          >
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  draggable={h.draggable}
                  onDragStart={h.onDragStart}
                  onDragEnd={h.onDragEnd}
                  className="cursor-grab active:cursor-grabbing p-1 text-muted-foreground hover:text-foreground"
                  aria-label="Geser untuk atur ulang"
                  data-testid={`cms-rep-drag-${field.name}-${i}`}
                >
                  <GripVertical className="h-4 w-4" />
                </button>
                <span className="text-xs font-medium text-muted-foreground">Item #{i + 1}</span>
              </div>
              <Button type="button" variant="ghost" size="icon" onClick={() => del(i)} aria-label="Hapus item">
                <Trash2 className="h-4 w-4 text-destructive" />
              </Button>
            </div>
            <div className="grid sm:grid-cols-2 gap-3">
              {field.item.map((sf) => (
                <div key={sf.name} className={sf.type === 'textarea' || sf.type === 'image' || sf.type === 'gallery' ? 'sm:col-span-2' : ''}>
                  <Label className="text-xs mb-1 block">{sf.label}</Label>
                  <Scalar field={sf} value={row?.[sf.name]} onChange={(v) => updRow(i, sf.name, v)} />
                </div>
              ))}
            </div>
          </div>
        );
      })}
      <Button type="button" variant="outline" size="sm" onClick={add} className="gap-1" data-testid={`cms-rep-add-${field.name}`}>
        <Plus className="h-3.5 w-3.5" /> Tambah Item
      </Button>
    </div>
  );
};

// ============================== ROOT ==============================
export const ContentForm = ({ fields, value, onChange }) => {
  const setField = (name, v) => onChange({ ...value, [name]: v });
  return (
    <div className="space-y-5" data-testid="admin-cms-form">
      {(fields || []).map((f) => (
        <div key={f.name}>
          <Label className="mb-1.5 block text-sm font-medium">{f.label}</Label>
          {f.type === 'list' ? (
            <ListField field={f} value={value?.[f.name]} onChange={(v) => setField(f.name, v)} />
          ) : f.type === 'repeater' ? (
            <RepeaterField field={f} value={value?.[f.name]} onChange={(v) => setField(f.name, v)} />
          ) : f.type === 'gallery' ? (
            <GalleryField field={f} value={value?.[f.name]} onChange={(v) => setField(f.name, v)} />
          ) : (
            <Scalar field={f} value={value?.[f.name]} onChange={(v) => setField(f.name, v)} />
          )}
        </div>
      ))}
    </div>
  );
};
