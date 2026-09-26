import React from 'react';
import { Link } from 'react-router-dom';
import { Mail, Phone, MapPin, MessageCircle, Instagram, ArrowRight, Navigation, Clock } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Textarea } from '../components/ui/textarea';
import { toast } from 'sonner';
import { Reveal } from '../components/shared/Reveal';
import Seo from '../components/shared/Seo';
import { useContent } from '../store/ContentContext';
import { fetchStores } from '../services/stores';
import { StoreMap } from '../components/shared/StoreMap';

const ICON_FOR = {
  WhatsApp: MessageCircle, 'WhatsApp 1': MessageCircle, 'WhatsApp 2': MessageCircle,
  Email: Mail, Telepon: Phone, LINE: MessageCircle,
  Studio: MapPin, 'Toko Pusat': MapPin, Instagram,
};
const CONTACT_DEFAULT = {
  eyebrow: 'Kontak', title: 'Mari', title_accent: 'ngobrol.',
  subtitle: 'Tanya ketersediaan aroma, minta rekomendasi, atau berdiskusi soal pembelian dalam jumlah besar — tim kami siap membantu pada jam kerja.',
  response_note: 'Senin–Jumat 09.00–17.00 · Sabtu 09.00–14.00 WIB',
  items: [
    { label: 'WhatsApp 1', value: '+62 857-2000-0105', href: 'https://wa.me/6285720000105' },
    { label: 'WhatsApp 2', value: '+62 857-2013-7777', href: 'https://wa.me/6285720137777' },
    { label: 'Email', value: 'cs@collectorparfum.com', href: 'mailto:cs@collectorparfum.com' },
    { label: 'LINE', value: '@collectorparfum', href: 'https://line.me/R/ti/p/@collectorparfum' },
    { label: 'Instagram', value: '@collectorparfum', href: 'https://instagram.com/collectorparfum' },
    { label: 'Toko Pusat', value: 'Jl. Paledang No. 58, Bandung', href: 'https://www.google.com/maps?q=Collector+Parfum+Jl.+Paledang+No.58+Bandung' },
  ],
  map_embed: 'https://www.google.com/maps?q=Collector+Parfum+Jl.+Paledang+No.58+Bandung&output=embed',
  stores_eyebrow: 'Kunjungi Kami', stores_title: 'Toko', stores_accent: 'offline', stores_after: 'kami.',
  stores_link_label: 'Lihat semua lokasi', form_success: 'Tim kami akan membalas dalam 1x24 jam.',
};

