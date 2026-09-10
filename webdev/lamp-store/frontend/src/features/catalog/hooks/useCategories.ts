import { useQuery } from '@tanstack/react-query';
import { getCategories } from '../../../api/productsApi';
import { queryKeys } from '../../../lib/queryKeys';
import type { PageParams } from '../../../types/common';

/**
 * Загружает список активных категорий для фильтра витрины.
 *
 * @param params - Пагинация (limit/offset). По умолчанию бэкенд отдаёт
 *   первые 20 — для выпадающего списка фильтра этого обычно достаточно.
 * @returns Результат React Query с `Paginated<Category>` в `data`.
 */
export function useCategories(params: PageParams = {}) {
  return useQuery({
    queryKey: queryKeys.categories.publicList(params),
    queryFn: () => getCategories(params),
    staleTime: 5 * 60 * 1000, // категории меняются редко — 5 минут кэша достаточно
  });
}
