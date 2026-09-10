import { keepPreviousData, useQuery } from '@tanstack/react-query';
import { getProducts } from '../../../api/productsApi';
import { queryKeys } from '../../../lib/queryKeys';
import type { ProductFilters } from '../../../types/product';

/**
 * Загружает страницу витрины с учётом фильтров.
 *
 * `placeholderData: keepPreviousData` оставляет предыдущую страницу
 * на экране, пока грузится следующая (смена фильтра/страницы) — без
 * этого список на миг мигает пустым/лоадером при каждом клике.
 *
 * @param filters - Фильтры и пагинация каталога.
 * @returns Результат React Query с `Paginated<ProductCatalogItem>` в `data`.
 */
export function useProducts(filters: ProductFilters = {}) {
  return useQuery({
    queryKey: queryKeys.products.list(filters),
    queryFn: () => getProducts(filters),
    placeholderData: keepPreviousData,
  });
}
