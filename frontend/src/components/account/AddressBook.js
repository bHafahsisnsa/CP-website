import React from 'react';
import { Loader2, Plus, MapPin, Star, Pencil, Trash2, Check, X } from 'lucide-react';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Textarea } from '../ui/textarea';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '../ui/dialog';
import {
  AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent,
  AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle,
} from '../ui/alert-dialog';
import { listAddresses, createAddress, updateAddress, deleteAddress, setDefaultAddress } from '../../services/account';
import { toast } from 'sonner';

const BLANK = { name: '', phone: '', street: '', district: '', city: '', province: '', postal: '', label: 'Rumah', is_default: false };

export default function AddressBook() {
  const [addresses, setAddresses] = React.useState([]);
  const [loading, setLoading] = React.useState(true);
  const [dialogOpen, setDialogOpen] = React.useState(false);
  const [editing, setEditing] = React.useState(null);
  const [form, setForm] = React.useState(BLANK);
  const [saving, setSaving] = React.useState(false);
  const [toDelete, setToDelete] = React.useState(null);

  const load = React.useCallback(async () => {
    setLoading(true);
    try { setAddresses(await listAddresses()); }
    catch (e) { toast.error('Gagal memuat alamat'); }
    finally { setLoading(false); }
  }, []);

  React.useEffect(() => { load(); }, [load]);

  const openAdd = () => { setEditing(null); setForm(BLANK); setDialogOpen(true); };
  const openEdit = (a) => { setEditing(a); setForm({ ...BLANK, ...a }); setDialogOpen(true); };
  const set = (k, v) => setForm((f) => ({ ...f, [k]: v }));
  const valid = form.name && form.phone && form.street && form.city && form.province;

  const save = async () => {
    if (!valid) { toast.error('Lengkapi nama, telepon, alamat, kota, provinsi'); return; }
    setSaving(true);
    try {
      if (editing) await updateAddress(editing.id, form);
      else await createAddress(form);
      toast.success(editing ? 'Alamat diperbarui' : 'Alamat ditambahkan');
      setDialogOpen(false);
      await load();
    } catch (e) {
      toast.error(e?.response?.data?.detail || 'Gagal menyimpan alamat');
    } finally { setSaving(false); }
  };

  const makeDefault = async (id) => {
    try { setAddresses(await setDefaultAddress(id)); toast.success('Alamat utama diperbarui'); }
    catch (e) { toast.error('Gagal mengatur alamat utama'); }
  };

  const confirmDelete = async () => {
    const id = toDelete?.id;
    setToDelete(null);
    try { await deleteAddress(id); toast.success('Alamat dihapus'); await load(); }
    catch (e) { toast.error(e?.response?.data?.detail || 'Gagal menghapus alamat'); }
  };

  return (
    <div className="rounded-2xl border border-black/10 bg-[color:var(--cp-paper-warm)] p-6" data-testid="account-address-book">
      <div className="flex items-center justify-between mb-4">
        <div className="cp-mono uppercase text-[11px] tracking-[0.22em]">Buku Alamat</div>
        <Button onClick={openAdd} className="rounded-full h-9 cp-btn-gold" data-testid="address-add-button">
          <Plus className="h-4 w-4 mr-1" /> Tambah
        </Button>
      </div>

      {loading ? (
        <div className="py-10 flex items-center justify-center text-black/50"><Loader2 className="h-5 w-5 animate-spin mr-2" /> Memuat alamat…</div>
      ) : addresses.length === 0 ? (
        <div className="py-10 text-center text-sm text-black/60" data-testid="address-empty">Belum ada alamat tersimpan. Tambahkan alamat pengiriman Anda.</div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {addresses.map((a) => (
            <div key={a.id} className={`rounded-2xl border p-4 ${a.is_default ? 'border-[color:var(--cp-market-blue)] bg-[color:var(--cp-market-blue-soft)]/40' : 'border-black/10 bg-white'}`} data-testid="address-card">
              <div className="flex items-center gap-2">
                <MapPin className="h-4 w-4 text-black/50" />
                <span className="font-semibold text-sm">{a.name}</span>
                <span className="cp-mono uppercase text-[10px] tracking-[0.2em] bg-[color:var(--cp-paper-fog)] px-2 py-0.5 rounded-full">{a.label}</span>
                {a.is_default && <span className="ml-auto inline-flex items-center gap-1 cp-mono uppercase text-[10px] tracking-[0.2em] text-[color:var(--cp-market-blue)]"><Star className="h-3 w-3 fill-current" /> Utama</span>}
              </div>
              <div className="text-xs text-black/70 mt-2 leading-relaxed">{a.phone} · {a.street}{a.district ? `, ${a.district}` : ''}, {a.city}, {a.province} {a.postal}</div>
              <div className="flex items-center gap-3 mt-3">
                {!a.is_default && (
                  <button onClick={() => makeDefault(a.id)} className="cp-mono uppercase text-[10px] tracking-[0.2em] text-[color:var(--cp-market-blue)] hover:underline" data-testid="address-set-default">Jadikan Utama</button>
                )}
                <button onClick={() => openEdit(a)} className="ml-auto inline-flex items-center gap-1 text-black/60 hover:text-black text-xs" data-testid="address-edit-button"><Pencil className="h-3.5 w-3.5" /> Ubah</button>
                <button onClick={() => setToDelete(a)} className="inline-flex items-center gap-1 text-red-600 hover:underline text-xs" data-testid="address-delete-button"><Trash2 className="h-3.5 w-3.5" /> Hapus</button>
              </div>
            </div>
          ))}
        </div>
      )}

      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="max-w-lg bg-[color:var(--cp-paper-warm)]">
          <DialogHeader>
            <DialogTitle className="cp-mono uppercase text-[11px] tracking-[0.22em]">{editing ? 'Ubah Alamat' : 'Tambah Alamat'}</DialogTitle>
            <DialogDescription className="text-xs text-black/60">
              Simpan alamat pengiriman agar checkout berikutnya lebih cepat.
            </DialogDescription>
          </DialogHeader>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <Input placeholder="Nama penerima" value={form.name} onChange={(e) => set('name', e.target.value)} className="bg-white" data-testid="address-input-name" />
            <Input placeholder="No. HP" value={form.phone} onChange={(e) => set('phone', e.target.value)} className="bg-white" data-testid="address-input-phone" />
            <Textarea placeholder="Alamat lengkap" value={form.street} onChange={(e) => set('street', e.target.value)} className="bg-white sm:col-span-2" data-testid="address-input-street" />
            <Input placeholder="Kecamatan" value={form.district} onChange={(e) => set('district', e.target.value)} className="bg-white" data-testid="address-input-district" />
            <Input placeholder="Kota" value={form.city} onChange={(e) => set('city', e.target.value)} className="bg-white" data-testid="address-input-city" />
            <Input placeholder="Provinsi" value={form.province} onChange={(e) => set('province', e.target.value)} className="bg-white" data-testid="address-input-province" />
            <Input placeholder="Kode pos" value={form.postal} onChange={(e) => set('postal', e.target.value)} className="bg-white" data-testid="address-input-postal" />
            <Input placeholder="Label (Rumah/Kantor)" value={form.label} onChange={(e) => set('label', e.target.value)} className="bg-white" data-testid="address-input-label" />
            <label className="sm:col-span-2 flex items-center gap-2 text-sm text-black/70 cursor-pointer">
              <input type="checkbox" checked={!!form.is_default} onChange={(e) => set('is_default', e.target.checked)} data-testid="address-input-default" /> Jadikan alamat utama
            </label>
          </div>
          <div className="flex items-center justify-end gap-2 mt-4">
            <Button variant="outline" onClick={() => setDialogOpen(false)} className="rounded-full"><X className="h-4 w-4 mr-1" /> Batal</Button>
            <Button onClick={save} disabled={saving || !valid} className="rounded-full cp-btn-gold disabled:opacity-60" data-testid="address-save-button">
              {saving ? <Loader2 className="h-4 w-4 mr-1 animate-spin" /> : <Check className="h-4 w-4 mr-1" />} Simpan
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      <AlertDialog open={!!toDelete} onOpenChange={(o) => !o && setToDelete(null)}>
        <AlertDialogContent className="bg-[color:var(--cp-paper-warm)]">
          <AlertDialogHeader>
            <AlertDialogTitle>Hapus alamat ini?</AlertDialogTitle>
            <AlertDialogDescription>Alamat “{toDelete?.name}” akan dihapus permanen dari buku alamat Anda.</AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Batal</AlertDialogCancel>
            <AlertDialogAction onClick={confirmDelete} className="bg-red-600 hover:bg-red-700" data-testid="address-delete-confirm">Hapus</AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
