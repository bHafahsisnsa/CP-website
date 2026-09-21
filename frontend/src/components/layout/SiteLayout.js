import React from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import { AnnouncementBar } from './AnnouncementBar';
import { SiteHeader } from './SiteHeader';
import { SiteFooter } from './SiteFooter';
import { MobileBottomNav } from './MobileBottomNav';
import { CartDrawer } from './CartDrawer';
import { SearchDrawer } from './SearchDrawer';
import { MobileMenuDrawer } from './MobileMenuDrawer';
import { QuickViewModal } from '../shared/QuickViewModal';
import { ChatWidget } from '../shared/ChatWidget';
import { QuickViewContext } from '../../store/QuickViewContext';
import { track } from '../../services/analytics';

export const SiteLayout = () => {
  const [searchOpen, setSearchOpen] = React.useState(false);
  const [menuOpen, setMenuOpen] = React.useState(false);
  const [qvProduct, setQvProduct] = React.useState(null);
  const location = useLocation();

  const openQuickView = React.useCallback((product) => setQvProduct(product), []);
  const closeQuickView = React.useCallback(() => setQvProduct(null), []);

  // Analytics first-party: kirim page_view tiap perubahan rute (best-effort, PII-free).
  React.useEffect(() => {
    track('page_view', { meta: { search: location.search ? 1 : 0 } });
  }, [location.pathname, location.search]);

  return (
    <QuickViewContext.Provider value={{ openQuickView }}>
      <div className="cp-store relative min-h-screen" data-testid="storefront-shell">
        <AnnouncementBar />
        <SiteHeader onOpenSearch={() => setSearchOpen(true)} onOpenMenu={() => setMenuOpen(true)} />
        <main className="min-h-[60vh]" data-testid="page-main">
          <Outlet />
        </main>
        <SiteFooter />
        <MobileBottomNav />
        <ChatWidget />
      </div>
      {/* Portals (render to body) — each carries `cp-store` so dark-mode remaps reach them */}
      <CartDrawer />
      <SearchDrawer open={searchOpen} onOpenChange={setSearchOpen} />
      <MobileMenuDrawer open={menuOpen} onOpenChange={setMenuOpen} />
      <QuickViewModal product={qvProduct} open={!!qvProduct} onOpenChange={(o) => (!o ? closeQuickView() : null)} />
    </QuickViewContext.Provider>
  );
};