export default function ContactPage() {
  const [form, setForm] = React.useState({ name: '', email: '', subject: '', message: '' });
  const [stores, setStores] = React.useState({ locations: [], config: {} });
  const c = useContent('contact', CONTACT_DEFAULT);
  const items = Array.isArray(c.items) && c.items.length ? c.items : CONTACT_DEFAULT.items;

  React.useEffect(() => {
    let cancelled = false;
    fetchStores().then((s) => { if (!cancelled) setStores(s); }).catch(() => {});
    return () => { cancelled = true; };
  }, []);

  const locations = stores.locations || [];
  const primary = locations[0];

  const submit = (e) => {
    e.preventDefault();
    if (!form.name || !form.email || !form.message) {
      toast.error('Mohon lengkapi nama, email, dan pesan Anda.');
      return;
    }
    toast.success('Pesan terkirim', { description: c.form_success });
    setForm({ name: '', email: '', subject: '', message: '' });
  };

  return (
    <div className="cp-container cp-section" data-testid="contact-page">
      <Seo title={`${c.title} ${c.title_accent} — Kontak Collector Parfum`} description={c.subtitle} />
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 lg:gap-16">
        <div className="lg:col-span-5">
          <div className="cp-eyebrow">{c.eyebrow}</div>
          <Reveal>
            <h1 className="cp-headline mt-2 text-4xl sm:text-6xl leading-none">
              {c.title} <em className="not-italic italic text-[color:var(--cp-brass)]">{c.title_accent}</em>
            </h1>
          </Reveal>
          <p className="mt-4 text-sm sm:text-base text-black/70 max-w-md">
            {c.subtitle}
          </p>
          <div className="mt-8 space-y-4">
            {items.map((it, i) => {
              const Icon = ICON_FOR[it.label] || MessageCircle;
              return (
                <a key={i} href={it.href || '#'} className="flex items-start gap-3 group">
                  <Icon className="h-5 w-5 text-[color:var(--cp-brass)] mt-1" />
                  <div>
                    <div className="cp-mono uppercase text-[10px] tracking-[0.22em] text-black/55">{it.label}</div>
                    <div className="text-sm sm:text-base cp-hover-underline">{it.value}</div>
                  </div>
                </a>
              );
            })}
          </div>
        </div>

        <div className="lg:col-span-7">
          <form onSubmit={submit} className="rounded-2xl border border-black/10 bg-[color:var(--cp-paper-warm)] p-6 sm:p-8" data-testid="contact-form">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <div className="cp-mono uppercase text-[10px] tracking-[0.22em] text-black/60 mb-1">Nama</div>
                <Input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} data-testid="contact-input-name" placeholder="Nama lengkap" className="bg-white h-11" />
              </div>
              <div>
                <div className="cp-mono uppercase text-[10px] tracking-[0.22em] text-black/60 mb-1">Email</div>
                <Input type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} data-testid="contact-input-email" placeholder="email@anda.com" className="bg-white h-11" />
              </div>
              <div className="sm:col-span-2">
                <div className="cp-mono uppercase text-[10px] tracking-[0.22em] text-black/60 mb-1">Subjek</div>
                <Input value={form.subject} onChange={(e) => setForm({ ...form, subject: e.target.value })} data-testid="contact-input-subject" placeholder="Rekomendasi aroma / ketersediaan / kerja sama" className="bg-white h-11" />
              </div>
              <div className="sm:col-span-2">
                <div className="cp-mono uppercase text-[10px] tracking-[0.22em] text-black/60 mb-1">Pesan</div>
                <Textarea rows={5} value={form.message} onChange={(e) => setForm({ ...form, message: e.target.value })} data-testid="contact-input-message" placeholder="Ceritakan kebutuhan Anda…" className="bg-white" />
              </div>
            </div>
            <div className="mt-6 flex items-center justify-between">
              <div className="cp-mono uppercase text-[10px] tracking-[0.22em] text-black/50">{c.response_note}</div>
              <Button type="submit" className="rounded-full h-11 px-6 bg-[color:var(--cp-ink)] text-[color:var(--cp-paper)] hover:bg-black" data-testid="contact-submit-button">
                Kirim Pesan <ArrowRight className="h-4 w-4 ml-2" />
              </Button>
            </div>
          </form>

          {primary ? (
            <div className="mt-6 rounded-2xl overflow-hidden aspect-[16/9] bg-[color:var(--cp-paper-fog)]" data-testid="contact-store-map">
              <StoreMap loc={primary} config={stores.config} className="h-full w-full" />
            </div>
          ) : c.map_embed ? (
            <div className="mt-6 rounded-2xl overflow-hidden aspect-[16/9] bg-[color:var(--cp-paper-fog)]">
              <iframe
                title="Peta Studio"
                src={c.map_embed}
                width="100%"
                height="100%"
                style={{ border: 0 }}
                allowFullScreen=""
                loading="lazy"
                referrerPolicy="no-referrer-when-downgrade"
              />
            </div>
          ) : null}
        </div>
      </div>

      {locations.length > 0 && (
        <section className="mt-16 sm:mt-24" data-testid="contact-store-locations">
          <div className="flex items-end justify-between flex-wrap gap-4 mb-8">
            <div>
              <div className="cp-eyebrow">{c.stores_eyebrow}</div>
              <Reveal>
                <h2 className="cp-headline text-3xl sm:text-5xl mt-2 leading-none">
                  {c.stores_title} <em className="not-italic italic text-[color:var(--cp-brass)]">{c.stores_accent}</em> {c.stores_after}
                </h2>
              </Reveal>
            </div>
            <Link to="/lokasi" className="inline-flex items-center gap-1 cp-mono uppercase text-[11px] tracking-[0.2em] text-black/60 hover:text-black">
              {c.stores_link_label} ({locations.length}) <ArrowRight className="h-3.5 w-3.5" />
            </Link>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {locations.map((loc) => (
              <div key={loc.id} className="rounded-2xl border border-black/10 bg-[color:var(--cp-paper-warm)] p-5 flex flex-col">
                <div className="cp-headline text-lg leading-tight">{loc.name}</div>
                <div className="mt-3 space-y-2 text-sm text-black/70 flex-1">
                  <div className="flex items-start gap-2"><MapPin className="h-4 w-4 text-[color:var(--cp-brass)] mt-0.5 flex-shrink-0" /><span>{loc.address}</span></div>
                  {loc.hours ? <div className="flex items-start gap-2"><Clock className="h-4 w-4 text-[color:var(--cp-brass)] mt-0.5 flex-shrink-0" /><span>{loc.hours}</span></div> : null}
                </div>
                <a
                  href={loc.map_url || `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(loc.maps_query || loc.address)}`}
                  target="_blank" rel="noopener noreferrer" className="mt-4"
                >
                  <Button variant="outline" className="w-full rounded-full h-10 border-black/20 gap-2"><Navigation className="h-4 w-4" /> Petunjuk Arah</Button>
                </a>
              </div>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
