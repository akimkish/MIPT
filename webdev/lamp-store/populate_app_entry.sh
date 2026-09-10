#!/usr/bin/env bash
#
# Создаёt точку входа приложения:
#   - src/main.tsx — монтирует React в DOM, импортирует styles/tokens.css
#   - app/App.tsx — оборачивает дерево в <Providers>, временно (без роутера)
#     переключает между CatalogPage и ProductDetailPage через useState
#
# ВНИМАНИЕ: если frontend/src/main.tsx уже существует (обычно создаётся
# автоматически `npm create vite`), этот скрипт его ПЕРЕЗАПИШЕТ — как и
# все предыдущие скрипты серии, он не проверяет существующее содержимое.
# Если там уже есть значимый код — сохраните его копию перед запуском.
#
# Запускать ПОСЛЕ всех предыдущих скриптов серии, ИЗ КОРНЯ РЕПОЗИТОРИЯ:
#
#   ./populate_app_entry.sh
#
# app/router.tsx этим скриптом НЕ создаётся — по договорённости в чате,
# это следующий отдельный шаг после подтверждения.

set -euo pipefail

if [[ ! -f "frontend/src/features/catalog/pages/CatalogPage.tsx" ]]; then
  echo "Ошибка: CatalogPage.tsx не найден." >&2
  echo "Сначала выполните все предыдущие скрипты серии по порядку." >&2
  exit 1
fi

SRC="frontend/src"

# ============================================================================
# app/App.tsx
# ============================================================================
cat > "$SRC/app/App.tsx" << 'EOF'
import { useState } from 'react';
import { CatalogPage } from '../features/catalog/pages/CatalogPage';
import { ProductDetailPage } from '../features/product-detail/pages/ProductDetailPage';
import { Providers } from './providers';

/**
 * Временная навигация между каталогом и карточкой товара БЕЗ роутера.
 *
 * `app/router.tsx` ещё не реализован (следующий шаг по договорённости) —
 * этот `useState` только временно занимает его место, чтобы уже сейчас
 * можно было открыть карточку товара и вернуться назад. `CatalogPage` и
 * `ProductDetailPage` спроектированы без прямой зависимости от роутера
 * (принимают колбэк/id пропом) именно для того, чтобы эта замена была
 * безболезненной: когда появится `router.tsx`, здесь останутся только
 * настоящие маршруты `/` и `/products/:id`, а сами страницы не изменятся.
 */
function AppContent() {
  const [openProductId, setOpenProductId] = useState<string | null>(null);

  if (openProductId) {
    return (
      <>
        <button
          type="button"
          onClick={() => setOpenProductId(null)}
          style={{
            margin: 'var(--space-4)',
            padding: 'var(--space-2) var(--space-4)',
            border: '1px solid var(--color-border)',
            borderRadius: 'var(--radius-sm)',
            background: 'var(--color-surface)',
            cursor: 'pointer',
            font: 'inherit',
          }}
        >
          ← Назад в каталог
        </button>
        <ProductDetailPage productId={openProductId} />
      </>
    );
  }

  return <CatalogPage onOpenProduct={setOpenProductId} />;
}

/** Корневой компонент приложения: провайдеры верхнего уровня + контент. */
export function App() {
  return (
    <Providers>
      <AppContent />
    </Providers>
  );
}
EOF

# ============================================================================
# src/main.tsx
# ============================================================================
cat > "$SRC/main.tsx" << 'EOF'
import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { App } from './app/App';
import './styles/tokens.css';

const rootElement = document.getElementById('root');

if (!rootElement) {
  throw new Error('Не найден элемент #root — проверьте frontend/index.html');
}

createRoot(rootElement).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
EOF

echo "Точка входа создана: src/main.tsx + app/App.tsx (обёрнут в <Providers>)."
echo
echo "Проверьте frontend/index.html — там должен быть:"
echo '  <div id="root"></div>'
echo '  <script type="module" src="/src/main.tsx"></script>'