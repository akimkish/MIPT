#!/usr/bin/env bash
#
# Реализует app/router.tsx (react-router-dom) и переключает app/App.tsx
# с временного useState-переключателя (из populate_app_entry.sh) на
# настоящие маршруты.
#
# Требует: npm install react-router-dom (не устанавливается этим скриптом).
#
# Запускать ПОСЛЕ populate_app_entry.sh, ИЗ КОРНЯ РЕПОЗИТОРИЯ:
#
#   ./populate_router.sh
#
# Идемпотентен: `cat > file` полностью перезаписывает app/router.tsx и
# app/App.tsx (последний — намеренно: временная реализация из
# populate_app_entry.sh заменяется этим скриптом на постоянную).

set -euo pipefail

if [[ ! -f "frontend/src/app/App.tsx" ]]; then
  echo "Ошибка: app/App.tsx не найден." >&2
  echo "Сначала выполните populate_app_entry.sh (и всё, что перед ним)." >&2
  exit 1
fi

SRC="frontend/src"

# ============================================================================
# app/router.tsx
# ============================================================================
cat > "$SRC/app/router.tsx" << 'EOF'
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
  border: '1px solid var(--color-border)',
  borderRadius: 'var(--radius-sm)',
  background: 'var(--color-surface)',
  color: 'var(--color-text)',
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
EOF

# ============================================================================
# app/App.tsx — заменяем временный useState-переключатель на AppRouter
# ============================================================================
cat > "$SRC/app/App.tsx" << 'EOF'
import { AppRouter } from './router';
import { Providers } from './providers';

/**
 * Корневой компонент приложения: провайдеры верхнего уровня + роутинг.
 *
 * Временный `useState`-переключатель между каталогом и карточкой товара
 * (из предыдущего шага) заменён на настоящие маршруты `AppRouter` —
 * `CatalogPage`/`ProductDetailPage` при этом не изменились, они были
 * спроектированы без прямой зависимости от роутера именно ради такой
 * безболезненной замены.
 */
export function App() {
  return (
    <Providers>
      <AppRouter />
    </Providers>
  );
}
EOF

echo "app/router.tsx реализован, app/App.tsx переключён на реальные маршруты."
echo
echo "Не забудьте: npm install react-router-dom"
echo
echo "Доступные маршруты:"
echo "  /                    — каталог"
echo "  /products/:productId — карточка товара"