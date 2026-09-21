// components/admin/AdminSidebar.js — navigasi admin (grup, depth<=2). Aktif = aksen champagne.
import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard, Package, FolderTree, Star, ShoppingBag, Ticket, Settings, Wallet,
  BarChart3, Users, FileText, ArrowLeftRight, MapPin, Tags, Sparkles, DatabaseBackup,
  Images,
} from 'lucide-react';
import { adminTestIds as T } from '../../constants/testIds/admin';
import { ACCENT, ACCENT_SOFT } from './adminUi';

export const ADMIN_NAV = [
  {
    group: 'Ringkasan',
    items: [{ to: '/admin', label: 'Dashboard', icon: LayoutDashboard, end: true }],
  },
  {
    group: 'Katalog',
    items: [
      { to: '/admin/produk', label: 'Produk', icon: Package, end: true },
      { to: '/admin/produk/impor', label: 'Impor / Ekspor', icon: ArrowLeftRight },
      { to: '/admin/kategori', label: 'Kategori', icon: FolderTree },
      { to: '/admin/occasion', label: 'Occasion', icon: Tags },
      { to: '/admin/karakter', label: 'Karakter', icon: Sparkles },
      { to: '/admin/ulasan', label: 'Ulasan', icon: Star },
    ],
  },
  {
    group: 'Penjualan',
    items: [
      { to: '/admin/pesanan', label: 'Pesanan', icon: ShoppingBag },
      { to: '/admin/pembayaran', label: 'Pembayaran', icon: Wallet },
      { to: '/admin/voucher', label: 'Voucher', icon: Ticket },
    ],
  },
  {
    group: 'Pertumbuhan',
    items: [
      { to: '/admin/analitik', label: 'Analitik', icon: BarChart3 },
      { to: '/admin/crm', label: 'CRM & Segmen', icon: Users },
    ],
  },
  {
    group: 'Konten',
    items: [
      { to: '/admin/media', label: 'Media', icon: Images },
      { to: '/admin/konten', label: 'Konten Situs', icon: FileText },
      { to: '/admin/lokasi', label: 'Lokasi & Ulasan', icon: MapPin },
    ],
  },
  {
    group: 'Pengaturan',
    items: [
      { to: '/admin/pengaturan', label: 'Pengaturan Toko', icon: Settings },
      { to: '/admin/backup', label: 'Backup & Restore', icon: DatabaseBackup },
    ],
  },
];

export const AdminSidebar = ({ onNavigate }) => (
  <nav className="flex flex-col gap-6 p-4" data-testid={T.sidebar}>
    <div className="px-2 pt-1">
      <div className="font-[\'DM_Serif_Display\',serif] text-lg text-foreground">Collector</div>
      <div className="text-[10px] uppercase tracking-[0.24em] text-muted-foreground">Admin Panel</div>
    </div>
    {ADMIN_NAV.map((section) => (
      <div key={section.group}>
        <div className="px-2 mb-2 text-[10px] font-semibold uppercase tracking-[0.16em] text-muted-foreground">
          {section.group}
        </div>
        <div className="flex flex-col gap-1">
          {section.items.map((it) => {
            const Icon = it.icon;
            return (
              <NavLink
                key={it.to}
                to={it.to}
                end={it.end}
                onClick={onNavigate}
                data-testid={T.navItem}
                className="group flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm transition-colors"
                style={({ isActive }) => ({
                  backgroundColor: isActive ? ACCENT_SOFT : 'transparent',
                  color: isActive ? ACCENT : undefined,
                  fontWeight: isActive ? 600 : 500,
                  boxShadow: isActive ? `inset 3px 0 0 ${ACCENT}` : 'none',
                })}
              >
                {({ isActive }) => (
                  <>
                    <Icon className="h-4 w-4" style={{ color: isActive ? ACCENT : undefined }} />
                    <span>{it.label}</span>
                  </>
                )}
              </NavLink>
            );
          })}
        </div>
      </div>
    ))}
  </nav>
);
