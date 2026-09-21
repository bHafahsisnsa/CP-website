// pages/admin/AdminSettingsPage.js — konfigurasi toko: kurir, pembayaran, settings, media, users (BR-7/8/10).
import React, { useEffect, useState, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { toast } from 'sonner';
import { Plus, Pencil, Trash2, Save, Images } from 'lucide-react';
import {
  getSettings, updateSettings, listShipping, createShipping, updateShipping, deleteShipping,
  listPayments, createPayment, updatePayment, deletePayment, listUsers,
} from '../../services/admin';
import { formatIDR } from '../../lib/format';
import { PageHeader, EmptyState, formatDateTime } from '../../components/admin/adminUi';
import { MediaField } from '../../components/admin/media/MediaField';
import { SmartImage } from '../../components/shared/SmartImage';
import { adminTestIds as T } from '../../constants/testIds/admin';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Label } from '../../components/ui/label';
import { Switch } from '../../components/ui/switch';
import { Badge } from '../../components/ui/badge';
import { Card, CardContent } from '../../components/ui/card';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '../../components/ui/tabs';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../../components/ui/table';
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from '../../components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '../../components/ui/dialog';

const Fld = ({ label, children }) => (
  <div className="space-y-1.5"><Label className="text-xs text-muted-foreground">{label}</Label>{children}</div>
);

// ---------- Tab: Pengaturan Toko ----------
const StoreTab = () => {
  const [s, setS] = useState(null);
  const [saving, setSaving] = useState(false);
  useEffect(() => { getSettings().then(setS).catch(() => toast.error('Gagal memuat settings.')); }, []);
  if (!s) return <div className="py-8 text-sm text-muted-foreground">Memuat…</div>;
  const set = (p) => setS({ ...s, ...p });
  const save = async () => {
    setSaving(true);
    try {
      await updateSettings({
        store_name: s.store_name, currency: s.currency, support_email: s.support_email,
        support_phone: s.support_phone, cod_fee: Number(s.cod_fee) || 0,
        free_shipping_threshold: Number(s.free_shipping_threshold) || 0,
        low_stock_threshold: Number(s.low_stock_threshold) || 0,
        inspired_by_enabled: s.inspired_by_enabled !== false,
        inspired_by_label: (s.inspired_by_label || 'Inspired by').trim() || 'Inspired by',
        house_brands: String(s.house_brands_text ?? (s.house_brands || []).join(', '))
          .split(',').map((x) => x.trim()).filter(Boolean),
      });
      toast.success('Pengaturan disimpan.');
    } catch (e) { toast.error('Gagal menyimpan.'); } finally { setSaving(false); }
  };
  const inspiredOn = s.inspired_by_enabled !== false;
  return (
    <div className="space-y-4 max-w-2xl">
      <div className="grid sm:grid-cols-2 gap-4">
        <Fld label="Nama Toko"><Input value={s.store_name || ''} onChange={(e) => set({ store_name: e.target.value })} /></Fld>
        <Fld label="Mata Uang"><Input value={s.currency || ''} onChange={(e) => set({ currency: e.target.value })} /></Fld>
        <Fld label="Email Dukungan"><Input value={s.support_email || ''} onChange={(e) => set({ support_email: e.target.value })} /></Fld>
        <Fld label="Telepon Dukungan"><Input value={s.support_phone || ''} onChange={(e) => set({ support_phone: e.target.value })} /></Fld>
        <Fld label="Biaya COD (Rp)"><Input type="number" value={s.cod_fee ?? 0} onChange={(e) => set({ cod_fee: e.target.value })} /></Fld>
        <Fld label="Ambang Gratis Ongkir (0=off)"><Input type="number" value={s.free_shipping_threshold ?? 0} onChange={(e) => set({ free_shipping_threshold: e.target.value })} /></Fld>
        <Fld label="Ambang Stok Menipis"><Input type="number" value={s.low_stock_threshold ?? 5} onChange={(e) => set({ low_stock_threshold: e.target.value })} /></Fld>
      </div>

      {/* Label merek storefront — produk "inspired by" merek luar */}
      <div className="rounded-xl border border-border/70 p-4 space-y-3">
        <div>
          <h4 className="text-sm font-semibold text-foreground">Label Merek Storefront</h4>
          <p className="text-xs text-muted-foreground mt-0.5">
            Katalog memuat produk yang meniru aroma merek luar. Agar jujur ke pembeli,
            merek yang BUKAN merek rumah ditampilkan sebagai
            &quot;<span className="font-medium">{(s.inspired_by_label || 'Inspired by')} Dior</span>&quot;.
            Data terstruktur SEO tetap memakai merek rumah.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Switch
            checked={inspiredOn}
            onCheckedChange={(v) => set({ inspired_by_enabled: v })}
            data-testid={T.settingsInspiredToggle}
            aria-label="Aktifkan label Inspired by"
          />
          <span className="text-sm text-foreground/80">
            {inspiredOn ? 'Aktif — merek luar diberi label' : 'Nonaktif — merek tampil apa adanya'}
          </span>
        </div>
        <div className="grid sm:grid-cols-2 gap-4">
          <Fld label="Teks label">
            <Input
              value={s.inspired_by_label ?? 'Inspired by'} disabled={!inspiredOn}
              onChange={(e) => set({ inspired_by_label: e.target.value })}
              data-testid="admin-settings-inspired-label"
            />
          </Fld>
          <Fld label="Merek rumah (pisahkan dengan koma)">
            <Input
              value={s.house_brands_text ?? (s.house_brands || []).join(', ')}
              onChange={(e) => set({ house_brands_text: e.target.value })}
              placeholder="Collector Parfum, Collector"
              data-testid={T.settingsHouseBrands}
            />
          </Fld>
        </div>
      </div>

      <Button onClick={save} disabled={saving} data-testid={T.settingsSave} className="gap-2"><Save className="h-4 w-4" /> {saving ? 'Menyimpan…' : 'Simpan Pengaturan'}</Button>
    </div>
  );
};

