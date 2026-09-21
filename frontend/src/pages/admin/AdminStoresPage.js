// pages/admin/AdminStoresPage.js — kelola lokasi toko, ulasan kurasi, & config maps/reviews.
import React, { useEffect, useState, useCallback } from 'react';
import { toast } from 'sonner';
import { Plus, Pencil, Trash2, Save, Star } from 'lucide-react';
import {
  listStoreLocations, createStoreLocation, updateStoreLocation, deleteStoreLocation,
  listStoreReviews, createStoreReview, updateStoreReview, deleteStoreReview,
  getStoreConfig, updateStoreConfig,
} from '../../services/stores';
import { PageHeader, EmptyState } from '../../components/admin/adminUi';
import { MediaField } from '../../components/admin/media/MediaField';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Label } from '../../components/ui/label';
import { Switch } from '../../components/ui/switch';
import { Badge } from '../../components/ui/badge';
import { Textarea } from '../../components/ui/textarea';
import { Card, CardContent } from '../../components/ui/card';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '../../components/ui/tabs';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../../components/ui/table';
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from '../../components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '../../components/ui/dialog';

const Fld = ({ label, children, hint }) => (
  <div className="space-y-1.5">
    <Label className="text-xs text-muted-foreground">{label}</Label>
    {children}
    {hint ? <p className="text-[11px] text-muted-foreground">{hint}</p> : null}
  </div>
);

const EMPTY_LOC = { name: '', address: '', phone: '', whatsapp: '', hours: '', maps_query: '', map_url: '', place_id: '', photo: '', order: 0, active: true };
const EMPTY_REV = { author: '', rating: 5, text: '', location: '', relative_time: '', active: true };

