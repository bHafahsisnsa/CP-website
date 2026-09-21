import React from 'react';
import { ShieldCheck, Loader2 } from 'lucide-react';
import { Button } from '../ui/button';
import { formatIDR } from '../../lib/format';

/**
 * Ringkasan pesanan (aside sticky) — dipisah dari CheckoutPage agar halaman tetap
 * ramping (guardrail <=500 baris). Semua angka berasal dari state halaman induk;
 * komponen ini murni presentasional.
 */
export default function CheckoutSummary({
  cart, checkoutDiscount, selectedShipping, shipPrice, codFee, total,
  placing, canPlace, onPlaceOrder,
}) {
  return (
    <aside className="lg:col-span-4" data-testid="checkout-summary-card">
      <div className="lg:sticky lg:top-28 rounded-2xl border border-black/10 bg-[color:var(--cp-paper-warm)] p-5 sm:p-6">
        <div className="cp-mono uppercase text-[11px] tracking-[0.22em] text-black/60 mb-3">Ringkasan Pesanan</div>
        <div className="space-y-2 text-sm">
          <div className="flex items-center justify-between">
            <span className="text-black/60">Subtotal ({cart.totalQty} item)</span>
            <span className="cp-mono">{formatIDR(cart.subtotal)}</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-black/60">Diskon Voucher</span>
            <span className="cp-mono text-[color:var(--cp-brass)]" data-testid="checkout-discount-amount">- {formatIDR(checkoutDiscount)}</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-black/60">Ongkir{selectedShipping ? ` (${selectedShipping.name})` : ''}</span>
            <span className="cp-mono">{shipPrice === 0 ? 'GRATIS' : formatIDR(shipPrice)}</span>
          </div>
          {codFee > 0 && (
            <div className="flex items-center justify-between">
              <span className="text-black/60">Biaya COD</span>
              <span className="cp-mono">{formatIDR(codFee)}</span>
            </div>
          )}
        </div>
        <hr className="my-5 border-black/10" />
        <div className="flex items-center justify-between">
          <span className="cp-mono uppercase text-[11px] tracking-[0.22em]">Total Pembayaran</span>
          <span className="cp-mono text-xl font-semibold" data-testid="checkout-total-amount">{formatIDR(total)}</span>
        </div>

        <Button
          onClick={onPlaceOrder}
          disabled={placing || !canPlace}
          data-testid="checkout-place-order-button"
          className="mt-5 w-full h-12 rounded-full cp-btn-gold disabled:opacity-60"
        >
          {placing ? (<><Loader2 className="h-4 w-4 mr-2 animate-spin" /> Memproses…</>) : 'Buat Pesanan'}
        </Button>

        <div className="mt-3 flex items-center justify-center gap-2 cp-mono uppercase text-[10px] tracking-[0.22em] text-black/50">
          <ShieldCheck className="h-3.5 w-3.5" /> Transaksi aman & terenkripsi
        </div>
        <div className="mt-4 text-[11px] text-black/50 leading-relaxed">
          Dengan menekan “Buat Pesanan”, Anda setuju dengan Syarat & Ketentuan serta Kebijakan Privasi Collector Parfum.
        </div>
      </div>
    </aside>
  );
}
