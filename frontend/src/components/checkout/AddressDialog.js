import React from 'react';
import { X, Check } from 'lucide-react';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Textarea } from '../ui/textarea';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '../ui/dialog';

// Dialog alamat pengiriman (checkout). Validasi minimal: nama/telepon/jalan/kota/provinsi.
export default function AddressDialog({ open, onOpenChange, address, onSave }) {
  const [form, setForm] = React.useState(address);
  React.useEffect(() => setForm(address), [address, open]);
  const set = (k, v) => setForm((f) => ({ ...f, [k]: v }));
  const valid = form.name && form.phone && form.street && form.city && form.province;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="cp-store max-w-lg bg-[color:var(--cp-paper-warm)]">
        <DialogHeader>
          <DialogTitle className="cp-mono uppercase text-[11px] tracking-[0.22em]">Alamat Pengiriman</DialogTitle>
          <DialogDescription className="text-xs text-black/60">
            Lengkapi nama penerima, nomor telepon, dan alamat lengkap untuk pengiriman pesanan.
          </DialogDescription>
        </DialogHeader>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div className="col-span-2 sm:col-span-1">
            <div className="cp-mono uppercase text-[10px] tracking-[0.22em] text-black/60 mb-1">Nama Penerima</div>
            <Input value={form.name} onChange={(e) => set('name', e.target.value)} data-testid="address-input-name" className="bg-white" />
          </div>
          <div className="col-span-2 sm:col-span-1">
            <div className="cp-mono uppercase text-[10px] tracking-[0.22em] text-black/60 mb-1">No. HP</div>
            <Input value={form.phone} onChange={(e) => set('phone', e.target.value)} data-testid="address-input-phone" className="bg-white" />
          </div>
          <div className="col-span-2">
            <div className="cp-mono uppercase text-[10px] tracking-[0.22em] text-black/60 mb-1">Alamat Lengkap</div>
            <Textarea value={form.street} onChange={(e) => set('street', e.target.value)} data-testid="address-input-street" className="bg-white" />
          </div>
          <div>
            <div className="cp-mono uppercase text-[10px] tracking-[0.22em] text-black/60 mb-1">Kecamatan</div>
            <Input value={form.district} onChange={(e) => set('district', e.target.value)} data-testid="address-input-district" className="bg-white" />
          </div>
          <div>
            <div className="cp-mono uppercase text-[10px] tracking-[0.22em] text-black/60 mb-1">Kota</div>
            <Input value={form.city} onChange={(e) => set('city', e.target.value)} data-testid="address-input-city" className="bg-white" />
          </div>
          <div>
            <div className="cp-mono uppercase text-[10px] tracking-[0.22em] text-black/60 mb-1">Provinsi</div>
            <Input value={form.province} onChange={(e) => set('province', e.target.value)} data-testid="address-input-province" className="bg-white" />
          </div>
          <div>
            <div className="cp-mono uppercase text-[10px] tracking-[0.22em] text-black/60 mb-1">Kode Pos</div>
            <Input value={form.postal} onChange={(e) => set('postal', e.target.value)} data-testid="address-input-postal" className="bg-white" />
          </div>
          <div>
            <div className="cp-mono uppercase text-[10px] tracking-[0.22em] text-black/60 mb-1">Label (Rumah/Kantor)</div>
            <Input value={form.label} onChange={(e) => set('label', e.target.value)} data-testid="address-input-label" className="bg-white" />
          </div>
        </div>
        <div className="flex items-center justify-end gap-2 mt-4">
          <Button variant="outline" onClick={() => onOpenChange(false)} className="rounded-full">
            <X className="h-4 w-4 mr-1" /> Batal
          </Button>
          <Button onClick={() => { onSave(form); onOpenChange(false); }} disabled={!valid}
            className="rounded-full cp-btn-gold disabled:opacity-60" data-testid="address-save-button">
            <Check className="h-4 w-4 mr-1" /> Simpan
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
