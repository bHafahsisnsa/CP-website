import React from 'react';
import { BrowserRouter, Routes, Route, useLocation } from 'react-router-dom';
import { CheckCircle2, XCircle, AlertTriangle, Info } from 'lucide-react';
import { Toaster } from './components/ui/sonner';
import { CatalogProvider } from './store/CatalogContext';
import { CartProvider } from './store/CartContext';
import { WishlistProvider } from './store/WishlistContext';
import { AuthProvider } from './store/AuthContext';
import { ContentProvider } from './store/ContentContext';
import { ThemeProvider } from './store/ThemeContext';
import { SettingsProvider } from './store/SettingsContext';
import { SiteLayout } from './components/layout/SiteLayout';
import { AppReadySignal } from './components/shared/AppReadySignal';

import HomePage from './pages/HomePage';
import ShopPage from './pages/ShopPage';
import ProductDetailPage from './pages/ProductDetailPage';
import CartPage from './pages/CartPage';
import CheckoutPage from './pages/CheckoutPage';
import OrderSuccessPage from './pages/OrderSuccessPage';
import VoucherPage from './pages/VoucherPage';
import AboutPage from './pages/AboutPage';
import ContactPage from './pages/ContactPage';
import WishlistPage from './pages/WishlistPage';
import AccountPage from './pages/AccountPage';
import StoreLocationsPage from './pages/StoreLocationsPage';

import { AdminLayout } from './components/admin/AdminLayout';
import AdminDashboardPage from './pages/admin/AdminDashboardPage';
import AdminProductsPage from './pages/admin/AdminProductsPage';
import AdminProductEditorPage from './pages/admin/AdminProductEditorPage';
import AdminProductImportPage from './pages/admin/AdminProductImportPage';
import AdminCategoriesPage from './pages/admin/AdminCategoriesPage';
import AdminOccasionsPage from './pages/admin/AdminOccasionsPage';
import AdminCharactersPage from './pages/admin/AdminCharactersPage';
import AdminVouchersPage from './pages/admin/AdminVouchersPage';
import AdminOrdersPage from './pages/admin/AdminOrdersPage';
import AdminOrderDetailPage from './pages/admin/AdminOrderDetailPage';
import AdminPaymentsPage from './pages/admin/AdminPaymentsPage';
import AdminReviewsPage from './pages/admin/AdminReviewsPage';
import AdminAnalyticsPage from './pages/admin/AdminAnalyticsPage';
import AdminCrmPage from './pages/admin/AdminCrmPage';
import AdminContentPage from './pages/admin/AdminContentPage';
import AdminMediaPage from './pages/admin/AdminMediaPage';
import AdminSettingsPage from './pages/admin/AdminSettingsPage';
import AdminStoresPage from './pages/admin/AdminStoresPage';
import AdminBackupPage from './pages/admin/AdminBackupPage';

function ScrollToTop() {
  const { pathname } = useLocation();
  React.useEffect(() => {
    window.scrollTo({ top: 0, behavior: 'auto' });
  }, [pathname]);
  return null;
}

export default function App() {
  return (
    <BrowserRouter>
      <ThemeProvider>
      <AuthProvider>
        <SettingsProvider>
        <CatalogProvider>
          <ContentProvider>
            <WishlistProvider>
              <CartProvider>
                <ScrollToTop />
                <AppReadySignal />
              <Routes>
                <Route element={<SiteLayout />}>
                  <Route index element={<HomePage />} />
                  <Route path="/shop" element={<ShopPage />} />
                  <Route path="/parfum/:slug" element={<ProductDetailPage />} />
                  <Route path="/keranjang" element={<CartPage />} />
                  <Route path="/checkout" element={<CheckoutPage />} />
                  <Route path="/voucher" element={<VoucherPage />} />
                  <Route path="/pesanan-sukses" element={<OrderSuccessPage />} />
                  <Route path="/tentang" element={<AboutPage />} />
                  <Route path="/kontak" element={<ContactPage />} />
                  <Route path="/lokasi" element={<StoreLocationsPage />} />
                  <Route path="/wishlist" element={<WishlistPage />} />
                  <Route path="/akun" element={<AccountPage />} />
                  <Route path="*" element={<HomePage />} />
                </Route>

                {/* Admin Backoffice (Epic E5) — pathless layout + absolute paths, RBAC di AdminLayout */}
                <Route element={<AdminLayout />}>
                  <Route path="/admin" element={<AdminDashboardPage />} />
                  <Route path="/admin/produk" element={<AdminProductsPage />} />
                  <Route path="/admin/produk/baru" element={<AdminProductEditorPage />} />
                  <Route path="/admin/produk/impor" element={<AdminProductImportPage />} />
                  <Route path="/admin/produk/:id" element={<AdminProductEditorPage />} />
                  <Route path="/admin/kategori" element={<AdminCategoriesPage />} />
                  <Route path="/admin/occasion" element={<AdminOccasionsPage />} />
                  <Route path="/admin/karakter" element={<AdminCharactersPage />} />
                  <Route path="/admin/voucher" element={<AdminVouchersPage />} />
                  <Route path="/admin/pesanan" element={<AdminOrdersPage />} />
                  <Route path="/admin/pesanan/:code" element={<AdminOrderDetailPage />} />
                  <Route path="/admin/pembayaran" element={<AdminPaymentsPage />} />
                  <Route path="/admin/ulasan" element={<AdminReviewsPage />} />
                  <Route path="/admin/analitik" element={<AdminAnalyticsPage />} />
                  <Route path="/admin/crm" element={<AdminCrmPage />} />
                  <Route path="/admin/konten" element={<AdminContentPage />} />
                  <Route path="/admin/media" element={<AdminMediaPage />} />
                  <Route path="/admin/lokasi" element={<AdminStoresPage />} />
                  <Route path="/admin/pengaturan" element={<AdminSettingsPage />} />
                  <Route path="/admin/backup" element={<AdminBackupPage />} />
                </Route>
              </Routes>
              <Toaster
                position="top-center"
                offset="90px"
                closeButton
                icons={{
                  success: <CheckCircle2 className="h-4 w-4 text-[color:var(--cp-brass)]" />,
                  error: <XCircle className="h-4 w-4 text-[hsl(var(--destructive))]" />,
                  warning: <AlertTriangle className="h-4 w-4 text-[color:var(--cp-brass)]" />,
                  info: <Info className="h-4 w-4 text-[color:var(--cp-ink)]" />,
                }}
              />
              </CartProvider>
            </WishlistProvider>
          </ContentProvider>
        </CatalogProvider>
        </SettingsProvider>
      </AuthProvider>
      </ThemeProvider>
    </BrowserRouter>
  );
}
