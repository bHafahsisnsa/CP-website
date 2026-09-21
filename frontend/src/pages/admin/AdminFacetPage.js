// pages/admin/AdminFacetPage.js — CRUD generik taksonomi facet MULTI (Occasions & Characters).
// Mirror pola AdminCategoriesPage + field khusus facet: `icon` (lucide key) & `order`.
// FK-safe: backend memblok hapus bila slug masih dipakai produk (400) -> toast error.
import React, { useEffect, useState, useCallback } from 'react';
import { toast } from 'sonner';
import { Plus, Pencil, Trash2 } from 'lucide-react';
import { PageHeader, TableSkeleton, EmptyState } from '../../components/admin/adminUi';
import { getFacetIcon, FACET_ICON_KEYS } from '../../lib/taxonomyIcons';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Label } from '../../components/ui/label';
import { Textarea } from '../../components/ui/textarea';
import { Switch } from '../../components/ui/switch';
import { Badge } from '../../components/ui/badge';
import { Card, CardContent } from '../../components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../../components/ui/table';
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from '../../components/ui/select';
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter,
} from '../../components/ui/dialog';

const BLANK = { name: '', slug: '', icon: 'sparkles', desc: '', order: 0, active: true };

/**
 * Generic facet CRUD page.
 * @param {string} title - Judul halaman.
 * @param {string} description - Deskripsi ringkas.
 * @param {string} entityLabel - Label entitas (mis. "Occasion" / "Karakter").
 * @param {{list:Function,create:Function,update:Function,remove:Function}} service - Fungsi API.
 * @param {{add:string,table:string,nameInput:string,iconSelect:string,saveBtn:string}} testIds
 */
