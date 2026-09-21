import React from 'react';
import { Loader2, Save } from 'lucide-react';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { useAuth } from '../../store/AuthContext';
import { updateProfile } from '../../services/account';
import { toast } from 'sonner';

// Form profil akun (nama/telepon). Email tak dapat diubah (immutable, BR-1).
export default function ProfileForm() {
  const { user, updateUser } = useAuth();
  const [name, setName] = React.useState(user?.name || '');
  const [phone, setPhone] = React.useState(user?.phone || '');
  const [busy, setBusy] = React.useState(false);

  React.useEffect(() => {
    setName(user?.name || '');
    setPhone(user?.phone || '');
  }, [user]);

  const save = async (e) => {
    e.preventDefault();
    setBusy(true);
    try {
      const updated = await updateProfile({ name: name.trim(), phone: phone.trim() || null });
      updateUser(updated);
      toast.success('Profil diperbarui');
    } catch (err) {
      toast.error(err?.response?.data?.detail || 'Gagal memperbarui profil');
    } finally { setBusy(false); }
  };

  return (
    <div className="rounded-2xl border border-black/10 bg-[color:var(--cp-paper-warm)] p-6" data-testid="account-profile-form">
      <div className="cp-mono uppercase text-[11px] tracking-[0.22em] mb-4">Profil Saya</div>
      <form onSubmit={save} className="space-y-4 max-w-lg">
        <div>
          <div className="cp-mono uppercase text-[10px] tracking-[0.22em] text-black/60 mb-1">Nama</div>
          <Input value={name} onChange={(e) => setName(e.target.value)} className="bg-white h-11 rounded-xl" data-testid="profile-name-input" />
        </div>
        <div>
          <div className="cp-mono uppercase text-[10px] tracking-[0.22em] text-black/60 mb-1">Email</div>
          <Input value={user?.email || ''} disabled className="bg-black/5 h-11 rounded-xl text-black/60" data-testid="profile-email-input" />
        </div>
        <div>
          <div className="cp-mono uppercase text-[10px] tracking-[0.22em] text-black/60 mb-1">No. HP</div>
          <Input value={phone} onChange={(e) => setPhone(e.target.value)} placeholder="08xxxxxxxxxx" className="bg-white h-11 rounded-xl" data-testid="profile-phone-input" />
        </div>
        <Button type="submit" disabled={busy} className="rounded-full bg-[color:var(--cp-ink)] text-[color:var(--cp-paper)] hover:bg-black disabled:opacity-60" data-testid="profile-save-button">
          {busy ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <Save className="h-4 w-4 mr-2" />} Simpan Perubahan
        </Button>
      </form>
    </div>
  );
}
