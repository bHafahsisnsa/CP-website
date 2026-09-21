// pages/admin/AdminContentPage.js — CMS Visual Builder (Epic E9+).
// Layout tiga kolom: nav section (kiri) | form editor (tengah) | iframe live preview (kanan).
// Live sync: setiap edit draft mem-broadcast postMessage {type:'CMS_DRAFT', content} ke iframe.
// Iframe dimuat dgn ?cms_preview=1 — ContentContext akan meng-override konten tanpa DB write.
import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import {
  ExternalLink, Save, Loader2, Undo2, Search, Monitor, Tablet, Smartphone,
  Home, Info, Mail, ShoppingBag, RefreshCw, Eye, EyeOff, CheckCircle2,
  History, RotateCcw, X,
} from 'lucide-react';
import { toast } from 'sonner';
import { getContentSchema, getContentAdmin, updateContentSection,
         listContentRevisions, revertContentSection } from '../../services/admin';
import { PageHeader } from '../../components/admin/adminUi';
import { ContentForm } from '../../components/admin/ContentForm';
import { growthTestIds as G } from '../../constants/testIds/growth';
import { Button } from '../../components/ui/button';
import { Card, CardContent } from '../../components/ui/card';
import { Input } from '../../components/ui/input';
import { Badge } from '../../components/ui/badge';

// Tautan preview cepat per section (auto-navigate iframe ke halaman relevan).
const SECTION_ROUTE = {
  hero: '/', announcement: '/', featured_categories: '/', featured_products: '/',
  brand_promise: '/', video_showcase: '/', ig_gallery: '/', testimonials: '/',
  faq_home: '/', cta_home: '/',
  about: '/tentang', contact: '/kontak',
  header: '/', footer: '/',
  shop_intro: '/shop', product_detail: '/shop',
  auth_promo: '/login', account_help: '/akun',
};

const DEVICES = [
  { id: 'desktop', label: 'Desktop', icon: Monitor, width: '100%', maxW: '1440px' },
  { id: 'tablet', label: 'Tablet', icon: Tablet, width: '820px', maxW: '820px' },
  { id: 'mobile', label: 'Mobile', icon: Smartphone, width: '390px', maxW: '390px' },
];

const QUICK_ROUTES = [
  { path: '/', label: 'Beranda', icon: Home },
  { path: '/shop', label: 'Toko', icon: ShoppingBag },
  { path: '/tentang', label: 'Tentang', icon: Info },
  { path: '/kontak', label: 'Kontak', icon: Mail },
];

const isEqual = (a, b) => JSON.stringify(a) === JSON.stringify(b);

