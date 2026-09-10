#!/usr/bin/env bash
#
# Наполняет компонентами и страницами фичи catalog и product-detail —
# первый (базовый) срез UI, по решению из чата: сначала каталог + карточка
# товара, остальное (корзина/чекаут/админка) — отдельными шагами позже.
#
# Заодно реализует lib/money.ts, lib/constants.ts, app/providers.tsx
# (нужны компонентам) и добавляет НОВУЮ папку styles/ с токенами дизайна —
# её не было в структуре шага 1, это осознанное дополнение (см. пояснение
# в чате).
#
# Запускать ПОСЛЕ create_frontend_structure.sh, populate_api_and_types.sh
# и populate_hooks_and_stores.sh — ИЗ КОРНЯ РЕПОЗИТОРИЯ:
#
#   ./populate_catalog_and_product_components.sh
#
# Идемпотентен: каждый `cat > file` полностью перезаписывает файл.

set -euo pipefail

if [[ ! -d "frontend/src/features/catalog/hooks" ]]; then
  echo "Ошибка: структура фронтенда не найдена или неполная." >&2
  echo "Сначала выполните по порядку: create_frontend_structure.sh," >&2
  echo "populate_api_and_types.sh, populate_hooks_and_stores.sh." >&2
  exit 1
fi

SRC="frontend/src"

mkdir -p "$SRC/styles"

# ============================================================================
# styles/tokens.css
# ============================================================================
cat > "$SRC/styles/tokens.css" << 'EOF'
/**
 * Design-токены проекта.
 *
 * Идея: магазин ламп — тема "свет в тёмной комнате". Тёплый жёлтый акцент
 * (свет лампы накаливания) на нейтральном фоне вместо дефолтного тёплого
 * крема с терракотой или чёрного с неоном — эти две палитры считаются
 * "типичными для генеративного дизайна" и сюда взяты намеренно не были.
 *
 * ВАЖНО ДЛЯ ИНТЕГРАЦИИ: этот файл нужно импортировать один раз в точке
 * входа приложения (src/main.tsx) или в app/App.tsx:
 *   import './styles/tokens.css';
 * Компоненты ниже используют CSS Modules и ссылаются на переменные
 * отсюда через var(--...) — без этого импорта они не увидят значений.
 */
:root {
  --color-bg: #14151a;
  --color-surface: #ffffff;
  --color-surface-muted: #f3f1ec;
  --color-text: #1b1a17;
  --color-text-muted: #6b6559;
  --color-text-inverse: #f4f1e8;
  --color-border: #e4e0d4;
  --color-accent: #f0a721;
  --color-accent-dim: #c98a12;
  --color-danger: #b3432d;
  --color-success: #3f7d55;

  --font-sans:
    'Inter', system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif;

  --radius-sm: 6px;
  --radius-md: 10px;

  --space-1: 4px;
  --space-2: 8px;
  --space-3: 12px;
  --space-4: 16px;
  --space-5: 20px;
  --space-6: 24px;
  --space-8: 32px;
}
EOF

# ============================================================================
# lib/money.ts
# ============================================================================
cat > "$SRC/lib/money.ts" << 'EOF'
/**
 * Форматирует Decimal-строку с бэкенда в отображаемую цену.
 *
 * Для отображения намеренно используем `Number` — точности `double`
 * достаточно для форматирования суммы в UI (цены ламп далеки от границ
 * точности числа с плавающей запятой). Вся денежная АРИФМЕТИКА (скидки,
 * итоговые суммы заказа) остаётся на бэкенде и никогда не идёт через
 * JS `number` — эта функция только меняет форму отображения готового
 * значения, не пересчитывает его.
 *
 * @param value - Цена в виде строки, например "1234.5".
 * @param currency - Код валюты ISO 4217.
 *   ДОПУЩЕНИЕ: валюта проекта нигде явно не зафиксирована в
 *   project_context — по умолчанию взят рубль. Поменять на месте, если
 *   магазин работает в другой валюте.
 * @returns Отформатированная строка, например "1 234,50 ₽". Если `value`
 *   не парсится как число, возвращает исходную строку как есть — лучше
 *   показать сырое значение, чем "NaN ₽".
 */
