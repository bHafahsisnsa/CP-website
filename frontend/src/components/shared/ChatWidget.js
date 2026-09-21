// components/shared/ChatWidget.js — Live chat shell + fallback WhatsApp (Epic E7).
// V1: widget bubble + panel ringkas. Kirim pesan => membuka WhatsApp (wa.me) dengan
// konteks keranjang. Nomor WA & nama toko dibaca dari /api/settings (admin-configurable).
import React, { useEffect, useMemo, useState } from 'react';
import { MessageCircle, X, Send } from 'lucide-react';
import { track } from '../../services/analytics';
import { useCart } from '../../store/CartContext';
import { useCmsPreview } from '../../store/ContentContext';
import { useStoreSettings } from '../../store/SettingsContext';
import { growthTestIds as G } from '../../constants/testIds/growth';

const digits = (s) => String(s || '').replace(/[^0-9]/g, '');
const WA_BASE = 'https://wa.me';
const EMPTY_ITEMS = []; // referensi stabil -> hindari useMemo re-run tiap render

export const ChatWidget = () => {
  const [open, setOpen] = useState(false);
  const { settings } = useStoreSettings();
  const [draft, setDraft] = useState('');
  const cart = useCart();
  const preview = useCmsPreview();
  const cartItems = cart?.items;
  const items = useMemo(
    () => (Array.isArray(cartItems) ? cartItems : EMPTY_ITEMS),
    [cartItems],
  );

  const phone = digits(settings?.whatsapp_number);
  const store = settings?.store_name || 'Collector Parfum';

  const cartLine = useMemo(() => {
    if (!items.length) return '';
    const parts = items.slice(0, 5).map((i) => `• ${i.name} (${i.volumeMl}ml x${i.quantity})`);
    return `\n\nKeranjang saya:\n${parts.join('\n')}`;
  }, [items]);

  const sendWa = () => {
    const msg = draft.trim() || 'Halo, saya ingin bertanya tentang produk.';
    const text = encodeURIComponent(`Halo ${store}! ${msg}${cartLine}`);
    track('wa_click', { meta: { has_cart: cartLine ? 1 : 0 } });
    const url = `${phone ? `${WA_BASE}/${phone}` : WA_BASE}?text=${text}`;
    window.open(url, '_blank', 'noopener,noreferrer');
  };

  return (
    <>
      {preview ? null : (
        <>
      {/* Panel */}
      {open && (
        <div
          data-testid={G.chatPanel}
          className="cp-chat-widget fixed z-[60] bottom-24 right-4 sm:right-6 w-[calc(100vw-2rem)] max-w-sm rounded-2xl border border-black/10 bg-white shadow-2xl overflow-hidden"
        >
          <div className="flex items-center justify-between px-4 py-3 bg-[color:var(--cp-ink)] text-[color:var(--cp-paper)]">
            <div>
              <div className="cp-mono uppercase text-[10px] tracking-[0.22em] text-white/60">Bantuan</div>
              <div className="font-semibold text-sm">Chat dengan {store}</div>
            </div>
            <button
              type="button"
              onClick={() => setOpen(false)}
              data-testid={G.chatClose}
              aria-label="Tutup chat"
              className="h-8 w-8 rounded-full grid place-items-center hover:bg-white/10"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
          <div className="p-4 space-y-3">
            <div className="rounded-xl bg-black/5 px-3 py-2.5 text-sm text-black/75">
              Halo! Tim kami siap membantu memilih aroma yang tepat. Tulis pertanyaan Anda,
              lalu lanjutkan ke WhatsApp untuk respon cepat.
            </div>
            {items.length > 0 && (
              <div className="text-[11px] cp-mono uppercase tracking-[0.18em] text-black/45">
                {items.length} item di keranjang akan disertakan
              </div>
            )}
            <textarea
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              rows={3}
              data-testid={G.chatInput}
              placeholder="Tulis pesan Anda…"
              className="w-full resize-none rounded-xl border border-black/15 px-3 py-2.5 text-sm outline-none focus:border-black/40"
            />
            <button
              type="button"
              onClick={sendWa}
              data-testid={G.waButton}
              className="w-full inline-flex items-center justify-center gap-2 rounded-full bg-[#25D366] text-white font-medium text-sm py-3 hover:brightness-95 transition"
            >
              <Send className="h-4 w-4" /> Chat via WhatsApp
            </button>
            <p className="text-center text-[11px] text-black/40">Kami balas di jam kerja, 09.00–21.00 WIB.</p>
          </div>
        </div>
      )}

      {/* Launcher */}
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        data-testid={G.chatLauncher}
        aria-label="Buka chat bantuan"
        className="cp-chat-widget fixed z-[60] bottom-20 sm:bottom-6 right-4 sm:right-6 h-14 w-14 rounded-full bg-[color:var(--cp-ink)] text-[color:var(--cp-paper)] shadow-xl grid place-items-center hover:scale-105 active:scale-95 transition-transform"
      >
        {open ? <X className="h-6 w-6" /> : <MessageCircle className="h-6 w-6" />}
      </button>
      </>
      )}
    </>
  );
};
