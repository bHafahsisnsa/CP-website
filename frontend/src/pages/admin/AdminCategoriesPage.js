// pages/admin/AdminCategoriesPage.js — CRUD kategori (BR-3).
import React, { useEffect, useState, useCallback } from 'react';
import { toast } from 'sonner';
import { Plus, Pencil, Trash2 } from 'lucide-react';
import { listCategories, createCategory, updateCategory, deleteCategory } from '../../services/admin';
import { PageHeader, TableSkeleton, EmptyState } from '../../components/admin/adminUi';
import { MediaField } from '../../components/admin/media/MediaField';
import { adminTestIds as T } from '../../constants/testIds/admin';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Label } from '../../components/ui/label';
import { Textarea } from '../../components/ui/textarea';
import { Switch } from '../../components/ui/switch';
import { Badge } from '../../components/ui/badge';
import { Card, CardContent } from '../../components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../../components/ui/table';
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter, DialogTrigger,
} from '../../components/ui/dialog';

const BLANK = { name: '', slug: '', desc: '', image: '', active: true };

export default function AdminCategoriesPage() {
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(true);
  const [open, setOpen] = useState(false);
  const [editing, setEditing] = useState(null);
  const [form, setForm] = useState(BLANK);
  const [saving, setSaving] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try { setRows(await listCategories() || []); }
    catch (e) { toast.error('Gagal memuat kategori.'); }
    finally { setLoading(false); }
  }, []);
  useEffect(() => { load(); }, [load]);

  const openNew = () => { setEditing(null); setForm(BLANK); setOpen(true); };
  const openEdit = (c) => { setEditing(c); setForm({ name: c.name, slug: c.slug, desc: c.desc || '', image: c.image || '', active: c.active !== false }); setOpen(true); };

  const save = async () => {
    if (!form.name.trim()) { toast.error('Nama kategori wajib.'); return; }
    setSaving(true);
    try {
      if (editing) { await updateCategory(editing.id, form); toast.success('Kategori diperbarui.'); }
      else { await createCategory(form); toast.success('Kategori dibuat.'); }
      setOpen(false); load();
    } catch (e) { toast.error(e?.response?.data?.detail || 'Gagal menyimpan.'); }
    finally { setSaving(false); }
  };
  const remove = async (c) => {
    try { await deleteCategory(c.id); toast.success('Kategori dihapus.'); load(); }
    catch (e) { toast.error(e?.response?.data?.detail || 'Tidak bisa dihapus.'); }
  };

  return (
    <div>
      <PageHeader title="Kategori" description="Keluarga aroma / koleksi produk."
        actions={<Button onClick={openNew} data-testid={T.categoryAdd} className="gap-2"><Plus className="h-4 w-4" /> Tambah Kategori</Button>} />
      <Card className="border-border/70"><CardContent className="p-4">
        {loading ? <TableSkeleton rows={5} cols={3} /> : (
          rows.length === 0 ? <EmptyState title="Belum ada kategori" /> : (
            <Table data-testid={T.categoriesTable}>
              <TableHeader><TableRow>
                <TableHead>Nama</TableHead><TableHead>Slug</TableHead><TableHead>Status</TableHead><TableHead className="w-24" />
              </TableRow></TableHeader>
              <TableBody>
                {rows.map((c) => (
                  <TableRow key={c.id}>
                    <TableCell className="font-medium capitalize">{c.name}</TableCell>
                    <TableCell className="font-[\'Azeret_Mono\',monospace] text-xs text-muted-foreground">{c.slug}</TableCell>
                    <TableCell><Badge variant="outline" className={c.active !== false ? 'bg-emerald-100 text-emerald-800 border-emerald-200' : 'bg-zinc-100 text-zinc-600 border-zinc-200'}>{c.active !== false ? 'Aktif' : 'Nonaktif'}</Badge></TableCell>
                    <TableCell className="text-right">
                      <Button variant="ghost" size="icon" onClick={() => openEdit(c)} aria-label="Edit"><Pencil className="h-4 w-4" /></Button>
                      <Button variant="ghost" size="icon" onClick={() => remove(c)} aria-label="Hapus"><Trash2 className="h-4 w-4 text-rose-600" /></Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )
        )}
      </CardContent></Card>

      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{editing ? 'Edit Kategori' : 'Tambah Kategori'}</DialogTitle>
            <DialogDescription>
              Atur nama, slug, dan deskripsi kategori aroma yang dipakai untuk filter katalog.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-1.5"><Label>Nama</Label><Input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} data-testid="admin-category-name" /></div>
            <div className="space-y-1.5"><Label>Slug (opsional)</Label><Input value={form.slug} onChange={(e) => setForm({ ...form, slug: e.target.value })} placeholder="otomatis dari nama" /></div>
            <div className="space-y-1.5"><Label>Deskripsi</Label><Textarea rows={3} value={form.desc} onChange={(e) => setForm({ ...form, desc: e.target.value })} /></div>
            <MediaField
              label="Gambar kategori"
              value={form.image}
              onChange={(url) => setForm({ ...form, image: url })}
              hint="Dipakai sebagai visual kategori di storefront. Pilih dari Media Manager atau unggah langsung."
              testId="admin-category-image-field"
            />
            <label className="flex items-center gap-2 text-sm"><Switch checked={form.active} onCheckedChange={(v) => setForm({ ...form, active: v })} /> Aktif</label>
          </div>
          <DialogFooter>
            <Button variant="secondary" onClick={() => setOpen(false)}>Batal</Button>
            <Button onClick={save} disabled={saving} data-testid="admin-category-save">{saving ? 'Menyimpan…' : 'Simpan'}</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
