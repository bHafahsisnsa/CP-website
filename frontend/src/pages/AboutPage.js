import React from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { ArrowRight } from 'lucide-react';
import { Reveal } from '../components/shared/Reveal';
import { BigMarquee } from '../components/shared/MarqueeStrip';
import Seo from '../components/shared/Seo';
import { useContent } from '../store/ContentContext';

import { moodBoard } from '../lib/moodArt';

const ABOUT_HERO = moodBoard({ title: 'Cerita Kami', subtitle: 'EDITORIAL · BANDUNG', mood: 'amber', ratio: '4:5', accentText: 'MANIFESTO' });
const ABOUT_2 = moodBoard({ title: 'Refill', subtitle: 'TELITI · SEJAK 1970', mood: 'woody', ratio: '4:5', accentText: 'JOURNEY' });

const ABOUT_DEFAULT = {
  eyebrow: 'Cerita Kami', title: 'Refill parfum pertama', title_accent: 'di Indonesia, sejak 1970.',
  intro: 'Pada 8 September 1970, usaha refill parfum pertama di Indonesia didirikan di Jalan Kolektor, Bandung. Karena jalannya sempit, toko berpindah ke Jalan Paledang No. 14, lalu memantapkan nama menjadi Collector Parfum dan menetap di Jalan Paledang No. 58, Bandung.',
  hero_image: '', marquee: 'Refill Perfume Distributor Since 1970',
  values_eyebrow: 'Nilai Kami', values_title: 'Biang pilihan, harga bersaing.',
  values: [
    { title: 'Biang Impor Pilihan', desc: 'Kami sangat teliti memilih produk biang unggulan (impor) sebelum dipasarkan.' },
    { title: 'Harga Bersaing', desc: 'Variasi aroma yang luas dengan harga relatif murah dan bersaing.' },
    { title: 'Dipercaya sebagai Supplier', desc: 'Selain ritel, kami melayani pelanggan yang menjadikan kami supplier parfum refill.' },
    { title: '3 Cabang di Bandung', desc: 'Paledang, Pasir Kaliki, dan Gatot Subroto — cium langsung sebelum membeli.' },
  ],
  journey_eyebrow: 'Perjalanan', journey_title: 'Dari Jalan Kolektor ke tiga cabang.', journey_image: '',
  timeline: [
    { year: '1970', title: 'Berdiri di Jalan Kolektor', text: '8 September 1970 — untuk pertama kalinya di Indonesia, usaha refill parfum didirikan di Jalan Kolektor, Bandung.' },
    { year: 'Awal', title: 'Pindah ke Paledang No. 14', text: 'Toko pertama berada di jalan yang sempit, sehingga kami berpindah ke Jalan Paledang No. 14.' },
    { year: 'Kini', title: 'Menetap di Paledang No. 58', text: 'Nama Collector Parfum dimantapkan dan toko menetap di Jalan Paledang No. 58, Bandung.' },
    { year: 'Berkembang', title: 'Cabang Pasir Kaliki & Gatot Subroto', text: 'Respons baik masyarakat dan kepercayaan sebagai supplier mendorong kami membuka cabang di Jalan Pasirkaliki No. 148A dan Jalan Gatot Subroto No. 271, Bandung.' },
  ],
  cta_eyebrow: 'Mulai perjalanan', cta_title: 'Temukan aroma yang', cta_accent: 'berbicara tentangmu.',
  cta_label: 'Lihat Katalog', cta_to: '/shop',
};

