// components/admin/ContentForm.js — form generik berbasis skema (Epic E9 CMS).
// Merender field: text, textarea, image (Media Manager picker + upload + URL + preview),
// list (drag-and-drop reorder + string), repeater (drag-and-drop reorder + sub-field).
// Controlled: onChange(nextValue) mengembalikan objek penuh.
import React, { useState } from 'react';
import { Plus, Trash2, GripVertical } from 'lucide-react';
import { Input } from '../ui/input';
import { Textarea } from '../ui/textarea';
import { Button } from '../ui/button';
import { Label } from '../ui/label';
import { MediaField } from './media/MediaField';

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

// ============================== SCALAR FIELD ==============================
const Scalar = ({ field, value, onChange }) => {
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
  const add = () => onChange([...arr, Object.fromEntries(field.item.map((f) => [f.name, '']))]);
  const { handlers, dragIdx } = useDnd((from, to) => onChange(reorderArr(arr, from, to)));
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
                <div key={sf.name} className={sf.type === 'textarea' || sf.type === 'image' ? 'sm:col-span-2' : ''}>
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
          ) : (
            <Scalar field={f} value={value?.[f.name]} onChange={(v) => setField(f.name, v)} />
          )}
        </div>
      ))}
    </div>
  );
};
