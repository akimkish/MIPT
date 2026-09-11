import { useQuery } from '@tanstack/react-query';
import { getManufacturers } from '../../../api/productsApi';
import { queryKeys } from '../../../lib/queryKeys';
import type { PageParams } from '../../../types/common';

/**
 * Загружает список активных производителей для фильтра витрины.
 *
 * @param params - Пагинация (limit/offset).
 * @returns Результат React Query с `Paginated<Manufacturer>` в `data`.
 */
export function useManufacturers(params: PageParams = {}) {
  return useQuery({
    queryKey: queryKeys.manufacturers.publicList(params),
    queryFn: () => getManufacturers(params),
    staleTime: 5 * 60 * 1000,
  });
}