export default function AdminContentPage() {
  const [schema, setSchema] = useState([]);
  const [content, setContent] = useState({});
  const [active, setActive] = useState(null);
  const [draft, setDraft] = useState({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [query, setQuery] = useState('');
  const [device, setDevice] = useState('desktop');
  const [showPreview, setShowPreview] = useState(true);
  const [previewPath, setPreviewPath] = useState('/');
  const [iframeKey, setIframeKey] = useState(0);
  const [iframeReady, setIframeReady] = useState(false);
  const [historyOpen, setHistoryOpen] = useState(false);
  const [revisions, setRevisions] = useState([]);
  const [revLoading, setRevLoading] = useState(false);
  const iframeRef = useRef(null);

  const load = useCallback(async (keepActive) => {
    setLoading(true);
    try {
      const [sc, ct] = await Promise.all([getContentSchema(), getContentAdmin()]);
      setSchema(sc);
      setContent(ct);
      const first = keepActive || (sc[0] && sc[0].key);
      setActive(first);
      setDraft({ ...(ct[first] || {}) });
    } catch (e) {
      toast.error('Gagal memuat konten.');
    } finally {
      setLoading(false);
    }
  }, []);
  // `load` dibuat dengan useCallback([]) sehingga referensinya stabil -> aman sebagai dep.
  useEffect(() => { load(); }, [load]);

  const groups = useMemo(() => {
    const g = {};
    schema
      .filter((s) => !query || s.label.toLowerCase().includes(query.toLowerCase()) || s.key.includes(query.toLowerCase()))
      .forEach((s) => { (g[s.group] = g[s.group] || []).push(s); });
    return g;
  }, [schema, query]);

  const activeSection = schema.find((s) => s.key === active);
  const dirty = active ? !isEqual(draft, content[active] || {}) : false;

  // Kirim draft ke iframe kapanpun draft/section/route berubah.
  const broadcastDraft = useCallback(() => {
    if (!iframeRef.current || !iframeReady || !active) return;
    const merged = { ...(content || {}), [active]: draft };
    try {
      iframeRef.current.contentWindow.postMessage(
        { type: 'CMS_DRAFT', content: merged },
        '*'
      );
    } catch (e) { /* noop */ }
  }, [draft, active, content, iframeReady]);

  useEffect(() => { broadcastDraft(); }, [broadcastDraft]);

  // Terima sinyal READY dari iframe.
  useEffect(() => {
    const onMsg = (ev) => {
      const data = ev && ev.data;
      if (data && data.type === 'CMS_PREVIEW_READY') {
        setIframeReady(true);
      }
    };
    window.addEventListener('message', onMsg);
    return () => window.removeEventListener('message', onMsg);
  }, []);

  const select = (key) => {
    if (dirty && !window.confirm('Perubahan belum disimpan. Buang perubahan?')) return;
    setActive(key);
    setDraft({ ...(content[key] || {}) });
    const route = SECTION_ROUTE[key] || '/';
    if (route !== previewPath) setPreviewPath(route);
  };

  const save = async () => {
    if (!active) return;
    setSaving(true);
    try {
      const res = await updateContentSection(active, draft);
      setContent((c) => ({ ...c, [active]: res.data }));
      setDraft({ ...res.data });
      toast.success('Konten disimpan & tayang di storefront.');
      // Refresh iframe untuk menampilkan versi terpublish (bukan draft override).
      setIframeKey((k) => k + 1);
      setIframeReady(false);
    } catch (e) {
      toast.error('Gagal menyimpan konten.');
    } finally {
      setSaving(false);
    }
  };

  const discard = () => {
    if (!active) return;
    setDraft({ ...(content[active] || {}) });
    toast.info('Perubahan dibuang.');
  };

  const openHistory = async () => {
    if (!active) return;
    setHistoryOpen(true);
    setRevLoading(true);
    try {
      const res = await listContentRevisions(active);
      setRevisions(res.revisions || []);
    } catch (e) {
      toast.error('Gagal memuat riwayat.');
    } finally {
      setRevLoading(false);
    }
  };

  const applyRevision = async (payload, label) => {
    if (!active) return;
    try {
      const res = await revertContentSection(active, payload);
      setContent((c) => ({ ...c, [active]: res.data }));
      setDraft({ ...res.data });
      toast.success(`Dikembalikan ke ${label}.`);
      setIframeKey((k) => k + 1); setIframeReady(false);
      // Reload revisions setelah revert (revert bikin revisi baru dari state sebelumnya)
      const r = await listContentRevisions(active);
      setRevisions(r.revisions || []);
    } catch (e) {
      toast.error('Gagal revert.');
    }
  };

  const dev = DEVICES.find((d) => d.id === device) || DEVICES[0];

  const iframeSrc = `${previewPath}${previewPath.includes('?') ? '&' : '?'}cms_preview=1&_k=${iframeKey}`;

  return (
    <div data-testid={G.cmsPage} className="space-y-4">
      <PageHeader
        title="Konten Situs — Visual Builder"
        description="Edit semua elemen storefront dengan preview langsung. Perubahan real-time, publish saat siap."
        actions={
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              onClick={() => setShowPreview((v) => !v)}
              className="gap-2"
              data-testid="cms-toggle-preview"
            >
              {showPreview ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              {showPreview ? 'Sembunyikan Preview' : 'Tampilkan Preview'}
            </Button>
            <a href={previewPath} target="_blank" rel="noopener noreferrer" data-testid={G.cmsPreview}>
              <Button variant="outline" className="gap-2"><ExternalLink className="h-4 w-4" /> Buka di Tab Baru</Button>
            </a>
          </div>
        }
      />

      {loading ? (
        <div className="py-24 grid place-items-center text-muted-foreground">
          <Loader2 className="h-6 w-6 animate-spin" />
        </div>
      ) : (
        <div className={`grid gap-4 ${showPreview ? 'lg:grid-cols-[260px_1fr_1fr]' : 'lg:grid-cols-[260px_1fr]'}`}>
          {/* KIRI — Section navigator */}
          <div className="space-y-3" data-testid={G.cmsSectionList}>
            <div className="relative">
              <Search className="h-4 w-4 absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
              <Input
                placeholder="Cari section…"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                className="pl-9 h-9"
                data-testid="cms-search"
              />
            </div>
            <div className="space-y-4 max-h-[calc(100vh-260px)] overflow-y-auto pr-1">
              {Object.entries(groups).map(([group, items]) => (
                <div key={group}>
                  <div className="text-[11px] uppercase tracking-[0.16em] text-muted-foreground mb-2 px-1">{group}</div>
                  <div className="space-y-1">
                    {items.map((s) => {
                      const isActive = active === s.key;
                      const isEdited = !isEqual(content[s.key] || {}, (s.default || {}));
                      return (
                        <button
                          key={s.key}
                          type="button"
                          onClick={() => select(s.key)}
                          data-testid={`cms-section-${s.key}`}
                          className={`w-full text-left px-3 py-2 rounded-lg text-sm transition-colors flex items-center justify-between gap-2 ${
                            isActive ? 'bg-foreground text-background font-medium' : 'hover:bg-muted'
                          }`}
                        >
                          <span className="truncate">{s.label}</span>
                          {isEdited && !isActive && (
                            <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 shrink-0" title="Sudah diedit" />
                          )}
                        </button>
                      );
                    })}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* TENGAH — Editor */}
          <Card className="border-border/70 h-fit sticky top-4">
            <CardContent className="p-5">
              {activeSection ? (
                <>
                  <div className="flex items-start justify-between mb-4 pb-4 border-b border-border/60 gap-3">
                    <div className="min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <div className="font-semibold truncate">{activeSection.label}</div>
                        {dirty ? (
                          <Badge variant="outline" className="border-amber-300 text-amber-700 bg-amber-50 text-[10px] gap-1">
                            <span className="h-1.5 w-1.5 rounded-full bg-amber-500 animate-pulse" />
                            Belum tersimpan
                          </Badge>
                        ) : (
                          <Badge variant="outline" className="border-emerald-300 text-emerald-700 bg-emerald-50 text-[10px] gap-1">
                            <CheckCircle2 className="h-3 w-3" />
                            Tersimpan
                          </Badge>
                        )}
                      </div>
                      <div className="text-xs text-muted-foreground mt-0.5">{activeSection.group} · <span className="font-mono">{activeSection.key}</span></div>
                    </div>
                    <div className="flex items-center gap-2 shrink-0">
                      <Button variant="ghost" size="sm" onClick={openHistory} className="gap-1.5 text-muted-foreground" data-testid="cms-history-open" title="Riwayat perubahan">
                        <History className="h-3.5 w-3.5" /> Riwayat
                      </Button>
                      {dirty && (
                        <Button variant="ghost" size="sm" onClick={discard} className="gap-1.5 text-muted-foreground" data-testid="cms-discard">
                          <Undo2 className="h-3.5 w-3.5" /> Buang
                        </Button>
                      )}
                      <Button onClick={save} disabled={saving || !dirty} className="gap-2" data-testid={G.cmsSave}>
                        {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
                        Publish
                      </Button>
                    </div>
                  </div>
                  <div className="max-h-[calc(100vh-320px)] overflow-y-auto pr-1">
                    <ContentForm fields={activeSection.fields} value={draft} onChange={setDraft} />
                  </div>
                </>
              ) : (
                <div className="text-muted-foreground text-sm py-8 text-center">Pilih section untuk mengedit.</div>
              )}
            </CardContent>
          </Card>

          {/* KANAN — Live Preview */}
          {showPreview && (
            <div className="space-y-3 sticky top-4 h-fit">
              <Card className="border-border/70">
                <div className="p-3 border-b border-border/60 flex items-center justify-between gap-2 flex-wrap">
                  <div className="flex items-center gap-1">
                    {QUICK_ROUTES.map((r) => {
                      const Icon = r.icon;
                      return (
                        <button
                          key={r.path}
                          type="button"
                          onClick={() => { setPreviewPath(r.path); setIframeReady(false); setIframeKey((k) => k + 1); }}
                          className={`px-2 py-1 rounded-md text-xs flex items-center gap-1.5 transition-colors ${
                            previewPath.split('?')[0] === r.path ? 'bg-foreground text-background' : 'hover:bg-muted'
                          }`}
                          title={r.label}
                        >
                          <Icon className="h-3.5 w-3.5" />
                          <span className="hidden xl:inline">{r.label}</span>
                        </button>
                      );
                    })}
                  </div>
                  <div className="flex items-center gap-1">
                    {DEVICES.map((d) => {
                      const Icon = d.icon;
                      return (
                        <button
                          key={d.id}
                          type="button"
                          onClick={() => setDevice(d.id)}
                          className={`p-1.5 rounded-md transition-colors ${
                            device === d.id ? 'bg-foreground text-background' : 'hover:bg-muted'
                          }`}
                          title={d.label}
                        >
                          <Icon className="h-3.5 w-3.5" />
                        </button>
                      );
                    })}
                    <button
                      type="button"
                      onClick={() => { setIframeReady(false); setIframeKey((k) => k + 1); }}
                      className="p-1.5 rounded-md hover:bg-muted"
                      title="Muat ulang preview"
                    >
                      <RefreshCw className="h-3.5 w-3.5" />
                    </button>
                  </div>
                </div>
                <div className="p-3 bg-muted/40 flex justify-center">
                  <div
                    className="bg-background border border-border/70 rounded-lg overflow-hidden shadow-sm transition-all"
                    style={{ width: dev.width, maxWidth: dev.maxW }}
                  >
                    <iframe
                      key={iframeKey}
                      ref={iframeRef}
                      src={iframeSrc}
                      title="Live Preview"
                      className="w-full block"
                      style={{ height: 'calc(100vh - 260px)', minHeight: 480 }}
                      onLoad={() => { /* iframe akan post CMS_PREVIEW_READY */ }}
                    />
                  </div>
                </div>
                <div className="px-3 py-2 border-t border-border/60 flex items-center justify-between text-xs text-muted-foreground">
                  <span className="font-mono truncate">{previewPath}</span>
                  <span className="flex items-center gap-1.5">
                    <span className={`h-1.5 w-1.5 rounded-full ${iframeReady ? 'bg-emerald-500' : 'bg-amber-500 animate-pulse'}`} />
                    {iframeReady ? (dirty ? 'Menampilkan draft' : 'Sinkron') : 'Memuat…'}
                  </span>
                </div>
              </Card>
            </div>
          )}
        </div>
      )}

      {/* HISTORY DRAWER */}
      {historyOpen && (
        <div className="fixed inset-0 z-50 flex" data-testid="cms-history-drawer">
          <div className="flex-1 bg-black/40" onClick={() => setHistoryOpen(false)} />
          <div className="w-full max-w-md bg-background border-l border-border shadow-2xl flex flex-col">
            <div className="p-4 border-b border-border/70 flex items-center justify-between">
              <div>
                <div className="font-semibold flex items-center gap-2"><History className="h-4 w-4" /> Riwayat Perubahan</div>
                <div className="text-xs text-muted-foreground">{activeSection?.label} · maksimal 20 revisi terakhir</div>
              </div>
              <Button variant="ghost" size="icon" onClick={() => setHistoryOpen(false)}><X className="h-4 w-4" /></Button>
            </div>
            <div className="p-3 border-b border-border/70">
              <Button
                variant="outline"
                size="sm"
                className="w-full gap-2"
                onClick={() => applyRevision({ to_default: true }, 'default pabrik')}
                data-testid="cms-revert-default"
              >
                <RotateCcw className="h-3.5 w-3.5" /> Kembalikan ke Default Pabrik
              </Button>
            </div>
            <div className="flex-1 overflow-y-auto p-3 space-y-2">
              {revLoading ? (
                <div className="py-8 grid place-items-center text-muted-foreground"><Loader2 className="h-5 w-5 animate-spin" /></div>
              ) : revisions.length === 0 ? (
                <div className="text-sm text-muted-foreground text-center py-8">Belum ada revisi tersimpan.</div>
              ) : (
                revisions.map((rev, idx) => {
                  const preview = JSON.stringify(rev.data).slice(0, 140);
                  const when = new Date(rev.created_at).toLocaleString('id-ID', {
                    dateStyle: 'medium', timeStyle: 'short',
                  });
                  return (
                    <div key={rev.id} className="border border-border/70 rounded-lg p-3 space-y-2 hover:bg-muted/40 transition-colors">
                      <div className="flex items-center justify-between gap-2">
                        <div className="text-xs font-medium">Revisi #{revisions.length - idx}</div>
                        <div className="text-[10px] cp-mono text-muted-foreground">{when}</div>
                      </div>
                      <div className="text-xs text-muted-foreground font-mono truncate" title={preview}>{preview}…</div>
                      <div className="flex justify-end">
                        <Button
                          variant="outline"
                          size="sm"
                          className="gap-1.5 text-xs"
                          onClick={() => applyRevision({ revision_id: rev.id }, `revisi ${when}`)}
                          data-testid={`cms-revert-${rev.id}`}
                        >
                          <RotateCcw className="h-3 w-3" /> Kembalikan
                        </Button>
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