// ---------------- Tab: Lokasi ----------------
const LocationsTab = () => {
  const [rows, setRows] = useState([]);
  const [open, setOpen] = useState(false);
  const [editing, setEditing] = useState(null);
  const [f, setF] = useState(EMPTY_LOC);
  const load = useCallback(() => listStoreLocations().then(setRows).catch(() => toast.error('Gagal memuat lokasi.')), []);
  useEffect(() => { load(); }, [load]);
  const openNew = () => { setEditing(null); setF(EMPTY_LOC); setOpen(true); };
  const openEdit = (r) => {
    setEditing(r);
    setF({ name: r.name || '', address: r.address || '', phone: r.phone || '', whatsapp: r.whatsapp || '', hours: r.hours || '', maps_query: r.maps_query || '', map_url: r.map_url || '', place_id: r.place_id || '', photo: r.photo || '', order: r.order || 0, active: r.active !== false });
    setOpen(true);
  };
  const save = async () => {
    if (!f.name.trim() || !f.address.trim()) { toast.error('Nama & alamat wajib diisi.'); return; }
    const body = { ...f, order: Number(f.order) || 0 };
    try {
      if (editing) await updateStoreLocation(editing.id, body); else await createStoreLocation(body);
      toast.success('Lokasi disimpan.'); setOpen(false); load();
    } catch (e) { toast.error('Gagal menyimpan lokasi.'); }
  };
  const remove = async (r) => { if (!window.confirm(`Hapus lokasi "${r.name}"?`)) return; try { await deleteStoreLocation(r.id); toast.success('Lokasi dihapus.'); load(); } catch (e) { toast.error('Gagal menghapus.'); } };
  return (
    <div>
      <div className="flex justify-end mb-3"><Button onClick={openNew} className="gap-2" data-testid="admin-store-location-add"><Plus className="h-4 w-4" /> Tambah Lokasi</Button></div>
      {rows.length === 0 ? <EmptyState title="Belum ada lokasi toko" hint="Tambahkan cabang toko offline Anda." /> : (
        <Table data-testid="admin-store-locations-table">
          <TableHeader><TableRow><TableHead>Nama</TableHead><TableHead>Alamat</TableHead><TableHead>Jam</TableHead><TableHead>Urutan</TableHead><TableHead>Status</TableHead><TableHead className="w-24" /></TableRow></TableHeader>
          <TableBody>
            {rows.map((r) => (
              <TableRow key={r.id}>
                <TableCell className="font-medium">{r.name}</TableCell>
                <TableCell className="text-sm text-muted-foreground max-w-xs truncate">{r.address}</TableCell>
                <TableCell className="text-sm text-muted-foreground">{r.hours || '—'}</TableCell>
                <TableCell className="text-sm">{r.order || 0}</TableCell>
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
        <DialogContent className="max-w-lg max-h-[85vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>{editing ? 'Edit Lokasi' : 'Tambah Lokasi'}</DialogTitle>
            <DialogDescription>
              Isi nama toko, alamat lengkap, jam operasional, kontak, dan koordinat peta.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-3">
            <Fld label="Nama cabang"><Input value={f.name} onChange={(e) => setF({ ...f, name: e.target.value })} placeholder="Collector Parfum — Pasir Kaliki" /></Fld>
            <Fld label="Alamat lengkap"><Textarea rows={2} value={f.address} onChange={(e) => setF({ ...f, address: e.target.value })} /></Fld>
            <div className="grid grid-cols-2 gap-3">
              <Fld label="Telepon"><Input value={f.phone} onChange={(e) => setF({ ...f, phone: e.target.value })} placeholder="+62 857-..." /></Fld>
              <Fld label="WhatsApp (angka)"><Input value={f.whatsapp} onChange={(e) => setF({ ...f, whatsapp: e.target.value })} placeholder="62857..." /></Fld>
            </div>
            <Fld label="Jam buka"><Input value={f.hours} onChange={(e) => setF({ ...f, hours: e.target.value })} placeholder="Setiap hari 09.00 – 20.00" /></Fld>
            <Fld label="Query peta (alamat / 'lat,lng')" hint="Dipakai untuk pin peta embed."><Input value={f.maps_query} onChange={(e) => setF({ ...f, maps_query: e.target.value })} /></Fld>
            <Fld label="Tautan Google Maps (petunjuk arah)"><Input value={f.map_url} onChange={(e) => setF({ ...f, map_url: e.target.value })} placeholder="https://maps.app.goo.gl/..." /></Fld>
            <Fld label="Place ID (opsional, utk Google Reviews)"><Input value={f.place_id} onChange={(e) => setF({ ...f, place_id: e.target.value })} /></Fld>
            <MediaField
              label="Foto cabang (opsional)"
              value={f.photo}
              onChange={(url) => setF({ ...f, photo: url })}
              hint="Foto tampak depan / interior cabang. Dipilih dari Media Manager atau diunggah langsung."
              testId="admin-store-photo-field"
            />
            <div className="grid grid-cols-2 gap-3 items-end">
              <Fld label="Urutan"><Input type="number" value={f.order} onChange={(e) => setF({ ...f, order: e.target.value })} /></Fld>
              <label className="flex items-center gap-2 text-sm pb-2"><Switch checked={f.active} onCheckedChange={(v) => setF({ ...f, active: v })} /> Aktif</label>
            </div>
          </div>
          <DialogFooter><Button variant="secondary" onClick={() => setOpen(false)}>Batal</Button><Button onClick={save} data-testid="admin-store-location-save">Simpan</Button></DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

// ---------------- Tab: Ulasan kurasi ----------------
const ReviewsTab = () => {
  const [rows, setRows] = useState([]);
  const [open, setOpen] = useState(false);
  const [editing, setEditing] = useState(null);
  const [f, setF] = useState(EMPTY_REV);
  const load = useCallback(() => listStoreReviews().then(setRows).catch(() => toast.error('Gagal memuat ulasan.')), []);
  useEffect(() => { load(); }, [load]);
  const openNew = () => { setEditing(null); setF(EMPTY_REV); setOpen(true); };
  const openEdit = (r) => { setEditing(r); setF({ author: r.author || '', rating: r.rating || 5, text: r.text || '', location: r.location || '', relative_time: r.relative_time || '', active: r.active !== false }); setOpen(true); };
  const save = async () => {
    if (!f.author.trim()) { toast.error('Nama pengulas wajib.'); return; }
    const body = { ...f, rating: Number(f.rating) || 5 };
    try {
      if (editing) await updateStoreReview(editing.id, body); else await createStoreReview(body);
      toast.success('Ulasan disimpan.'); setOpen(false); load();
    } catch (e) { toast.error('Gagal menyimpan ulasan.'); }
  };
  const remove = async (r) => { if (!window.confirm('Hapus ulasan ini?')) return; try { await deleteStoreReview(r.id); toast.success('Ulasan dihapus.'); load(); } catch (e) { toast.error('Gagal menghapus.'); } };
  return (
    <div>
      <div className="flex items-center justify-between mb-3">
        <p className="text-xs text-muted-foreground">Ulasan kurasi tampil bila sumber ulasan = <b>manual</b>.</p>
        <Button onClick={openNew} className="gap-2" data-testid="admin-store-review-add"><Plus className="h-4 w-4" /> Tambah Ulasan</Button>
      </div>
      {rows.length === 0 ? <EmptyState title="Belum ada ulasan kurasi" /> : (
        <Table data-testid="admin-store-reviews-table">
          <TableHeader><TableRow><TableHead>Pengulas</TableHead><TableHead>Rating</TableHead><TableHead>Ulasan</TableHead><TableHead>Status</TableHead><TableHead className="w-24" /></TableRow></TableHeader>
          <TableBody>
            {rows.map((r) => (
              <TableRow key={r.id}>
                <TableCell className="font-medium">{r.author}<div className="text-[11px] text-muted-foreground">{r.relative_time} {r.location}</div></TableCell>
                <TableCell><span className="inline-flex items-center gap-1 text-sm"><Star className="h-3.5 w-3.5 fill-amber-400 text-amber-400" />{r.rating}</span></TableCell>
                <TableCell className="text-sm text-muted-foreground max-w-sm truncate">{r.text}</TableCell>
                <TableCell><Badge variant="outline" className={r.active !== false ? 'bg-emerald-100 text-emerald-800 border-emerald-200' : 'bg-zinc-100 text-zinc-600 border-zinc-200'}>{r.active !== false ? 'Tayang' : 'Sembunyi'}</Badge></TableCell>
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
            <DialogTitle>{editing ? 'Edit Ulasan' : 'Tambah Ulasan'}</DialogTitle>
            <DialogDescription>
              Ulasan kurasi yang ditampilkan pada halaman Lokasi &amp; Ulasan toko.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-3">
            <div className="grid grid-cols-2 gap-3">
              <Fld label="Nama pengulas"><Input value={f.author} onChange={(e) => setF({ ...f, author: e.target.value })} /></Fld>
              <Fld label="Rating (1-5)">
                <Select value={String(f.rating)} onValueChange={(v) => setF({ ...f, rating: Number(v) })}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>{[5, 4, 3, 2, 1].map((n) => <SelectItem key={n} value={String(n)}>{n} bintang</SelectItem>)}</SelectContent>
                </Select>
              </Fld>
            </div>
            <Fld label="Ulasan"><Textarea rows={3} value={f.text} onChange={(e) => setF({ ...f, text: e.target.value })} /></Fld>
            <div className="grid grid-cols-2 gap-3">
              <Fld label="Lokasi/cabang"><Input value={f.location} onChange={(e) => setF({ ...f, location: e.target.value })} placeholder="Pasir Kaliki" /></Fld>
              <Fld label="Waktu relatif"><Input value={f.relative_time} onChange={(e) => setF({ ...f, relative_time: e.target.value })} placeholder="2 minggu lalu" /></Fld>
            </div>
            <label className="flex items-center gap-2 text-sm"><Switch checked={f.active} onCheckedChange={(v) => setF({ ...f, active: v })} /> Tayang</label>
          </div>
          <DialogFooter><Button variant="secondary" onClick={() => setOpen(false)}>Batal</Button><Button onClick={save} data-testid="admin-store-review-save">Simpan</Button></DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

// ---------------- Tab: Config maps & reviews ----------------
const ConfigTab = () => {
  const [c, setC] = useState(null);
  const [saving, setSaving] = useState(false);
  useEffect(() => { getStoreConfig().then(setC).catch(() => toast.error('Gagal memuat config.')); }, []);
  if (!c) return <div className="py-8 text-sm text-muted-foreground">Memuat…</div>;
  const set = (p) => setC({ ...c, ...p });
  const save = async () => {
    setSaving(true);
    try {
      await updateStoreConfig({
        maps_mode: c.maps_mode || 'embed',
        reviews_source: c.reviews_source || 'manual',
        google_maps_api_key: c.google_maps_api_key || '',
        google_places_api_key: c.google_places_api_key || '',
        google_place_id: c.google_place_id || '',
        rating_avg: Number(c.store_rating_avg) || 0,
        rating_count: Number(c.store_rating_count) || 0,
        intro: c.stores_intro || '',
      });
      toast.success('Konfigurasi disimpan.');
    } catch (e) { toast.error('Gagal menyimpan.'); } finally { setSaving(false); }
  };
  return (
    <div className="space-y-6 max-w-2xl" data-testid="admin-store-config">
      <div>
        <div className="text-sm font-semibold mb-3">Peta (Google Maps)</div>
        <div className="grid sm:grid-cols-2 gap-4">
          <Fld label="Mode peta" hint="Embed = tanpa API key. JS = interaktif (butuh API key).">
            <Select value={c.maps_mode || 'embed'} onValueChange={(v) => set({ maps_mode: v })}>
              <SelectTrigger data-testid="admin-store-maps-mode"><SelectValue /></SelectTrigger>
              <SelectContent><SelectItem value="embed">Embed (tanpa API key)</SelectItem><SelectItem value="js">Maps JavaScript API</SelectItem></SelectContent>
            </Select>
          </Fld>
          <Fld label="Google Maps API Key (client)" hint="Hanya dipakai bila mode = JS. Batasi HTTP-referrer di Google Cloud."><Input value={c.google_maps_api_key || ''} onChange={(e) => set({ google_maps_api_key: e.target.value })} placeholder="AIza..." /></Fld>
        </div>
      </div>
      <div>
        <div className="text-sm font-semibold mb-3">Ulasan (Google Reviews)</div>
        <div className="grid sm:grid-cols-2 gap-4">
          <Fld label="Sumber ulasan" hint="Manual = kurasi di tab Ulasan. Google = tarik dari Places API (butuh key + Place ID).">
            <Select value={c.reviews_source || 'manual'} onValueChange={(v) => set({ reviews_source: v })}>
              <SelectTrigger data-testid="admin-store-reviews-source"><SelectValue /></SelectTrigger>
              <SelectContent><SelectItem value="manual">Manual (kurasi)</SelectItem><SelectItem value="google">Google Places API</SelectItem></SelectContent>
            </Select>
          </Fld>
          <Fld label="Google Places API Key (server)" hint="Untuk menarik ulasan asli (maks 5). Disimpan aman di server."><Input value={c.google_places_api_key || ''} onChange={(e) => set({ google_places_api_key: e.target.value })} placeholder="AIza..." /></Fld>
          <Fld label="Google Place ID" hint="ID tempat dari Google Business Profile."><Input value={c.google_place_id || ''} onChange={(e) => set({ google_place_id: e.target.value })} placeholder="ChIJ..." /></Fld>
        </div>
      </div>
      <div>
        <div className="text-sm font-semibold mb-3">Ringkasan Rating (tampilan)</div>
        <div className="grid sm:grid-cols-2 gap-4">
          <Fld label="Rating rata-rata (0-5)"><Input type="number" step="0.1" value={c.store_rating_avg ?? 0} onChange={(e) => set({ store_rating_avg: e.target.value })} /></Fld>
          <Fld label="Jumlah ulasan"><Input type="number" value={c.store_rating_count ?? 0} onChange={(e) => set({ store_rating_count: e.target.value })} /></Fld>
        </div>
      </div>
      <Fld label="Intro halaman Lokasi"><Textarea rows={2} value={c.stores_intro || ''} onChange={(e) => set({ stores_intro: e.target.value })} /></Fld>
      <Button onClick={save} disabled={saving} data-testid="admin-store-config-save" className="gap-2"><Save className="h-4 w-4" /> {saving ? 'Menyimpan…' : 'Simpan Konfigurasi'}</Button>
    </div>
  );
};

export default function AdminStoresPage() {
  return (
    <div>
      <PageHeader title="Lokasi & Ulasan" description="Kelola cabang toko offline, ulasan Google (kurasi/asli), dan peta." testId="admin-stores-header" />
      <Card className="border-border/70"><CardContent className="p-4">
        <Tabs defaultValue="lokasi">
          <TabsList className="flex flex-wrap h-auto">
            <TabsTrigger value="lokasi" data-testid="admin-stores-tab-locations">Lokasi Toko</TabsTrigger>
            <TabsTrigger value="ulasan" data-testid="admin-stores-tab-reviews">Ulasan</TabsTrigger>
            <TabsTrigger value="config" data-testid="admin-stores-tab-config">Konfigurasi</TabsTrigger>
          </TabsList>
          <TabsContent value="lokasi" className="pt-5"><LocationsTab /></TabsContent>
          <TabsContent value="ulasan" className="pt-5"><ReviewsTab /></TabsContent>
          <TabsContent value="config" className="pt-5"><ConfigTab /></TabsContent>
        </Tabs>
      </CardContent></Card>
    </div>
  );
}
