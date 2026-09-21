import React from 'react';
import { LogIn, Loader2 } from 'lucide-react';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import { useAuth } from '../../store/AuthContext';
import { toast } from 'sonner';

// Form Masuk/Daftar minimal (Epic E4). Dipakai di AccountPage saat belum login.
export default function AuthForms() {
  const { login, register } = useAuth();
  const [tab, setTab] = React.useState('login');
  const [busy, setBusy] = React.useState(false);
  const [login_, setLogin] = React.useState({ email: '', password: '' });
  const [reg, setReg] = React.useState({ name: '', email: '', password: '', phone: '' });

  const doLogin = async (e) => {
    e.preventDefault();
    setBusy(true);
    try {
      await login(login_.email.trim(), login_.password);
      toast.success('Berhasil masuk');
    } catch (err) {
      toast.error(err?.response?.data?.detail || 'Email atau kata sandi salah');
    } finally { setBusy(false); }
  };

  const doRegister = async (e) => {
    e.preventDefault();
    setBusy(true);
    try {
      await register({ name: reg.name.trim(), email: reg.email.trim(), password: reg.password, phone: reg.phone.trim() || null });
      toast.success('Akun dibuat & masuk');
    } catch (err) {
      toast.error(err?.response?.data?.detail || 'Gagal mendaftar. Email mungkin sudah terpakai.');
    } finally { setBusy(false); }
  };

  return (
    <div className="rounded-2xl border border-black/10 bg-[color:var(--cp-paper-warm)] p-6 max-w-md" data-testid="auth-panel">
      <Tabs value={tab} onValueChange={setTab}>
        <TabsList className="bg-[color:var(--cp-paper-fog)] rounded-full h-11 p-1 w-full grid grid-cols-2">
          <TabsTrigger value="login" data-testid="auth-tab-login" className="rounded-full data-[state=active]:bg-[color:var(--cp-ink)] data-[state=active]:text-[color:var(--cp-paper)] cp-mono uppercase text-[10px] tracking-[0.22em]">Masuk</TabsTrigger>
          <TabsTrigger value="register" data-testid="auth-tab-register" className="rounded-full data-[state=active]:bg-[color:var(--cp-ink)] data-[state=active]:text-[color:var(--cp-paper)] cp-mono uppercase text-[10px] tracking-[0.22em]">Daftar</TabsTrigger>
        </TabsList>

        <TabsContent value="login" className="pt-5">
          <form onSubmit={doLogin} className="space-y-3">
            <Input type="email" required placeholder="Email" value={login_.email} onChange={(e) => setLogin((s) => ({ ...s, email: e.target.value }))} className="bg-white h-11 rounded-xl" data-testid="login-email-input" />
            <Input type="password" required placeholder="Kata sandi" value={login_.password} onChange={(e) => setLogin((s) => ({ ...s, password: e.target.value }))} className="bg-white h-11 rounded-xl" data-testid="login-password-input" />
            <Button type="submit" disabled={busy} className="w-full h-11 rounded-full bg-[color:var(--cp-ink)] text-[color:var(--cp-paper)] hover:bg-black disabled:opacity-60" data-testid="login-submit-button">
              {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : (<><LogIn className="h-4 w-4 mr-2" /> Masuk</>)}
            </Button>
            <p className="text-[11px] text-black/50 text-center">Demo: customer@collectorparfum.id / Customer#2026</p>
          </form>
        </TabsContent>

        <TabsContent value="register" className="pt-5">
          <form onSubmit={doRegister} className="space-y-3">
            <Input required placeholder="Nama lengkap" value={reg.name} onChange={(e) => setReg((s) => ({ ...s, name: e.target.value }))} className="bg-white h-11 rounded-xl" data-testid="register-name-input" />
            <Input type="email" required placeholder="Email" value={reg.email} onChange={(e) => setReg((s) => ({ ...s, email: e.target.value }))} className="bg-white h-11 rounded-xl" data-testid="register-email-input" />
            <Input placeholder="No. HP (opsional)" value={reg.phone} onChange={(e) => setReg((s) => ({ ...s, phone: e.target.value }))} className="bg-white h-11 rounded-xl" data-testid="register-phone-input" />
            <Input type="password" required minLength={6} placeholder="Kata sandi (min. 6 karakter)" value={reg.password} onChange={(e) => setReg((s) => ({ ...s, password: e.target.value }))} className="bg-white h-11 rounded-xl" data-testid="register-password-input" />
            <Button type="submit" disabled={busy} className="w-full h-11 rounded-full cp-btn-gold disabled:opacity-60" data-testid="register-submit-button">
              {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Buat Akun'}
            </Button>
          </form>
        </TabsContent>
      </Tabs>
    </div>
  );
}
