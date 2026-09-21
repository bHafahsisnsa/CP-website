// components/admin/AdminLayout.js — shell admin: RBAC gate + login admin + sidebar + topbar + Outlet.
import React, { useState, useEffect } from 'react';
import { Outlet, useNavigate, useLocation, Link } from 'react-router-dom';
import { Menu, LogOut, Store, Sun, Moon, ShieldAlert, WifiOff, RefreshCw } from 'lucide-react';
import { toast } from 'sonner';
import { useAuth } from '../../store/AuthContext';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import {
  Sheet, SheetContent, SheetTrigger, SheetHeader, SheetTitle, SheetDescription,
} from '../ui/sheet';
import {
  DropdownMenu, DropdownMenuTrigger, DropdownMenuContent, DropdownMenuItem, DropdownMenuSeparator, DropdownMenuLabel,
} from '../ui/dropdown-menu';
import { AdminSidebar, ADMIN_NAV } from './AdminSidebar';
import { adminTestIds as T } from '../../constants/testIds/admin';

const titleFor = (pathname) => {
  const map = {
    '/admin': 'Dashboard', '/admin/produk': 'Produk', '/admin/kategori': 'Kategori',
    '/admin/ulasan': 'Ulasan', '/admin/pesanan': 'Pesanan', '/admin/voucher': 'Voucher',
    '/admin/analitik': 'Analitik', '/admin/crm': 'CRM & Segmen',
    '/admin/konten': 'Konten Situs',
    '/admin/pengaturan': 'Pengaturan Toko',
    '/admin/backup': 'Backup & Restore',
  };
  if (map[pathname]) return map[pathname];
  if (pathname === '/admin/produk/impor') return 'Impor / Ekspor Produk';
  if (pathname.startsWith('/admin/produk')) return 'Editor Produk';
  if (pathname.startsWith('/admin/pesanan/')) return 'Detail Pesanan';
  return 'Admin';
};

const AdminLogin = () => {
  const { login } = useAuth();
  const [email, setEmail] = useState('admin@collectorparfum.id');
  const [password, setPassword] = useState('');
  const [busy, setBusy] = useState(false);
  const submit = async (e) => {
    e.preventDefault();
    setBusy(true);
    try {
      const u = await login(email, password);
      if (u?.role !== 'admin') {
        toast.error('Akun ini bukan admin.');
      } else {
        toast.success('Selamat datang, Admin.');
      }
    } catch (err) {
      toast.error(err?.response?.data?.detail || 'Email atau kata sandi salah.');
    } finally {
      setBusy(false);
    }
  };
  return (
    <div className="min-h-screen grid place-items-center bg-background px-4">
      <Card className="w-full max-w-sm border-border">
        <CardHeader>
          <CardTitle className="font-[\'DM_Serif_Display\',serif] text-2xl">Masuk Admin</CardTitle>
          <p className="text-sm text-muted-foreground">Collector Parfum — Backoffice</p>
        </CardHeader>
        <CardContent>
          <form onSubmit={submit} className="space-y-4" data-testid={T.loginForm}>
            <div className="space-y-1.5">
              <Label htmlFor="adm-email">Email</Label>
              <Input id="adm-email" type="email" value={email} onChange={(e) => setEmail(e.target.value)}
                required data-testid={T.loginEmail} />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="adm-pass">Kata Sandi</Label>
              <Input id="adm-pass" type="password" value={password} onChange={(e) => setPassword(e.target.value)}
                required data-testid={T.loginPassword} placeholder="••••••••" />
            </div>
            <Button type="submit" className="w-full" disabled={busy} data-testid={T.loginSubmit}>
              {busy ? 'Memproses…' : 'Masuk'}
            </Button>
            <p className="text-center text-xs text-muted-foreground">
              <Link to="/" className="underline hover:text-foreground">Kembali ke storefront</Link>
            </p>
          </form>
        </CardContent>
      </Card>
    </div>
  );
};

// Server tak terjangkau (offline/timeout/502) SEDANGKAN token masih tersimpan.
// Jangan buang admin ke form login — sesi masih sah, cukup coba lagi.
const AdminSessionOffline = () => {
  const { retrySession, logout } = useAuth();
  const [busy, setBusy] = useState(false);
  const retry = async () => {
    setBusy(true);
    retrySession();
    setTimeout(() => setBusy(false), 1200);
  };
  return (
    <div className="min-h-screen grid place-items-center bg-background px-4" data-testid={T.sessionOffline}>
      <Card className="w-full max-w-sm border-border text-center">
        <CardHeader>
          <WifiOff className="h-9 w-9 mx-auto text-muted-foreground" />
          <CardTitle className="mt-2 text-lg">Server belum terjangkau</CardTitle>
          <p className="text-sm text-muted-foreground">
            Sesi admin Anda <strong>masih aktif</strong> — koneksi ke server sedang terganggu.
            Tidak perlu masuk ulang; coba lagi sebentar.
          </p>
        </CardHeader>
        <CardContent className="space-y-2">
          <Button className="w-full gap-2" onClick={retry} disabled={busy} data-testid={T.sessionRetry}>
            <RefreshCw className={`h-4 w-4 ${busy ? 'animate-spin' : ''}`} />
            {busy ? 'Menghubungkan…' : 'Coba Lagi'}
          </Button>
          <Button
            variant="outline"
            className="w-full"
            onClick={() => { logout(); toast.message('Sesi diakhiri. Silakan masuk kembali.'); }}
            data-testid={T.sessionSignOut}
          >
            Keluar & Masuk Manual
          </Button>
        </CardContent>
      </Card>
    </div>
  );
};

