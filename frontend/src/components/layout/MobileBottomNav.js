import React from 'react';
import { NavLink } from 'react-router-dom';
import { Home, Store, ShoppingBag, Heart, User } from 'lucide-react';
import { useCart } from '../../store/CartContext';
import { useWishlist } from '../../store/WishlistContext';

export const MobileBottomNav = () => {
  const cart = useCart();
  const wish = useWishlist();

  const items = [
    { to: '/', label: 'Beranda', icon: Home, end: true },
    { to: '/shop', label: 'Toko', icon: Store },
    { to: '/keranjang', label: 'Keranjang', icon: ShoppingBag, badge: cart.totalQty },
    { to: '/wishlist', label: 'Wishlist', icon: Heart, badge: wish.ids.length },
    { to: '/akun', label: 'Profil', icon: User },
  ];

  return (
    <>
      {/* Spacer so content isn't hidden behind bottom nav */}
      <div className="lg:hidden h-16" aria-hidden />
      <nav
        data-testid="mobile-bottom-nav"
        className="lg:hidden fixed bottom-0 left-0 right-0 z-50 bg-[color:var(--cp-paper-warm)] border-t border-black/10 shadow-[0_-8px_30px_rgba(0,0,0,0.05)]"
        style={{ paddingBottom: 'env(safe-area-inset-bottom, 0px)' }}
      >
        <div className="grid grid-cols-5 h-16">
          {items.map(({ to, label, icon: Icon, end, badge }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              data-testid="mobile-bottom-nav-item"
              className={({ isActive }) =>
                `relative flex flex-col items-center justify-center gap-1 text-[10px] tracking-wide ${
                  isActive ? 'text-[color:var(--cp-ink)]' : 'text-black/55'
                }`
              }
            >
              <div className="relative">
                <Icon className="h-5 w-5" />
                {typeof badge === 'number' && badge > 0 && (
                  <span
                    data-testid="mobile-bottom-nav-cart-badge"
                    className="absolute -top-1.5 -right-2 bg-[color:var(--cp-ink)] text-[color:var(--cp-paper)] cp-mono text-[9px] rounded-full h-4 min-w-4 px-1 flex items-center justify-center"
                  >
                    {badge}
                  </span>
                )}
              </div>
              <span className="cp-mono uppercase text-[9px] tracking-[0.18em]">{label}</span>
            </NavLink>
          ))}
        </div>
      </nav>
    </>
  );
};