export function formatMoney(value: string, currency = 'RUB'): string {
  const amount = Number(value);
  if (Number.isNaN(amount)) return value;

  return new Intl.NumberFormat('ru-RU', {
    style: 'currency',
    currency,
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(amount);
}
EOF

# ============================================================================
# lib/constants.ts
# ============================================================================
cat > "$SRC/lib/constants.ts" << 'EOF'
import type { SocketType } from '../types/enums';

/** Человекочитаемые подписи типов цоколя — для селектов фильтра и карточки товара. */
export const SOCKET_TYPE_LABELS: Record<SocketType, string> = {
  E14: 'E14 (миньон)',
  E27: 'E27 (стандартный)',
  E40: 'E40 (промышленный)',
  G4: 'G4',
  G9: 'G9',
  G13: 'G13 (трубчатый)',
  GU10: 'GU10',
  'GU5.3': 'GU5.3',
};
EOF

# ============================================================================
# app/providers.tsx
# ============================================================================
cat > "$SRC/app/providers.tsx" << 'EOF'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import type { ReactNode } from 'react';

/**
 * Единственный QueryClient на всё приложение.
 *
 * Создаётся модульной константой, а не через `useState` внутри
 * компонента — иначе он пересоздавался бы при каждом ре-рендере
 * `Providers` вместе со всем накопленным кэшем.
 */
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1, // дефолт React Query — 3 повтора — слишком долго держит спиннер при реальном сбое
      staleTime: 30 * 1000,
    },
  },
});

interface ProvidersProps {
  children: ReactNode;
}

/** Оборачивает приложение всеми контекст-провайдерами верхнего уровня. */
export function Providers({ children }: ProvidersProps) {
  return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
}
EOF

# ============================================================================
# features/catalog/components/ProductCard.*
# ============================================================================
cat > "$SRC/features/catalog/components/ProductCard.module.css" << 'EOF'
.card {
  display: flex;
  flex-direction: column;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  overflow: hidden;
  cursor: pointer;
  transition: box-shadow 0.15s ease, border-color 0.15s ease;
}

.card:hover,
.card:focus-visible {
  border-color: var(--color-accent);
  box-shadow: 0 0 0 3px rgba(240, 167, 33, 0.18);
}

.imageWrap {
  aspect-ratio: 4 / 3;
  background: var(--color-surface-muted);
}

.image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.imagePlaceholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-text-muted);
  font-size: 0.875rem;
}

.body {
  padding: var(--space-4);
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.title {
  margin: 0;
  font-size: 1rem;
  font-weight: 600;
  color: var(--color-text);
}

.meta {
  margin: 0;
  font-size: 0.8125rem;
  color: var(--color-text-muted);
}

.priceRow {
  display: flex;
  align-items: baseline;
  gap: var(--space-2);
  margin-top: var(--space-1);
}

.price {
  font-size: 1.125rem;
  font-weight: 700;
  color: var(--color-text);
}

.hint {
  font-size: 0.75rem;
  color: var(--color-accent-dim);
}

.addButton {
  margin-top: var(--space-2);
  padding: var(--space-2) var(--space-3);
  border: none;
  border-radius: var(--radius-sm);
  background: var(--color-accent);
  color: var(--color-text);
  font-weight: 600;
  cursor: pointer;
}

.addButton:hover:not(:disabled) {
  background: var(--color-accent-dim);
}

.addButton:disabled {
  background: var(--color-surface-muted);
  color: var(--color-text-muted);
  cursor: not-allowed;
}
EOF

cat > "$SRC/features/catalog/components/ProductCard.tsx" << 'EOF'
import type { MouseEvent } from 'react';
import { SOCKET_TYPE_LABELS } from '../../../lib/constants';
import { formatMoney } from '../../../lib/money';
import type { ProductCatalogItem } from '../../../types/product';
import { useCart } from '../../cart/hooks/useCart';
import styles from './ProductCard.module.css';

interface ProductCardProps {
  product: ProductCatalogItem;
  /** Открыть карточку товара. Необязателен: без него карточка не кликабельна. */
  onOpen?: (productId: string) => void;
}

/**
 * Карточка товара в сетке витрины.
 *
 * "В корзину" добавляет 1 штуку сразу, без диалога выбора количества —
 * количество можно изменить прямо в корзине. Товар без остатка
 * (`quantity === 0`) показывает подпись "Нет в наличии" вместо кнопки:
 * снятый с продажи (`is_active=false`) товар витрина вообще не покажет,
 * а вот видимый товар с нулевым остатком — обычная ситуация (раскупили,
 * админ ещё не деактивировал), это разные вещи.
 *
 * @param product - Элемент витрины с уже посчитанной ценой по акциям.
 * @param onOpen - Колбэк перехода на страницу товара.
 */
export function ProductCard({ product, onOpen }: ProductCardProps) {
  const { addItem } = useCart();
  const outOfStock = product.quantity === 0;

  function handleAddToCart(event: MouseEvent) {
    event.stopPropagation(); // не открывать карточку товара кликом по кнопке
    addItem({
      productId: product.product_id,
      productName: product.product_name,
      sku: product.sku,
      imageUrl: product.image_url,
      unitPrice: product.display_price,
    });
  }

  return (
    <article
      className={styles.card}
      onClick={() => onOpen?.(product.product_id)}
      role={onOpen ? 'button' : undefined}
      tabIndex={onOpen ? 0 : undefined}
    >
      <div className={styles.imageWrap}>
        {product.image_url ? (
          <img src={product.image_url} alt={product.product_name} className={styles.image} />
        ) : (
          <div className={styles.imagePlaceholder} aria-hidden="true">
            {SOCKET_TYPE_LABELS[product.socket_type]}
          </div>
        )}
      </div>

      <div className={styles.body}>
        <h3 className={styles.title}>{product.product_name}</h3>
        <p className={styles.meta}>
          {SOCKET_TYPE_LABELS[product.socket_type]} · {product.power_watts} Вт ·{' '}
          {product.color_temperature_k} К
        </p>

        <div className={styles.priceRow}>
          <span className={styles.price}>{formatMoney(product.display_price)}</span>
          {product.bulk_discount_hint && <span className={styles.hint}>{product.bulk_discount_hint}</span>}
        </div>

        <button type="button" className={styles.addButton} disabled={outOfStock} onClick={handleAddToCart}>
          {outOfStock ? 'Нет в наличии' : 'В корзину'}
        </button>
      </div>
    </article>
  );
}
EOF

# ============================================================================
# features/catalog/components/CatalogFilters.*
# ============================================================================
cat > "$SRC/features/catalog/components/CatalogFilters.module.css" << 'EOF'
.panel {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-3);
  align-items: center;
  padding: var(--space-4);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  margin-bottom: var(--space-6);
}

