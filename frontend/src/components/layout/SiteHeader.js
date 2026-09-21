import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Search, User, Heart, ShoppingBag, Menu, Sun, Moon } from 'lucide-react';
import { useCart } from '../../store/CartContext';
import { useWishlist } from '../../store/WishlistContext';
import { useContent } from '../../store/ContentContext';
import { useTheme } from '../../store/ThemeContext';

const HEADER_DEFAULT = {
  logo_name: 'Collector', logo_suffix: 'Parfum',
  nav: [
    { label: 'Beranda', to: '/' },
    { label: 'Toko', to: '/shop' },
    { label: 'Koleksi', to: '/shop?featured=1' },
    { label: 'Tentang', to: '/tentang' },
    { label: 'Kontak', to: '/kontak' },
  ],
};

export const SiteHeader = ({ onOpenSearch, onOpenMenu }) => {
  const cart = useCart();
  const wish = useWishlist();
  const location = useLocation();
  const [scrolled, setScrolled] = React.useState(false);
  const c = useContent('header', HEADER_DEFAULT);

  React.useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 8);
    onScroll();
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  const nav = Array.isArray(c.nav) && c.nav.length ? c.nav : HEADER_DEFAULT.nav;
  const { theme, toggle } = useTheme();

  return (
    <header
      data-testid="site-header"
      className={`sticky top-0 z-40 border-b transition-colors duration-300 ${
        scrolled ? 'bg-[color:var(--cp-paper-warm)]/70 backdrop-blur-[20px] backdrop-saturate-150 border-white/40 shadow-[0_12px_34px_rgba(20,16,10,0.10),inset_0_1px_0_rgba(255,255,255,0.6)]' : 'bg-[color:var(--cp-paper-warm)]/95 backdrop-blur-[10px] border-transparent'
      }`}
    >
      {/* Container LEBAR (cp-container-wide) agar sejajar dengan halaman katalog/PDP yang
          kini immersive (gutter tipis). Header edge-to-edge = kesan premium & konsisten. */}
      <div className="cp-container-wide flex items-center justify-between" style={{ height: 'var(--header-h)' }}>
        {/* Mobile menu button */}
        <button
          type="button"
          onClick={onOpenMenu}
          className="lg:hidden -ml-2 p-2 rounded-full hover:bg-black/5"
          data-testid="header-menu-button"
          aria-label="Buka menu"
        >
          <Menu className="h-5 w-5" />
        </button>

        {/* Left nav (desktop) */}
        <nav className="hidden lg:flex items-center gap-8">
          {nav.slice(0, 2).map((n) => (
            <Link
              key={n.to}
              to={n.to}
              className={`cp-hover-underline text-sm tracking-wide ${
                location.pathname === n.to ? 'font-semibold' : ''
              }`}
            >
              {n.label}
            </Link>
          ))}
        </nav>

        {/* Logo center */}
        <Link to="/" className="flex items-baseline gap-1.5" data-testid="site-logo" aria-label="Collector Parfum">
          <span className="cp-logo text-2xl sm:text-3xl leading-none">Collector</span>
          <span className="cp-logo text-2xl sm:text-3xl leading-none hidden sm:inline">Parfum</span>
        </Link>

        {/* Right nav (desktop) */}
        <nav className="hidden lg:flex items-center gap-8">
          {nav.slice(2).map((n) => (
            <Link key={n.to} to={n.to} className="cp-hover-underline text-sm tracking-wide">
              {n.label}
            </Link>
          ))}
        </nav>

        {/* Actions */}
        <div className="flex items-center gap-1 sm:gap-2">
          <button
            type="button"
            onClick={toggle}
            className="p-2 rounded-full hover:bg-black/5 transition-colors"
            data-testid="header-theme-toggle"
            aria-label={theme === 'dark' ? 'Aktifkan mode terang' : 'Aktifkan mode gelap'}
            title={theme === 'dark' ? 'Mode terang' : 'Mode gelap'}
          >
            {theme === 'dark' ? <Sun className="h-5 w-5" /> : <Moon className="h-5 w-5" />}
          </button>
          <button
            type="button"
            onClick={onOpenSearch}
            className="p-2 rounded-full hover:bg-black/5"
            data-testid="header-search-button"
            aria-label="Cari parfum"
          >
            <Search className="h-5 w-5" />
          </button>
          <Link
            to="/wishlist"
            className="relative p-2 rounded-full hover:bg-black/5 hidden sm:inline-flex"
            data-testid="header-wishlist-button"
            aria-label="Wishlist"
          >
            <Heart className="h-5 w-5" />
            {wish.ids.length > 0 && (
              <span className="absolute -top-0.5 -right-0.5 bg-[color:var(--cp-ink)] text-[color:var(--cp-paper)] text-[10px] cp-mono rounded-full h-4 min-w-4 px-1 flex items-center justify-center">
                {wish.ids.length}
              </span>
            )}
          </Link>
          <button
            type="button"
            onClick={() => cart.open()}
            className="relative p-2 rounded-full hover:bg-black/5"
            data-testid="header-cart-button"
            aria-label="Keranjang belanja"
          >
            <ShoppingBag className="h-5 w-5" />
            {cart.totalQty > 0 && (
              <span
                className="absolute -top-0.5 -right-0.5 bg-[color:var(--cp-ink)] text-[color:var(--cp-paper)] text-[10px] cp-mono rounded-full h-4 min-w-4 px-1 flex items-center justify-center"
                data-testid="header-cart-count"
              >
                {cart.totalQty}
              </span>
            )}
          </button>
          <Link
            to="/akun"
            className="p-2 rounded-full hover:bg-black/5 hidden sm:inline-flex"
            data-testid="header-account-button"
            aria-label="Akun"
          >
            <User className="h-5 w-5" />
          </Link>
        </div>
      </div>
    </header>
  );
};
