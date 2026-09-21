import React from 'react';
import { Link } from 'react-router-dom';
import { User, ShoppingBag, Heart, MapPin, LogOut, Loader2, WifiOff, RefreshCw } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Reveal } from '../components/shared/Reveal';
import { useAuth } from '../store/AuthContext';
import AuthForms from '../components/account/AuthForms';
import ProfileForm from '../components/account/ProfileForm';
import OrderHistory from '../components/account/OrderHistory';
import AddressBook from '../components/account/AddressBook';
import WishlistTab from '../components/account/WishlistTab';
import { toast } from 'sonner';

const TABS = [
  { id: 'profile', label: 'Profil', icon: User },
  { id: 'orders', label: 'Pesanan', icon: ShoppingBag },
  { id: 'addresses', label: 'Alamat', icon: MapPin },
  { id: 'wishlist', label: 'Wishlist', icon: Heart },
];

export default function AccountPage() {
  const { user, isAuthenticated, loading, logout, sessionError, retrySession } = useAuth();
  const [tab, setTab] = React.useState('profile');

  return (
    <div className="cp-container cp-section" data-testid="account-page">
      <div className="mb-8">
        <div className="cp-eyebrow">Akun</div>
        <Reveal>
          <h1 className="cp-headline text-4xl sm:text-6xl mt-2">
            {isAuthenticated ? `Halo, ${(user?.name || 'Kolektor').split(' ')[0]}.` : 'Halo, Kolektor.'}
          </h1>
        </Reveal>
      </div>

      {loading ? (
        <div className="rounded-2xl border border-black/10 bg-[color:var(--cp-paper-warm)] p-6 flex items-center gap-2 text-black/50 max-w-md">
          <Loader2 className="h-4 w-4 animate-spin" /> Memuat sesi…
        </div>
      ) : sessionError ? (
        <div
          className="rounded-2xl border border-black/10 bg-[color:var(--cp-paper-warm)] p-6 max-w-md"
          data-testid="account-session-offline"
        >
          <div className="flex items-center gap-2 text-black/70">
            <WifiOff className="h-4 w-4" />
            <span className="cp-mono uppercase text-[11px] tracking-[0.22em]">Koneksi terganggu</span>
          </div>
          <p className="mt-3 text-sm text-black/70 leading-relaxed">
            Sesi Anda <strong>masih tersimpan</strong> — kami hanya belum bisa menghubungi server.
            Tidak perlu masuk ulang; coba muat sesi lagi.
          </p>
          <div className="mt-5 flex gap-3">
            <Button onClick={retrySession} className="rounded-full gap-2" data-testid="account-session-retry">
              <RefreshCw className="h-4 w-4" /> Coba Lagi
            </Button>
            <Button
              variant="outline"
              className="rounded-full"
              onClick={() => { logout(); toast.message('Sesi diakhiri. Silakan masuk kembali.'); }}
              data-testid="account-session-signout"
            >
              Keluar
            </Button>
          </div>
        </div>
      ) : !isAuthenticated ? (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          <div className="lg:col-span-5">
            <AuthForms />
          </div>
          <div className="lg:col-span-7">
            <div className="rounded-2xl border border-black/10 bg-[color:var(--cp-paper-warm)] p-8 h-full flex flex-col justify-center">
              <div className="cp-mono uppercase text-[11px] tracking-[0.22em] text-black/60">Keanggotaan Collector</div>
              <p className="mt-3 text-black/70 text-sm leading-relaxed max-w-md">
                Masuk untuk menyimpan alamat, melacak pesanan, dan menyinkronkan wishlist Anda di semua perangkat.
                Belum punya akun? Daftar gratis dalam hitungan detik. Anda juga tetap bisa checkout sebagai tamu.
              </p>
              <div className="mt-5 flex gap-3">
                <Link to="/shop"><Button variant="outline" className="rounded-full">Jelajahi Koleksi</Button></Link>
                <Link to="/keranjang"><Button variant="outline" className="rounded-full">Ke Keranjang</Button></Link>
              </div>
            </div>
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          {/* Sidebar */}
          <div className="lg:col-span-3 space-y-6">
            <div className="rounded-2xl border border-black/10 bg-[color:var(--cp-paper-warm)] p-6" data-testid="account-profile-card">
              <div className="flex items-center gap-4">
                <div className="h-14 w-14 rounded-full bg-[color:var(--cp-market-blue-soft)] flex items-center justify-center">
                  <User className="h-6 w-6 text-[color:var(--cp-market-blue)]" />
                </div>
                <div className="min-w-0">
                  <div className="font-semibold truncate" data-testid="account-user-name">{user?.name}</div>
                  <div className="text-xs text-black/60 truncate">{user?.email}</div>
                </div>
              </div>
              <Button onClick={() => { logout(); toast.message('Anda telah keluar'); }} variant="outline" className="mt-5 w-full rounded-full" data-testid="account-logout-button">
                <LogOut className="h-4 w-4 mr-2" /> Keluar
              </Button>
            </div>

            <nav className="rounded-2xl border border-black/10 bg-[color:var(--cp-paper-warm)] p-2" data-testid="account-nav">
              {TABS.map((t) => {
                const Icon = t.icon;
                const active = tab === t.id;
                return (
                  <button
                    key={t.id}
                    onClick={() => setTab(t.id)}
                    data-testid={`account-tab-${t.id}`}
                    className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm transition-colors ${active ? 'bg-[color:var(--cp-ink)] text-[color:var(--cp-paper)]' : 'hover:bg-[color:var(--cp-paper-fog)]'}`}
                  >
                    <Icon className="h-4 w-4" /> {t.label}
                  </button>
                );
              })}
            </nav>
          </div>

          {/* Content */}
          <div className="lg:col-span-9">
            {tab === 'profile' && <ProfileForm />}
            {tab === 'orders' && <OrderHistory />}
            {tab === 'addresses' && <AddressBook />}
            {tab === 'wishlist' && <WishlistTab />}
          </div>
        </div>
      )}
    </div>
  );
}