.search {
  flex: 1 1 220px;
  padding: var(--space-2) var(--space-3);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  font: inherit;
}

.select {
  padding: var(--space-2) var(--space-3);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  font: inherit;
  background: var(--color-surface);
}

.priceRange {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.priceInput {
  width: 96px;
  padding: var(--space-2) var(--space-3);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  font: inherit;
}

.priceDash {
  color: var(--color-text-muted);
}

.checkbox {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: 0.875rem;
  color: var(--color-text);
  white-space: nowrap;
}
EOF

cat > "$SRC/features/catalog/components/CatalogFilters.tsx" << 'EOF'
import type { ChangeEvent } from 'react';
import { SOCKET_TYPE_LABELS } from '../../../lib/constants';
import type { Category } from '../../../types/category';
import type { SocketType } from '../../../types/enums';
import type { Manufacturer } from '../../../types/manufacturer';
import type { ProductFilters } from '../../../types/product';
import styles from './CatalogFilters.module.css';

interface CatalogFiltersProps {
  filters: ProductFilters;
  onChange: (filters: ProductFilters) => void;
  categories: Category[];
  manufacturers: Manufacturer[];
}

const SOCKET_TYPES = Object.keys(SOCKET_TYPE_LABELS) as SocketType[];

/**
 * Панель фильтров каталога.
 *
 * Каждое изменение сразу уходит наружу через `onChange`, без отдельной
 * кнопки "Применить" — на масштабе учебного магазина лишний шаг только
 * замедляет пользователя (запросы не настолько частые, чтобы требовался
 * дебаунс — если станут, это отдельная точечная правка здесь).
 *
 * Смена ЛЮБОГО фильтра, кроме листания страниц, сбрасывает `offset` на 0 —
 * иначе легко залипнуть на пустой странице после того, как фильтр сузил
 * выборку сильнее, чем было заказано страниц.
 *
 * @param filters - Текущие значения фильтров (управляемый компонент).
 * @param onChange - Вызывается с новым набором фильтров при любом изменении.
 * @param categories - Список категорий для выпадающего списка.
 * @param manufacturers - Список производителей для выпадающего списка.
 */
export function CatalogFilters({ filters, onChange, categories, manufacturers }: CatalogFiltersProps) {
  function update(patch: Partial<ProductFilters>) {
    onChange({ ...filters, ...patch, offset: 0 });
  }

  function handleSearch(event: ChangeEvent<HTMLInputElement>) {
    update({ search: event.target.value || undefined });
  }

  return (
    <div className={styles.panel}>
      <input
        type="search"
        className={styles.search}
        placeholder="Найти лампу по названию"
        value={filters.search ?? ''}
        onChange={handleSearch}
      />

      <select
        className={styles.select}
        value={filters.category_id ?? ''}
        onChange={(e) => update({ category_id: e.target.value || undefined })}
      >
        <option value="">Все категории</option>
        {categories.map((c) => (
          <option key={c.category_id} value={c.category_id}>
            {c.name}
          </option>
        ))}
      </select>

      <select
        className={styles.select}
        value={filters.manufacturer_id ?? ''}
        onChange={(e) => update({ manufacturer_id: e.target.value || undefined })}
      >
        <option value="">Все производители</option>
        {manufacturers.map((m) => (
          <option key={m.manufacturer_id} value={m.manufacturer_id}>
            {m.name}
          </option>
        ))}
      </select>

      <select
        className={styles.select}
        value={filters.socket_type ?? ''}
        onChange={(e) => update({ socket_type: (e.target.value || undefined) as SocketType | undefined })}
      >
        <option value="">Любой цоколь</option>
        {SOCKET_TYPES.map((s) => (
          <option key={s} value={s}>
            {SOCKET_TYPE_LABELS[s]}
          </option>
        ))}
      </select>

      <div className={styles.priceRange}>
        <input
          type="number"
          min={0}
          inputMode="decimal"
          className={styles.priceInput}
          placeholder="Цена от"
          value={filters.min_price ?? ''}
          onChange={(e) => update({ min_price: e.target.value || undefined })}
        />
        <span className={styles.priceDash}>—</span>
        <input
          type="number"
          min={0}
          inputMode="decimal"
          className={styles.priceInput}
          placeholder="до"
          value={filters.max_price ?? ''}
          onChange={(e) => update({ max_price: e.target.value || undefined })}
        />
      </div>

      <label className={styles.checkbox}>
        <input
          type="checkbox"
          checked={filters.in_stock_only ?? false}
          onChange={(e) => update({ in_stock_only: e.target.checked || undefined })}
        />
        Только в наличии
      </label>
    </div>
  );
}
EOF

# ============================================================================
# features/catalog/components/Pagination.*
# ============================================================================
cat > "$SRC/features/catalog/components/Pagination.module.css" << 'EOF'
.wrap {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-4);
  margin-top: var(--space-8);
}

