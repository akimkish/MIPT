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
   * конкретный роутер — `app/router.tsx` подставляет сюда навигацию.
   */
  onOpenProduct?: (productId: string) => void;
}

/**
 * Страница витрины: тёмная "панель управления" сверху (заголовок,
 * счётчик товаров, фильтры единым блоком) и светлая зона с сеткой
 * товаров-бирок ниже — единственный сильный цветовой контраст на
 * странице, всё остальное сознательно сдержанное.
 *
 * Состояние фильтров живёт в `useState`, а не синхронизируется с URL —
 * осознанное упрощение этого шага (см. историю чата).
 *
 * @param onOpenProduct - Колбэк перехода на страницу товара.
 */
export function CatalogPage({ onOpenProduct }: CatalogPageProps) {
  const [filters, setFilters] = useState<ProductFilters>({ limit: PAGE_SIZE, offset: 0 });

  const categoriesQuery = useCategories({ limit: 100 });
  const manufacturersQuery = useManufacturers({ limit: 100 });
  const productsQuery = useProducts(filters);

  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <div className={styles.headerInner}>
          <h1 className={styles.heading}>Каталог ламп</h1>
          {/* \u00A0 (неразрывный пробел) держит высоту строки постоянной,
              пока total ещё не загружен — без этого разметка дёргается. */}
          <p className={styles.subheading}>{productsQuery.data ? `${productsQuery.data.total} товаров` : '\u00A0'}</p>

          <CatalogFilters
            filters={filters}
            onChange={setFilters}
            categories={categoriesQuery.data?.items ?? []}
            manufacturers={manufacturersQuery.data?.items ?? []}
          />
        </div>
      </header>

      <div className={styles.content}>
        {productsQuery.isLoading && <p className={styles.status}>Загружаем каталог…</p>}

        {productsQuery.isError && (
          <div className={styles.error}>
            <p>Каталог не загрузился.</p>
            <button type="button" className={styles.retryButton} onClick={() => productsQuery.refetch()}>
              Повторить
            </button>
          </div>
        )}

        {productsQuery.data && productsQuery.data.items.length === 0 && (
          <p className={styles.empty}>Ничего не нашлось. Попробуйте снять часть фильтров.</p>
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
    </div>
  );
}
