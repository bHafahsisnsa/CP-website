import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { ArrowRight, Ticket } from 'lucide-react';
import { Button } from '../components/ui/button';
import { VoucherCenter } from '../components/shared/VoucherCenter';
import { useCart } from '../store/CartContext';
import { validateVoucher } from '../services/vouchers';
import { Reveal } from '../components/shared/Reveal';
import { toast } from 'sonner';
import { useContent } from '../store/ContentContext';
import Seo from '../components/shared/Seo';

const VOUCHER_DEFAULT = {
  eyebrow: 'Voucher', title: 'Kumpulkan & pakai voucher.',
  subtitle: 'Diskon dihitung langsung oleh sistem saat checkout — angka di keranjang dan di pembayaran selalu sama.',
  list_title: 'Voucher Tersedia',
};

// Halaman /voucher — Voucher Center penuh. Klik "Pakai" memvalidasi ke server lalu ke keranjang.
export default function VoucherPage() {
  const cart = useCart();
  const navigate = useNavigate();
  const [applyingCode, setApplyingCode] = React.useState(null);
  const cms = useContent('voucher_page', VOUCHER_DEFAULT);

  const handleApply = async (code) => {
    setApplyingCode(code);
    try {
      const res = await validateVoucher({ code, subtotal: cart.subtotal, items: cart.items });
      if (res.valid) {
        cart.applyVoucher(res);
        toast.success('Voucher diterapkan', { description: res.label });
      } else {
        toast.error(res.reason || 'Voucher tidak dapat digunakan');
      }
    } catch (e) {
      toast.error('Gagal memvalidasi voucher');
    } finally {
      setApplyingCode(null);
    }
  };

  return (
    <div className="cp-container cp-section" data-testid="voucher-page">
      <Seo title={`${cms.title} — Collector Parfum`} description={cms.subtitle} />
      <div className="mb-8 flex items-end justify-between gap-4 flex-wrap">
        <div>
          <div className="cp-eyebrow">{cms.eyebrow}</div>
          <Reveal>
            <h1 className="cp-headline text-4xl sm:text-6xl mt-2">{cms.title}</h1>
          </Reveal>
          <p className="text-sm text-black/60 mt-3 max-w-xl">{cms.subtitle}</p>
        </div>
        <Link to="/keranjang">
          <Button variant="outline" className="rounded-full">
            Ke Keranjang <ArrowRight className="h-4 w-4 ml-2" />
          </Button>
        </Link>
      </div>

      <div className="rounded-2xl border border-black/10 bg-[color:var(--cp-paper-warm)] p-5 sm:p-6">
        <div className="flex items-center gap-2 mb-4">
          <Ticket className="h-5 w-5 text-[color:var(--cp-brass)]" />
          <div className="cp-mono uppercase text-[11px] tracking-[0.22em]">{cms.list_title}</div>
          <span className="ml-auto cp-mono text-[11px] text-black/50">Subtotal: {cart.totalQty} item</span>
        </div>
        <VoucherCenter
          subtotal={cart.subtotal}
          appliedCode={cart.voucher?.code || null}
          applyingCode={applyingCode}
          onApply={handleApply}
        />
        <div className="mt-6 flex justify-end">
          <Button
            onClick={() => navigate('/checkout')}
            disabled={cart.items.length === 0}
            className="rounded-full cp-btn-gold disabled:opacity-50"
          >
            Lanjut ke Checkout <ArrowRight className="h-4 w-4 ml-2" />
          </Button>
        </div>
      </div>
    </div>
  );
}