.button {
  padding: var(--space-2) var(--space-4);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: var(--color-surface);
  cursor: pointer;
  font: inherit;
}

.button:disabled {
  color: var(--color-text-muted);
  cursor: not-allowed;
  opacity: 0.6;
}

.status {
  font-size: 0.875rem;
  color: var(--color-text-muted);
}
EOF

cat > "$SRC/features/catalog/components/Pagination.tsx" << 'EOF'
import styles from './Pagination.module.css';

interface PaginationProps {
  limit: number;
  offset: number;
  total: number;
  onChange: (offset: number) => void;
}

/**
 * Постраничная навигация по `limit`/`offset` — форме пагинации, которую
 * реально отдаёт бэкенд (`PaginatedResponse`), а не по номеру страницы
 * с отдельным полем `page`.
 *
 * @param limit - Размер страницы.
 * @param offset - Текущее смещение.
 * @param total - Общее количество элементов (из ответа сервера).
 * @param onChange - Вызывается с новым `offset` при переходе на другую страницу.
 */
export function Pagination({ limit, offset, total, onChange }: PaginationProps) {
  const currentPage = Math.floor(offset / limit) + 1;
  const totalPages = Math.max(1, Math.ceil(total / limit));

  if (totalPages <= 1) return null;

  return (
    <div className={styles.wrap}>
      <button
        type="button"
        className={styles.button}
        disabled={offset === 0}
        onClick={() => onChange(Math.max(0, offset - limit))}
      >
        Назад
      </button>
      <span className={styles.status}>
        Страница {currentPage} из {totalPages}
      </span>
      <button
        type="button"
        className={styles.button}
        disabled={currentPage >= totalPages}
        onClick={() => onChange(offset + limit)}
      >
        Вперёд
      </button>
    </div>
  );
}
EOF