export default function AboutPage() {
  const c = useContent('about', ABOUT_DEFAULT);
  const values = Array.isArray(c.values) && c.values.length ? c.values : ABOUT_DEFAULT.values;
  const timeline = Array.isArray(c.timeline) && c.timeline.length ? c.timeline : ABOUT_DEFAULT.timeline;
  return (
    <div data-testid="about-page">
      <Seo title={`${c.title} ${c.title_accent} — Collector Parfum`} description={c.intro} />
      {/* Hero */}
      <section className="relative overflow-hidden bg-[color:var(--cp-paper-warm)]">
        <div className="cp-container cp-section grid grid-cols-1 lg:grid-cols-12 gap-8 lg:gap-12 items-end">
          <div className="lg:col-span-7">
            <div className="cp-eyebrow">{c.eyebrow}</div>
            <Reveal>
              <h1 className="cp-headline mt-2 text-[12vw] sm:text-[8vw] lg:text-[6vw] leading-[0.95]">
                {c.title} <em className="not-italic italic text-[color:var(--cp-brass)]">{c.title_accent}</em>
              </h1>
            </Reveal>
            <Reveal delay={0.1}>
              <p className="mt-5 max-w-lg text-sm sm:text-base text-black/70 leading-relaxed">
                {c.intro}
              </p>
            </Reveal>
          </div>
          <div className="lg:col-span-5">
            <motion.div
              initial={{ opacity: 0, scale: 1.05 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 1.2, ease: [0.22, 1, 0.36, 1] }}
              className="relative aspect-[4/5] rounded-2xl overflow-hidden bg-[color:var(--cp-paper-fog)]"
            >
              <img src={c.hero_image || ABOUT_HERO} alt="Botol parfum editorial" className="h-full w-full object-cover" />
            </motion.div>
          </div>
        </div>
      </section>

      <BigMarquee text={c.marquee || 'Aroma yang membekas'} />

      {/* Values */}
      <section className="cp-section bg-[color:var(--cp-paper-fog)]">
        <div className="cp-container grid grid-cols-1 lg:grid-cols-12 gap-8 lg:gap-16">
          <div className="lg:col-span-4">
            <Reveal>
              <div className="cp-eyebrow">{c.values_eyebrow}</div>
              <h2 className="cp-headline mt-2 text-4xl sm:text-5xl">{c.values_title}</h2>
            </Reveal>
          </div>
          <div className="lg:col-span-8 grid grid-cols-1 sm:grid-cols-2 gap-6">
            {values.map((v, i) => (
              <Reveal key={i} delay={i * 0.08}>
                <div className="rounded-2xl border border-black/10 bg-[color:var(--cp-paper-warm)] p-6 h-full">
                  <div className="cp-mono uppercase text-[10px] tracking-[0.22em] text-black/50">0{i + 1}</div>
                  <div className="cp-headline text-2xl mt-2">{v.title}</div>
                  <div className="text-sm text-black/70 mt-2">{v.desc}</div>
                </div>
              </Reveal>
            ))}
          </div>
        </div>
      </section>

      {/* Timeline / story */}
      <section className="cp-section">
        <div className="cp-container grid grid-cols-1 lg:grid-cols-12 gap-8 lg:gap-16">
          <div className="lg:col-span-5">
            <Reveal>
              <div className="cp-eyebrow">{c.journey_eyebrow}</div>
              <h2 className="cp-headline mt-2 text-4xl sm:text-5xl">{c.journey_title}</h2>
            </Reveal>
            <Reveal delay={0.1}>
              <div className="mt-6 rounded-2xl overflow-hidden aspect-[4/5] bg-[color:var(--cp-paper-fog)]">
                <img src={c.journey_image || ABOUT_2} alt="Detail botol" className="h-full w-full object-cover" />
              </div>
            </Reveal>
          </div>
          <div className="lg:col-span-7 space-y-6">
            {timeline.map((t, i) => (
              <Reveal key={i} delay={i * 0.06}>
                <div className="grid grid-cols-12 gap-4 border-b border-black/10 pb-6">
                  <div className="col-span-3 cp-mono uppercase text-[11px] tracking-[0.22em] text-black/60 pt-1">{t.year}</div>
                  <div className="col-span-9">
                    <div className="cp-headline text-2xl">{t.title}</div>
                    <div className="text-sm text-black/70 mt-1">{t.text}</div>
                  </div>
                </div>
              </Reveal>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="cp-section bg-[color:var(--cp-ink)] text-[color:var(--cp-paper)]">
        <div className="cp-container grid grid-cols-1 lg:grid-cols-12 gap-8 items-end">
          <div className="lg:col-span-8">
            <div className="cp-mono uppercase text-[11px] tracking-[0.22em] text-white/60">{c.cta_eyebrow}</div>
            <Reveal>
              <h2 className="cp-headline text-4xl sm:text-6xl mt-2">
                {c.cta_title} <em className="not-italic italic text-[color:var(--cp-brass)]">{c.cta_accent}</em>
              </h2>
            </Reveal>
          </div>
          <div className="lg:col-span-4 lg:text-right">
            <Link to={c.cta_to || '/shop'} className="inline-flex items-center gap-2 cp-mono uppercase text-[11px] tracking-[0.22em] border border-white/25 rounded-full px-5 py-3 hover:bg-white/5">
              {c.cta_label} <ArrowRight className="h-4 w-4" />
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}
