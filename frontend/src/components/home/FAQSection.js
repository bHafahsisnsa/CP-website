import React from 'react';
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '../ui/accordion';
import { FAQ_ITEMS } from '../../data/products';
import { Reveal } from '../shared/Reveal';
import { Link } from 'react-router-dom';
import { ArrowRight } from 'lucide-react';
import { useContent } from '../../store/ContentContext';

import { HOME_IMAGES } from '../../lib/realImages';

const FAQ_IMAGE = HOME_IMAGES.faq.image;
const FAQ_DEFAULT = {
  eyebrow: 'Pusat Bantuan', title: 'Pertanyaan yang', title_accent: 'sering ditanya.',
  cta_label: 'Hubungi Tim Kami', cta_to: '/kontak', items: FAQ_ITEMS,
};

export const FAQSection = () => {
  const c = useContent('faq', FAQ_DEFAULT);
  const items = (Array.isArray(c.items) && c.items.length ? c.items : FAQ_ITEMS);
  return (
    <section className="cp-section-md" data-testid="home-faq">
      <div className="cp-container-wide grid grid-cols-1 lg:grid-cols-12 gap-8 lg:gap-12 items-start">
        <div className="lg:col-span-5">
          <div className="sticky top-28">
            <div className="cp-eyebrow">{c.eyebrow}</div>
            <Reveal>
              <h2 className="cp-headline mt-2 text-3xl sm:text-5xl lg:text-6xl">
                {c.title} <em className="not-italic italic text-[color:var(--cp-brass)]">{c.title_accent}</em>
              </h2>
            </Reveal>
            <Reveal delay={0.1}>
              <div className="mt-6 aspect-[4/5] rounded-2xl overflow-hidden bg-[color:var(--cp-paper-fog)]">
                <img src={FAQ_IMAGE} alt="Detail parfum" className="h-full w-full object-cover" />
              </div>
            </Reveal>
            <Reveal delay={0.15}>
              <Link
                to={c.cta_to || '/kontak'}
                className="mt-6 inline-flex items-center gap-2 cp-mono uppercase text-[11px] tracking-[0.22em] cp-hover-underline"
              >
                {c.cta_label} <ArrowRight className="h-4 w-4" />
              </Link>
            </Reveal>
          </div>
        </div>

        <div className="lg:col-span-7">
          <Accordion type="single" collapsible className="w-full" data-testid="home-faq-accordion">
            {items.map((item, i) => (
              <AccordionItem key={i} value={`item-${i}`} data-testid="faq-item" className="border-b border-black/10 last:border-0">
                <AccordionTrigger
                  className="cp-headline text-xl sm:text-2xl text-left hover:no-underline py-5"
                  data-testid="home-faq-trigger"
                >
                  {item.q}
                </AccordionTrigger>
                <AccordionContent className="text-sm sm:text-base text-black/70 pb-5 leading-relaxed">
                  {item.a}
                </AccordionContent>
              </AccordionItem>
            ))}
          </Accordion>
        </div>
      </div>
    </section>
  );
};