# ============================================================================
# features/catalog/pages/CatalogPage.*
# ============================================================================
cat > "$SRC/features/catalog/pages/CatalogPage.module.css" << 'EOF'
.page {
  max-width: 1120px;
  margin: 0 auto;
  padding: var(--space-8) var(--space-4);
}

.heading {
  margin: 0 0 var(--space-6);
  font-size: 1.75rem;
  color: var(--color-text);
}

.grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: var(--space-4);
}

.status,
.empty {
  color: var(--color-text-muted);
  padding: var(--space-6) 0;
  text-align: center;
}

.error {
  color: var(--color-danger);
  padding: var(--space-6) 0;
  text-align: center;
}
EOF

cat > "$SRC/features/catalog/pages/CatalogPage.tsx" << 'EOF'
import { useState } from 'react';
import type { ProductFilters } from '../../../types/product';
import { CatalogFilters } from '../components/CatalogFilters';
import { Pagination } from '../components/Pagination';
import { ProductCard } from '../components/ProductCard';
import { useCategories } from '../hooks/useCategories';
import { useManufacturers } from '../hooks/useManufacturers';
import { useProducts } from '../hooks/useProducts';
import styles from './CatalogPage.module.css';

const PAGE_SIZE = 20;

interface CatalogPageProps {
  /**
   * Переход на страницу товара. Страница намеренно не завязана на
   * конкретный роутер (react-router и т.п. ещё не подключены) — когда
   * появится `app/router.tsx`, сюда просто передадут функцию навигации.
   */
  onOpenProduct?: (productId: string) => void;
}

/**
 * Страница витрины: фильтры, сетка товаров и пагинация.
 *
 * Состояние фильтров живёт в `useState`, а не синхронизируется с URL —
 * упрощение для этого шага: без него фильтр сбрасывается при обновлении
 * страницы и им нельзя поделиться ссылкой. Если это понадобится, стоит
 * вынести фильтры в query-параметры при подключении роутера, а не менять
 * форму самих фильтров.
 */
export function CatalogPage({ onOpenProduct }: CatalogPageProps) {
  const [filters, setFilters] = useState<ProductFilters>({ limit: PAGE_SIZE, offset: 0 });

  const categoriesQuery = useCategories({ limit: 100 });
  const manufacturersQuery = useManufacturers({ limit: 100 });
  const productsQuery = useProducts(filters);

  return (
    <div className={styles.page}>
      <h1 className={styles.heading}>Каталог ламп</h1>

      <CatalogFilters
        filters={filters}
        onChange={setFilters}
        categories={categoriesQuery.data?.items ?? []}
        manufacturers={manufacturersQuery.data?.items ?? []}
      />

      {productsQuery.isLoading && <p className={styles.status}>Загружаем каталог…</p>}

      {productsQuery.isError && (
        <p className={styles.error}>Не удалось загрузить каталог. Попробуйте обновить страницу.</p>
      )}

      {productsQuery.data && productsQuery.data.items.length === 0 && (
        <p className={styles.empty}>По заданным фильтрам ничего не нашлось.</p>
      )}

      {productsQuery.data && productsQuery.data.items.length > 0 && (
        <>
          <div className={styles.grid}>
            {productsQuery.data.items.map((product) => (
              <ProductCard key={product.product_id} product={product} onOpen={onOpenProduct} />
            ))}
          </div>

          <Pagination
            limit={filters.limit ?? PAGE_SIZE}
            offset={filters.offset ?? 0}
            total={productsQuery.data.total}
            onChange={(offset) => setFilters((f) => ({ ...f, offset }))}
          />
        </>
      )}
    </div>
  );
}
EOF

# ============================================================================
# features/product-detail/components/ReviewList.*
# ============================================================================
cat > "$SRC/features/product-detail/components/ReviewList.module.css" << 'EOF'
.list {
  list-style: none;
  margin: 0 0 var(--space-6);
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.item {
  padding: var(--space-4);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-surface);
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-2);
}

.author {
  font-weight: 600;
  color: var(--color-text);
}

.rating {
  color: var(--color-accent-dim);
  letter-spacing: 1px;
}

.text {
  margin: 0;
  color: var(--color-text);
}

.empty {
  color: var(--color-text-muted);
  margin: 0 0 var(--space-6);
}
EOF

cat > "$SRC/features/product-detail/components/ReviewList.tsx" << 'EOF'
import type { Review } from '../../../types/review';
import styles from './ReviewList.module.css';

interface ReviewListProps {
  reviews: Review[];
}