// ---------- Tab: Kurir ----------
const ShippingTab = () => {
  const [rows, setRows] = useState([]);
  const [open, setOpen] = useState(false);
  const [editing, setEditing] = useState(null);
  const [f, setF] = useState({ name: '', eta: '', price: 0, active: true });
  const load = useCallback(() => listShipping().then(setRows).catch(() => toast.error('Gagal memuat kurir.')), []);
  useEffect(() => { load(); }, [load]);
  const openNew = () => { setEditing(null); setF({ name: '', eta: '', price: 0, active: true }); setOpen(true); };
  const openEdit = (r) => { setEditing(r); setF({ name: r.name, eta: r.eta || '', price: r.price || 0, active: r.active !== false }); setOpen(true); };
  const save = async () => {
    if (!f.name.trim()) { toast.error('Nama kurir wajib.'); return; }
    const body = { name: f.name, eta: f.eta, price: Number(f.price) || 0, active: f.active };
    try {
      if (editing) await updateShipping(editing.id, body); else await createShipping(body);
      toast.success('Kurir disimpan.'); setOpen(false); load();
    } catch (e) { toast.error('Gagal menyimpan kurir.'); }
  };
  const remove = async (r) => { try { await deleteShipping(r.id); toast.success('Kurir dihapus.'); load(); } catch (e) { toast.error('Gagal menghapus.'); } };
  return (
    <div>
      <div className="flex justify-end mb-3"><Button onClick={openNew} className="gap-2" data-testid="admin-shipping-add"><Plus className="h-4 w-4" /> Tambah Kurir</Button></div>
      {rows.length === 0 ? <EmptyState title="Belum ada metode kirim" /> : (
        <Table data-testid="admin-shipping-table">
          <TableHeader><TableRow><TableHead>Nama</TableHead><TableHead>Estimasi</TableHead><TableHead className="text-right">Tarif</TableHead><TableHead>Status</TableHead><TableHead className="w-24" /></TableRow></TableHeader>
          <TableBody>
            {rows.map((r) => (
              <TableRow key={r.id}>
                <TableCell className="font-medium">{r.name}</TableCell>
                <TableCell className="text-sm text-muted-foreground">{r.eta || '—'}</TableCell>
                <TableCell className="text-right font-['Azeret_Mono',monospace] text-sm">{formatIDR(r.price || 0)}</TableCell>
                <TableCell><Badge variant="outline" className={r.active !== false ? 'bg-emerald-100 text-emerald-800 border-emerald-200' : 'bg-zinc-100 text-zinc-600 border-zinc-200'}>{r.active !== false ? 'Aktif' : 'Nonaktif'}</Badge></TableCell>
                <TableCell className="text-right">
                  <Button variant="ghost" size="icon" onClick={() => openEdit(r)} aria-label="Edit"><Pencil className="h-4 w-4" /></Button>
                  <Button variant="ghost" size="icon" onClick={() => remove(r)} aria-label="Hapus"><Trash2 className="h-4 w-4 text-rose-600" /></Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      )}
      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{editing ? 'Edit Kurir' : 'Tambah Kurir'}</DialogTitle>
            <DialogDescription>
              Atur nama kurir, tarif pengiriman, dan estimasi waktu tiba.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-3">
            <Fld label="Nama"><Input value={f.name} onChange={(e) => setF({ ...f, name: e.target.value })} /></Fld>
            <Fld label="Estimasi (mis. 2-3 hari)"><Input value={f.eta} onChange={(e) => setF({ ...f, eta: e.target.value })} /></Fld>
            <Fld label="Tarif (Rp)"><Input type="number" value={f.price} onChange={(e) => setF({ ...f, price: e.target.value })} /></Fld>
            <label className="flex items-center gap-2 text-sm"><Switch checked={f.active} onCheckedChange={(v) => setF({ ...f, active: v })} /> Aktif</label>
          </div>
          <DialogFooter><Button variant="secondary" onClick={() => setOpen(false)}>Batal</Button><Button onClick={save}>Simpan</Button></DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

// ---------- Tab: Pembayaran ----------
const PaymentTab = () => {
  const [rows, setRows] = useState([]);
  const [open, setOpen] = useState(false);
  const [editing, setEditing] = useState(null);
  const [f, setF] = useState({ group: 'transfer', name: '', extra: '', fee: 0, active: true, logo: '', qr_image: '' });
  const load = useCallback(() => listPayments().then(setRows).catch(() => toast.error('Gagal memuat metode bayar.')), []);
  useEffect(() => { load(); }, [load]);
  const openNew = () => { setEditing(null); setF({ group: 'transfer', name: '', extra: '', fee: 0, active: true, logo: '', qr_image: '' }); setOpen(true); };
  const openEdit = (r) => { setEditing(r); setF({ group: r.group || 'transfer', name: r.name, extra: r.extra || '', fee: r.fee || 0, active: r.active !== false, logo: r.logo || '', qr_image: r.qr_image || '' }); setOpen(true); };
  const save = async () => {
    if (!f.name.trim()) { toast.error('Nama metode wajib.'); return; }
    const body = {
      group: f.group, name: f.name, extra: f.extra, fee: Number(f.fee) || 0, active: f.active,
      logo: f.logo || null, qr_image: f.qr_image || null,
    };
    try {
      if (editing) await updatePayment(editing.id, body); else await createPayment(body);
      toast.success('Metode bayar disimpan.'); setOpen(false); load();
    } catch (e) { toast.error('Gagal menyimpan.'); }
  };
  const remove = async (r) => { try { await deletePayment(r.id); toast.success('Metode dihapus.'); load(); } catch (e) { toast.error('Gagal menghapus.'); } };
  return (
    <div>
      <div className="flex justify-end mb-3"><Button onClick={openNew} className="gap-2" data-testid="admin-payment-add"><Plus className="h-4 w-4" /> Tambah Metode</Button></div>
      {rows.length === 0 ? <EmptyState title="Belum ada metode bayar" /> : (
        <Table data-testid="admin-payment-table">
          <TableHeader><TableRow><TableHead>Grup</TableHead><TableHead>Nama</TableHead><TableHead className="text-right">Biaya</TableHead><TableHead>Status</TableHead><TableHead className="w-24" /></TableRow></TableHeader>
          <TableBody>
            {rows.map((r) => (
              <TableRow key={r.id}>
                <TableCell className="capitalize text-sm">{r.group}</TableCell>
                <TableCell className="font-medium">
                  <div className="flex items-center gap-2">
                    {r.logo ? (
                      <SmartImage
                        src={r.logo}
                        alt={r.name}
                        className="h-8 w-8 shrink-0 rounded-md border border-border/60"
                        fit="contain"
                        showRetry={false}
                        fallbackLabel=""
                      />
                    ) : null}
                    <span className="min-w-0 truncate">{r.name}</span>
                    {r.qr_image ? (
                      <Badge variant="outline" className="shrink-0 text-[10px]">QR</Badge>
                    ) : null}
                  </div>
                </TableCell>
                <TableCell className="text-right font-['Azeret_Mono',monospace] text-sm">{formatIDR(r.fee || 0)}</TableCell>
                <TableCell><Badge variant="outline" className={r.active !== false ? 'bg-emerald-100 text-emerald-800 border-emerald-200' : 'bg-zinc-100 text-zinc-600 border-zinc-200'}>{r.active !== false ? 'Aktif' : 'Nonaktif'}</Badge></TableCell>
                <TableCell className="text-right">
                  <Button variant="ghost" size="icon" onClick={() => openEdit(r)} aria-label="Edit"><Pencil className="h-4 w-4" /></Button>
                  <Button variant="ghost" size="icon" onClick={() => remove(r)} aria-label="Hapus"><Trash2 className="h-4 w-4 text-rose-600" /></Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      )}
      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{editing ? 'Edit Metode' : 'Tambah Metode'}</DialogTitle>
            <DialogDescription>
              Atur metode pembayaran: grup, nama, nomor/tujuan, dan biaya tambahan.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-3">
            <Fld label="Grup">
              <Select value={f.group} onValueChange={(v) => setF({ ...f, group: v })}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent><SelectItem value="transfer">Transfer Bank</SelectItem><SelectItem value="ewallet">E-Wallet</SelectItem><SelectItem value="cod">COD</SelectItem></SelectContent>
              </Select>
            </Fld>
            <Fld label="Nama"><Input value={f.name} onChange={(e) => setF({ ...f, name: e.target.value })} /></Fld>
            <Fld label="Keterangan (opsional)"><Input value={f.extra} onChange={(e) => setF({ ...f, extra: e.target.value })} /></Fld>
            <Fld label="Biaya (Rp)"><Input type="number" value={f.fee} onChange={(e) => setF({ ...f, fee: e.target.value })} /></Fld>
            <MediaField
              label="Logo bank / e-wallet (opsional)"
              value={f.logo}
              onChange={(url) => setF({ ...f, logo: url })}
              hint="Logo kecil yang tampil di halaman checkout."
              previewClassName="h-16 w-16"
              testId="admin-payment-logo-field"
            />
            <MediaField
              label="Gambar QR / QRIS (opsional)"
              value={f.qr_image}
              onChange={(url) => setF({ ...f, qr_image: url })}
              hint="QR statis yang ditampilkan ke pembeli saat memilih metode ini."
              previewClassName="h-20 w-20"
              testId="admin-payment-qr-field"
            />
            <label className="flex items-center gap-2 text-sm"><Switch checked={f.active} onCheckedChange={(v) => setF({ ...f, active: v })} /> Aktif</label>
          </div>
          <DialogFooter><Button variant="secondary" onClick={() => setOpen(false)}>Batal</Button><Button onClick={save}>Simpan</Button></DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

// ---------- Tab: Media ----------
// E20: pustaka media URL-only lama DIGANTI oleh Media Manager penuh di /admin/media
// (folder bertingkat, upload nyata ke disk lokal, pencarian, aksi massal).
const MediaTab = () => (
  <div className="max-w-2xl space-y-4" data-testid="admin-settings-media-tab">
    <div className="rounded-2xl border border-border/70 bg-muted/40 p-5">
      <div className="flex items-start gap-3">
        <span className="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-card">
          <Images className="h-5 w-5" style={{ color: '#B89B6A' }} aria-hidden="true" />
        </span>
        <div className="min-w-0">
          <h3 className="text-sm font-semibold text-foreground">Media Manager</h3>
          <p className="mt-1 text-xs leading-relaxed text-muted-foreground">
            Semua gambar sekarang dikelola di halaman <strong className="text-foreground">Media</strong>:
            folder bertingkat, upload seret & lepas hingga 15MB per berkas, thumbnail otomatis,
            pencarian, aksi massal, dan penyimpanan di disk lokal server. Gambar dari URL
            eksternal juga ikut diunduh agar tidak pernah broken.
          </p>
          <Button asChild className="mt-3 gap-2 rounded-lg">
            <Link to="/admin/media" data-testid="admin-settings-open-media">
              <Images className="h-4 w-4" /> Buka Media Manager
            </Link>
          </Button>
        </div>
      </div>
    </div>
    <div className="rounded-xl border border-border/70 bg-card px-4 py-3">
      <div className="text-[10px] font-semibold uppercase tracking-[0.16em] text-muted-foreground">
        Dipakai di mana saja?
      </div>
      <ul className="mt-2 space-y-1 text-xs text-muted-foreground">
        <li>• Editor produk → tab <strong className="text-foreground">Media</strong> (galeri produk)</li>
        <li>• Konten Situs (CMS homepage) → setiap field gambar</li>
        <li>• Kategori → gambar kategori</li>
        <li>• Lokasi & Ulasan → foto cabang</li>
        <li>• Pengaturan → OG Image, logo & QR metode pembayaran</li>
      </ul>
    </div>
  </div>
);

// ---------- Tab: Pengguna ----------
const UsersTab = () => {
  const [rows, setRows] = useState([]);
  useEffect(() => { listUsers().then(setRows).catch(() => toast.error('Gagal memuat pengguna.')); }, []);
  return (
    rows.length === 0 ? <EmptyState title="Belum ada pengguna" /> : (
      <Table data-testid="admin-users-table">
        <TableHeader><TableRow><TableHead>Nama</TableHead><TableHead>Email</TableHead><TableHead>Peran</TableHead><TableHead>Bergabung</TableHead></TableRow></TableHeader>
        <TableBody>
          {rows.map((u) => (
            <TableRow key={u.id}>
              <TableCell className="font-medium">{u.name || '—'}</TableCell>
              <TableCell className="text-sm text-muted-foreground">{u.email}</TableCell>
              <TableCell><Badge variant="outline" className={u.role === 'admin' ? 'bg-amber-100 text-amber-800 border-amber-200' : 'bg-zinc-100 text-zinc-700 border-zinc-200'}>{u.role}</Badge></TableCell>
              <TableCell className="text-xs text-muted-foreground">{formatDateTime(u.created_at)}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    )
  );
};

// ---------- Tab: Pertumbuhan (WA, SEO, sosial, GA4) — Epic E7 ----------
const GrowthTab = () => {
  const [s, setS] = useState(null);
  const [saving, setSaving] = useState(false);
  useEffect(() => { getSettings().then(setS).catch(() => toast.error('Gagal memuat settings.')); }, []);
  if (!s) return <div className="py-8 text-sm text-muted-foreground">Memuat…</div>;
  const set = (p) => setS({ ...s, ...p });
  const save = async () => {
    setSaving(true);
    try {
      await updateSettings({
        whatsapp_number: s.whatsapp_number || '', site_url: s.site_url || '',
        seo_title: s.seo_title || '', seo_description: s.seo_description || '',
        og_image: s.og_image || '', social_instagram: s.social_instagram || '',
        social_tiktok: s.social_tiktok || '', social_facebook: s.social_facebook || '',
        ga_measurement_id: s.ga_measurement_id || '',
      });
      toast.success('Pengaturan pertumbuhan disimpan.');
    } catch (e) { toast.error('Gagal menyimpan.'); } finally { setSaving(false); }
  };
  return (
    <div className="space-y-6 max-w-2xl" data-testid="admin-growth-settings">
      <div>
        <div className="text-sm font-semibold mb-3">WhatsApp & Chat</div>
        <div className="grid sm:grid-cols-2 gap-4">
          <Fld label="Nomor WhatsApp (mis. 6281234567890)"><Input value={s.whatsapp_number || ''} onChange={(e) => set({ whatsapp_number: e.target.value })} data-testid="admin-growth-whatsapp" placeholder="628xxxxxxxxxx" /></Fld>
        </div>
      </div>
      <div>
        <div className="text-sm font-semibold mb-3">SEO</div>
        <div className="space-y-4">
          <Fld label="Judul SEO (title)"><Input value={s.seo_title || ''} onChange={(e) => set({ seo_title: e.target.value })} data-testid="admin-growth-seo-title" /></Fld>
          <Fld label="Deskripsi SEO (meta description)"><Input value={s.seo_description || ''} onChange={(e) => set({ seo_description: e.target.value })} /></Fld>
          <div className="grid sm:grid-cols-2 gap-4">
            <Fld label="OG Image (gambar berbagi sosial)">
              <MediaField
                value={s.og_image || ''}
                onChange={(url) => set({ og_image: url })}
                hint="Gambar yang tampil saat tautan situs dibagikan (rasio 1200×630 disarankan)."
                testId="admin-growth-og-image-field"
              />
            </Fld>
            <Fld label="Site URL (untuk sitemap; kosong = otomatis)"><Input value={s.site_url || ''} onChange={(e) => set({ site_url: e.target.value })} /></Fld>
          </div>
        </div>
      </div>
      <div>
        <div className="text-sm font-semibold mb-3">Media Sosial</div>
        <div className="grid sm:grid-cols-2 gap-4">
          <Fld label="Instagram URL"><Input value={s.social_instagram || ''} onChange={(e) => set({ social_instagram: e.target.value })} /></Fld>
          <Fld label="Facebook URL"><Input value={s.social_facebook || ''} onChange={(e) => set({ social_facebook: e.target.value })} /></Fld>
          <Fld label="TikTok URL"><Input value={s.social_tiktok || ''} onChange={(e) => set({ social_tiktok: e.target.value })} /></Fld>
        </div>
      </div>
      <div>
        <div className="text-sm font-semibold mb-3">Analytics Pihak Ketiga</div>
        <Fld label="Google Analytics Measurement ID (opsional, mis. G-XXXX)"><Input value={s.ga_measurement_id || ''} onChange={(e) => set({ ga_measurement_id: e.target.value })} data-testid="admin-growth-ga" placeholder="G-XXXXXXX" /></Fld>
        <p className="text-xs text-muted-foreground mt-1.5">Kosongkan jika hanya memakai analitik first-party. GA4 diaktifkan otomatis bila diisi.</p>
      </div>
      <Button onClick={save} disabled={saving} data-testid="admin-growth-save" className="gap-2"><Save className="h-4 w-4" /> {saving ? 'Menyimpan…' : 'Simpan'}</Button>
    </div>
  );
};

export default function AdminSettingsPage() {
  return (
    <div>
      <PageHeader title="Pengaturan Toko" description="Kurir, metode pembayaran, media, pertumbuhan, dan preferensi toko." />
      <Card className="border-border/70"><CardContent className="p-4">
        <Tabs defaultValue="toko">
          <TabsList className="flex flex-wrap h-auto">
            <TabsTrigger value="toko">Toko</TabsTrigger>
            <TabsTrigger value="kurir">Kurir</TabsTrigger>
            <TabsTrigger value="bayar">Pembayaran</TabsTrigger>
            <TabsTrigger value="pertumbuhan" data-testid="admin-settings-tab-growth">Pertumbuhan</TabsTrigger>
            <TabsTrigger value="media">Media</TabsTrigger>
            <TabsTrigger value="pengguna">Pengguna</TabsTrigger>
          </TabsList>
          <TabsContent value="toko" className="pt-5"><StoreTab /></TabsContent>
          <TabsContent value="kurir" className="pt-5"><ShippingTab /></TabsContent>
          <TabsContent value="bayar" className="pt-5"><PaymentTab /></TabsContent>
          <TabsContent value="pertumbuhan" className="pt-5"><GrowthTab /></TabsContent>
          <TabsContent value="media" className="pt-5"><MediaTab /></TabsContent>
          <TabsContent value="pengguna" className="pt-5"><UsersTab /></TabsContent>
        </Tabs>
      </CardContent></Card>
    </div>
  );
}