export default function AdminFacetPage({ title, description, entityLabel, service, testIds }) {
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(true);
  const [open, setOpen] = useState(false);
  const [editing, setEditing] = useState(null);
  const [form, setForm] = useState(BLANK);
  const [saving, setSaving] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try { setRows(await service.list() || []); }
    catch (e) { toast.error(`Gagal memuat ${entityLabel}.`); }
    finally { setLoading(false); }
  }, [service, entityLabel]);
  useEffect(() => { load(); }, [load]);

  const openNew = () => { setEditing(null); setForm(BLANK); setOpen(true); };
  const openEdit = (c) => {
    setEditing(c);
    setForm({
      name: c.name, slug: c.slug, icon: c.icon || 'sparkles',
      desc: c.desc || '', order: c.order ?? 0, active: c.active !== false,
    });
    setOpen(true);
  };

  const save = async () => {
    if (!form.name.trim()) { toast.error('Nama wajib diisi.'); return; }
    setSaving(true);
    const body = { ...form, name: form.name.trim(), order: Number(form.order) || 0 };
    try {
      if (editing) { await service.update(editing.id, body); toast.success(`${entityLabel} diperbarui.`); }
      else { await service.create(body); toast.success(`${entityLabel} dibuat.`); }
      setOpen(false); load();
    } catch (e) { toast.error(e?.response?.data?.detail || 'Gagal menyimpan.'); }
    finally { setSaving(false); }
  };
  const remove = async (c) => {
    try { await service.remove(c.id); toast.success(`${entityLabel} dihapus.`); load(); }
    catch (e) { toast.error(e?.response?.data?.detail || 'Tidak bisa dihapus (mungkin dipakai produk).'); }
  };

  const PreviewIcon = getFacetIcon(form.icon);

  return (
    <div>
      <PageHeader title={title} description={description}
        actions={<Button onClick={openNew} data-testid={testIds.add} className="gap-2"><Plus className="h-4 w-4" /> Tambah {entityLabel}</Button>} />
      <Card className="border-border/70"><CardContent className="p-4">
        {loading ? <TableSkeleton rows={6} cols={5} /> : (
          rows.length === 0 ? <EmptyState title={`Belum ada ${entityLabel}`} /> : (
            <Table data-testid={testIds.table}>
              <TableHeader><TableRow>
                <TableHead className="w-16">Ikon</TableHead>
                <TableHead>Nama</TableHead>
                <TableHead>Slug</TableHead>
                <TableHead className="w-20">Urutan</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="w-24" />
              </TableRow></TableHeader>
              <TableBody>
                {rows.map((c) => {
                  const Icon = getFacetIcon(c.icon);
                  return (
                    <TableRow key={c.id}>
                      <TableCell>
                        <span className="h-9 w-9 rounded-full grid place-items-center bg-[color:var(--cp-brass)]/15 text-[color:var(--cp-brass)]">
                          <Icon className="h-4 w-4" strokeWidth={1.7} />
                        </span>
                      </TableCell>
                      <TableCell className="font-medium capitalize">{c.name}</TableCell>
                      <TableCell className="text-xs text-muted-foreground">{c.slug}</TableCell>
                      <TableCell className="text-sm">{c.order ?? 0}</TableCell>
                      <TableCell>
                        <Badge variant="outline" className={c.active !== false ? 'bg-emerald-100 text-emerald-800 border-emerald-200' : 'bg-zinc-100 text-zinc-600 border-zinc-200'}>
                          {c.active !== false ? 'Aktif' : 'Nonaktif'}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-right">
                        <Button variant="ghost" size="icon" onClick={() => openEdit(c)} aria-label="Edit"><Pencil className="h-4 w-4" /></Button>
                        <Button variant="ghost" size="icon" onClick={() => remove(c)} aria-label="Hapus"><Trash2 className="h-4 w-4 text-rose-600" /></Button>
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          )
        )}
      </CardContent></Card>

      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{editing ? `Edit ${entityLabel}` : `Tambah ${entityLabel}`}</DialogTitle>
            <DialogDescription>
              Atur nama, slug, ikon, dan urutan tampil {entityLabel.toLowerCase()} pada storefront.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-1.5"><Label>Nama</Label><Input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} data-testid={testIds.nameInput} /></div>
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1.5"><Label>Slug (opsional)</Label><Input value={form.slug} onChange={(e) => setForm({ ...form, slug: e.target.value })} placeholder="otomatis dari nama" /></div>
              <div className="space-y-1.5"><Label>Urutan</Label><Input type="number" value={form.order} onChange={(e) => setForm({ ...form, order: e.target.value })} /></div>
            </div>
            <div className="space-y-1.5">
              <Label>Ikon</Label>
              <div className="flex items-center gap-3">
                <span className="h-10 w-10 shrink-0 rounded-full grid place-items-center bg-[color:var(--cp-brass)]/15 text-[color:var(--cp-brass)]">
                  <PreviewIcon className="h-5 w-5" strokeWidth={1.6} />
                </span>
                <Select value={form.icon} onValueChange={(v) => setForm({ ...form, icon: v })}>
                  <SelectTrigger data-testid={testIds.iconSelect}><SelectValue placeholder="Pilih ikon" /></SelectTrigger>
                  <SelectContent className="max-h-64">
                    {FACET_ICON_KEYS.map((k) => {
                      const KIcon = getFacetIcon(k);
                      return (
                        <SelectItem key={k} value={k}>
                          <span className="flex items-center gap-2"><KIcon className="h-4 w-4" /> {k}</span>
                        </SelectItem>
                      );
                    })}
                  </SelectContent>
                </Select>
              </div>
            </div>
            <div className="space-y-1.5"><Label>Deskripsi</Label><Textarea rows={3} value={form.desc} onChange={(e) => setForm({ ...form, desc: e.target.value })} /></div>
            <label className="flex items-center gap-2 text-sm"><Switch checked={form.active} onCheckedChange={(v) => setForm({ ...form, active: v })} /> Aktif</label>
          </div>
          <DialogFooter>
            <Button variant="secondary" onClick={() => setOpen(false)}>Batal</Button>
            <Button onClick={save} disabled={saving} data-testid={testIds.saveBtn}>{saving ? 'Menyimpan…' : 'Simpan'}</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