/**
 * Список опубликованных отзывов товара.
 *
 * Модерация (одобрение/удаление) сюда не входит — она делается в
 * админке, эта версия компонента только читает и показывает.
 *
 * @param reviews - Опубликованные отзывы (`is_approved === true`).
 */
export function ReviewList({ reviews }: ReviewListProps) {
  if (reviews.length === 0) {
    return <p className={styles.empty}>Отзывов пока нет — будьте первым.</p>;
  }

  return (
    <ul className={styles.list}>
      {reviews.map((review) => (
        <li key={review.review_id} className={styles.item}>
          <div className={styles.header}>
            <span className={styles.author}>{review.user_name}</span>
            <span className={styles.rating} aria-label={`Оценка ${review.rating} из 5`}>
              {'★'.repeat(review.rating)}
              {'☆'.repeat(5 - review.rating)}
            </span>
          </div>
          {review.description && <p className={styles.text}>{review.description}</p>}
        </li>
      ))}
    </ul>
  );
}
EOF

# ============================================================================
# features/product-detail/components/ReviewForm.*
# ============================================================================
cat > "$SRC/features/product-detail/components/ReviewForm.module.css" << 'EOF'
.form {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
  padding: var(--space-4);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-surface);
  max-width: 480px;
}

.heading {
  margin: 0;
  font-size: 1.125rem;
  color: var(--color-text);
}

.field {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
  font-size: 0.875rem;
  color: var(--color-text);
}

.field input,
.field select,
.field textarea {
  padding: var(--space-2) var(--space-3);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  font: inherit;
  resize: vertical;
}

.submit {
  align-self: flex-start;
  padding: var(--space-2) var(--space-4);
  border: none;
  border-radius: var(--radius-sm);
  background: var(--color-accent);
  color: var(--color-text);
  font-weight: 600;
  cursor: pointer;
}

.submit:hover:not(:disabled) {
  background: var(--color-accent-dim);
}

.submit:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.success {
  padding: var(--space-4);
  border: 1px solid var(--color-success);
  border-radius: var(--radius-md);
  color: var(--color-success);
  max-width: 480px;
}

.error {
  color: var(--color-danger);
  font-size: 0.875rem;
  margin: 0;
}
EOF

cat > "$SRC/features/product-detail/components/ReviewForm.tsx" << 'EOF'
import { useState } from 'react';
import type { FormEvent } from 'react';
import { useCreateReview } from '../hooks/useCreateReview';
import styles from './ReviewForm.module.css';

interface ReviewFormProps {
  productId: string;
}

/**
 * Форма отправки отзыва на товар.
 *
 * Без аутентификации — только имя и email для связи (аккаунтов
 * покупателей в проекте нет, см. project_context). Отзыв уходит на
 * модерацию (`is_approved=false` по умолчанию) и не появляется в списке
 * сразу — форма явно сообщает об этом после отправки, чтобы не выглядело
 * так, будто отзыв потерялся.
 *
 * @param productId - Идентификатор товара, к которому относится отзыв.
 */
export function ReviewForm({ productId }: ReviewFormProps) {
  const [userName, setUserName] = useState('');
  const [userEmail, setUserEmail] = useState('');
  const [description, setDescription] = useState('');
  const [rating, setRating] = useState(5);

  const createReview = useCreateReview(productId);

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    createReview.mutate(
      { product_id: productId, user_name: userName, user_email: userEmail, description, rating },
      {
        onSuccess: () => {
          setUserName('');
          setUserEmail('');
          setDescription('');
          setRating(5);
        },
      },
    );
  }

  if (createReview.isSuccess) {
    return (
      <p className={styles.success}>
        Спасибо! Отзыв отправлен и появится на странице после проверки модератором.
      </p>
    );
  }

  return (
    <form className={styles.form} onSubmit={handleSubmit}>
      <h3 className={styles.heading}>Оставить отзыв</h3>

      <label className={styles.field}>
        Имя
        <input type="text" required maxLength={100} value={userName} onChange={(e) => setUserName(e.target.value)} />
      </label>

      <label className={styles.field}>
        Email
        <input
          type="email"
          required
          maxLength={255}
          value={userEmail}
          onChange={(e) => setUserEmail(e.target.value)}
        />
      </label>

      <label className={styles.field}>
        Оценка
        <select value={rating} onChange={(e) => setRating(Number(e.target.value))}>
          {[5, 4, 3, 2, 1].map((n) => (
            <option key={n} value={n}>
              {n} {n === 1 ? 'звезда' : n < 5 ? 'звезды' : 'звёзд'}
            </option>
          ))}
        </select>
      </label>

      <label className={styles.field}>
        Отзыв
        <textarea rows={4} value={description} onChange={(e) => setDescription(e.target.value)} />
      </label>

      {createReview.isError && <p className={styles.error}>Не получилось отправить отзыв: {createReview.error.message}</p>}

      <button type="submit" className={styles.submit} disabled={createReview.isPending}>
        {createReview.isPending ? 'Отправляем…' : 'Отправить отзыв'}
      </button>
    </form>
  );
}
EOF

