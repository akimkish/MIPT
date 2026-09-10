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
