// pages/admin/AdminVouchersPage.js — CRUD voucher (BR-4). used_count read-only.
import React, { useEffect, useState, useCallback } from 'react';
import { toast } from 'sonner';
import { Plus, Pencil, Trash2 } from 'lucide-react';
import { listVouchers, createVoucher, updateVoucher, deleteVoucher } from '../../services/admin';
import { formatIDR } from '../../lib/format';
import { PageHeader, TableSkeleton, EmptyState } from '../../components/admin/adminUi';
import { adminTestIds as T } from '../../constants/testIds/admin';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Label } from '../../components/ui/label';
import { Switch } from '../../components/ui/switch';
import { Badge } from '../../components/ui/badge';
import { Card, CardContent } from '../../components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../../components/ui/table';
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from '../../components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '../../components/ui/dialog';

const BLANK = { code: '', type: 'percent', value: 10, label: '', min_spend: 0, usage_limit: 0, per_user_limit: 0, active: true };
const typeLabel = { percent: 'Persen', flat: 'Potongan', free_shipping: 'Gratis Ongkir' };

export default function AdminVouchersPage() {
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(true);
  const [open, setOpen] = useState(false);
  const [editing, setEditing] = useState(null);
  const [form, setForm] = useState(BLANK);
  const [saving, setSaving] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try { setRows(await listVouchers() || []); }
    catch (e) { toast.error('Gagal memuat voucher.'); }
    finally { setLoading(false); }
  }, []);
  useEffect(() => { load(); }, [load]);

  const openNew = () => { setEditing(null); setForm(BLANK); setOpen(true); };
  const openEdit = (v) => {
    setEditing(v);
    setForm({ code: v.code, type: v.type, value: v.value, label: v.label || '', min_spend: v.min_spend || 0, usage_limit: v.usage_limit || 0, per_user_limit: v.per_user_limit || 0, active: v.active !== false });
    setOpen(true);
  };

  const save = async () => {
    if (!form.code.trim()) { toast.error('Kode voucher wajib.'); return; }
    const payload = {
      code: form.code, type: form.type, value: Number(form.value) || 0, label: form.label,
      min_spend: Number(form.min_spend) || 0, usage_limit: Number(form.usage_limit) || 0,
      per_user_limit: Number(form.per_user_limit) || 0, active: form.active,
    };
    setSaving(true);
    try {
      if (editing) { await updateVoucher(editing.id, payload); toast.success('Voucher diperbarui.'); }
      else { await createVoucher(payload); toast.success('Voucher dibuat.'); }
      setOpen(false); load();
    } catch (e) { toast.error(e?.response?.data?.detail || 'Gagal menyimpan voucher.'); }
    finally { setSaving(false); }
  };
  const remove = async (v) => {
    try { await deleteVoucher(v.id); toast.success('Voucher dihapus.'); load(); }
    catch (e) { toast.error(e?.response?.data?.detail || 'Tidak bisa dihapus.'); }
  };

  return (
    <div>
      <PageHeader title="Voucher" description="Kelola kode promo (persen / potongan / gratis ongkir)."
        actions={<Button onClick={openNew} data-testid={T.voucherAdd} className="gap-2"><Plus className="h-4 w-4" /> Tambah Voucher</Button>} />
      <Card className="border-border/70"><CardContent className="p-4">
        {loading ? <TableSkeleton rows={5} cols={5} /> : (
          rows.length === 0 ? <EmptyState title="Belum ada voucher" /> : (
            <div className="overflow-x-auto">
              <Table data-testid={T.vouchersTable}>
                <TableHeader><TableRow>
                  <TableHead>Kode</TableHead><TableHead>Tipe</TableHead><TableHead>Nilai</TableHead>
                  <TableHead>Min. Belanja</TableHead><TableHead>Dipakai</TableHead><TableHead>Status</TableHead><TableHead className="w-24" />
                </TableRow></TableHeader>
                <TableBody>
                  {rows.map((v) => (
                    <TableRow key={v.id}>
                      <TableCell className="font-[\'Azeret_Mono\',monospace] font-semibold">{v.code}</TableCell>
                      <TableCell className="text-sm">{typeLabel[v.type] || v.type}</TableCell>
                      <TableCell className="text-sm">{v.type === 'percent' ? `${v.value}%` : v.type === 'flat' ? formatIDR(v.value) : '—'}</TableCell>
                      <TableCell className="text-sm">{formatIDR(v.min_spend || 0)}</TableCell>
                      <TableCell className="text-sm font-[\'Azeret_Mono\',monospace]">{v.used_count || 0}{v.usage_limit ? `/${v.usage_limit}` : ''}</TableCell>
                      <TableCell><Badge variant="outline" className={v.active !== false ? 'bg-emerald-100 text-emerald-800 border-emerald-200' : 'bg-zinc-100 text-zinc-600 border-zinc-200'}>{v.active !== false ? 'Aktif' : 'Nonaktif'}</Badge></TableCell>
                      <TableCell className="text-right">
                        <Button variant="ghost" size="icon" onClick={() => openEdit(v)} aria-label="Edit"><Pencil className="h-4 w-4" /></Button>
                        <Button variant="ghost" size="icon" onClick={() => remove(v)} aria-label="Hapus"><Trash2 className="h-4 w-4 text-rose-600" /></Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )
        )}
      </CardContent></Card>

      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{editing ? 'Edit Voucher' : 'Tambah Voucher'}</DialogTitle>
            <DialogDescription>
              Atur kode, jenis diskon, nilai, periode berlaku, dan batas pemakaian voucher.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1.5"><Label>Kode</Label><Input value={form.code} onChange={(e) => setForm({ ...form, code: e.target.value.toUpperCase() })} data-testid="admin-voucher-code" /></div>
              <div className="space-y-1.5"><Label>Tipe</Label>
                <Select value={form.type} onValueChange={(v) => setForm({ ...form, type: v })}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="percent">Persen (%)</SelectItem>
                    <SelectItem value="flat">Potongan (Rp)</SelectItem>
                    <SelectItem value="free_shipping">Gratis Ongkir</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1.5"><Label>Nilai {form.type === 'percent' ? '(1-100)' : ''}</Label><Input type="number" value={form.value} onChange={(e) => setForm({ ...form, value: e.target.value })} disabled={form.type === 'free_shipping'} /></div>
              <div className="space-y-1.5"><Label>Min. Belanja</Label><Input type="number" value={form.min_spend} onChange={(e) => setForm({ ...form, min_spend: e.target.value })} /></div>
            </div>
            <div className="space-y-1.5"><Label>Label</Label><Input value={form.label} onChange={(e) => setForm({ ...form, label: e.target.value })} /></div>
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1.5"><Label>Batas Pakai (0=∞)</Label><Input type="number" value={form.usage_limit} onChange={(e) => setForm({ ...form, usage_limit: e.target.value })} /></div>
              <div className="space-y-1.5"><Label>Batas/Pengguna (0=∞)</Label><Input type="number" value={form.per_user_limit} onChange={(e) => setForm({ ...form, per_user_limit: e.target.value })} /></div>
            </div>
            <label className="flex items-center gap-2 text-sm"><Switch checked={form.active} onCheckedChange={(v) => setForm({ ...form, active: v })} /> Aktif</label>
          </div>
          <DialogFooter>
            <Button variant="secondary" onClick={() => setOpen(false)}>Batal</Button>
            <Button onClick={save} disabled={saving} data-testid="admin-voucher-save">{saving ? 'Menyimpan…' : 'Simpan'}</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