# ============================================================================
# features/product-detail/pages/ProductDetailPage.*
# ============================================================================
cat > "$SRC/features/product-detail/pages/ProductDetailPage.module.css" << 'EOF'
.page {
  max-width: 1120px;
  margin: 0 auto;
  padding: var(--space-8) var(--space-4);
}

.layout {
  display: grid;
  grid-template-columns: minmax(280px, 420px) 1fr;
  gap: var(--space-8);
}

@media (max-width: 720px) {
  .layout {
    grid-template-columns: 1fr;
  }
}

.imageWrap {
  aspect-ratio: 4 / 3;
  background: var(--color-surface-muted);
  border-radius: var(--radius-md);
  overflow: hidden;
}

.image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.imagePlaceholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-text-muted);
}

.info {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.breadcrumb {
  margin: 0;
  font-size: 0.8125rem;
  color: var(--color-text-muted);
}

.title {
  margin: 0;
  font-size: 1.75rem;
  color: var(--color-text);
}

.rating {
  color: var(--color-accent-dim);
  letter-spacing: 1px;
  margin: 0;
}

.ratingValue {
  margin-left: var(--space-2);
  color: var(--color-text-muted);
  letter-spacing: normal;
}

.specs {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--space-2) var(--space-4);
  margin: var(--space-3) 0;
}

.specs dt {
  font-size: 0.75rem;
  color: var(--color-text-muted);
}

.specs dd {
  margin: 0;
  font-size: 0.9375rem;
  color: var(--color-text);
}

.description {
  color: var(--color-text);
  line-height: 1.5;
}

.priceBlock {
  display: flex;
  align-items: baseline;
  gap: var(--space-3);
  margin-top: var(--space-2);
}

.price {
  font-size: 1.75rem;
  font-weight: 700;
  color: var(--color-text);
}

.hint {
  color: var(--color-accent-dim);
  font-size: 0.875rem;
}

.addRow {
  display: flex;
  gap: var(--space-3);
  margin-top: var(--space-3);
}

.quantityInput {
  width: 72px;
  padding: var(--space-2) var(--space-3);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  font: inherit;
}

.addButton {
  padding: var(--space-2) var(--space-6);
  border: none;
  border-radius: var(--radius-sm);
  background: var(--color-accent);
  color: var(--color-text);
  font-weight: 600;
  cursor: pointer;
}

.addButton:hover {
  background: var(--color-accent-dim);
}

.outOfStock {
  color: var(--color-danger);
  font-weight: 600;
  margin-top: var(--space-3);
}

.reviewsSection {
  margin-top: var(--space-8);
  padding-top: var(--space-8);
  border-top: 1px solid var(--color-border);
}

.reviewsHeading {
  margin: 0 0 var(--space-4);
  font-size: 1.375rem;
  color: var(--color-text);
}

.status {
  color: var(--color-text-muted);
}

.error {
  color: var(--color-danger);
}
EOF

cat > "$SRC/features/product-detail/pages/ProductDetailPage.tsx" << 'EOF'
import { useState } from 'react';
import { SOCKET_TYPE_LABELS } from '../../../lib/constants';
import { formatMoney } from '../../../lib/money';
import { useCart } from '../../cart/hooks/useCart';
import { ReviewForm } from '../components/ReviewForm';
import { ReviewList } from '../components/ReviewList';
import { useProduct } from '../hooks/useProduct';
import { useProductReviews } from '../hooks/useProductReviews';
import styles from './ProductDetailPage.module.css';

interface ProductDetailPageProps {
  productId: string;
}

/**
 * Страница товара: изображение, характеристики, цена с учётом акций,
 * добавление в корзину, отзывы и форма нового отзыва.
 *
 * `productId` передаётся пропом, а не читается из `useParams` внутри
 * компонента — страница не завязана на конкретный роутер, пока
 * `app/router.tsx` не реализован; подстановка id из URL — забота
 * вызывающего кода (когда появится роутинг).
 *
 * @param productId - Идентификатор товара.
 */
