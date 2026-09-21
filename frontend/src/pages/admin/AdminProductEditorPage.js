// pages/admin/AdminProductEditorPage.js — editor 2-panel + live preview (BR-2/BR-9).
// Varian N-dimensi: definisikan dimensi (options) → generate kombinasi (variants ber-SKU).
import React, { useEffect, useState, useCallback, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { toast } from 'sonner';
import {
  Save, Plus, Trash2, Star, ArrowLeft, Wand2, ImagePlus, Upload, Loader2,
  ChevronLeft, ChevronRight, Link2,
} from 'lucide-react';
import {
  getProduct, createProduct, updateProduct, listCategories,
  listOccasions, listCharactersAdmin,
} from '../../services/admin';
import {
  MEDIA_ACCEPT, ingestUrl, mediaErrorMessage, uploadAsset,
} from '../../services/media';
import { MediaPickerDialog } from '../../components/admin/media/MediaPickerDialog';
import { validateFile } from '../../components/admin/media/useMediaUpload';
import { SmartImage } from '../../components/shared/SmartImage';
import { CHECKER_STYLE, isLocalMedia } from '../../lib/mediaUrl';
import { getFacetIcon } from '../../lib/taxonomyIcons';
import { compositeType, parseMl, sizeDimName } from '../../lib/variants';
import { PageHeader } from '../../components/admin/adminUi';
import { ProductPreview } from '../../components/admin/ProductPreview';
import { adminTestIds as T } from '../../constants/testIds/admin';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Label } from '../../components/ui/label';
import { Textarea } from '../../components/ui/textarea';
import { Switch } from '../../components/ui/switch';
import { Card, CardContent } from '../../components/ui/card';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '../../components/ui/tabs';
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from '../../components/ui/select';

const BLANK = {
  name: '', slug: '', brand: 'Collector', category: '', concentration: 'EDP', gender: 'Unisex',
  compare_at_price: '', best_seller: false, is_new: false, status: 'active',
  description: '', ingredients: '', video_url: '',
  options: [], variants: [],
  images: [], notes: { top: [], heart: [], base: [] },
  occasions: [], characters: [],
  seo: { title: '', description: '', keywords: [] },
};
const csv = (s) => (s || '').split(',').map((x) => x.trim()).filter(Boolean);
const join = (a) => (a || []).join(', ');
const DEFAULT_OPTROWS = [{ name: 'Konsentrasi', valuesText: 'EDP' }, { name: 'Ukuran', valuesText: '50ml' }];

