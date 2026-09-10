import type { CSSProperties } from 'react';
import { BrowserRouter, Link, Navigate, Route, Routes, useNavigate, useParams } from 'react-router-dom';
import { CatalogPage } from '../features/catalog/pages/CatalogPage';
import { ProductDetailPage } from '../features/product-detail/pages/ProductDetailPage';

/**
 * Роутинг приложения.
 *
 * Выбор: `react-router-dom` с классическим `<BrowserRouter>`/`<Routes>`,
 * а НЕ data-router API (`createBrowserRouter` с `loader`/`action`) —
 * загрузка данных в проекте и так идёт через React Query хуки
 * (`useProducts`, `useProduct` и т.д.); дублировать её ещё и в
 * router-лоадерах значило бы получить два источника данных вместо
 * одного. Альтернатива — TanStack Router — даёт типобезопасные
 * параметры маршрута "из коробки", но это отдельная библиотека со
 * своей кривой обучения; для текущих двух маршрутов её возможности
 * не окупаются.
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
 * `ProductDetailPage` тоже не знает о роутере (принимает `productId`
 * пропом) — этот компонент превращает параметр URL в проп. `useParams`
 * типизирован как `string | undefined`; если `productId` вдруг
 * отсутствует (в норме такого не бывает при соответствии маршруту,
 * но тип этого не гарантирует), редиректим на каталог, а не рендерим
 * страницу с `undefined`.
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
 * Только два реальных маршрута на данный момент — витрина и карточка
 * товара (остальное: корзина/чекаут/админка — ещё не реализованы как
 * страницы, добавятся сюда отдельными `<Route>` по мере готовности).
 */
export function AppRouter() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<CatalogRoute />} />
        <Route path="/products/:productId" element={<ProductDetailRoute />} />
        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </BrowserRouter>
  );
}