export function ProductDetailPage({ productId }: ProductDetailPageProps) {
  const [quantity, setQuantity] = useState(1);
  const { addItem } = useCart();

  const productQuery = useProduct(productId);
  const reviewsQuery = useProductReviews(productId, { limit: 20 });

  if (productQuery.isLoading) {
    return <p className={styles.status}>Загружаем товар…</p>;
  }

  if (productQuery.isError || !productQuery.data) {
    return <p className={styles.error}>Товар не найден или временно недоступен.</p>;
  }

  const product = productQuery.data;
  const outOfStock = product.quantity === 0;
  const maxQuantity = Math.max(1, product.quantity);
  const roundedRating =
    product.average_rating !== null ? Math.round(product.average_rating) : null;

  function handleAddToCart() {
    addItem(
      {
        productId: product.product_id,
        productName: product.product_name,
        sku: product.sku,
        imageUrl: product.image_url,
        unitPrice: product.display_price,
      },
      quantity,
    );
  }

  return (
    <div className={styles.page}>
      <div className={styles.layout}>
        <div className={styles.imageWrap}>
          {product.image_url ? (
            <img src={product.image_url} alt={product.product_name} className={styles.image} />
          ) : (
            <div className={styles.imagePlaceholder} aria-hidden="true">
              {SOCKET_TYPE_LABELS[product.socket_type]}
            </div>
          )}
        </div>

        <div className={styles.info}>
          <p className={styles.breadcrumb}>
            {product.category.name} · {product.manufacturer.name}
          </p>
          <h1 className={styles.title}>{product.product_name}</h1>

          {product.average_rating !== null && roundedRating !== null && (
            <p className={styles.rating} aria-label={`Средняя оценка ${product.average_rating.toFixed(1)} из 5`}>
              {'★'.repeat(roundedRating)}
              {'☆'.repeat(5 - roundedRating)}
              <span className={styles.ratingValue}>{product.average_rating.toFixed(1)}</span>
            </p>
          )}

          <dl className={styles.specs}>
            <div>
              <dt>Цоколь</dt>
              <dd>{SOCKET_TYPE_LABELS[product.socket_type]}</dd>
            </div>
            <div>
              <dt>Мощность</dt>
              <dd>{product.power_watts} Вт</dd>
            </div>
            <div>
              <dt>Цветовая температура</dt>
              <dd>{product.color_temperature_k} К</dd>
            </div>
            <div>
              <dt>Артикул</dt>
              <dd>{product.sku}</dd>
            </div>
          </dl>

          {product.description && <p className={styles.description}>{product.description}</p>}

          <div className={styles.priceBlock}>
            <span className={styles.price}>{formatMoney(product.display_price)}</span>
            {product.bulk_discount_hint && <span className={styles.hint}>{product.bulk_discount_hint}</span>}
          </div>

          {outOfStock ? (
            <p className={styles.outOfStock}>Нет в наличии</p>
          ) : (
            <div className={styles.addRow}>
              <input
                type="number"
                min={1}
                max={maxQuantity}
                value={quantity}
                onChange={(e) => setQuantity(Math.min(maxQuantity, Math.max(1, Number(e.target.value))))}
                className={styles.quantityInput}
              />
              <button type="button" className={styles.addButton} onClick={handleAddToCart}>
                В корзину
              </button>
            </div>
          )}
        </div>
      </div>

      <section className={styles.reviewsSection}>
        <h2 className={styles.reviewsHeading}>Отзывы</h2>
        {reviewsQuery.isLoading && <p className={styles.status}>Загружаем отзывы…</p>}
        {reviewsQuery.data && <ReviewList reviews={reviewsQuery.data.items} />}
        <ReviewForm productId={productId} />
      </section>
    </div>
  );
}
EOF

echo "Компоненты и страницы catalog + product-detail созданы."
echo
echo "ВАЖНО ДЛЯ ЗАПУСКА:"
echo "1. Импортировать один раз глобально: import './styles/tokens.css';"
echo "   (в src/main.tsx или app/App.tsx — какой из них у вас точка входа)."
echo "2. Обернуть дерево компонентов в <Providers> из app/providers.tsx —"
echo "   без него хуки useQuery/useMutation не будут работать."
echo "3. npm install @tanstack/react-query zustand — если ещё не установлены."