export const AdminLayout = () => {
  const { user, loading, isAuthenticated, logout, sessionError } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [dark, setDark] = useState(() => document.documentElement.classList.contains('dark'));

  const isAdmin = isAuthenticated && user?.role === 'admin';

  useEffect(() => {
    if (!loading && isAuthenticated && user?.role !== 'admin') {
      toast.error('Akses ditolak — khusus admin.');
      navigate('/', { replace: true });
    }
  }, [loading, isAuthenticated, user, navigate]);

  const toggleTheme = () => {
    const el = document.documentElement;
    el.classList.toggle('dark');
    setDark(el.classList.contains('dark'));
  };

  if (loading) {
    return (
      <div className="min-h-screen grid place-items-center bg-background">
        <div className="h-8 w-8 rounded-full border-2 border-border border-t-foreground animate-spin" />
      </div>
    );
  }
  if (!isAuthenticated) return sessionError ? <AdminSessionOffline /> : <AdminLogin />;
  if (!isAdmin) {
    return (
      <div className="min-h-screen grid place-items-center bg-background px-4 text-center">
        <div>
          <ShieldAlert className="h-10 w-10 mx-auto text-muted-foreground" />
          <p className="mt-3 text-sm text-foreground">Akses ditolak — halaman khusus admin.</p>
          <Button className="mt-4" onClick={() => navigate('/')}>Ke Storefront</Button>
        </div>
      </div>
    );
  }

  const flatCrumb = titleFor(location.pathname);

  return (
    <div className="min-h-screen bg-background text-foreground" data-testid={T.shell}>
      {/* Sidebar desktop */}
      <aside className="hidden lg:flex fixed inset-y-0 left-0 w-64 flex-col border-r border-border bg-card overflow-y-auto">
        <AdminSidebar />
      </aside>

      <div className="lg:pl-64">
        {/* Topbar */}
        <header className="sticky top-0 z-30 flex items-center justify-between gap-3 border-b border-border bg-card/90 backdrop-blur px-4 sm:px-6 h-16">
          <div className="flex items-center gap-3 min-w-0">
            <Sheet open={mobileOpen} onOpenChange={setMobileOpen}>
              <SheetTrigger asChild>
                <Button variant="ghost" size="icon" className="lg:hidden" data-testid="admin-mobile-menu-button">
                  <Menu className="h-5 w-5" />
                </Button>
              </SheetTrigger>
              <SheetContent side="left" className="w-72 p-0 bg-card">
                <SheetHeader className="sr-only">
                  <SheetTitle>Menu Admin</SheetTitle>
                  <SheetDescription>Navigasi backoffice Collector Parfum.</SheetDescription>
                </SheetHeader>
                <AdminSidebar onNavigate={() => setMobileOpen(false)} />
              </SheetContent>
            </Sheet>
            <div className="min-w-0" data-testid={T.breadcrumb}>
              <div className="text-[11px] uppercase tracking-[0.14em] text-muted-foreground">Admin</div>
              <div className="text-base font-semibold truncate">{flatCrumb}</div>
            </div>
          </div>
          <div className="flex items-center gap-1.5">
            <Button variant="ghost" size="icon" onClick={toggleTheme} data-testid={T.themeToggle} aria-label="Ganti tema">
              {dark ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
            </Button>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="secondary" size="sm" data-testid={T.menu} className="gap-2">
                  <span className="hidden sm:inline max-w-[140px] truncate">{user?.name || 'Admin'}</span>
                  <span className="sm:hidden">Menu</span>
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-52">
                <DropdownMenuLabel className="truncate">{user?.email}</DropdownMenuLabel>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={() => navigate('/')}>
                  <Store className="h-4 w-4 mr-2" /> Ke Storefront
                </DropdownMenuItem>
                <DropdownMenuItem
                  onClick={() => { logout(); toast('Anda telah keluar.'); }}
                  data-testid={T.logout}
                >
                  <LogOut className="h-4 w-4 mr-2" /> Keluar
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </header>

        <main className="px-4 sm:px-6 lg:px-8 py-6 max-w-[1400px] mx-auto">
          <Outlet />
        </main>
      </div>
    </div>
  );
};
