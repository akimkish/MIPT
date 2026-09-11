import type { CSSProperties } from 'react';
import {
  BrowserRouter,
  Link,
  Navigate,
  Outlet,
  Route,
  Routes,
  useNavigate,
  useParams,
} from 'react-router-dom';
import { RequireAdmin } from '../features/admin-auth/components/RequireAdmin';
import { AdminHomePage } from '../features/admin-auth/pages/AdminHomePage';
import { LoginPage } from '../features/admin-auth/pages/LoginPage';
import { CartPage } from '../features/cart/pages/CartPage';
import { CatalogPage } from '../features/catalog/pages/CatalogPage';
import { CheckoutPage } from '../features/checkout/pages/CheckoutPage';
import { ProductDetailPage } from '../features/product-detail/pages/ProductDetailPage';
import { AdminLayout } from './AdminLayout';
import { AppHeader } from './AppHeader';

/**
 * Роутинг приложения.
 *
 * Выбор: `react-router-dom` с классическим `<BrowserRouter>`/`<Routes>`,
 * а НЕ data-router API — загрузка данных и так идёт через React Query.
 *
 * Два независимых layout-роута:
 *   - `AppLayout` (AppHeader + витрина/товар/корзина/чекаут) — покупатель;
 *   - `RequireAdmin` → `AdminLayout` (шапка с ролью + выход) — админка,
 *     не показывает и не переиспользует покупательский `AppHeader`
 *     намеренно: разный контекст навигации, разная аудитория.
 * `/admin/login` вынесен ЗА пределы `RequireAdmin` — иначе страница
 * входа сама была бы защищена входом, замкнутый круг.
 *
 * Требует: `npm install react-router-dom`.
 */

const backLinkStyle: CSSProperties = {
  display: 'inline-block',
  margin: 'var(--space-4)',
  padding: 'var(--space-2) var(--space-4)',
  border: '1px solid var(--border)',
  borderRadius: 'var(--radius-sm)',
  background: 'var(--paper)',
  color: 'var(--ink)',
  textDecoration: 'none',
  font: 'inherit',
};

/** Общий каркас покупательских страниц: постоянный header + текущий маршрут. */
function AppLayout() {
  return (
    <>
      <AppHeader />
      <Outlet />
    </>
  );
}

/**
 * Роут `/` — витрина.
 *
 * `CatalogPage` не знает о роутере (принимает колбэк `onOpenProduct`
 * пропом) — здесь единственное место, где клик по карточке товара
 * превращается в реальную навигацию `useNavigate`.
 */
function CatalogRoute() {
  const navigate = useNavigate();

  return <CatalogPage onOpenProduct={(productId) => navigate(`/products/${productId}`)} />;
}

/**
 * Роут `/products/:productId` — карточка товара.
 *
 * `useParams` типизирован как `string | undefined`; если `productId`
 * вдруг отсутствует, редиректим на каталог, а не рендерим страницу
 * с `undefined`.
 */
function ProductDetailRoute() {
  const { productId } = useParams<{ productId: string }>();

  if (!productId) {
    return <Navigate to="/" replace />;
  }

  return (
    <>
      <Link to="/" style={backLinkStyle}>
        ← Назад в каталог
      </Link>
      <ProductDetailPage productId={productId} />
    </>
  );
}

/** Роут `/cart` — корзина. */
function CartRoute() {
  const navigate = useNavigate();

  return <CartPage onContinueShopping={() => navigate('/')} onCheckout={() => navigate('/checkout')} />;
}

/** Роут `/checkout` — оформление заказа. */
function CheckoutRoute() {
  const navigate = useNavigate();

  return <CheckoutPage onContinueShopping={() => navigate('/')} />;
}

/** Роут `/admin/login` — вход администратора. */
function AdminLoginRoute() {
  const navigate = useNavigate();

  return <LoginPage onLoginSuccess={() => navigate('/admin')} />;
}

/** Заглушка для несуществующих маршрутов. */
function NotFoundPage() {
  return (
    <div style={{ padding: 'var(--space-8)', textAlign: 'center' }}>
      <p>Страница не найдена.</p>
      <Link to="/">Вернуться в каталог</Link>
    </div>
  );
}

/**
 * Корневой роутер приложения.
 *
 * Покупательская ветка (витрина, товар, корзина, чекаут) под
 * `AppLayout`; независимая админская ветка — публичный `/admin/login` и
 * защищённый `/admin` под `RequireAdmin` → `AdminLayout`. Остальные
 * разделы админки добавятся дочерними `<Route>` внутри `/admin` по мере
 * готовности их страниц.
 */
export function AppRouter() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<AppLayout />}>
          <Route path="/" element={<CatalogRoute />} />
          <Route path="/products/:productId" element={<ProductDetailRoute />} />
          <Route path="/cart" element={<CartRoute />} />
          <Route path="/checkout" element={<CheckoutRoute />} />
        </Route>

        <Route path="/admin/login" element={<AdminLoginRoute />} />

        <Route path="/admin" element={<RequireAdmin />}>
          <Route element={<AdminLayout />}>
            <Route index element={<AdminHomePage />} />
          </Route>
        </Route>

        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </BrowserRouter>
  );
}