export default function AdminProductEditorPage() {
  const { id } = useParams();
  const isNew = !id || id === 'baru';
  const navigate = useNavigate();
  const [form, setForm] = useState(BLANK);
  const [optRows, setOptRows] = useState(DEFAULT_OPTROWS);
  const [notesText, setNotesText] = useState({ top: '', heart: '', base: '' });
  const [tagsText, setTagsText] = useState('');
  const [kwText, setKwText] = useState('');
  const [mediaUrl, setMediaUrl] = useState('');
  const [pickerOpen, setPickerOpen] = useState(false);
  const [mediaBusy, setMediaBusy] = useState(false);
  const mediaFileRef = useRef(null);
  const [cats, setCats] = useState([]);
  const [occ, setOcc] = useState([]);
  const [chars, setChars] = useState([]);
  const [loading, setLoading] = useState(!isNew);
  const [saving, setSaving] = useState(false);

  const set = (patch) => setForm((f) => ({ ...f, ...patch }));

  // Toggle slug facet MULTI (occasions/characters).
  const toggleFacet = (field, slug) => setForm((f) => {
    const cur = f[field] || [];
    return { ...f, [field]: cur.includes(slug) ? cur.filter((s) => s !== slug) : [...cur, slug] };
  });

  useEffect(() => {
    (async () => {
      try {
        const [c, oc, ch] = await Promise.all([
          listCategories(), listOccasions(), listCharactersAdmin(),
        ]);
        setCats((c || []).filter((x) => x.active !== false));
        setOcc((oc || []).filter((x) => x.active !== false));
        setChars((ch || []).filter((x) => x.active !== false));
        if (!isNew) {
          const p = await getProduct(id);
          setForm({
            ...BLANK, ...p,
            compare_at_price: p.compare_at_price || '',
            ingredients: p.ingredients || '', video_url: p.video_url || '',
            occasions: p.occasions || [], characters: p.characters || [],
            options: p.options || [],
            variants: (p.variants || []).map((v) => ({
              options: v.options || {}, price: v.price, stock: v.stock,
              compare_at_price: v.compare_at_price || '', sku: v.sku || '',
            })),
            notes: p.notes || BLANK.notes, images: p.images || [],
            seo: { title: p.seo?.title || '', description: p.seo?.description || '', keywords: p.seo?.keywords || [] },
          });
          setOptRows((p.options || []).map((o) => ({ name: o.name, valuesText: (o.values || []).join(', ') }))
            .concat((p.options || []).length ? [] : DEFAULT_OPTROWS));
          setNotesText({ top: join(p.notes?.top), heart: join(p.notes?.heart), base: join(p.notes?.base) });
          setTagsText(join(p.tags));
          setKwText(join(p.seo?.keywords));
        } else if ((c || []).length) {
          set({ category: c[0].slug });
          // varian default agar admin bisa langsung isi.
          set({ variants: [{ options: { Konsentrasi: 'EDP', Ukuran: '50ml' }, price: '', stock: 0, compare_at_price: '', sku: '' }] });
        }
      } catch (e) {
        toast.error('Gagal memuat data editor.');
      } finally {
        setLoading(false);
      }
    })();
  }, [id]); // eslint-disable-line

  // ---- OPSI (dimensi) & VARIAN (kombinasi ber-SKU) ----
  const buildOptions = useCallback(() => optRows
    .map((r) => ({ name: (r.name || '').trim(), values: csv(r.valuesText) }))
    .filter((o) => o.name && o.values.length), [optRows]);

  const setOptRow = (i, patch) => setOptRows((rows) => rows.map((r, idx) => (idx === i ? { ...r, ...patch } : r)));
  const addOptRow = () => setOptRows((rows) => (rows.length >= 4 ? rows : [...rows, { name: '', valuesText: '' }]));
  const rmOptRow = (i) => setOptRows((rows) => rows.filter((_, idx) => idx !== i));

  const comboKey = (opts, options) => options.map((o) => opts[o.name]).join('||');
  const genCombos = () => {
    const options = buildOptions();
    if (!options.length) { toast.error('Isi minimal 1 dimensi beserta nilainya.'); return; }
    if (!options.some((o) => /ukuran|size|ml|volume/i.test(o.name))) {
      toast.error('Wajib ada dimensi ukuran (mis. "Ukuran": 30ml, 50ml).'); return;
    }
    let combos = [{}];
    options.forEach((o) => {
      const next = [];
      combos.forEach((c) => o.values.forEach((val) => next.push({ ...c, [o.name]: val })));
      combos = next;
    });
    if (combos.length > 100) { toast.error('Maksimum 100 kombinasi varian.'); return; }
    const existing = new Map((form.variants || []).map((v) => [comboKey(v.options || {}, options), v]));
    const variants = combos.map((opts) => {
      const prev = existing.get(comboKey(opts, options));
      return prev ? { ...prev, options: opts }
        : { options: opts, price: '', stock: 0, compare_at_price: '', sku: '' };
    });
    set({ variants });
    toast.success(`Dibuat ${variants.length} kombinasi varian.`);
  };

  const setVariant = (i, patch) => setForm((f) => ({ ...f, variants: f.variants.map((v, idx) => (idx === i ? { ...v, ...patch } : v)) }));
  const rmVariant = (i) => setForm((f) => ({ ...f, variants: f.variants.filter((_, idx) => idx !== i) }));

  // ---- MEDIA GALERI PRODUK (E20) ----
  // Sumber gambar: Media Manager (picker), upload langsung, atau URL (diunduh ke lokal).
  const addImages = (urls) => {
    const list = (Array.isArray(urls) ? urls : [urls])
      .map((u) => (u || '').trim())
      .filter(Boolean);
    if (!list.length) return;
    setForm((f) => {
      const merged = [...f.images];
      let dup = 0;
      list.forEach((u) => {
        if (merged.includes(u)) { dup += 1; return; }
        merged.push(u);
      });
      if (dup) toast(`${dup} gambar sudah ada di galeri.`);
      return { ...f, images: merged };
    });
  };
  const setPrimary = (i) => set({ images: [form.images[i], ...form.images.filter((_, idx) => idx !== i)] });
  const rmImage = (i) => set({ images: form.images.filter((_, idx) => idx !== i) });
  const moveImage = (i, dir) => {
    const j = i + dir;
    if (j < 0 || j >= form.images.length) return;
    const next = [...form.images];
    [next[i], next[j]] = [next[j], next[i]];
    set({ images: next });
  };

  const uploadProductImages = async (files) => {
    const list = Array.from(files || []);
    if (!list.length) return;
    setMediaBusy(true);
    const okUrls = [];
    for (const file of list) {
      const err = validateFile(file);
      if (err) { toast.error(`${file.name}: ${err}`); continue; }
      try {
        // eslint-disable-next-line no-await-in-loop
        const asset = await uploadAsset(file);
        okUrls.push(asset.url);
      } catch (e) {
        toast.error(`${file.name}: ${mediaErrorMessage(e, 'Upload gagal.')}`);
      }
    }
    setMediaBusy(false);
    if (mediaFileRef.current) mediaFileRef.current.value = '';
    if (okUrls.length) {
      addImages(okUrls);
      toast.success(`${okUrls.length} gambar terunggah & masuk galeri.`);
    }
  };

  const addFromUrl = async () => {
    const u = (mediaUrl || '').trim();
    if (!u) return;
    if (u.startsWith('/api/media/')) { addImages(u); setMediaUrl(''); return; }
    setMediaBusy(true);
    try {
      const asset = await ingestUrl(u);
      addImages(asset.url);
      setMediaUrl('');
      toast.success('Gambar diunduh dari URL & disimpan lokal.');
    } catch (e) {
      toast.error(mediaErrorMessage(e, 'Gagal mengunduh gambar dari URL.'));
    } finally { setMediaBusy(false); }
  };

  const editorOptions = buildOptions();
  // Turunkan volumes utk live preview (type = gabungan dimensi non-ukuran, ml = parse ukuran).
  const previewVolumes = (form.variants || []).map((v) => ({
    type: compositeType(v.options || {}, editorOptions),
    ml: parseMl((v.options || {})[sizeDimName(editorOptions)]),
    price: Number(v.price) || 0, stock: Number(v.stock) || 0,
    compare_at_price: v.compare_at_price ? Number(v.compare_at_price) : null,
    sku: v.sku || '',
  }));
  const previewProduct = {
    ...form,
    notes: { top: csv(notesText.top), heart: csv(notesText.heart), base: csv(notesText.base) },
    compare_at_price: form.compare_at_price ? Number(form.compare_at_price) : null,
    volumes: previewVolumes.length ? previewVolumes : [{ type: '', ml: 50, price: 0, stock: 0 }],
  };

  const save = useCallback(async () => {
    if (!form.name.trim()) { toast.error('Nama produk wajib diisi.'); return; }
    if (!form.category) { toast.error('Pilih kategori.'); return; }
    const options = buildOptions();
    if (!options.length) { toast.error('Definisikan minimal 1 dimensi varian.'); return; }
    if (!(form.variants || []).length) { toast.error('Buat kombinasi varian (klik "Generate Kombinasi").'); return; }
    if ((form.variants || []).some((v) => !(Number(v.price) > 0))) {
      toast.error('Setiap varian harus punya harga > 0.'); return;
    }
    setSaving(true);
    const payload = {
      name: form.name.trim(), slug: form.slug || undefined, brand: form.brand || 'Collector',
      category: form.category, concentration: form.concentration, gender: form.gender,
      compare_at_price: form.compare_at_price ? Number(form.compare_at_price) : null,
      best_seller: !!form.best_seller, is_new: !!form.is_new, tags: csv(tagsText),
      occasions: form.occasions || [], characters: form.characters || [],
      options,
      variants: (form.variants || []).map((v) => ({
        options: v.options || {}, price: Number(v.price) || 0, stock: Number(v.stock) || 0,
        compare_at_price: v.compare_at_price ? Number(v.compare_at_price) : null,
        sku: (v.sku || '').trim() || null,
      })),
      notes: { top: csv(notesText.top), heart: csv(notesText.heart), base: csv(notesText.base) },
      description: form.description || '', ingredients: form.ingredients || null,
      images: form.images, video_url: form.video_url || null,
      seo: { title: form.seo.title || '', description: form.seo.description || '', keywords: csv(kwText) },
      status: form.status,
    };
    try {
      if (isNew) { await createProduct(payload); toast.success('Produk dibuat.'); }
      else { await updateProduct(id, payload); toast.success('Produk diperbarui.'); }
      navigate('/admin/produk');
    } catch (e) {
      toast.error(e?.response?.data?.detail || 'Gagal menyimpan produk.');
    } finally {
      setSaving(false);
    }
  }, [form, optRows, notesText, tagsText, kwText, id, isNew, navigate]); // eslint-disable-line

  if (loading) return <div className="h-64 grid place-items-center text-muted-foreground">Memuat editor…</div>;

  return (
    <div data-testid={T.productEditor}>
      <PageHeader
        title={isNew ? 'Tambah Produk' : 'Edit Produk'}
        description="Isi detail produk; pratinjau storefront tampil di kanan."
        actions={(
          <div className="flex gap-2">
            <Button variant="secondary" onClick={() => navigate('/admin/produk')} className="gap-2">
              <ArrowLeft className="h-4 w-4" /> Kembali
            </Button>
            <Button onClick={save} disabled={saving} data-testid={T.productSave} className="gap-2">
              <Save className="h-4 w-4" /> {saving ? 'Menyimpan…' : 'Simpan'}
            </Button>
          </div>
        )}
      />

      <div className="grid lg:grid-cols-2 gap-6 items-start">
        {/* LEFT: form */}
        <Card className="border-border/70">
          <CardContent className="p-5">
            <Tabs defaultValue="info">
              <TabsList className="grid grid-cols-4 w-full">
                <TabsTrigger value="info">Info</TabsTrigger>
                <TabsTrigger value="varian">Varian</TabsTrigger>
                <TabsTrigger value="media">Media</TabsTrigger>
                <TabsTrigger value="seo">SEO</TabsTrigger>
              </TabsList>

              {/* INFO */}
              <TabsContent value="info" className="space-y-4 pt-4">
                <Field label="Nama Produk"><Input value={form.name} onChange={(e) => set({ name: e.target.value })} data-testid="admin-product-name" /></Field>
                <div className="grid grid-cols-2 gap-3">
                  <Field label="Merek"><Input value={form.brand} onChange={(e) => set({ brand: e.target.value })} /></Field>
                  <Field label="Slug (opsional)"><Input value={form.slug} onChange={(e) => set({ slug: e.target.value })} placeholder="otomatis dari nama" /></Field>
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <Field label="Kategori">
                    <Select value={form.category} onValueChange={(v) => set({ category: v })}>
                      <SelectTrigger data-testid="admin-product-category"><SelectValue placeholder="Pilih kategori" /></SelectTrigger>
                      <SelectContent>
                        {cats.map((c) => <SelectItem key={c.slug} value={c.slug} className="capitalize">{c.name}</SelectItem>)}
                      </SelectContent>
                    </Select>
                  </Field>
                  <Field label="Konsentrasi (default)">
                    <Select value={form.concentration} onValueChange={(v) => set({ concentration: v })}>
                      <SelectTrigger><SelectValue /></SelectTrigger>
                      <SelectContent><SelectItem value="EDP">EDP</SelectItem><SelectItem value="EDT">EDT</SelectItem></SelectContent>
                    </Select>
                  </Field>
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <Field label="Gender">
                    <Select value={form.gender} onValueChange={(v) => set({ gender: v })}>
                      <SelectTrigger><SelectValue /></SelectTrigger>
                      <SelectContent>
                        <SelectItem value="Pria">Pria</SelectItem><SelectItem value="Wanita">Wanita</SelectItem><SelectItem value="Unisex">Unisex</SelectItem>
                      </SelectContent>
                    </Select>
                  </Field>
                  <Field label="Status">
                    <Select value={form.status} onValueChange={(v) => set({ status: v })}>
                      <SelectTrigger data-testid="admin-product-status"><SelectValue /></SelectTrigger>
                      <SelectContent><SelectItem value="active">Aktif</SelectItem><SelectItem value="archived">Diarsipkan</SelectItem></SelectContent>
                    </Select>
                  </Field>
                </div>
                <Field label="Harga Coret Produk (opsional)">
                  <Input type="number" value={form.compare_at_price} onChange={(e) => set({ compare_at_price: e.target.value })} placeholder="harus > harga varian termurah" />
                </Field>
                <div className="grid grid-cols-3 gap-3">
                  <Field label="Notes Top"><Input value={notesText.top} onChange={(e) => setNotesText({ ...notesText, top: e.target.value })} placeholder="pisah koma" /></Field>
                  <Field label="Notes Heart"><Input value={notesText.heart} onChange={(e) => setNotesText({ ...notesText, heart: e.target.value })} placeholder="pisah koma" /></Field>
                  <Field label="Notes Base"><Input value={notesText.base} onChange={(e) => setNotesText({ ...notesText, base: e.target.value })} placeholder="pisah koma" /></Field>
                </div>
                <Field label="Tag (pisah koma)"><Input value={tagsText} onChange={(e) => setTagsText(e.target.value)} /></Field>
                <FacetPicker label="Occasion (facet)" items={occ} selected={form.occasions} onToggle={(s) => toggleFacet('occasions', s)} testid={T.productOccasions} />
                <FacetPicker label="Character (facet)" items={chars} selected={form.characters} onToggle={(s) => toggleFacet('characters', s)} testid={T.productCharacters} />
                <Field label="Deskripsi"><Textarea rows={4} value={form.description} onChange={(e) => set({ description: e.target.value })} /></Field>
                <Field label="Kandungan (opsional)"><Textarea rows={2} value={form.ingredients} onChange={(e) => set({ ingredients: e.target.value })} /></Field>
                <div className="flex items-center gap-6">
                  <label className="flex items-center gap-2 text-sm"><Switch checked={form.best_seller} onCheckedChange={(v) => set({ best_seller: v })} /> Best Seller</label>
                  <label className="flex items-center gap-2 text-sm"><Switch checked={form.is_new} onCheckedChange={(v) => set({ is_new: v })} /> Produk Baru</label>
                </div>
              </TabsContent>

              {/* VARIAN — N-dimensi (options builder + variant grid) */}
              <TabsContent value="varian" className="space-y-4 pt-4">
                <div className="rounded-xl border border-dashed border-border p-3 bg-muted/30 space-y-3">
                  <div className="flex items-center justify-between">
                    <div className="text-xs font-medium text-muted-foreground">Dimensi Varian (mis. Konsentrasi, Tipe, Ukuran)</div>
                    <Button variant="ghost" size="sm" onClick={addOptRow} disabled={optRows.length >= 4} className="gap-1 h-7 text-xs"><Plus className="h-3.5 w-3.5" /> Dimensi</Button>
                  </div>
                  {optRows.map((r, i) => (
                    <div key={i} className="grid grid-cols-12 gap-2 items-end" data-testid="admin-option-row">
                      <div className="col-span-4"><Label className="text-xs">Nama Dimensi</Label><Input value={r.name} onChange={(e) => setOptRow(i, { name: e.target.value })} placeholder="Ukuran" data-testid="admin-option-name" /></div>
                      <div className="col-span-7"><Label className="text-xs">Nilai (pisah koma)</Label><Input value={r.valuesText} onChange={(e) => setOptRow(i, { valuesText: e.target.value })} placeholder="30ml, 50ml, 100ml" data-testid="admin-option-values" /></div>
                      <div className="col-span-1 flex justify-end">
                        <Button variant="ghost" size="icon" onClick={() => rmOptRow(i)} disabled={optRows.length <= 1} aria-label="Hapus dimensi"><Trash2 className="h-4 w-4 text-rose-600" /></Button>
                      </div>
                    </div>
                  ))}
                  <Button variant="secondary" onClick={genCombos} data-testid="admin-variant-generate" className="gap-2"><Wand2 className="h-4 w-4" /> Generate Kombinasi</Button>
                  <p className="text-[11px] text-muted-foreground">Wajib ada dimensi ukuran (nama mengandung "ukuran/size/ml"). Generate membuat 1 baris per kombinasi; harga/stok/SKU yang sudah diisi dipertahankan.</p>
                </div>

                {(form.variants || []).map((v, i) => {
                  const label = editorOptions.length
                    ? editorOptions.map((o) => (v.options || {})[o.name]).filter(Boolean).join(' / ')
                    : Object.values(v.options || {}).filter(Boolean).join(' / ');
                  return (
                    <div key={i} className="grid grid-cols-2 md:grid-cols-12 gap-2 items-end border border-border rounded-xl p-3" data-testid={T.variantRow}>
                      <div className="md:col-span-3">
                        <Label className="text-xs">Kombinasi</Label>
                        <div className="h-9 flex items-center px-2 text-xs font-medium rounded-md bg-muted/60 border border-border capitalize truncate" title={label} data-testid="admin-variant-combo">{label || '—'}</div>
                      </div>
                      <div className="md:col-span-3"><Label className="text-xs">Harga</Label><Input type="number" value={v.price} onChange={(e) => setVariant(i, { price: e.target.value })} data-testid="admin-variant-price" /></div>
                      <div className="md:col-span-2"><Label className="text-xs">Harga Coret</Label><Input type="number" value={v.compare_at_price} onChange={(e) => setVariant(i, { compare_at_price: e.target.value })} placeholder="opsional" /></div>
                      <div className="md:col-span-1"><Label className="text-xs">Stok</Label><Input type="number" value={v.stock} onChange={(e) => setVariant(i, { stock: e.target.value })} data-testid="admin-variant-stock" /></div>
                      <div className="md:col-span-2"><Label className="text-xs">SKU</Label><Input value={v.sku} onChange={(e) => setVariant(i, { sku: e.target.value })} placeholder="auto" /></div>
                      <div className="md:col-span-1 flex justify-end">
                        <Button variant="ghost" size="icon" onClick={() => rmVariant(i)} aria-label="Hapus varian"><Trash2 className="h-4 w-4 text-rose-600" /></Button>
                      </div>
                    </div>
                  );
                })}
                {!(form.variants || []).length && (
                  <p className="text-sm text-muted-foreground">Belum ada varian. Definisikan dimensi lalu klik <span className="font-medium">Generate Kombinasi</span>.</p>
                )}
                <p className="text-xs text-muted-foreground">Harga display = varian termurah. SKU kosong = dibuat otomatis. Stok dikelola per SKU (SSOT).</p>
              </TabsContent>

              {/* MEDIA */}
              <TabsContent value="media" className="space-y-4 pt-4">
                <div className="rounded-xl border border-border/70 bg-muted/40 px-3 py-2.5 text-[11px] leading-relaxed text-muted-foreground">
                  Gambar produk diambil dari <strong className="text-foreground">Media Manager</strong> dan
                  disimpan di penyimpanan lokal server. Gambar pertama menjadi <strong className="text-foreground">gambar utama</strong> di
                  katalog. Seret kartu atau pakai tombol panah untuk mengurutkan.
                </div>

                <div className="flex flex-wrap gap-2">
                  <Button
                    type="button"
                    onClick={() => setPickerOpen(true)}
                    className="gap-2 rounded-lg"
                    data-testid={T.productMediaPick}
                  >
                    <ImagePlus className="h-4 w-4" /> Pilih dari Media Manager
                  </Button>
                  <input
                    ref={mediaFileRef}
                    type="file"
                    multiple
                    accept={MEDIA_ACCEPT}
                    className="hidden"
                    onChange={(e) => uploadProductImages(e.target.files)}
                    data-testid={T.productMediaFileInput}
                  />
                  <Button
                    type="button"
                    variant="secondary"
                    onClick={() => mediaFileRef.current?.click()}
                    disabled={mediaBusy}
                    className="gap-2 rounded-lg"
                    data-testid={T.productMediaUpload}
                  >
                    {mediaBusy ? <Loader2 className="h-4 w-4 animate-spin" /> : <Upload className="h-4 w-4" />}
                    {mediaBusy ? 'Mengunggah…' : 'Upload Gambar'}
                  </Button>
                </div>

                <div className="flex gap-2">
                  <Input
                    value={mediaUrl}
                    onChange={(e) => setMediaUrl(e.target.value)}
                    onKeyDown={(e) => { if (e.key === 'Enter') { e.preventDefault(); addFromUrl(); } }}
                    placeholder="Tempel URL gambar… (otomatis diunduh ke penyimpanan lokal)"
                    data-testid="admin-media-url-input"
                  />
                  <Button
                    type="button"
                    variant="secondary"
                    onClick={addFromUrl}
                    disabled={mediaBusy || !mediaUrl.trim()}
                    data-testid={T.mediaAdd}
                    className="shrink-0 gap-2 rounded-lg"
                  >
                    <Link2 className="h-4 w-4" /> Unduh & Tambah
                  </Button>
                </div>

                {form.images.length ? (
                  <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
                    {form.images.map((src, i) => (
                      <div
                        key={`${src}-${i}`}
                        className="group relative overflow-hidden rounded-xl border border-border/70 bg-card"
                        data-testid={T.productMediaTile}
                        draggable
                        onDragStart={(e) => { try { e.dataTransfer.setData('text/plain', String(i)); } catch (_) { /* noop */ } }}
                        onDragOver={(e) => e.preventDefault()}
                        onDrop={(e) => {
                          e.preventDefault();
                          const from = Number(e.dataTransfer.getData('text/plain'));
                          if (Number.isNaN(from) || from === i) return;
                          const next = [...form.images];
                          const [it] = next.splice(from, 1);
                          next.splice(i, 0, it);
                          set({ images: next });
                        }}
                      >
                        <span className="relative block aspect-square w-full bg-muted/40" style={CHECKER_STYLE}>
                          <SmartImage
                            src={src}
                            alt={`Gambar produk ${i + 1}`}
                            className="absolute inset-0 h-full w-full"
                            fit="cover"
                          />
                        </span>
                        {i === 0 ? (
                          <span className="absolute left-1.5 top-1.5 rounded bg-black px-1.5 py-0.5 text-[10px] font-medium text-white">
                            Utama
                          </span>
                        ) : null}
                        {!isLocalMedia(src) ? (
                          <span className="absolute right-1.5 top-1.5 rounded bg-amber-100 px-1.5 py-0.5 text-[9px] font-semibold text-amber-800">
                            EKSTERNAL
                          </span>
                        ) : null}
                        <div className="flex items-center justify-between gap-1 border-t border-border/60 bg-card px-1.5 py-1.5">
                          <div className="flex gap-0.5">
                            <Button
                              type="button"
                              size="icon"
                              variant="ghost"
                              className="h-7 w-7"
                              disabled={i === 0}
                              onClick={() => moveImage(i, -1)}
                              aria-label="Geser ke kiri"
                              data-testid={T.productMediaMoveLeft}
                            >
                              <ChevronLeft className="h-3.5 w-3.5" />
                            </Button>
                            <Button
                              type="button"
                              size="icon"
                              variant="ghost"
                              className="h-7 w-7"
                              disabled={i === form.images.length - 1}
                              onClick={() => moveImage(i, 1)}
                              aria-label="Geser ke kanan"
                              data-testid={T.productMediaMoveRight}
                            >
                              <ChevronRight className="h-3.5 w-3.5" />
                            </Button>
                          </div>
                          <div className="flex gap-0.5">
                            {i !== 0 ? (
                              <Button
                                type="button"
                                size="icon"
                                variant="ghost"
                                className="h-7 w-7"
                                onClick={() => setPrimary(i)}
                                aria-label="Jadikan gambar utama"
                                data-testid={T.mediaSetPrimary}
                              >
                                <Star className="h-3.5 w-3.5" />
                              </Button>
                            ) : null}
                            <Button
                              type="button"
                              size="icon"
                              variant="ghost"
                              className="h-7 w-7 text-rose-600 hover:text-rose-700"
                              onClick={() => rmImage(i)}
                              aria-label="Hapus dari galeri"
                              data-testid={T.productMediaRemove}
                            >
                              <Trash2 className="h-3.5 w-3.5" />
                            </Button>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="rounded-xl border border-dashed border-border bg-muted/30 px-4 py-10 text-center">
                    <ImagePlus className="mx-auto h-7 w-7 text-muted-foreground" aria-hidden="true" />
                    <p className="mt-2 text-sm font-medium text-foreground">Belum ada gambar produk</p>
                    <p className="mt-1 text-xs text-muted-foreground">
                      Klik “Pilih dari Media Manager” untuk memakai gambar yang sudah ada, atau
                      “Upload Gambar” untuk mengunggah dari perangkat Anda.
                    </p>
                  </div>
                )}

                <MediaPickerDialog
                  open={pickerOpen}
                  onOpenChange={setPickerOpen}
                  mode="multi"
                  title="Pilih Gambar Produk"
                  description="Pilih satu atau beberapa gambar dari pustaka media. Bisa juga langsung upload atau ambil dari URL."
                  onConfirm={(assets) => addImages(assets.map((a) => a.url))}
                />
              </TabsContent>

              {/* SEO */}
              <TabsContent value="seo" className="space-y-4 pt-4">
                <Field label={`Judul SEO (${(form.seo.title || '').length}/60)`}>
                  <Input value={form.seo.title} maxLength={70} onChange={(e) => set({ seo: { ...form.seo, title: e.target.value } })} data-testid={T.seoTitle} />
                </Field>
                <Field label={`Deskripsi SEO (${(form.seo.description || '').length}/160)`}>
                  <Textarea rows={3} value={form.seo.description} maxLength={180} onChange={(e) => set({ seo: { ...form.seo, description: e.target.value } })} />
                </Field>
                <Field label="Keyword (pisah koma)"><Input value={kwText} onChange={(e) => setKwText(e.target.value)} /></Field>
                <div className="rounded-xl border border-border p-3 bg-muted/40">
                  <div className="text-[#1a0dab] text-sm truncate">{form.seo.title || form.name || 'Judul Produk'}</div>
                  <div className="text-[#006621] text-xs">collectorparfum.com › parfum › {form.slug || 'slug'}</div>
                  <div className="text-xs text-muted-foreground line-clamp-2">{form.seo.description || form.description || 'Deskripsi ringkas produk…'}</div>
                </div>
              </TabsContent>
            </Tabs>
          </CardContent>
        </Card>

        {/* RIGHT: live preview */}
        <div className="lg:sticky lg:top-20">
          <ProductPreview product={previewProduct} />
        </div>
      </div>
    </div>
  );
}

const Field = ({ label, children }) => (
  <div className="space-y-1.5">
    <Label className="text-xs text-muted-foreground">{label}</Label>
    {children}
  </div>
);

// Chip multi-select untuk facet (occasions/characters). Ikon dari lucide via taxonomyIcons.
const FacetPicker = ({ label, items = [], selected = [], onToggle, testid }) => (
  <div className="space-y-1.5">
    <Label className="text-xs text-muted-foreground">{label}</Label>
    {items.length === 0 ? (
      <p className="text-xs text-muted-foreground">
        Belum ada taksonomi. Tambahkan lewat menu <span className="font-medium">Katalog</span> di sidebar admin.
      </p>
    ) : (
      <div className="flex flex-wrap gap-2" data-testid={testid}>
        {items.map((f) => {
          const active = (selected || []).includes(f.slug);
          const Icon = getFacetIcon(f.icon);
          return (
            <button
              key={f.slug}
              type="button"
              onClick={() => onToggle(f.slug)}
              data-testid={`${testid}-chip`}
              aria-pressed={active}
              title={f.desc || f.name}
              className={`inline-flex items-center gap-1.5 rounded-full border px-3 py-1.5 text-xs transition-colors ${
                active
                  ? 'bg-[color:var(--cp-brass)] text-white border-[color:var(--cp-brass)]'
                  : 'bg-background text-foreground border-border hover:border-[color:var(--cp-brass)]/60'
              }`}
            >
              <Icon className="h-3.5 w-3.5" strokeWidth={1.7} />
              <span className="capitalize">{f.name}</span>
            </button>
          );
        })}
      </div>
    )}
  </div>
);
